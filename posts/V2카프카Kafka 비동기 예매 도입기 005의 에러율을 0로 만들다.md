# [V2]카프카(Kafka) 비동기 예매 도입기: 0.05%의 에러율을 0%로 만들다

**발행일:** Sun, 1 Mar 2026 22:59:55 +0900

**링크:** https://hee-story6.tistory.com/238

---

<h2>발단: 99.95%의 성공, 0.05%의 에러</h2>
<p><span>대용량 트래픽이 몰리는 콘서트 티켓팅 시스템을 개발하며 대기열(Queue) 시스템을 도입했다.</span><span> 수많은 유저가 몰려도 직렬 처리를 통해 서버가 다운되는 것은 막았지만,</span><span> k6 부하 테스트 결과 </span><b>0.05%의 에러율</b><span>이 지속적으로 발생했다.</span></p>
<p><span>원인은 명확했다.</span><span> "DB 저장 실패가 곧 예매 응답 실패"로 이어지는 동기식(Synchronous) 구조 때문이었다.</span><span> 트래픽 피크 타임에 DB 커넥션 풀이 고갈되거나 일시적인 DB 지연이 발생하면,</span><span> 사용자는 좌석을 선점했음에도 예매 실패 화면을 봐야 했다.</span><span></span></p>
<h2>해결책: Kafka를 활용한 비동기 이벤트 기반 아키텍처(EDA) 도입</h2>
<p>클라이언트가 예매를 요청하면, 서버는 DB에 쿼리를 날리는 대신 Kafka Topic에 '예매 요청 이벤트'를 발행(Publish)하고 즉시 202 Accepted를 응답한다. 실제 DB 저장은 백그라운드에서 Kafka Consumer가 안전하게 처리한다.</p>
<p><b>최종 처리 흐름:</b></p>
<ol>
<li><b>[클라이언트]</b> 예매 버튼 클릭</li>
<li><b>[API 서버]</b> Redis 분산락 획득 (좌석 선점) &rarr; Kafka에 이벤트 발행 &rarr; 202 Accepted 및 reservation_id 반환 (수 ms 이내)</li>
<li><b>[클라이언트]</b> "잠시 처리 중입니다..." 화면 노출 후 GET /status 폴링 (1~2초 간격)</li>
<li><b>[Consumer]</b> Kafka 메시지 수신 &rarr; DB 저장 &rarr; Status COMPLETED 업데이트</li>
<li><b>[클라이언트]</b> Status 확인 후 "예매 완료 페이지" 이동</li>
</ol>
<h2>핵심 트러블슈팅 및 설계 결정사항</h2>
<h3>1. Kafka의 At-least-once 특성 극복: 이중 멱등성(Idempotency) 보장</h3>
<p>Kafka는 네트워크 이슈 등으로 인해 동일한 메시지가 두 번 이상 전달될 가능성이 있다. 중복 예매를 막기 위해 <b>이중 방어선</b>을 구축했다.</p>
<ul>
<li><b>방어 1 (Consumer 레벨):</b> Redis를 활용해 eventId를 키로 O(1) 조회를 수행하여 이미 처리된 이벤트인지 빠르게 검증한다.</li>
<li><b>방어 2 (DB 레벨):</b> Reservation 테이블의 event_id 컬럼에 Unique Constraint를 걸어 최후의 데이터 정합성을 보장했다.</li>
</ul>
<h3>2. 분산 환경의 딜레마: Redis 락과 DB 저장 사이의 생명주기 불일치</h3>
<p>가장 골치 아팠던 부분이다. Redis 락으로 좌석을 점유하고 202 응답을 보냈는데, Consumer가 DB 저장을 실패하면 어떻게 될까? Redis 락은 TTL 만료로 풀리고, 사용자는 예매된 줄 알지만 실제 데이터는 없는 <b>데이터 불일치</b>가 발생한다.</p>
<p>이를 해결하기 위해 좌석 상태 관리를 고도화했다.</p>
<ul>
<li>Redis에 좌석 상태를 PENDING_KAFKA 상태로 기록한다.</li>
<li>Consumer가 DB 저장에 성공하면 상태를 CONFIRMED로 변경한다.</li>
<li>실패 시 해당 키를 삭제하여 좌석을 즉시 반납한다.</li>
<li>스케줄러는 PENDING_KAFKA 상태인 좌석을 건드리지 않도록 격리하여 정합성을 지켜냈다.</li>
</ul>
<h3>3. 장애 격리: Dead Letter Queue (DLQ) 도입</h3>
<p>데이터 유실은 티켓팅 시스템에서 치명적이다. DB 일시 장애 등으로 Consumer가 처리에 실패할 경우, 3회 재시도(FixedBackOff) 후 메시지를 DLQ(Dead Letter Queue)로 이동시키도록 구성했다. DLT(Dead Letter Topic) 전용 Consumer를 별도로 두어, 슬랙(Slack) 알림을 발송하고 관리자가 수동 재처리하거나 사용자에게 안전하게 실패를 안내할 수 있는 파이프라인을 구축했다. (최신 트렌드에 맞게 Zookeeper 없는 Kafka 3.7 KRaft 모드를 도입해 인프라 복잡도도 낮췄다.)</p>
<h2>결과 및 배운 점</h2>
<p><span>도입 결과,</span><span> 1000 VUs k6 부하 테스트에서 에러율 0%를 달성했다.</span><span> 단순히 성능을 높인 것을 넘어,</span><span> 시스템을 설계하고 바라보는 관점이 완전히 달라진 계기가 되었다.</span><span>&nbsp;</span></p>
<p><figure class="imageblock alignCenter"><span><img height="842" src="https://blog.kakaocdn.net/dn/6gyAU/dJMcaivC1xO/GZ0TnAcfNKsaTvsYj9KEJK/img.png" width="821" /></span></figure>
</p>
<p><b>1. 빠른 응답의 대가는 복잡한 실패 처리다</b> <br />비동기 전환 전에는 DB 에러가 곧 예매 실패로 이어지는 단순한 구조였다. 하지만 응답 속도를 높이기 위해 DB 저장을 비동기로 분리하자, 실패 경로는 기하급수적으로 복잡해졌다. 메시지가 유실되거나 중복 소비되는 상황, Consumer가 DB 저장에 실패하는 상황 등을 모두 방어해야 했다. 결국 비동기 시스템에서 <b>DLQ(Dead Letter Queue)를 통한 실패 격리와 멱등성(Idempotency) 보장은 선택이 아니라 필수</b>임을 깨달았다.</p>
<p><b>2. 데이터베이스는 생각보다 훨씬 취약하다</b> <br />애플리케이션 서버는 트래픽이 몰리면 비교적 쉽게 버티거나 스케일 아웃을 할 수 있지만, 디스크 I/O를 수반하는 DB는 그렇지 않다. 이번 프로젝트를 통해 Kafka가 단순히 데이터를 전달하는 통로(Pipe)나 성능 향상 도구가 아니라, <b>DB가 감당할 수 없는 엄청난 쓰기 부하를 대신 맞아주는 든든한 '방파제'</b> 역할을 한다는 것을 깊이 체감했다.</p>
<p><b>3. 분산 시스템에서 정합성은 저절로 보장되지 않는다</b> <br />과거에는 단일 RDBMS의 트랜잭션(ACID)에만 의존하면 데이터가 안전했다. 하지만 이번에는 좌석 상태를 관리하는 Redis, 이벤트를 전달하는 Kafka, 최종 데이터를 영속화하는 DB까지 총 3개의 저장소가 얽혔다. Redis 락은 풀렸는데 DB 저장은 실패하는 등의 생명주기 불일치를 직접 해결하며, "분산 환경에서 트랜잭션을 관리하는 것이 왜 그렇게 어려운가"를 온몸으로 경험할 수 있었다.</p>
<p>&nbsp;</p>
<p>Kafka 도입으로 1,000 VUs 환경에서는 에러율 0%를 달성했지만, 한계는 곧바로 찾아왔다. 부하를 <b>3,000 VUs 이상</b>으로 끌어올리자 시스템 전반에서 다시 에러가 발생하기 시작했다. 원인을 분석해 보니 애플리케이션의 로직 문제가 아닌, <b>단일 서버(Single Server)가 가진 물리적 리소스(CPU, 메모리, 네트워크 대역폭)의 명백한 한계</b>였다.</p>
<p>결국 1,000만 명 단위의 대규모 트래픽을 감당하려면 애플리케이션 레벨의 최적화를 넘어, 인프라 레벨의 확장(Scaling)이 필수적이다.향후 V3 아키텍처는 AWS 클라우드 환경을 적극 활용하여 다음과 같이 확장할 계획이다.</p>
<ul>
<li><b>컴퓨팅 리소스의 수평적 확장 (Scale-out):</b> 단일 서버에 집중된 트래픽을 분산하기 위해 ALB(Application Load Balancer)를 앞단에 배치하고, 부하에 따라 서버가 유연하게 늘어나는 <b>EC2 Auto Scaling Group</b>을 구성하여 트래픽 스파이크에 대응한다.</li>
<li><b>DB 고가용성 및 읽기 부하 분산:</b> 단일 DB의 한계를 극복하기 위해 <b>Amazon RDS Multi-AZ</b>로 장애 조치(Failover) 환경을 구축하고, <b>Read Replica</b>를 두어 예매 내역 조회나 좌석 확인 등의 읽기(Read) 트래픽을 물리적으로 분산시킨다.</li>
<li><b>완전 관리형 서비스로의 전환 검토:</b> 현재 직접 구축해 운영 중인 Redis와 Kafka 노드를 각각 <b>Amazon ElastiCache</b>와 Amazon MSK(Managed Streaming for Apache Kafka)로 전환하여 인프라 관리 포인트를 줄이고 시스템 안정성을 극대화할 예정이다.</li>
</ul>
<p>비동기 설계를 통해 애플리케이션의 병목을 뚫어냈으니, 이제는 인프라의 병목을 뚫어낼 차례다. 진정한 대용량 트래픽 처리를 향한 도전은 계속된다!!!</p>