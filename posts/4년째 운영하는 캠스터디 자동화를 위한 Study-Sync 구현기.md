# 4년째 운영하는 캠스터디, 자동화를 위한 Study-Sync 구현기

**발행일:** Sun, 21 Jun 2026 12:35:22 +0900

**링크:** https://hee-story6.tistory.com/246

---

<div>
<div>&nbsp;</div>
</div>
<div>
<p>국비 수강 시절, 공부 습관이 약했던 나를 붙잡기 위해 캠스터디를 시작했다. 캠을 켜놓고 목표 시간에 맞춰 공부한 뒤 인증하는 방식이었다. 그게 벌써 4년이 넘었다. 지금은 약 22명을 관리하는 방장이 되어 있다.</p>
<p>&nbsp;</p>
<p>문제는 어느 순간부터 "공부"보다 "운영"이 더 힘들어졌다는 점이었다.</p>
<h3 style="color: #000000; text-align: start;">매일 반복되는 수작업들</h3>
</div>
<div>
<div>
<ul>
<li>각 스터디원의 공부 시간 확인</li>
<li>병가/시험/월휴 같은 예외 처리</li>
<li>벌금 계산 후 1/N 정산 및 입금 관리</li>
</ul>
</div>
</div>
<div><figure class="imageblock alignCenter"><span><img height="470" src="https://blog.kakaocdn.net/dn/pZUtF/dJMcafNR34T/mLsaG6Y4vHxxaPK641kuhK/img.png" width="300" /></span></figure>

<p>&nbsp;</p>
<p>매일 이렇게 올라오는 단톡방 인증 캡처를 하나하나 확인하고, 다음 날 처리를 해야 했다. 수작업이다 보니 실수도 있었고, 휴가를 다녀온 날 이후엔 밀린 업무처럼 긴 시간을 쏟아야 했다. (솔직히 이게 제일 두려웠다.) &nbsp;</p>
<p>시간을 거짓으로 제출하는 경우도 있어 모든 인증 사진을 직접 대조해야 했다. 그리고 무엇보다 힘들었던 건 응대였다.&nbsp; "이번 한 번만 봐주세요", "깜빡했어요" 같은 요청을 하나씩 처리하다 보면, 공정성을 지키려는 기준과 사람적인 마음 사이에서 스트레스가 쌓였다.</p>
<figure class="imageblock alignCenter"><span><img height="352" src="https://blog.kakaocdn.net/dn/bUc5tQ/dJMcafNR35o/IFNIAROFz2sEwVxfP2SV80/img.png" width="600" /></span></figure>

<p>&nbsp;</p>
<p>이런 톡에 가끔 어떻게 답을 해야할지 난감할 때도 있고, 바로 수긍을 못하시는 분들도 있어 지속적인 대화를 해야하는 경우도 있었다.</p>
</div>
<div>
<p><b>처음 개발자가 된 이유가 사람들이 불편한 것을 해결해주겠다. 였는데 그게 지금이다. 나를 위한 프로젝트!</b><b></b></p>
<h3>목표: 기존 흐름을 깨지 않는 자동화</h3>
<p>자동화 설계 시 가장 먼저 정한 원칙은 다음이었다.</p>
<ul>
<li>기존 오픈카톡 사용 흐름을 최대한 유지할 것</li>
<li>회원가입/추가 앱 설치 같은 진입 장벽을 만들지 않을 것</li>
<li>"버튼 누르고 인증" 정도의 최소 행동만 요구할 것</li>
</ul>
<p>이 부분을 꽤 오래 고민했다. 별도 웹 페이지를 만들어 그쪽에서 인증하게 하면, 카카오톡의 편리함이 오히려 반감된다. 결국 가장 이질감이 적은 방식은 <b>카카오 오픈빌더 챗봇 기반 UX</b>였다. 사용자는 익숙한 채팅방에서 버튼만 누르면 되고, 서버는 그 입력을 기준으로 규칙을 일관되게 처리한다.</p>
<h3>구현 방식 (Study-Sync 아키텍처)</h3>
<p>전체 흐름은 다음과 같다.</p>
<ol>
<li>카카오톡에서 인증 이미지/버튼 입력</li>
<li>FastAPI webhook 수신</li>
<li>OCR로 공부시간&middot;누적시간 추출</li>
<li>규칙 엔진으로 판정 (정상/미달/결석/예외)</li>
<li>Google Sheets에 기록 및 상태 업데이트(DB 겸용)</li>
<li>배치 작업으로 결석 처리/주간 정산 자동화</li>
</ol>
<p>기술 스택은 다음과 같다.</p>
<ul>
<li><b>Backend</b>: FastAPI (Python)</li>
<li><b>OCR</b>: Google Cloud Vision API</li>
<li><b>저장소</b>: Google Sheets API</li>
<li><b>챗봇</b>: 카카오 i 오픈빌더</li>
<li><b>배치 자동화</b>: GitHub Actions Cron</li>
</ul>
<p>핵심은 "화려한 UI"가 아니라 <b>운영 규칙을 코드로 고정</b>하는 것이었다.</p>
<h3>기술적으로 가장 고민했던 것: 카카오 4초 응답 제한</h3>
<h4>문제</h4>
<p>카카오 오픈빌더는 스킬 서버가 <b>4초 안에 응답</b>해야 한다. 그런데 이 플로우에는 OCR 판독, 누적 시간 검증, 벌금/정산 로직까지 한 번에 들어가야 했다. 동기 처리로 구성했더니 타임아웃이 간헐적으로 터졌고, 사용자 입장에선 인증이 됐는지 안 됐는지 알 수 없는 상황이 발생했다.</p>
<h4>해결</h4>
<p>요청 처리를 두 단계로 분리했다.</p>
<ol>
<li><b>즉시 응답</b>: "인증이 접수되었습니다. 분석 후 결과를 안내드릴게요." 반환</li>
<li><b>비동기 처리</b>: OCR/검증/정산을 백그라운드에서 처리 후 최종 결과 메시지 전송</li>
</ol>
<p>사용자 체감은 "바로 접수됨", 시스템 내부는 "안정적으로 후속 처리"하는 구조다.</p>
<figure class="imageblock alignCenter"><span><img height="440" src="https://blog.kakaocdn.net/dn/cMCfPA/dJMcafmMud4/Lmt7cvyvCRTGfpb560UAN0/img.png" width="300" /></span></figure>

