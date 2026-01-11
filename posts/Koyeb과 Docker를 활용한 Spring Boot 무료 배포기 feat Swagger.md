# Koyeb과 Docker를 활용한 Spring Boot 무료 배포기 (feat. Swagger 공유)

**발행일:** Sat, 10 Jan 2026 17:28:29 +0900

**링크:** https://hee-story6.tistory.com/227

---

<h2>1. 왜 Koyeb을 선택했는가?</h2>
<p>협업 과정에서 백엔드 개발자로서 가장 먼저 부딪힌 문제는 'API 명세서(Swagger) 공유'였다. 로컬 환경에서 구동되는 Swagger는 외부 협업자(프론트엔드)가 접근할 수 없기 때문. 이를 해결하기 위해 외부 배포가 필요했고, 여러 플랫폼 중 <b>Koyeb</b>을 선택한 이유는 다음과 같다.</p>
<ul>
<li><b>Spring Boot 배포 최적화:</b> Dockerfile만 있으면 별도의 복잡한 설정 없이 즉시 배포가 가능.</li>
<li><b>Git-Ops 지원:</b> GitHub 리포지토리와 연동되어 push 발생 시 자동으로 빌드 및 배포(CI/CD)가 진행.</li>
<li><b>DB 연동 편의성:</b> Neon(PostgreSQL) 등 외부 DB와 연동하여 서버를 운영하기 좋음.</li>
<li><b>가성비:</b> 초기 테스트 단계에서 무료 또는 매우 저렴한 비용(Micro 인스턴스)으로 고성능 인프라를 경험.</li>
</ul>
<p><b>  프론트/백엔드 분리 배포 시 알아두면 좋은 이론: CORS</b> 서버와 클라이언트의 도메인이 다를 경우 브라우저에서 보안상 이유로 요청을 차단합니다. 배포 시 백엔드 코드 내에서 프론트엔드 배포 주소를 <b>CORS 허용 리스트</b>에 반드시 추가해야 한다.</p>
<p>(다음 블로그 글 , 작성 시 링크 연동)</p>
<h2>2. 배포 준비: Dockerfile 작성</h2>
<p>배포의 핵심은 <b>Dockerfile</b>입니다. 이는 "어떤 환경에서 어떤 명령어를 통해 앱을 실행할지" 정의한 설정 파일이다. <span style="color: #333333; text-align: start;">이 파일에는 Docker 파일에 대한 파일 읽는 권한부터 자바 실행 메모리까지 담는다.&nbsp;<span>&nbsp;</span></span></p>
<p>배포 플랫폼은 이 파일을 읽어 동일한 환경의 컨테이너를 생성합니다.</p>
<pre class="java" id="code_1768032844088"><code># 예시: 간단한 Spring Boot Dockerfile 구조
FROM openjdk:17-jdk-slim
COPY build/libs/*.jar app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]</code></pre>
<p>&nbsp;</p>
<p>&nbsp;</p>
<h2>3. GitHub 연동 및 브랜치 전략</h2>
<ol>
<li><b>커밋 &amp; 푸시:</b> GitHub 연동 방식이므로 코드를 push해야 빌드가 시작됩니다.</li>
<li><b>브랜치 관리:</b> 메인 서비스에 영향을 주지 않기 위해 처음에는 <b>테스트용 개인 브랜치</b>에서 작업을 진행한 뒤, Koyeb 설정에서 해당 브랜치를 타겟으로 지정합니다.(개인 브랜치를 koyeb에 적용하는 건 뒤에 나옴)</li>
</ol>
<h2>4. Koyeb 설정 및 서비스 생성</h2>
<h3>회원가입 및 프로젝트 생성</h3>
<ul>
<li><a href="https://www.koyeb.com/">Koyeb 공식 홈페이지</a>에서 GitHub 계정으로 가입하는 것을 권장. (이메일 가입 시 인증 코드가 스팸함으로 갈 수 있으니 주의)</li>
</ul>
<p><a href="https://www.koyeb.com/" rel="noopener&nbsp;noreferrer" target="_blank">https://www.koyeb.com/</a></p>
<figure contenteditable="false" id="og_1767938865546"><a href="https://www.koyeb.com/" rel="noopener" target="_blank">
<div class="og-image">&nbsp;</div>
<div class="og-text">
<p class="og-title">Koyeb: High-performance Infrastructure for APIs, Inference, and Databases</p>
<p class="og-desc">Deploy intensive applications across GPUs, CPUs, and Accelerators in minutes - scale in 50+ locations.</p>
<p class="og-host">www.koyeb.com</p>
</div>
</a></figure>
<p>&nbsp;</p>
<ul>
<li>Organization<span style="color: #333333; text-align: start;"><span>&nbsp;</span>설정 후</span> Organization's name 입력한 뒤에 각 물음에 대해 클릭하면 바로 프로젝트 생성</li>
<li>GitHub을 클릭&nbsp;&rarr; install GitHub app 클릭 하고 어떤 리포지토리를 연결할지 선택 &rarr; all repositories 선택 &rarr; 메일 검증</li>
</ul>
<p><figure class="imagegridblock">
  <div class="image-container"><span style="width: 53.5962%; margin-right: 10px;"><img height="960" src="https://blog.kakaocdn.net/dn/cVz4gm/dJMcaaRw4W0/uuJpTwbkCqZ5VZfOL5F8Ik/img.png" width="2340" /></span><span style="width: 45.2411%;"><img height="1217" src="https://blog.kakaocdn.net/dn/cyjzM3/dJMcabv8pUC/nus5n8eyJPRglEGhmV5cS1/img.png" width="2504" /></span></div>
</figure>
</p>
<p>&nbsp;</p>
<ul>
<li>&nbsp;install GitHub app 클릭 하고 어떤 리포지토리를 연결할지 선택&nbsp;&rarr;&nbsp;all repositories 선택 &rarr; Save</li>
</ul>
<p><figure class="imagegridblock">
  <div class="image-container"><span style="width: 68.2635%; margin-right: 10px;"><img height="732" src="https://blog.kakaocdn.net/dn/0UHNS/dJMcaaYiM93/fIeX2hPkRXihQhlSM977e1/img.png" width="2293" /></span><span style="width: 30.5737%;"><img height="938" src="https://blog.kakaocdn.net/dn/bzcSgO/dJMcaiPv6fN/hNWPtuNBxUDRYxtseVRCD1/img.png" width="1316" /></span></div>
</figure>
<figure class="imagegridblock">
  <div class="image-container"><span style="width: 41.3052%; margin-right: 10px;"><img height="1380" src="https://blog.kakaocdn.net/dn/cBDChV/dJMcac9Ba95/1W1KJw9KilRpCSdopYxVHK/img.png" width="1032" /></span><span style="width: 57.532%;"><img height="745" src="https://blog.kakaocdn.net/dn/eHcGPt/dJMcadAFtSs/QKoe1lBE4H1k9YBaPAa7ok/img.png" width="776" /></span></div>
</figure>
</p>
<p>&nbsp;</p>
<ul>
<li>Koyeb의 service를 들어가면 GitHub &rarr; 연결 된 gitHub Repository가 보인다.</li>
</ul>
<p><span style="color: #006dd7;"><b>여기서 처음과 동일한 화면이 반복된다면 Danger Zone에서 Uninstall "Koyeb" 후에 다시 작업을 반복하면 보인다.</b></span></p>
<p><figure class="imageblock alignCenter"><span><img height="419" src="https://blog.kakaocdn.net/dn/wG7V7/dJMcaiounA5/er3T8TOuUFYTNOhjUO48TK/img.png" width="969" /></span></figure>
</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<h3>서비스 상세 설정</h3>
<p>가장 중요한 설정 단계라고 생각한다.</p>
<p>&nbsp;</p>
<p><b>1. Build 방식 선택:</b> Dockerfile을 선택한다.(각자 방식에 맞게)</p>
<ul>
<li><b>주의:</b> Work directory는 루트 경로를, Dockerfile location은 해당 워크 디렉토리로부터의 상대 경로를 적어야 한다. (예: @backend/Dockerfile) 경로 설정이 잘못되면 빌드 시 Dockerfile을 찾지 못하는 오류가 발생!</li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="711" src="https://blog.kakaocdn.net/dn/BaHDx/dJMcaaKLCOY/fjFMrxdoNjWRF6Fa7xcRfk/img.png" width="947" /></span></figure>
</p>
<p>&nbsp;</p>
<p><b>2. 인스턴스 및 리전 선택:</b> * <b>Micro 인스턴스:</b> 테스트용으로 최적의 가성비(월 약 $5.36)를 제공.</p>
<ul>
<li><b>Tokyo 리전:</b> 한국 사용자에게 가장 빠른 응답 속도(Low Latency)를 제공하기 위해 물리적으로 가까운 일본 리전을 선택</li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="635" src="https://blog.kakaocdn.net/dn/cTZW72/dJMcafyxsfy/TXMo9Kji8kWBkLBNKeMBp1/img.png" width="751" /></span></figure>
</p>
<p><b>3. 브랜치(Ssource), 환경 변수(Environment Variables), 포트(Ports) 설정</b></p>
<p><b>포트(Exposing Port):</b> Spring Boot의 기본 포트(보통 8080)를 Koyeb 설정의 Port 섹션에 입력해 주어야 외부 통신이 가능</p>
<p><figure class="imageblock alignCenter"><span><img height="649" src="https://blog.kakaocdn.net/dn/tXyau/dJMcafrL5T2/eEp364d9d0Isb1fHwkQkD0/img.png" width="937" /></span></figure>
</p>
<p>&nbsp;</p>
<ul>
<li>나의 경우는 테스트 용으로 개인 브랜치에서만 Dockerfile을 push 했기 때문에 개인 브랜치만 현재 Deploy가 가능하다. 그렇게 때문에 여기서 내가 push한 개인 브랜치를 설정해야한다.</li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="439" src="https://blog.kakaocdn.net/dn/bfbxDr/dJMcaivdH7X/42iuK1XZKmqvx68GDS6EWK/img.png" width="391" /></span></figure>
</p>
<p>&nbsp;</p>
<ul>
<li>환경 변수(Environment Variables): DB 접속 정보나 API 키 같은 민감한 정보는 소스 코드에 노출되면 안 된다. Koyeb 설정창의 Raw Editor를 활용해 한 번에 관리하면 편리하다.</li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="224" src="https://blog.kakaocdn.net/dn/dfpFKA/dJMcai9OQqq/YskWUj8XZxI50caFcoSA4k/img.png" width="626" /></span></figure>
</p>
<h2>5. 배포 및 트러블슈팅</h2>
<p>설정을 마치고 <b>Deploy</b>를 누르면 빌드가 시작된다.</p>
<ul>
<li><b>배포 실패 시:</b> Runtime Logs를 확인하여 경로 설정 오류인지, 환경 변수 누락인지 분석해야 한다.</li>
<li><b>재배포:</b> 수정 후에는 Settings -&gt; Redeploy를 클릭.</li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="705" src="https://blog.kakaocdn.net/dn/chVlo7/dJMcacIA5M0/OqLjRYLTFP9w2AkIgoB7F1/img.png" width="812" /></span></figure>
</p>
<p>&nbsp;</p>
<p>그렇게 해서 보는 swagger - 여기서 작동하는 것과 프론트엔드 로컬에서 접속 가능한지 확인하는 과정이 좀 오래 걸린거같다.</p>
<p><figure class="imageblock alignCenter"><span><img height="607" src="https://blog.kakaocdn.net/dn/dBPlsb/dJMcadm8rhH/KhSAeJ578HmMAkmOtkuPTK/img.png" width="1114" /></span></figure>
</p>
<hr contenteditable="false" />
<p>처음엔 로컬 Swagger 공유가 목적이었지만, 직접 배포해보니 실제 서비스 운영 환경에 대해 많은 것을 이해하게 되었다. 다음 포스팅에서는 배포 과정에서 내가 겪었던 <b>보안 헤더 설정</b>과 <b>CORS 트러블슈팅</b>에 대해 더 자세히 다뤄보겠다.</p>