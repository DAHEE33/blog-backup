# [TroubleShooting]공연 등록 API 타임아웃과 비동기 처리 도입

**발행일:** Sun, 12 Apr 2026 23:18:37 +0900

**링크:** https://hee-story6.tistory.com/244

---

<h2>1. 배경</h2>
<p>관리자 화면에서 공연을 등록할 때, 회차나 이미지가 늘어나면 클라이언트에서 30초 타임아웃이 발생했다.</p>
<p>서버 로그와 DB를 확인해보니 S3 업로드와 DB 반영은 타임아웃 이후에도 계속 진행되어 결국 완료되는 경우가 있었다. 즉, <b>"요청은 실패로 보이는데 데이터는 들어가 있다"</b> 는 불일치 현상이 발생했고, 이를 해결하는 과정을 정리했다.</p>
<h2>2. 원인 정리</h2>
<h3>2.1 긴 요청 처리 시간</h3>
<p>createShow() 하나를 호출하면 아래 작업들이 <b>순차적으로, 하나의 트랜잭션 안에서</b> 실행되고 있었다.</p>
<div>
<div>
<pre class="java" id="code_1776003136896"><code>[단일 @Transactional 범위]
①  S3 포스터 업로드              &larr; 네트워크 I/O
②  DB: Show INSERT
③  S3 상세이미지 업로드 &times; N장    &larr; 네트워크 I/O &times; N (순차 처리 시 누적)
④  DB: ShowSchedule.save() &times; 회차 수   &larr; 개별 호출, N번 왕복
⑤  DB: ShowSeatGrade.save() &times; 구역 수  &larr; 개별 호출, M번 왕복
[트랜잭션 커밋]</code></pre>
</div>
</div>
<p>이 전체가 하나의 트랜잭션 안에서 돌아가면, S3 업로드를 기다리는 동안에도 DB 커넥션을 계속 붙잡고 있게 된다. 이미지가 4장 이상되거나, 공연 스케줄이 많아지면 상당한 시간이 누적됐다.</p>
<h3>2.2 클라이언트 타임아웃과의 불일치</h3>
<p>Axios에 고정 타임아웃(30초)이 설정되어 있으면, 서버가 아직 처리 중이어도 클라이언트만 먼저 연결을 끊는다. 그러나 <b>서버 스레드는 끊기지 않고 계속 동작</b>하므로 결국 DB 저장까지 완료된다.</p>
<p>이것이 "타임아웃인데 등록은 됐다"는 현상의 원인이었다.</p>
<p>타임아웃 값만 늘리는 건 임시방편에 불과하다. 사용자 경험과 운영 안정성 측면 모두에서 <b>응답을 빨리 돌려주고 무거운 작업은 뒤로 미루는 구조</b>로 가는 것이 맞다고 판단했다.</p>
<h2>3. 해결 방향</h2>
<h3>3.1 동기 구간 최소화 &mdash; 즉시 202 Accepted 반환</h3>
<p>DB에 "등록 진행 중(PROCESSING)" 상태만 먼저 저장하고, HTTP 응답은 즉시 반환했다. 무거운 작업(S3 업로드, 스케줄/좌석 생성)은 이후 비동기로 처리했다.</p>
<div>
<div>
<div>
<div>
<div>
<pre class="java" id="code_1776003213375"><code>POST /api/v1/admin/shows
   │
   ▼
① Show 저장 (processingStatus = PROCESSING)
② 202 Accepted + { showId } 즉시 반환
   │
   ▼ (비동기 시작)
③ S3 업로드 &rarr; DB 업데이트 &rarr; processingStatus = DONE</code></pre>
</div>
</div>
</div>
</div>
</div>
<h3>3.2 트랜잭션 커밋 이후 비동기 실행</h3>
<p>@Async를 트랜잭션 안에서 바로 호출하면, 외부 트랜잭션이 커밋되기 전에 비동기 스레드가 먼저 실행될 수 있다. 이 경우 비동기 스레드에서 showId로 조회해도 아직 DB에 레코드가 없는 레이스 컨디션이 발생한다.</p>
<p>TransactionSynchronization#afterCommit 훅을 사용하면 커밋이 확정된 이후에 비동기 작업을 시작할 수 있어 안전하다.</p>
<div>
<div>
<pre class="java" id="code_1776003243794"><code>// 잘못된 패턴: 커밋 전에 비동기 호출
@Transactional
public void createShow(...) {
    Show show = showRepository.save(newShow); // 아직 커밋 안 됨
    asyncService.doHeavyWork(show.getId());   // DB에 show가 없을 수 있음
}