<h4>결과</h4>
<ul>
<li>타임아웃성 오류/혼선 감소</li>
<li>"왜 답이 안 와요?" 류의 운영 문의 감소</li>
<li>도입 2개월 차, 운영자가 체감할 정도로 안정화 효과 확인</li>
</ul>
<h3>운영에서 중요했던 로직들</h3>
<p><b>시간 검증 로직</b> 인증 가능 시간, 마감 시간, 예외 인정 구간을 코드로 명확히 정의했다. 방장 컨디션에 따라 판단이 달라지는 문제가 줄었다.</p>
<p><b>휴무/예외 처리 자동화</b> 반휴&middot;주휴&middot;월휴의 잔여량 확인과 차감을 버튼 플로우로 자동 처리했다. 수기 누락이나 중복 처리가 사실상 사라졌다.</p>
<p><b>조작 방지 </b>처음엔 OCR로 읽은 당일/누적 시간을 기존 데이터와 교차 검증해 비정상 패턴을 감지하려 했다. 그런데 실운영해보니 스터디 외 시간에 공부를 누적하는 멤버도 있어서 오탐이 잦았다. 결국 시간 교차검증은 걷어내고, 닉네임 확인 수준으로 다운그레이드했다. 완벽한 설계보다 <b>운영 가능한 설계</b>가 더 중요했다.</p>
<h3>결과: 감정노동이 줄었다</h3>
<p>이 시스템을 만들고 나서 가장 크게 달라진 건 단순 작업 시간보다 <b>심리적 피로도</b>였다.</p>
<ul>
<li>누가 예외 대상인지, 기준이 시스템에 의해 동일하게 적용됨</li>
<li>"이번 한 번만요"에 당당하게 "시스템상 어렵습니다" 답할 수 있게 됨</li>
<li>주간 정산이 자동화되어 반복 계산 실수 감소</li>
<li>실시간 대시보드로 벌금 &middot; 출결 &middot; 잔여 월휴 &middot; 예치금 현황 확인 가능</li>
<li>상금 배분도 자동 정리</li>
</ul>
<figure class="imagegridblock">
  <div class="image-container"><span style="width: 36.9273%; margin-right: 10px;"><img height="352" src="https://blog.kakaocdn.net/dn/cXxRuN/dJMcajbvJjW/3AZrAocquiV9I7DN720bgK/img.png" width="706" /></span><span style="width: 33.5349%; margin-right: 10px;"><img height="392" src="https://blog.kakaocdn.net/dn/BGGRB/dJMcahkCcrt/ekK542atmL384eKIyJ7sMK/img.png" width="714" /></span><span style="width: 27.2122%;"><img height="1410" src="https://blog.kakaocdn.net/dn/bC2886/dJMcafUBErV/Jq0kEsuRaIH2kOuvtYXDn0/img.png" width="2084" /></span></div>
</figure>

<p>매번 구글 시트에 기록한 캡처본을 올려 확인을 바랬었지만 각 스터디원들도 실시간으로 직접 확인 가능하니 스터디원에게도 나름 좋은 평판 받는중ㅎㅎㅎ</p>
<h3>마무리</h3>
<p>거창한 서비스라기보다, 오래 운영해온 스터디의 실제 문제를 해결하기 위한 도구다.</p>
<p>솔직히 말하면 <b>처음으로 혼자 설계하고, 혼자 배포해서, 실제 사람들이 매일 쓰는 서비스가 생겼다는 게 아직도 신기하고 재밌다.</b> 애착이 가서 자꾸 더 수정하고, 관리하고 싶어져..</p>
<p>버그가 터지면 당연히 식겁하지만, 그 버그를 잡고 나서 시스템이 조용히 잘 돌아가는 걸 보면 괜히 뿌듯해진다.</p>
<p><br />지금은 새벽 캠스터디도 지금 코드에서 좀 더 유동성 있게 변경하여 적용 예정이다.</p>
<p>그 다음엔 또 다른 누군가의 불편함을 해결할 무언가를 만들고 싶다.</p>
<p>결국 개발자가 된 이유로 다시 돌아온 것 같아서, 그게 좋다!&nbsp;</p>
</div>