# [성능테스트] 대용량 트래픽 환경에서 비관적 락(Pessimistic Lock)의 성능 한계 분석

**발행일:** Fri, 30 Jan 2026 10:03:26 +0900

**링크:** https://hee-story6.tistory.com/234

---

<p>현재 개발 중인 티켓 예매 프로젝트의 핵심 비즈니스 로직은 '선착순 동시성 제어'다. 초기 구현 단계에서는 데이터의 정합성을 최우선으로 고려하여 비관적 락(Pessimistic Lock)을 적용해 동시성을 제어했다.</p>
<p>하지만 개발 도중 <b>"과연 트래픽이 수천 명 단위로 늘어나도, 디스크 I/O 기반인 DB가 버틸 수 있을까?"</b> 라는 의문이 들었다. 단순히 "그럴 것이다"라는 뇌피셜이 아닌, <b>정량적인 데이터</b>로 한계를 확인하고, 캐시 저장소(Redis) 도입의 확실한 근거를 마련하기 위해 극한의 부하 테스트를 진행했다.</p>
<hr contenteditable="false" />
<h2>1. 테스트 배경 및 설계</h2>
<p><b>DB 비관적 락</b>은 확실한 데이터 일관성을 보장하지만, 다음과 같은 치명적인 성능 저하가 예상되었다.</p>
<ol>
<li><b>Row Lock 경합:</b> 다수가 한 데이터를 노릴 때 발생하는 대기 시간(Blocking).</li>
<li><b>Connection Pool 고갈:</b> 잦은 대기열 조회(Polling)로 인한 DB 리소스 점유.</li>
</ol>
<p>이를 검증하기 위해 k6를 사용하여 두 가지 시나리오를 설계했다.</p>
<h2>2. 시나리오 1: 좌석 쟁탈전 (Seat Lock Contention)</h2>
<p>첫 번째 시나리오는 <b>"다수의 사용자가 소수의 좌석을 동시에 선점하려 할 때"</b> 발생하는 DB Row Lock의 경합 상황을 시뮬레이션했다.</p>
<h3>2-1. 테스트 설계 및 스크립트</h3>
<ul>
<li><b>목적:</b> 비관적 락 환경에서의 성능 비용(Latency) 및 정합성 검증</li>
<li><b>환경:</b> VUs(가상 유저) 100명</li>
<li><b>핵심 로직:</b> contentionPool을 사용하여 100명이 앞쪽 10개 좌석만 노리도록 강제 경합 유도</li>
</ul>
<pre class="javascript" id="code_1769734592119"><code>    check(lockRes, {
        'Lock Success (200)': (r) =&gt; r.status === 200,
        'Lock Conflict (409)': (r) =&gt; r.status === 409,
        'DB Lock Timeout (500)': (r) =&gt; r.status === 500,
    });</code></pre>