// 올바른 패턴: 커밋 이후 비동기 트리거
TransactionSynchronizationManager.registerSynchronization(
    new TransactionSynchronization() {
        @Override
        public void afterCommit() {
            asyncService.doHeavyWork(show.getId()); // 커밋 확정 후 실행
        }
    }
);</code></pre>
</div>
</div>
<h3>3.3 MultipartFile과 비동기 경계</h3>
<p>MultipartFile은 HTTP 요청이 끝나면 임시 파일 스트림이 닫힌다. 비동기 스레드에서 그대로 사용하면 이미 닫힌 스트림에 접근하게 되어 예외가 발생할 수 있다. 비동기로 넘기기 전에 반드시 byte[] 등으로 내용을 복사해두어야 한다.</p>
<div>
<div>
<pre class="java" id="code_1776003285288"><code>// 요청 처리 시점에 미리 복사
byte[] posterBytes = poster.getBytes();
List&lt;byte[]&gt; detailBytes = detailImages.stream()
    .map(MultipartFile::getBytes)
    .toList();

// 복사된 데이터를 비동기 메서드에 전달
asyncService.doHeavyWork(show.getId(), posterBytes, detailBytes);</code></pre>
</div>
</div>
<h3>3.4 S3 병렬 업로드</h3>
<p>기존에는 포스터와 상세 이미지를 하나씩 순차적으로 업로드했다. CompletableFuture로 병렬화하면 이미지 장수와 관계없이 가장 느린 한 장의 업로드 시간만 걸린다.</p>
<div>
<div>
<pre class="java" id="code_1776003305230"><code>// 기존: 순차 업로드 (이미지 3장 = 3배 시간)
for (byte[] imageBytes : detailBytesList) {
    fileService.uploadBytes(imageBytes, "details");
}

// 개선: 병렬 업로드 (이미지 3장 = 가장 느린 1장 시간)
List&lt;CompletableFuture&lt;String&gt;&gt; futures = detailBytesList.stream()
    .map(bytes -&gt; CompletableFuture.supplyAsync(
        () -&gt; fileService.uploadBytes(bytes, "details"), uploadExecutor))
    .toList();

List&lt;String&gt; urls = futures.stream()
    .map(CompletableFuture::join)
    .toList();</code></pre>
</div>
</div>
<h3>3.5 배치 INSERT</h3>
<p>스케줄, 좌석 등급 등을 개별 save()로 호출하면 row 수만큼 DB 왕복이 발생한다. saveAll()과 Hibernate JDBC batch 설정을 함께 적용하면 여러 row를 한 번의 왕복으로 처리할 수 있다.</p>
<div>
<div>
<pre class="java" id="code_1776003317853"><code>// 기존: N번 DB 왕복
for (ScheduleRequest req : scheduleRequests) {
    showScheduleRepository.save(buildSchedule(req, show));
}

// 개선: 1번 DB 왕복
List&lt;ShowSchedule&gt; schedules = scheduleRequests.stream()
    .map(req -&gt; buildSchedule(req, show))
    .toList();
