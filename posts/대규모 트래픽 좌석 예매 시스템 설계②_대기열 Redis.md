# 대규모 트래픽 좌석 예매 시스템 설계②_대기열, Redis

**발행일:** Sat, 27 Dec 2025 16:11:08 +0900

**링크:** https://hee-story6.tistory.com/224

---

<h3>전체 예매 프로세스 흐름도</h3>
<p><b>핵심:</b> 대기열 &rarr; 좌석 선택(눈으로만) &rarr; 결제하기 버튼(이때 락!)</p>
<p>&nbsp;</p>
<h4>1단계: 대기열 진입 (문지기)</h4>
<p>사용자가 공연 상세 페이지에서 <b>[예매하기]</b> 버튼을 누름</p>
<ol>
<li>바로 <span style="color: #333333; text-align: start;"><span>&nbsp;</span>좌석표가 나오지 않고</span>&nbsp;<b><b>대기 화면 뜸<span>&nbsp;</span>&rarr;<span>&nbsp;</span></b></b><span style="color: #333333; text-align: start;"><b><span>대기열 진입</span></b><span>:<span>&nbsp;</span></span><span>POST /api/v1/queue/enter</span></span> &nbsp;</li>
<li>현재 대기 50명... 10명..." 이렇게 순번을 확인 <b><b>&rarr; 대기<b><span>중 (Polling)</span></b><span style="color: #333333; text-align: start;">:</span></b></b>GET /api/v1/queue/{queueId}</li>
<li>좌석 선택 페이지&nbsp;</li>
<li>나의 상태가 READY가 되면 <b>입장 가능</b> <b><b>&rarr; </b></b><span style="color: #333333; text-align: start;"><span>POST /api/v1/queue/{queueId}/enter</span><span>를 호출하여 입장(SessionId)</span></span></li>
</ol>
<hr />
<h4>2단계: 좌석 선택 (눈치 게임)</h4>
<p>좌석 배치도에서 좌석 선택</p>
<ol>
<li><span><b><span>좌석 조회</span></b><span>: </span><span>GET /api/v1/schedules/{id}/seats</span><span> </span></span><span><span></span></span><br />
<ul>
<li>사용자가 화면에서 A1, A2 좌석을 클릭</li>
<li><b>이때는 서버에 아무런 요청을 보내지 않음</b>&nbsp;(단순 프론트엔드 상태)</li>
<li>즉, 내가 A1을 찍고 있어도, 아직 내 것이 아님</li>
</ul>
</li>
<li><span><b><span>좌석 클릭 (UI)</span></b><span>: </span></span><span><span></span></span></li>
</ol>
<hr />
<h4>3단계: 결제하기 버튼 클릭 (진검 승부)&nbsp;</h4>
<p>사용자가 좌석을 다 고르고 <b>[결제하기]</b> 버튼을 누르는 순간 서버 API가 호출됩니다.</p>
<ul>
<li><span></span><span><span>이 API 하나가 "<b>좌석 락(Lock) + 예매 데이터 생성 + 결제 준비</b>"를 한 번에 처리합니다</span></span><span><span></span></span><span>.</span></li>
<li><span><b><span>API 호출</span></b><span>: </span><span>POST /api/v1/reservations</span><span> </span></span><span><span></span></span></li>
</ul>
<p>&nbsp;</p>
<hr contenteditable="false" />
<p>&nbsp;</p>
<p><b>[시나리오: 사용자 A vs 사용자 B]</b></p>
<p>상황: 둘 다 A1 좌석을 보고 있고, 거의 동시에 [결제하기]를 눌렀습니다.</p>
<ol>
<li><b>사용자 A (0.1초 빠름)</b>:
<ul>
<li>서버: "A1 좌석 락(Lock) 성공!"</li>
<li>결과: 200 OK 응답을 받고 <b>토스 결제창</b>으로 넘어갑니다.</li>
</ul>
</li>
<li><b>사용자 B (0.1초 느림)</b>:
<ul>
<li>서버: "어? A1 좌석은 방금 A가 락 걸었는데?"</li>
<li><span></span><span><span>결과: </span><span>409 Conflict</span><span> 에러 발생</span></span><span><span></span></span><span>.</span></li>
<li><span></span><span><span>응답 메시지: </span><span>"선택하신 좌석이 이미 예약되었습니다"</span></span><span><span></span></span><span>.</span></li>
</ul>
</li>
<li><b>사용자 B의 화면 처리</b>:
<ul>
<li>프론트엔드: 에러 메시지를 alert으로 띄워줍니다.</li>
<li><b>새로고침</b>: 좌석 선택 페이지를 새로고침(또는 리로드)하여, A1이 이미 나갔다는(SOLD/LOCKED) 최신 상태의 좌석표를 다시 보여줍니다<span style="letter-spacing: 0px;"></span><span style="letter-spacing: 0px;">.</span></li>
</ul>
</li>
</ol>
<hr />
<h3>설계 시 주의할 점</h3>
<ol>
<li><b>DB 스키마 관점</b>:
<ul>
<li>POST /reservations 요청이 들어오면, DB(또는 Redis)에서 해당 좌석이 <b>이미 선점(PENDING)되었거나 판매(SOLD)되었는지</b> 확인하는 로직이 가장 중요합니다.</li>
<li>앞서 설계한 ReservationSeat 엔티티가 생성되기 전에 이 검증이 먼저 수행되어야 합니다.</li>
</ul>
</li>
<li><b>트랜잭션</b>:
<ul>
<li><span></span><span><span>여러 좌석을 선택했을 때 (예: A1, A2), 하나라도 이미 선점되어 있으면 </span><b><span>전체 실패(All or Nothing)</span></b><span> 처리해야 합니다</span></span><span><span></span></span><span>. A1은 성공하고 A2는 실패하는 상황은 없습니다.</span></li>
</ul>
</li>
</ol>