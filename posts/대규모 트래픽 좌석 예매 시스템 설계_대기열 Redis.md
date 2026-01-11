# 대규모 트래픽 좌석 예매 시스템 설계_대기열, Redis

**발행일:** Fri, 19 Dec 2025 11:27:18 +0900

**링크:** https://hee-story6.tistory.com/223

---

<p>올리브영/무신사/지그재그 등 쇼핑을 즐겨하는 나인데</p>
<p>늘 시간 쿠폰만 받으려고 하면 그게 그렇게 어렵더라.</p>
<p>올리브영의 경우 12시면 11:59:45분부터 쿠폰 페이지를 누르면 대기 몇번 + 예상 시간이 생기고</p>
<p>지그재그의 경우는 페이지는 바로 들어가지면 결제하기 누르는 순간부터 대기가 생겨서 그런지 거기서부터 로딩이 있다가 결국 내가 받는 메세지는 "이미 품절 된 상품입니다"</p>
<p>ㅎㅎ</p>
<p>&nbsp;</p>
<p>이런 대기열, 대규모 트래픽 서비스가 궁금했다.</p>
<p>마침 프론트 친구들과 함께한 포폴겸 토이 프로젝트를 만들기로 했는데 여기에 대규모 트래픽 예매 서비스를 넣어보기로 했다.</p>
<p>사용하고 싶었던 거 다 공부하면서 써보자!!&nbsp;</p>
<p>&nbsp;</p>
<p>티켓팅 서비스처럼 찰나의 순간에 수만 명의 사용자가 몰리는 시스템을 설계할 때 가장 큰 고민은</p>
<p>"어떻게 하면 중복 결제를 막으면서도 사용자에게 짜증 나지 않는 경험을 줄 것인가?"</p>
<p>&nbsp;</p>
<p>오늘 고민하고 정리한 핵심 설계 전략을 잊지 않게 작성한다!</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<p>&nbsp;</p>
<p>1. 전체 프로세스 설계: 2단계 권한 분리</p>
<p>- 대기를 위한 만료시간과 좌석 선점에 대한 시간이 필요한데 이 부분에 대해서는&nbsp;</p>
<p>현재 날짜를 누르면 팝업으로 예매하기 &rarr; 좌석선택 <span style="color: #333333; text-align: start;"><span>&nbsp;</span></span>&rarr; 결제하기 이렇게 흐름이 간다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="width: 11.2791%;">단계</td>
<td style="width: 28.7209%;">핵심 트리거</td>
<td style="width: 20%;">관리 대상</td>
<td style="width: 20%;">만료 시간(예시)</td>
<td style="width: 20%;">만료 시 결과</td>
</tr>
<tr>
<td style="width: 11.2791%;">좌석 선택</td>
<td style="width: 28.7209%;">대기열 통과 시</td>
<td style="width: 20%;">페이지 이용 권한</td>
<td style="width: 20%;">10분</td>
<td style="width: 20%;">대기열로 재이동</td>
</tr>
<tr>
<td style="width: 11.2791%;">결제 진행</td>
<td style="width: 28.7209%;">'결제하기' 클릭</td>
<td style="width: 20%;">좌석 임시 선점</td>
<td style="width: 20%;">5분</td>
<td style="width: 20%;">좌석 점유 해제</td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<p>2. 동시성 제어: Redis를 활용한 "임시 선점(Lock)"</p>
<p>처음 실시간 좌석 공유고 websocket을 써보고 싶어서 이걸 써야지 했었는데 하단의 차이로 폴링과 reids를 이용하기로 했다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="width: 100%;">
<ul>
<li><span><b>WebSocket:</b> 서버와 클라이언트가 연결(Connection)을 계속 유지해야 합니다. 10만 명이 접속하면 서버는 10만 개의 연결 통로를 계속 열어두어야 하므로 <b>서버 메모리(RAM)와 부하</b>가 엄청납니다.</span></li>
<li><span><b>Short Polling:</b> 3~5초마다 API를 쏘지만, 응답을 주면 즉시 연결이 끊깁니다.</span><br />
<ul>
<li><span><b>트래픽 문제 해결법:</b> 이때 API가 DB를 조회하면 서버가 터지지만, **Redis에 저장된 가벼운 데이터(JSON 스냅샷)**만 읽어서 바로 던져주면 서버 부하를 최소화할 수 있습니다.</span></li>
<li><span><b>현실적인 타협안:</b> 트래픽이 아주 몰리는 오픈 직후에는 Polling 주기를 10초로 늘리거나, 아예 클라이언트가 "좌석 새로고침" 버튼을 누를 때만 조회하게 만들기도 합니다.</span></li>
</ul>
</li>
</ul>
</td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>3. 그렇다면 왜 Redis를 쓰는가?</p>
<p>가장 큰 차이는 <b>속도</b>와 휘발성(TTL)이다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="width: 100%;">
<ul>
<li><b>DB (MySQL 등):</b><span>&nbsp;</span>디스크에 저장하므로 안전하지만 느립니다. "결제 중"인 상태를 DB에 저장하면, 수많은 사용자가 "결제 취소"를 하거나 "이탈"했을 때 일일이 DB의 상태를 다시 Available로 바꾸는 Update 쿼리를 날려야 합니다. 이는 DB에 큰 부하를 줍니다.</li>
<li><b>Redis:</b><span>&nbsp;</span>메모리(RAM)에 저장해서<span>&nbsp;</span><b>DB보다 수십 배 빠릅니다.</b><span>&nbsp;</span>*<span>&nbsp;</span><b>핵심 기능 (TTL):</b><span>&nbsp;</span>"이 좌석은 5분 동안만 사용자 A가 점유한다"라고 설정하면, 5분이 지나면 Redis가<span>&nbsp;</span><b>알아서 데이터를 지워버립니다.</b><span>&nbsp;</span>* 따라서 사용자 A가 결제하다가 그냥 브라우저를 닫고 도망가도, 서버가 별도의 작업을 안 해도 5분 뒤에 좌석이 자동으로 풀립니다.</li>
</ul>
</td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<p>&nbsp;</p>
<h4>[실제 흐름]</h4>
<ol>
<li><b>사용자 A가 좌석 1번 선택 후 결제 클릭</b>
<ul>
<li>서버는 먼저 Redis에 "seat:1"이라는 키가 있는지 확인</li>
<li>없다면 Redis에 "seat:1" : "occupying" 이라고 저장하고 유효시간 5분을 Lock</li>
</ul>
</li>
<li><b>사용자 B가 좌석 1번 선택 후 결제 클릭</b>
<ul>
<li>서버가 Redis를 보니 이미 "seat:1" 키가 쥰재</li>
<li>서버는 DB까지 가보지도 않고 바로 B에게 "이미 선점된 좌석입니다"라고 응답함으로써 DB 부하 방지</li>
</ul>
</li>
<li><b>사용자 A가 결제 완료</b>
<ul>
<li>그제서야 DB에 1번 좌석을 "예약 완료" 변경</li>
<li>Redis에 있던 임시 키 "seat:1"은 삭제</li>
</ul>
</li>
</ol>
<p>&nbsp;</p>