showScheduleRepository.saveAll(schedules);</code></pre>
</div>
</div>
<div>
<div>&nbsp;</div>
<div>
<pre class="ini" style="color: #eaecf0;"><code># application.properties &mdash; 이 설정이 없으면 saveAll()도 batch로 동작하지 않는다
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
spring.jpa.properties.hibernate.jdbc.batch_versioned_data=true</code></pre>
</div>
</div>
<blockquote>
<p>&nbsp;@GeneratedValue(strategy = IDENTITY) 전략은 Hibernate가 기본적으로 batch insert를 비활성화한다. 대량 INSERT가 필요한 엔티티는 SEQUENCE 전략으로 전환하는 것이 근본적인 해결이다.</p>
</blockquote>
<h3>3.6 처리 상태 필드 (processingStatus) 추가</h3>
<p>기존 ShowStatus(WAITING, ON_SALE, SOLD_OUT &hellip;)는 <b>비즈니스 상태</b>다. 비동기 처리가 완료됐는지를 나타내는 것은 <b>시스템 처리 상태</b>이므로 관심사가 다르다. Show 엔티티에 별도 컬럼으로 분리했다.</p>
<div>
<div>
<pre class="java" id="code_1776003339102"><code>@Enumerated(EnumType.STRING)
private ProcessingStatus processingStatus; // PROCESSING, DONE, FAILED</code></pre>
</div>
</div>
<p>관리자 목록&middot;상세 API 응답에 processingStatus를 포함시키면, 프론트엔드에서 "준비 중" 배지 표시, 클릭 제한, 폴링 등에 활용할 수 있다.</p>
<h2>4. 구현 시 주의한 점</h2>
<h3>실패 시 보상 처리</h3>
<p>비동기 메서드에서 발생한 예외는 일반 try-catch로 전파되지 않는다. 내부에서 반드시 잡아서 상태를 업데이트해야 한다.</p>
<div>
<div>
<pre class="java" id="code_1776003373874"><code>@Async
public void doHeavyWork(Long showId, byte[] posterBytes, List&lt;byte[]&gt; detailBytes) {
    try {
        // S3 업로드, 스케줄 생성, 좌석 생성 ...
        updateProcessingStatus(showId, ProcessingStatus.DONE);
    } catch (Exception e) {
        log.error("공연 등록 비동기 작업 실패: showId={}", showId, e);
        updateProcessingStatus(showId, ProcessingStatus.FAILED);
        rollbackUploadedS3Files(showId); // 이미 올라간 S3 파일 삭제
    }
}</code></pre>
</div>
</div>
<h3>기존 데이터 호환</h3>
<p>processingStatus 컬럼이 없는 기존 데이터는 DTO 매핑 시 null이 내려올 수 있다. null인 경우 DONE으로 간주하는 방식으로 하위 호환성을 유지했다.</p>
<div>
<div>
<pre class="java" id="code_1776003383832"><code>ProcessingStatus status = show.getProcessingStatus();
return status != null ? status : ProcessingStatus.DONE;</code></pre>
</div>
</div>
<h2>5. API 변경</h2>
<div>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td>항목 변경</td>
<td>전</td>
<td>후</td>
</tr>
<tr>
<td>POST /api/v1/admin/shows 응답 코드</td>
<td>201 Created</td>
<td>202 Accepted</td>
</tr>
<tr>
<td>응답 메시지</td>
<td>등록 완료</td>
<td>"공연 등록이 시작되었습니다"</td>
</tr>
<tr>
<td>관리자 목록&middot;상세 응답</td>
<td>processingStatus 없음</td>
<td>processingStatus 필드 추가</td>
</tr>
</tbody>
</table>
</div>
<p>프론트엔드와 상태 코드 및 필드 계약을 명확히 맞추는 것이 중요했다. 202를 받으면 곧바로 완료로 처리하지 않고, processingStatus를 폴링해서 DONE이 되면 완료 처리하는 흐름으로 변경됐다.</p>
<h2>6. 정리</h2>
<ul>
<li>"느린 작업을 한 HTTP 요청에 모두 실어 보내는" 패턴은 타임아웃&middot;커넥션 점유&middot;UX 모두에 불리하다.</li>
<li>202 + 비동기 + 처리 상태 폴링은 관리자 기능처럼 무거운 작업을 다룰 때 유효한 패턴이다.</li>
<li>S3 병렬화와 배치 INSERT를 함께 적용하면 실제 처리 시간도 줄일 수 있다.</li>
<li>@Async와 @Transactional을 함께 쓸 때는 커밋 타이밍을 반드시 신경 써야 하고, MultipartFile은 비동기 경계에서 미리 복사해두어야 한다.</li>
<li>프론트엔드와는 상태 코드&middot;응답 필드 계약을 명확히 맞추는 것이 중요하다.</li>
</ul>