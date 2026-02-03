# [Project] 공연 예매 시스템 대용량 트래픽 대응기: 해결 방안 설계 (V1 &rarr; V2)

**발행일:** Tue, 3 Feb 2026 11:14:29 +0900

**링크:** https://hee-story6.tistory.com/235

---

<h2>1. 문제 상황: DB만으로는 버틸 수 없다</h2>
<p>지난 프로젝트에서 DB 비관적 락(Pessimistic Lock)을 사용하여 동시성을 제어했다. 하지만 부하 테스트 결과, 수천 명의 대기열 조회 요청(SELECT)과 좌석 선점 요청(FOR UPDATE)이 DB 커넥션 풀을 고갈시키는 현상이 발생했기 때문이다.</p>
<p>이후 글에서 말한 것처럼 고도화를 통해 이런 트래픽을 분산할 것이다</p>
<p>&nbsp;</p>
<p><a href="https://hee-story6.tistory.com/234" rel="noopener" target="_blank">2026.01.30 - [Data Engineering/DBMS &amp; Tuning] - [성능테스트] 대용량 트래픽 환경에서 비관적 락(Pessimistic Lock)의 성능 한계 분석</a></p>
<p>&nbsp;</p>
<h2>2. 핵심 전략: DB 부하를 0으로 만들기</h2>
<p>대용량 트래픽 대응을 위해 다음 3가지 핵심 전략을 수립했다.</p>
<ol>
<li><b>대기열 시스템 (Queue):</b> DB 테이블 대신 <b>Redis Sorted Set</b>으로 전환하여 메모리단에서 빠른 순서 관리를 수행한다.</li>
<li><b>분산 락 (Distributed Lock):</b> DB 락 대신 <b>Redisson 분산 락</b>을 사용하여 DB 부하를 제거하고 락 획득 속도를 높인다.</li>
<li><b>토큰 기반 입장 제어 (Flow Control):</b> 대기열을 통과한 사용자에게만 입장권(Token)을 발급하여 예매 API 접근 권한을 부여한다.</li>
</ol>
<p><span style="color: #ee2323;"><i>※지난 번 글들은 초기 설계라 지난 글과 다르다.&nbsp;</i></span></p>
<h2>3. V1 vs V2 아키텍처 변화</h2>
<h3><b>V1: DB 기반 아키텍처 (AS-IS)</b></h3>
<p><figure class="imageblock alignCenter"><span><img height="1040" src="https://blog.kakaocdn.net/dn/kVcUc/dJMcaajQ53A/hwWNSdfQgYsR52W9fz8l01/img.png" width="1323" /></span></figure>
</p>
<p>모든 트래픽이 DB로 직행하는 구조였다.</p>
<ul>
<li><b>대기열:</b> Queue 테이블에 INSERT 후 폴링(SELECT) &rarr; 초당 수천 건의 쿼리 발생.</li>
<li><b>좌석 선점:</b> SELECT ... FOR UPDATE로 Row Lock을 검 &rarr; 트랜잭션 대기 시간 급증.</li>
<li><b>결과:</b> DB CPU 사용률 80% 이상, 병목 현상 발생.</li>
</ul>
<h3><b>V2: Redis 기반 아키텍처 (TO-BE)</b></h3>
<p><figure class="imageblock alignCenter"><span><img height="1378" src="https://blog.kakaocdn.net/dn/lwfM4/dJMcagYE094/lQHMKNaWYTSVfpxmOzVsu1/img.png" width="2073" /></span></figure>
</p>
<p>Redis가 '문지기' 역할을 수행하여 DB를 보호하는 구조로 변경했다.</p>
<ul>
<li><b>대기열:</b> ZADD로 타임스탬프 기준 줄 세우기 &rarr; O(logN) 속도로 순번 조회.</li>
<li><b>스케줄러:</b> 1초마다 상위 N명에게 토큰 발급 (ShedLock으로 중복 실행 방지).</li>
<li><b>좌석 선점:</b> Redisson으로 메모리단에서 락 획득 후, 성공한 1명만 DB 업데이트.</li>
<li><b>결과:</b> DB 부하 20% 이하로 감소, 응답 속도 획기적 개선.</li>
</ul>
<hr />
<h2>4. 핵심 컴포넌트 설계</h2>
<h3><b>① Redis 대기열 (Sorted Set + String)</b></h3>
<p>대기열은 <b>'선착순(FIFO)'</b> 보장이 필수다. RabbitMQ나 Kafka 같은 메시지 큐 대신 Redis를 선택한 이유는 "내 앞에 몇 명이 남았는지(Rank)"를 실시간으로 조회해야 하기 때문이다.</p>
<ul>
<li><b>Waiting Queue (Sorted Set):</b>
<ul>
<li>Key: waiting:queue:{scheduleId}</li>
<li>Value: userId</li>
<li>Score: timestamp (진입 시간)</li>
</ul>
</li>
<li><b>Access Token (String):</b>
<ul>
<li>Key: token:{uuid}</li>
<li>TTL: 5분 (자동 만료)</li>
<li><b>UUID 선택 이유:</b> JWT는 암호화 연산 비용이 든다. 입장권은 상태 관리(만료, 사용 완료)가 필요하므로 Redis에서 생명주기를 직접 관리하기 편한 UUID가 더 적합했다.</li>
</ul>
</li>
</ul>
<h3><b>② Redisson 분산 락</b></h3>
<p>스프링 부트의 기본 클라이언트인 Lettuce를 사용하면, 락 획득 재시도를 위해 Redis에 요청을 지속적으로 보내는 스핀 락(Spin Lock) 방식은 Redis에 부하를 줄 수 있다. 따라서 Redisson은 Pub/Sub 기능을 이용해 락 해제 시에만 요청을 보내도록 설계되어 있어, Redis의 부하를 획기적으로 줄일 수 있기에 도입했다.</p>
<ul>
<li><b>동작:</b> 락 획득을 위해 계속 재시도(Retry)하는 대신, 락이 해제되었다는 알림(Subscribe)을 받으면 그때 락을 획득한다.</li>
<li><b>효과:</b> Redis 부하 감소 및 구현 복잡도 해결.</li>
</ul>
<h3><b>③ 다중 서버 환경 대응 (ShedLock)</b></h3>
<p>AWS Auto Scaling으로 서버가 여러 대 실행될 경우, 스케줄러가 중복 실행되어 토큰을 과다 발급할 위험이 있다. 이를 방지하기 위해 <b>ShedLock</b>을 도입하여 분산 환경에서도 스케줄러가 오직 한 서버에서만 실행되도록 보장했다.(개발 서버에서는 서버 1대지만, 추후 AWS Auto Scaling을 도입을 위해 미리 도입하였다.)</p>
<p>&nbsp;</p>
<h2>5. 예상 성능 개선 및 기대 효과</h2>
<p>설계 변경을 통해 메모리를 약간 더 사용하는 대신 처리 처리량 5배, 응답 속도 6배라는 압도적인 성능 개선을 이끌어낼 수 있는 구조를 설계했으며, 성능 개선 기대중이다.<b></b></p>
<h2 style="color: #000000; text-align: start;">6. 마치며</h2>
<p>이번 V2 설계를 진행하면서 Redis가 단순한 캐시 저장소를 넘어, 동시성 제어와 대기열 관리를 위한 핵심 도구로 어떻게 활용되는지 깊이 이해할 수 있었다.</p>
<p>이론적으로 설계한 이 구조가 실제 부하 테스트에서 기존 DB 비관적 락 방식보다 어떤 성능 차이를 보여줄지 벌써부터 기대가 된다. 무엇보다 트래픽이 몰려도 유연하게 대응할 수 있는 '확장성 있는 아키텍처'를 내 손으로 완성했다는 점도 뿌듯ㅎㅎ&nbsp;</p>
<p>다음 포스팅은 실제 코드로 어떻게 구현했는지 개선되었는지 보여주도록 하겠다!</p>