# [V2]동시에 예매를 눌렀을 때, 서버는 살아남을 수 있을까? &mdash; 부하 테스트와 트랜잭션 최적화 기록

**발행일:** Sat, 28 Feb 2026 09:30:21 +0900

**링크:** https://hee-story6.tistory.com/237

---

<h2>들어가며</h2>
<p>티켓팅, 선착순 예매는 백엔드 개발자라면 누구나 한 번쯤 고민해보는 고난도 주제다. "내가 만든 예매 서버는 동시에 몰릴 때도 버틸 수 있을까?"라는 질문에서 이번 작업이 시작되었다.</p>
<p>현재 개발 중인 V2 예매 시스템에 k6를 이용한 실제 부하 테스트를 적용해 보았다. 이 글은 병목 지점을 수치로 찾아내고, 코드 수준에서 원인을 분석하여 제거해 나간 엔지니어링 사이클의 기록이다.</p>
<h2>1. 시스템 구조 개요</h2>
<p>현재 V2 시스템은 DB로 향하는 트래픽을 제어하기 위해 Redis를 적극적으로 활용하고 있다. Redis의 역할은 크게 두 가지다.</p>
<ul>
<li><b>대기열(Queue):</b> 입장 순번을 관리해 동시 접근 유저 수를 서버 한계 이하로 1차 컷오프한다.</li>
<li><b>분산락(Redisson RLock):</b> 같은 좌석을 여러 유저가 동시에 예약하지 못하도록 원자적(Atomic)으로 잠근다.</li>
</ul>
<h2>2. 문제 발견 &mdash; k6 부하 테스트 결과</h2>
<p>대기열과 분산락이 있으니 안전할 것이라 믿고, ramp-up-test.js로 <b>VUs 1000명, 5분 30초</b> 동안 부하를 가해보았다. 결과는 예상 밖이었다. 연결 요청 974건이 waiting 상태에서 10초를 기다리다 모두 타임아웃으로 튕겨 나갔다.</p>
<p><figure class="imageblock alignCenter"><span><img height="1472" src="https://blog.kakaocdn.net/dn/Y8gVQ/dJMcacIZwjw/ZS9Eo2aLdC7dA2whp5MxK1/img.png" width="1744" /></span></figure>
</p>
<h2>3. 원인 분석: 범인은 '트랜잭션 점유 시간'</h2>
<p>3-1.실제 서버 에러 로그를 확인해 보니, DB 커넥션 풀(HikariCP)이 최대치에 도달해 더 이상 연결을 받지 못하고 있었다.</p>
<p><figure class="imageblock alignCenter"><span><img height="521" src="https://blog.kakaocdn.net/dn/8qFoJ/dJMcabpMPZX/lJ07oOkuEUmlxtTCfzxhy0/img.png" width="1574" /></span></figure>
</p>
<p>&nbsp;</p>
<p>3-2.트랜잭션&nbsp;범위&nbsp;문제&nbsp;&mdash;&nbsp;"왜&nbsp;커넥션을&nbsp;오래&nbsp;물고&nbsp;있었나?" <br />핵심 원인: 트랜잭션 범위가 Redis 락 대기 구간까지 감싸고 있었다.</p>
<p>@Transactional이 걸려있으면 메서드 시작과 동시에 DB 커넥션을 하나 가져온다. 커넥션 풀 최대치가 100개일 때 1000명이 몰리면, 운 좋은 100명만 커넥션을 선점하고 900명은 밖에서 대기해야 한다.</p>
<p>문제는 커넥션을 선점한 100명조차 바로 DB 작업을 하는 게 아니라, "Redis 분산락(내 차례)을 얻기 위해 짧게는 수백 ms, 길게는 수 초 동안 대기"하고 있었다는 점이다. 식당 테이블이 100개인데, 밥을 다 먹은 손님이 나가지 않고 1시간 동안 앉아있는 것과 같다. 밖에서 기다리던 900명은 타임아웃(10초)이 지나도 빈자리가 나지 않아 결국 500 에러가 터져버린 것이다.</p>
<h2>4. 해결 &mdash; 트랜잭션 범위 분리와 점유 시간 최소화</h2>
<p>해결의 핵심 원칙은 하나다. "DB 커넥션은 락을 얻고 나서, 실제 DB에 쿼리를 날리기 직전에 열고 순식간에 닫아야 한다."</p>
<p>&nbsp;</p>
<p>4-1. DB 쓰기 및 트랜잭션 전담 클래스 분리 실제 DB에 기록을 남기는 찰나의 순간에만 트랜잭션이 발동하도록, 쓰기 로직만 ReservationPersistService라는 별도의 서비스 클래스로 완전히 분리했다.</p>
<pre class="java" id="code_1772198330914"><code>@Service
public class ReservationPersistService {
    @Transactional  // ✅ 실제 DB 작업 구간만 묶음 (수십 ms 안에 종료)
    public ReserveResponse saveReservationData(...) {
        // 엔티티 저장, 상태 업데이트 등..
    }
}</code></pre>
<p>&nbsp;</p>
<p>4-2. 메인 로직에서는 트랜잭션을 빼고 락만 대기 이제 예매 메인 로직에서는 @Transactional을 과감히 제거했다. 줄을 서서 락을 기다리는 동안에는 DB 커넥션을 아예 건드리지 않는다. <b></b></p>
<h3>변경 전/후 커넥션 점유 시간 비교</h3>
<ul>
<li><b>[AS-IS]</b> DB 커넥션 점유 (최대 수 초) = [Redis 락 대기] + [실제 DB 저장]</li>
<li><b>[TO-BE]</b> DB 커넥션 점유 (0.05초) = [실제 DB 저장]</li>
</ul>
<p>락 대기 구간에서 커넥션을 완전히 해방시켰다. 똑같은 커넥션 100개로도 한 번에 소화할 수 있는 트래픽 양이 수십 배 늘어났다.</p>
<h2>5. 결과 &mdash; 개선 후 k6 부하 테스트</h2>
<p>동일한 조건으로 다시 부하 테스트를 진행한 결과, 성능이 극적으로 개선되었다.</p>
<p><figure class="imageblock alignCenter"><span><img height="1579" src="https://blog.kakaocdn.net/dn/ptIvE/dJMcahcqK6S/wfX5MdMaIlEYgb0asO90Nk/img.png" width="1589" /></span></figure>
</p>
<p>참고로, 로그에 찍힌 Business Fail(99.93%)은 에러가 아니다. 5개 좌석에 1000명이 몰렸을 때, Redis 분산락이 단 1명에게만 예매를 허용하고 나머지 999명은 "이미 예약된 좌석"으로 정확히 튕겨냈다는 뜻이다. 데이터 무결성이 완벽하게 지켜졌다.</p>
<h2>6. 한계와 다음 단계 (feat. Kafka)</h2>
<p>이번 최적화는 동기(Synchronous) 아키텍처 안에서 쥐어짤 수 있는 최상위 수준의 개선이었다고 생각한다. 하지만 로컬 DB 환경에서 1000명 기준 0.05%의 에러가 여전히 발생하는 물리적 한계는 존재한다. 10만, 100만 명 수준의 트래픽을 0% 에러로 처리하려면 패러다임 전환이 필요하다.</p>
<p>&nbsp;</p>
<p>그래서 다음 단계로 <b>Kafka 비동기 이벤트 처리</b>를 도입할 예정이다.</p>
<ul>
<li><b>현재 동기식 구조:</b> 예매 요청 &rarr; 락 획득 &rarr; <b>DB 저장</b> &rarr; 200 응답</li>
<li><b>Kafka 비동기 구조:</b> 예매 요청 &rarr; 락 획득 &rarr; <b>Kafka 이벤트 발행</b> &rarr; 즉시 200 응답 <i>(이후 백그라운드에서 Consumer가 DB 저장)</i></li>
</ul>
<p>Kafka를 도입하면 사용자 응답 속도에서 DB 파이프 사용량이 완전히 분리되므로, 이론적으로 DB 커넥션 고갈로 인한 응답 실패를 0%로 만들 수 있다. 이후에 대용량 10만, 100만 이상가면 단일서버기 때문에 또 에러가 날 것이고 내가 배운 AWS를 기반으로 DB풀과 여러 서버를 두고 테스트를 진행해 볼 예정이다.</p>