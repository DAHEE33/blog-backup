# [Project01]설문조사 서비스 요구사항 및 설계

**발행일:** Sun, 15 Jun 2025 15:05:59 +0900

**링크:** https://hee-story6.tistory.com/221

---

<h2>1. 설문 조사 서비스&nbsp;</h2>
<h3>기술 스택</h3>
<ul>
<li><b>DB</b>: H2 Database (개발/테스트용, 추후 실DB로 교체 용이)</li>
<li><b>ORM</b>: JPA(Hibernate)</li>
<li><b>API 명세/테스트</b>: Swagger(OpenAPI)</li>
<li><b>인프라/확장성</b>: 추후 클라우드/운영환경으로 전환 가능하게 구조화</li>
</ul>
<h3>주요 특징</h3>
<ul>
<li><b>익명 응답</b>: 로그인 없이 누구나 참여(브라우저별 UUID 활용)</li>
<li><b>설문 그룹화, 버전 관리</b>: 비즈니스적으로 의미 있는 설문 분류, 변경 이력 관리</li>
<li><b>중복 응답 제한</b>: 1회만 응답 가능</li>
<li><b>문항/옵션 자유 설계</b>: 다양한 질문 유형/옵션 지원</li>
<li><b>대용량 트래픽/운영 실전 고려</b></li>
<li><b>확장 가능한 API 구조</b>: Swagger로 문서화/테스트, 협업에 용이</li>
</ul>
<hr />
<h2>2. 기능별 상세 요구사항</h2>
<h3>2.1 설문 생성/수정/버전 관리</h3>
<h4><b>설문 생성</b></h4>
<ul>
<li>설문 그룹(시리즈) 내에 새로운 설문을 생성</li>
<li>필수값: title, description, items, startDate, endDate, isOpen</li>
<li>설문당 문항은 <b>최대 10개</b>까지 등록 가능</li>
</ul>
<h4><b>설문 수정(버전업)</b></h4>
<ul>
<li>문항(구조) 변경 시 <b>기존 설문/응답은 이력으로 보존</b>,<br />새 버전 설문을 Deep Copy 방식으로 생성</li>
<li>오타/설명 등 단순 수정은 정책적으로 예외 처리 가능(버전업 없이 바로 반영)</li>
</ul>
<h4><b>설문 만료/공개 관리</b></h4>
<ul>
<li>startDate, endDate, isOpen 값으로 설문 응답 가능/불가 자동 제어</li>
<li>만료일 경과 또는 비공개 상태에서는 응답 제출 불가</li>
</ul>
<hr />
<h3>2.2 문항(질문) 관리</h3>
<ul>
<li>설문 내 <b>1~10개</b>의 문항 등록</li>
<li>각 문항은 다음 필드로 구성:
<ul>
<li>question (질문 텍스트)</li>
<li>type (문항 유형: SHORT_TEXT, LONG_TEXT, SINGLE_CHOICE, MULTI_CHOICE)</li>
<li>required (필수 여부)</li>
<li>options (객관식의 경우 선택지 목록)</li>
</ul>
</li>
<li>**소프트 삭제(isDeleted)**로 문항 삭제 처리 (DB에서는 남아있지만 UI/API에선 미노출)</li>
</ul>
<hr />
<h3>2.3 설문 응답/응답항목 관리</h3>
<h4><b>응답 제출</b></h4>
<ul>
<li><b>익명 응답(브라우저별 UUID)으로 1회만 응답 가능</b></li>
<li>설문 버전별로 응답 관리<br />(설문 구조 변경 후에는 새 버전 설문으로만 응답 가능)</li>
<li>각 응답은 항목별 값에 대해 필수/유효성 체크 후 저장</li>
<li>만료/비공개 설문엔 응답 자체가 차단됨</li>
</ul>
<h4><b>응답 조회</b></h4>
<ul>
<li>설문별, 버전별로 전체 응답 및 각 문항별 답변 결과를 조회</li>
<li>(향후) 고급 검색/필터, 관리자 통계/대시보드 기능도 추가 예정</li>
</ul>
<hr />
<h2>3. 확장 요구사항</h2>
<ul>
<li><b>통계/조회</b>:<br />응답 데이터 실시간 통계, 고급 필터/관리자 전용 대시보드 개발</li>
<li><b>API Rate Limiting</b>:<br />과도한 요청(봇/어뷰징) 방지를 위한 정책 도입</li>
<li><b>멀티테넌시/외부 연동</b>:<br />여러 조직/고객사가 각각 독립적으로 설문 운영 가능<br />외부 시스템 연동(알림, API 등)까지 확장 고려</li>
<li><b>대용량/성능</b>:<br />인덱싱/파티셔닝/캐싱/아카이빙 등 실운영 환경의 대량 데이터 대응 설계</li>
</ul>
<hr />
<h2>4. 엔티티별 설계 및 매핑 원칙</h2>
<h3>4-1. 엔티티 구조 및 역할</h3>
<h4><b>1. SurveySeries (설문 그룹)</b></h4>
<ul>
<li><b>필드</b>: id, code(비즈니스 키), name, description, createdAt</li>
<li><b>설명</b>: 여러 설문을 그룹핑하는 상위 분류(예: 출퇴근조사, 만족도조사)</li>
<li><b>매핑</b>: Survey 엔티티에서 seriesId(FK)로만 단방향 참조</li>
</ul>
<h4><b>2. Survey (설문, 버전 포함)</b></h4>
<ul>
<li><b>필드</b>: id, seriesId(FK), version, title, description, createdAt, updatedAt, startDate, endDate, isOpen</li>
<li><b>설명</b>: 하나의 설문(폼), 버전별로 존재 가능</li>
<li><b>매핑</b>: SurveySeries, SurveyItem, SurveyResponse와 모두 id(FK)만으로 연결</li>
</ul>
<h4><b>3. SurveyItem (문항/질문)</b></h4>
<ul>
<li><b>필드</b>: id, surveyId(FK), question, description, type, required, options, isDeleted</li>
<li><b>설명</b>: 설문을 구성하는 개별 문항(질문)</li>
<li><b>매핑</b>: Survey에서 surveyId만 FK로 참조(객체참조/컬렉션 없음)</li>
</ul>
<h4><b>4. SurveyResponse (설문 응답)</b></h4>
<ul>
<li><b>필드</b>: id, surveyId(FK), uuid, submittedAt</li>
<li><b>설명</b>: 익명 사용자의 설문 1회 응답</li>
<li><b>매핑</b>: Survey에서 surveyId만 FK로 참조</li>
</ul>
<h4><b>5. SurveyResponseItem (문항별 응답)</b></h4>
<ul>
<li><b>필드</b>: id, responseId(FK), surveyItemId(FK), questionText, answer</li>
<li><b>설명</b>: 설문 응답 한 건이 가진 개별 문항별 답변</li>
<li><b>매핑</b>: SurveyResponse, SurveyItem에서 각 id(FK)만 보관</li>
</ul>
<h4><b>6. QuestionType (문항 유형 enum)</b></h4>
<ul>
<li>SHORT_TEXT, LONG_TEXT, SINGLE_CHOICE, MULTI_CHOICE</li>
<li>문항 입력 타입 제어</li>
</ul>
<hr />
<h3>4-2. 매핑/의존성 최소화 원칙</h3>
<ul>
<li>모든 연관관계는 Long id(FK) 단방향만 사용<br />(객체 참조/양방향/컬렉션 매핑 전부 제거)</li>
<li>불필요한 순환/의존성/지연 로딩 이슈 원천 차단</li>
<li>서비스/쿼리 레이어에서만 필요한 데이터 조합</li>
<li>Cascade/orphanRemoval 등도 꼭 필요한 경우에만 사용</li>
</ul>
<hr />
<h3>4-3. 설계 정리</h3>
<ul>
<li>설문 생성/수정/응답/조회 모든 흐름에서<br />Survey, SurveyItem, SurveyResponse, SurveyResponseItem, SurveySeries<br />이 5개 엔티티가 단방향(FK)으로만 연결됨</li>
<li>데이터 저장/수정/조회시<br />필요한 엔티티/필드만 골라서 효율적으로 쿼리/가공</li>
</ul>
<p>&nbsp;</p>
<p>&nbsp;</p>
<h2>5. API/DTO 예시</h2>
<h3>5.1 설문조사 생성 API</h3>
<ul>
<li>Survey(설문)에서 URL이 필요한가? <br />: 설문 생성 시, 설문에 접근할 수 있는 &ldquo;고유 URL&rdquo;을 저장/생성</li>
</ul>
<p>요청</p>
<pre class="java" id="code_1749965042918"><code>POST /api/surveys
{
  "seriesCode": "commuteSurvey",
  "title": "2024 출퇴근 설문",
  "description": "임직원 출퇴근 현황조사",
  "items": [
    {
      "question": "출근 시간은 언제입니까?",
      "type": "SINGLE_CHOICE",
      "required": true,
      "options": ["8시", "9시", "10시", "기타"]
    }
  ],
  "startDate": "2024-07-01T00:00:00",
  "endDate": "2024-07-10T23:59:59",
  "isOpen": true
}</code></pre>
<p>&nbsp;</p>
<p>응답</p>
<pre class="java" id="code_1749965056563"><code>{
  "surveyId": 1001,
  "seriesCode": "commuteSurvey",
  "version": 1,
  "title": "2024 출퇴근 설문",
  "createdAt": "2024-06-15T13:22:11"
}</code></pre>
<p>&nbsp;</p>
<p>&nbsp;</p>
<h3 style="color: #000000; text-align: start;">5.2 설문응답 제출 API</h3>
<p>&nbsp;5.2.1.고객이 설문 URL을 받는 실제 플로우</p>
<ul>
<li><b>관리자/서비스가 설문을 생성</b>
<ul>
<li>서버에서 surveyId=101인 설문이 만들어짐</li>
<li>설문 URL을 생성(<a href="https://survey.yourservice.com/surveys/101">https://survey.yourservice.com/surveys/101</a>)</li>
</ul>
</li>
<li><b>고객에게 설문 URL을 전달</b>
<ul>
<li>메일, 카톡, 사이트 등으로 설문 링크 공유</li>
</ul>
</li>
<li><b>고객이 URL을 클릭해서 설문 페이지에 진입</b>
<ul>
<li><b>이때 surveyId는 URL의 Path에서 이미 자동 추출</b>됨</li>
</ul>
</li>
<li><b>응답 작성 후, 제출</b>
<ul>
<li>POST /api/surveys/101/responses로 서버에 요청</li>
<li>서버는 URL에서 surveyId(101)을 파싱, 해당 설문에 응답 저장</li>
</ul>
</li>
</ul>
<p>&nbsp;</p>
<p>요청</p>
<pre class="java" id="code_1749965119180"><code>POST /api/surveys/1001/responses
{
  "uuid": "eb5a5b85-9932-4fa6-8430-123456789abc",
  "answers": [
    {
      "itemId": 201,
      "answer": "9시"
    }
  ]
}</code></pre>
<p>&nbsp;</p>
<p>응답</p>
<pre class="java" id="code_1749965126890"><code>{
  "responseId": 5001,
  "submittedAt": "2024-07-03T14:32:00"
}</code></pre>
<p>&nbsp;</p>
<p><br /><br /></p>
<h3 style="color: #000000; text-align: start;">5.3 설문조사 응답 전체 조회 API</h3>
<p>요청 (GET /api/surveys/{surveyId}/responses)</p>
<pre class="java" id="code_1749966117912"><code>GET /api/surveys/101/responses</code></pre>
<p>&nbsp;</p>
<p>응답</p>
<pre class="java" id="code_1749966146053"><code>[
  {
    "responseId": 5002,
    "surveyId": 101,
    "uuid": "7a02f9e4-3ee5-4e0a-b0b5-2a13a9ac23ee",
    "submittedAt": "2024-07-06T10:33:10",
    "answers": [
      {
        "itemId": 2001,
        "question": "워크숍 장소는 만족스러웠나요?",
        "answer": "매우 만족"
      },
      {
        "itemId": 2002,
        "question": "가장 기억에 남는 세션을 적어주세요.",
        "answer": "AI 기초 강연"
      },
      {
        "itemId": 2003,
        "question": "추가로 바라는 점이 있다면 적어주세요.",
        "answer": "점심시간이 더 길었으면 좋겠습니다."
      }
    ]
  }
]</code></pre>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>