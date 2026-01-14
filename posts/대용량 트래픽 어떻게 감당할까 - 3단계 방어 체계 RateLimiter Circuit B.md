# 대용량 트래픽, 어떻게 감당할까? - 3단계 방어 체계 (RateLimiter, Circuit Breaker, DB Lock)

**발행일:** Wed, 14 Jan 2026 19:19:39 +0900

**링크:** https://hee-story6.tistory.com/230

---

<p>평소 지그재그나 쿠폰 선착순 이벤트를 보면서 항상 궁금했던 점이 있었다.</p>
<blockquote>
<p>"수만 명이 동시에 접속하는데 서버는 어떻게 터지지 않고 순서대로 처리하는 걸까?"</p>
</blockquote>
<p>극한의 상황을 가정한 대용량 트래픽 처리나 동시성 제어에 대해서는 항상 막연한 갈증이 있었다.</p>
<p>. 단순히 "서버를 늘리면 되는 거 아닌가?"라고 생각하기엔, DB의 커넥션 한계나 데이터 정합성 문제는 해결되지 않는다.</p>
<p>이 갈증을 해소하기 위해 토이프로젝트 하면서 redis 대기열 프로세스를 대략 작성해봤지만 막연하게 작성한거라 최근 강의 수강 시작! 강의를 수강하며 대기열 시스템과 시스템 보호 장치들을 공부하기 시작했고, 오늘 그 핵심이 되는 아키텍처와 이론을 정리해보고자 한다.</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<h4><b>1.전체 아키텍처: 방어와 수비의 조화</b></h4>
<p>대용량 처리는 단순히 코드만 잘 짠다고 되는 것이 아니었다. 트래픽이 들어오는 입구부터 데이터가 저장되는 곳까지 단계별 방어 전략이 필요했다.</p>
<p><figure class="imageblock alignCenter"><span><img height="5590" src="https://blog.kakaocdn.net/dn/citiPy/dJMcabXeOHQ/u6ViwoJkRgYBJQUe7unPbk/img.png" width="7537" /></span></figure>
</p>
<p>내가 설계하고 학습한 구조는 크게 두 단계로 나뉜다.</p>
<ol>
<li><b>Gateway (입구):</b> Redis와 서킷 브레이커를 이용해 감당 불가능한 트래픽은 아예 들이지 않는다.</li>
<li><b>Database (최종 목적지):</b> 락(Lock)을 이용해 들어온 요청들이 데이터(재고)를 안전하게 수정하도록 줄을 세운다.</li>
</ol>
<p>이제 각 단계별 핵심 기술을 살펴보자.</p>
<h4><b>2.방어선 1단계: Gateway에서의 문지기 (Redis &amp; Resilience4j)</b></h4>
<p>가장 먼저 배운 것은 "모든 요청을 서버 내부로 들이지 말라"는 것이다. DB까지 가기 전에 앞단(Gateway)에서 걸러내는 것이 시스템 안정성의 핵심이다.</p>
<p><b>1) Redis Request Rate Limiter (처리율 제한 장치)</b> 마치 놀이공원 입구의 회전식 문처럼, 단위 시간당 처리할 수 있는 요청 수를 제한하는 기술이다. Redis의 Token Bucket 알고리즘을 사용한다.</p>
<p><figure class="imageblock alignCenter"><span><img height="392" src="https://blog.kakaocdn.net/dn/djBA5I/dJMcaajI0ak/ysnYXdRlkrORCYY2e6DQL1/img.png" width="597" /></span></figure>
</p>
<ul>
<li><b>replenishRate (충전 속도):</b> 초당 생성되는 토큰 수. (예: 초당 10명 입장 가능)</li>
<li><b>burstCapacity (버스트 용량):</b> 순간적으로 몰릴 때 허용하는 최대치.</li>
<li><b>원리:</b> 토큰이 없으면 요청을 아예 거절(429 Error)하여 서버가 부하로 인해 다운되는 것을 막는다.<br />토큰 1개당 API를 호출할 수 있는데 초당 10개 생성할 수 있는게 replenishRate이고, 한 번에 100개를 받아낼 수 있는 능력이 burstCapacity</li>
</ul>
<p><b>2) Circuit Breaker (서킷 브레이커)</b> 특정 서비스(예: 유저 서비스)에 장애가 발생했을 때, 계속 요청을 보내서 전체 시스템이 같이 느려지는(연쇄 장애) 것을 방지하는 기술이다.</p>
<ul>
<li><b>동작:</b> 실패율이 임계치(예: 50%)를 넘으면 회로를 차단(Open)하고, 즉시 대체 응답(Fallback)을 보낸다.</li>
<li><b>효과:</b> 무한 로딩을 막고, 장애가 난 서버가 회복할 시간을 벌어준다.</li>
<li><b>동작 원리:</b> 에러율이 임계치(예: 50%)를 넘으면 회로를 차단(Open)하고, 즉시 대체 응답(Fallback)을 보낸다.</li>
<li><b>재미있는 점:</b> 단순히 끊는 게 아니라 Half-Open 상태를 통해 서버가 회복되었는지 '간'을 보고 다시 연결해준다.(재부팅 아닌 reOpen)</li>
</ul>
<h4><b>3. 방어선 2단계: DB 앞에서의 줄 세우기 (Lock 전략)</b></h4>
<p>Gateway를 뚫고 들어온 요청들이 하나의 데이터(예: 쿠폰 재고)를 수정하려 할 때, 데이터 무결성(Data Integrity)을 지키기 위한 전략이다.</p>
<ul>
<li>Gateway를 뚫고 들어온 '선택받은 요청'들이라고 안심할 수 없다. **하나의 쿠폰 재고(데이터)**를 두고 여러 스레드가 동시에 수정하려 하면 **동시성 이슈(Race Condition)**가 발생해 재고가 마이너스가 될 수 있다.<br /><b>1) 비관적 락 (Pessimistic Lock)<br /></b>
<ul>
<li><b>개념:</b> "충돌이 무조건 발생할 것이다"라고 비관적으로 가정하고, 데이터를 읽을 때부터 문을 걸어 잠근다.</li>
<li><b>사용처:</b> <b>선착순 쿠폰 발급, 재고 차감</b> 등 데이터 정합성이 100% 보장되어야 하는 곳</li>
</ul>
<b>2) 낙관적 락 (Optimistic Lock)</b>
<ul>
<li><b>개념:</b> "설마 충돌 나겠어?"라고 낙관적으로 가정하고 락을 걸지 않는다. 대신 수정할 때 버전(Version)을 체크한다.</li>
<li><b>사용처:</b> 충돌 빈도가 낮은 일반 게시판 수정, 회원 정보 수정 등.<br /><br /></li>
<li><b>차이점:</b> 비관적 락은 대기(Wait)를 하지만, 낙관적 락은 충돌 시 예외를 뱉고 튕겨낸다.</li>
</ul>
</li>
</ul>
<hr contenteditable="false" />
<h4><b>정리하며</b></h4>
<p>학습을 통해 대용량 트래픽 처리는 단순히 "서버 성능 좋게 만들기"가 아니라, "적절한 제어와 포기"의 미학이라는 것을 알게 되었다.</p>
<ul>
<li><b>Rate Limiter</b>로 우리 시스템이 감당 가능한 만큼만 들여보낸다.</li>
<li><b>Circuit Breaker</b>로 아픈 서버는 쉬게 해준다.</li>
<li><b>DB Lock</b>으로 최후의 데이터 무결성을 지킨다.</li>
</ul>
<p>지그재그나 무신사 같은 서비스들이 왜 이렇게 복잡한 아키텍처를 가질 수밖에 없는지 이론적으로나마 이해할 수 있는 시간이었다. 다음 강의는 kafka를 사용하고 성능테스트인데 어서 듣고 실전에 써보고 싶다!!!</p>