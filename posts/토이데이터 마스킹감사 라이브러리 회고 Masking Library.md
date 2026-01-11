# [토이]데이터 마스킹/감사 라이브러리 회고: Masking Library

**발행일:** Wed, 9 Jul 2025 21:51:32 +0900

**링크:** https://hee-story6.tistory.com/222

---

<p style="text-align: center;">&nbsp;</p>
<p><figure class="imageblock alignCenter"><span><img height="96" src="https://blog.kakaocdn.net/dn/AW8LS/btsPckA4h92/Khal7TPYp2KZtat2FphKq0/img.png" width="244" /></span></figure>
</p>
<blockquote><span style="font-family: 'Noto Serif KR';"> 라이브러리 생성, STMP, Webhook, CI/CD</span></blockquote>
<p>&nbsp;</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<h2>1. 프로젝트 배경</h2>
<ul>
<li><b>요구사항</b>
<ul>
<li>개인정보(이메일, SSN 등)를 다양한 방식(마스킹, 토큰화, 암호화)으로 처리해야 하는 비즈니스 로직이 필요</li>
<li>처리 과정 전후에 감사(audit) 로그를 남겨야 했고, 이는 콘솔&middot;DB&middot;Slack&middot;Email 등 여러 경로로 통합 관리.</li>
</ul>
</li>
<li><b>목표</b>
<ul>
<li>Action/Step 기반의 <b>유연한 파이프라인</b> 구현</li>
<li><b>YAML 외부화</b>를 통한 감사 설정(채널, SMTP, Webhook)</li>
<li><b>테스트 자동화</b>(단위 + 통합) 및 CI/CD 적용</li>
</ul>
</li>
</ul>
<p>&nbsp; &nbsp;</p>
<h2>2. 주요 학습/경험 포인트</h2>
<h3>2.1 설계 경험</h3>
<ul>
<li><b>Action vs Step</b>
<ul>
<li>MaskAction, TokenizeAction, EncryptAction 등 단일 책임(Action)을 통해 <span style="color: #006dd7;">재사용성을 높임</span></li>
<li>MaskPipelineBuilder를 통해 원하는 순서대로 Step을 조합하는 파이프라인 빌더 패턴을 적용</li>
</ul>
</li>
<li><b>전략 패턴(Strategy Pattern)</b>
<ul>
<li>마스킹(MaskStrategy), 토큰화(TokenizationStrategy), 암호화(EncryptionStrategy)를 인터페이스로 분리하고, 구현체를 주입하여 런타임에 선택할 수 있도록 함</li>
</ul>
</li>
<li><b>템플릿 외부화</b>
<ul>
<li>audit-templates.yml에서 Slack/Webhook, Email, DB 설정을 모두 관리하게 하여, <span style="color: #006dd7;">하드코딩 없이</span> 운영 환경별 설정 분리가 가능</li>
</ul>
</li>
</ul>
<h3>2.2 구현 및 기술 스택(상세 하단, git README 참고)</h3>
<ul>
<li><b>Java 8 + Gradle (Kotlin DSL)</b></li>
<li><b>Jackson Databind</b>로 YAML &rarr; DTO 바인딩</li>
<li><b>JUnit5</b> + <b>WireMock</b>(Slack stub) + <b>GreenMail</b>(SMTP 테스트) + <b>H2</b>(in-memory DB)로 통합 테스트 자동화</li>
<li><b>AuditEventHandler</b> 추상화:
<ul>
<li>콘솔, DB, Slack, Email 각 핸들러를 구현</li>
<li>DatabaseAuditEventHandler: JDBC PreparedStatement 기반 INSERT</li>
<li>EmailAuditEventHandler: JavaMail + STARTTLS 설정</li>
<li>SlackAuditEventHandler: Incoming Webhook 호출</li>
</ul>
</li>
</ul>
<h3><span>2.3. GitHub Actions 워크플로우</span></h3>
<ul>
<li><span><b>ci.yml</b></span><span>: PR 오픈 시 </span><span>./gradlew test</span><span> 실행, 메인 머지 시 </span><span>./gradlew publish</span><span>로 Maven Central/JitPack 배포</span></li>
<li><span><b>시크릿 관리</b></span><span>: SMTP 계정, Webhook URL, Maven 퍼블리시 토큰을 GitHub Secrets로 안전하게 등록</span></li>
<li><span><b>품질 관리</b></span><span>: Javadoc, 코드 커버리지(60% 이상), SpotBugs 정적 분석, 라이선스&middot;SCM 정보 검증</span></li>
</ul>
<h3><span>2.4 테스트 자동화의 깨달음</span></h3>
<ul>
<li><span><b>통합 테스트</b></span><span>: WireMock + GreenMail + H2를 동시에 띄워 </span><span>FullPipelineIntegrationTest</span><span> 하나로 전체 플로우 검증</span></li>
<li><span>오타 하나(&ldquo;ture&rdquo; vs </span><span>true</span><span>)로 STARTTLS 에러 발생 &rarr; </span><span><b>환경별 설정</b></span><span>(yml vs 코드) 검증 중요성 체감</span></li>
<li><span><b>의존성 스코프</b></span><span> 관리 학습: </span><span>testImplementation</span><span> vs </span><span>implementation</span><span> 차이로 인해 런타임 클래스 누락 경험</span></li>
</ul>
<ul>
<li>&nbsp;</li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="774" src="https://blog.kakaocdn.net/dn/cT5BTj/btsPcFLK3CH/zEmBhFQtGnPX7VlAG0jNGk/img.png" width="1283" /></span><figcaption>github의 CI/CD의 수많은 경험</figcaption>
</figure>
</p>
<h2>&nbsp;</h2>
<h2>3. 아쉬웠던 점 &amp; 개선 아이디어</h2>
<ol>
<li><b>플러그인 확장 포인트 부족</b>
<ul>
<li>현재는 새 전략 구현체를 코드에 직접 추가해야 함.</li>
<li>SPI(Service Provider Interface)나 java.util.ServiceLoader를 활용해, 런타임에 외부 JAR을 플러그인으로 로딩할 수 있도록 개선.</li>
</ul>
</li>
<li><b>Kafka&middot;Event Handler 연동</b>
<ul>
<li>트랜잭션 경계에서 바로 DB/Email/Slack으로 로깅하는 대신, 이벤트 버스로 분리해 장애 내성을 높이는 구조로 발전.</li>
</ul>
</li>
<li><b>템플릿 엔진 도입</b>
<ul>
<li>현재는 ${field}/before/after 단순 치환.</li>
<li>Thymeleaf, Mustache 같은 템플릿 엔진을 도입하면 더 복잡한 메시지 포맷도 유연하게 지원</li>
</ul>
</li>
</ol>
<hr />
<h2>4. 앞으로의 로드맵</h2>
<ol>
<li><b>이메일&middot;DB&middot;Slack 동시&middot;선택적 전송</b> API 개선</li>
<li><b>Spring Boot 스타터</b> 패키징 (Auto-configuration 지원)</li>
<li><b>추가 전략</b>: 라운딩, 날짜 포맷 변환, 필드 단위 필터링 등</li>
<li><b>모니터링 대시보드</b>: 감사 로그를 시각화하는 간단한 웹 UI 제공</li>
</ol>
<hr contenteditable="false" />
<p>&nbsp;</p>
<p><span>이번 프로젝트를 통해, Java 라이브러리 개발의 핵심 요소&mdash;</span><span><b>설계</b></span><span>, </span><span><b>테스트 자동화</b></span><span>, </span><span><b>CI/CD</b></span><span>, </span><span><b>배포</b></span><span>&mdash;를 처음부터 끝까지 직접 구현해 보았습니다. 시행착오가 많았지만, 하나하나 해결해나가며 쌓인 경험은 실무 역량으로 크게 성장한 거 같닿ㅎㅎ. 앞으로는 이 기반 위에 </span><span><b>플러그인 확장</b></span><span>, </span><span><b>이벤트 기반 로깅</b></span><span>, </span><span><b>템플릿 엔진</b></span><span> 등을 더해 오픈소스 생태계에 기여하고 싶다. </span></p>
<p>&nbsp;</p>
<p><span><b>GitHub</b></span><span>: <a href="https://github.com/DAHEE33/masking-library-dsl.git" rel="noopener&nbsp;noreferrer" target="_blank">https://github.com/DAHEE33/masking-library-dsl.git</a></span><span></span><br /><span><b>기여 환영</b></span><span> (Fork &amp; PR)</span><br /><span><b>라이선스</b></span><span>: Apache‑2.0</span></p>