<p><figure class="imageblock alignCenter"><span><img height="1415" src="https://blog.kakaocdn.net/dn/b0eYke/dJMcagK7VMY/yWBYAnvfeWCnvKJpKVPzM0/img.png" width="1608" /></span></figure>
</p>
<h3>2-2. 테스트 결과 분석</h3>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>지표</b></td>
<td><b>결과값</b></td>
<td><b>비고</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>성공 (200 OK)</b></span></td>
<td><span>20% (33건)</span></td>
<td><span>선착순 성공</span></td>
</tr>
<tr>
<td><span><b>실패 (409 Conflict)</b></span></td>
<td><span><b>80% (132건)</b></span></td>
<td><span>이미 선점된 좌석</span></td>
</tr>
<tr>
<td><span><b>p95 Latency</b></span></td>
<td><span><b>1.29s</b></span></td>
<td><span>하위 95% 요청 처리 시간</span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<p>테스트 결과, <b>데이터 정합성은 완벽하게 보장되었다.</b> 100명이 동시에 요청을 보냈음에도 중복 예약은 발생하지 않았으며, 선점 실패 시 정확히 409 Conflict를 반환했다.</p>
<p>하지만 <b>성능 측면에서는 명확한 한계</b>가 드러났다. 고작 100명의 동시 접속임에도 불구하고, 락 대기 시간으로 인해 <b>p95 응답 속도가 1.29초</b>까지 지연되었다. 만약 유저가 1,000명 단위로 늘어난다면, 모든 트랜잭션이 직렬화(Serialization)되어 줄을 서게 될 것이고, 응답 시간은 기하급수적으로 늘어날 것임이 자명했다.</p>
<p>&nbsp;</p>
<h2>3. 시나리오 2: 대기열 지옥 (Queue Polling Hell)</h2>
<p>두 번째 시나리오는 <b>"대기 순번을 확인하려는 단순 조회 트래픽이 폭주할 때"</b> DB Connection Pool이 어떻게 반응하는지 확인했다.</p>
<h3>3-1. 테스트 설계 및 스크립트</h3>
<ul>
<li><b>목적:</b> 잦은 폴링(Polling)이 DB 리소스(HikariCP)에 미치는 영향 확인</li>
<li><b>환경:</b> VUs 3,000명, 1초마다 대기열 상태 조회</li>
<li><b>핵심 로직:</b> 한 명의 유저가 루프를 돌며 조회를 반복하여 조회 트래픽 부하를 극대화</li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="755" src="https://blog.kakaocdn.net/dn/boND9K/dJMcafZIQAc/npOoL9m19D9IsYkyl0CInK/img.png" width="907" /></span></figure>
</p>
<h3>3-2. 테스트 결과 분석</h3>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>지표</b></td>
<td><b>결과값</b></td>
<td><b>비고</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>HTTP 에러율</b></span></td>
<td><span><b>0%</b></span></td>
<td><span>표면적으로는 모두 성공</span></td>
</tr>
<tr>
<td><span><b>평균 응답 시간</b></span></td>
<td><span><b>39.29초</b></span></td>
<td><span>사용자 이탈 발생 구간</span></td>
</tr>
<tr>
<td><span><b>p95 응답 시간</b></span></td>
<td><span><b>50.79초</b></span></td>
<td><span>사실상 서비스 장애</span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<p>k6 결과만 보면 에러율이 0%라 성공한 것처럼 보일 수 있다. 하지만 응답 시간이 50초라는 것은 UX 관점에서 명백한 서비스 장애다. 원인을 파악하기 위해 서버 로그를 확인한 결과, 범인은 <b>HikariCP의 Connection 고갈</b>이었다.</p>
<p><figure class="imageblock alignCenter"><span><img height="78" src="https://blog.kakaocdn.net/dn/bvo47W/dJMcadU6xlS/K2PJaMKWGLxu5GYFkMSLlk/img.png" width="725" /></span></figure>
</p>
<p>&nbsp;</p>
<ul>
<li><b>Pool 고갈:</b> 총 50개의 커넥션이 모두 사용 중(active=50)이었다.</li>
<li><b>병목 발생:</b> 148개의 스레드(waiting=148)가 커넥션을 얻지 못해 대기열에 갇혀 있었다.</li>
<li><b>장애 확산:</b> Spring Boot는 커넥션 획득을 위해 최대 30초(기본값)를 대기한다. 이 때문에 단순 조회 요청들이 WAS의 스레드를 모두 점유해버려, 정작 중요한 다른 서비스까지 마비시키는 결과를 초래했다.</li>
</ul>
<h2>4. 결론 및 향후 계획</h2>
<p>이번 부하 테스트를 통해 "대용량 트래픽 처리에 DB 락과 폴링은 적합하지 않다"는 것을 코드로 검증했다. 데이터 정합성은 지켰을지 몰라도, 가용성과 성능은 지키지 못했기 때문이다.</p>
<p>이에 따라 다음과 같이 아키텍처를 개선하기로 결정했다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>구분</b></td>
<td><b>AS-IS (현재)</b></td>
<td><b>TO-BE (개선안)</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>좌석 선점</b></span></td>
<td><span>DB 비관적 락 (Lock Wait 발생)</span></td>
<td><span>Redis 분산 락 도입</span></td>
</tr>
<tr>
<td><span><b>대기열 조회</b></span></td>
<td><span>DB 조회 (Connection 고갈)</span></td>
<td><span>Redis In-Memory 조회 (DB 부하 Zero)</span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<p>Redis 도입을 통해 p95 Latency를 100ms 이하로 줄이는 것이 목표다. 다음 포스팅에서는 Redis 적용 후 동일한 시나리오에서 성능이 얼마나 개선되었는지, Before &amp; After 데이터를 통해 다룰 예정이다.</p>
<p><b>"에러가 나지 않았다고 문제가 없는 것이 아니다. 50초의 지연은 곧 장애다."</b></p>
<p>&nbsp;</p>