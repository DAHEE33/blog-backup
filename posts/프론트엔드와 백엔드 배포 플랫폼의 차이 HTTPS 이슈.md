# 프론트엔드와 백엔드 배포 플랫폼의 차이, HTTPS 이슈

**발행일:** Sun, 11 Jan 2026 13:03:30 +0900

**링크:** https://hee-story6.tistory.com/228

---

<div>
<div>
<p>프로젝트 개발 중 백엔드 Swagger를 먼저 배포하여 프론트엔드 로컬 환경에서 API를 테스트하려고 했다. AWS만 사용해봤던 나는 당연히 다른 플랫폼들(Railway, Koyeb, Render 등)도 백엔드와 프론트엔드를 모두 잘 지원할 거라 생각했다.</p>
</div>
</div>
<div>
<div>
<p>하지만 무료 배포 플랫폼을 찾아보는 과정에서 <b>백엔드와 프론트엔드를 지원하는 플랫폼이 각각 다르다</b>는 사실을 알게 되었다. 그리고 배포 후에는 HTTP/HTTPS, SSL 인증서, CORS 등 다양한 보안 이슈를 마주하게 되었다.</p>
</div>
</div>
<div>
<div>
<p>이번 포스팅에서는 플랫폼 선택부터 배포 환경에서 필수적인 보안 설정까지, 실제로 겪으며 배운 내용들을 정리해본다.</p>
<hr contenteditable="false" /></div>
</div>
<div>
<div>
<h2>1. 백엔드와 프론트엔드, 왜 지원하는 플랫폼이 다를까?</h2>
</div>
</div>
<div>
<div>
<h3>백엔드와 프론트엔드의 근본적인 차이</h3>
</div>
</div>
<div>
<div>
<p>백엔드와 프론트엔드는 <b>동작 방식과 요구사항</b>이 완전히 다르다.</p>
</div>
</div>
<div>
<div>
<p><b>프론트엔드의 특성</b></p>
<ul>
<li><b>정적 파일</b> 제공 (HTML, CSS, JavaScript)</li>
<li>빌드 결과물: build/ 폴더 내 정적 파일들</li>
<li>CDN을 통한 빠른 전송이 핵심</li>
<li>사용자와의 물리적 거리를 최소화해야 함</li>
<li>트래픽이 많아도 캐싱으로 대응 가능</li>
</ul>
</div>
</div>
<div>
<p><b>백엔드의 특성</b></p>
<ul>
<li><b>동적 처리</b>가 필요 (DB 조회, 비즈니스 로직 실행)</li>
<li>빌드 결과물: 실행 파일 (Java &rarr; JAR, Node.js &rarr; 번들)</li>
<li>24시간 서버가 실행되어야 함</li>
<li>메모리, CPU 등 컴퓨팅 리소스 필요</li>
<li>요청마다 새로운 연산 수행</li>
</ul>
<div>
<div>
<h3>플랫폼별 특화 방향</h3>
</div>
</div>
<div>
<div>
<p>이러한 특성 차이 때문에 각 플랫폼은 특정 영역에 최적화되어 있다.</p>
</div>
</div>
<div>
<table border="1" style="border-collapse: collapse; width: 100%; height: 174px;">
<tbody>
<tr>
<td><b>&nbsp;</b></td>
<td>프론트엔드 특화</td>
<td>백엔드 특화</td>
<td>풀스택 특화</td>
</tr>
<tr style="height: 34px;">
<td style="height: 34px;"><b>대표 플랫폼</b></td>
<td style="height: 34px;">Vercel, Netlify<br />Cloudflare Pages</td>
<td style="height: 34px;">Railway, Render<br />Koyeb, Fly.io</td>
<td style="height: 34px;">AWS, GCP, Azure</td>
</tr>
<tr style="height: 65px;">
<td style="height: 65px;"><b>핵심 기능</b></td>
<td style="height: 65px;">- CDN 자동 배포<br />- 엣지 캐싱<br />- 빠른 정적 파일 서빙</td>
<td style="height: 65px;">- 컨테이너 실행<br />- 24시간 서버 운영<br />- DB 연결 지원</td>
<td style="height: 65px;">- 모든 서비스 제공<br />- 인프라 직접 구성</td>
</tr>
<tr style="height: 65px;">
<td style="height: 65px;"><b>무료 제약</b></td>
<td style="height: 65px;">빌드 횟수 제한<br />대역폭 제한</td>
<td style="height: 65px;">실행 시간 제한<br />메모리 제한<br />슬립 모드</td>
<td style="height: 65px;">프리티어 존재<br />(사용량 기반 과금)</td>
</tr>
</tbody>
</table>
</div>
</div>
<div>
<div>
<h3>내가 선택한 방향</h3>
</div>
</div>
<div>
<div>
<ul>
<li><b>백엔드</b>: Koyeb (무료 플랜, 자동 HTTPS, 컨테이너 지원)</li>
<li><b>프론트엔드</b> (향후): Vercel 또는 Netlify (빠른 배포, CDN)</li>
</ul>
</div>
</div>
<div>
<p>무료 플랫폼 선택 시 가장 중요한 건 각 플랫폼이 어떤 워크로드에 최적화되어 있는지 이해하는 것이다.</p>
<hr contenteditable="false" />
<h2>2. HTTP vs HTTPS, 왜 이게 문제가 될까?&nbsp;</h2>
<h3>배포 후 마주한 상황</h3>
<p>백엔드를 Koyeb에 배포하니 자동으로 HTTPS가 적용되었다.</p>
<ul>
<li><b>백엔드</b>: <a href="https://api.myproject.com">https://api.myproject.com</a></li>
<li><b>프론트엔드</b>: http://localhost:3000 (로컬 개발 환경)</li>
</ul>
<p>단순히 API를 호출하면 되겠지라고 생각했지만, 브라우저는 이 두 환경의 차이를 민감하게 구분했다. CORS 에러부터 쿠키가 저장되지 않는 문제까지, 다양한 이슈들이 터져 나왔다.</p>
<h3>HTTP와 HTTPS의 차이</h3>
<p><b>HTTP (HyperText Transfer Protocol)</b></p>
<div>
<div>
<pre class="css" style="color: #abb2bf; text-align: left;"><code>클라이언트 &rarr; [평문 데이터] &rarr; 서버
           &uarr;
      중간에서 가로채기 가능
      데이터 위변조 가능</code></pre>
</div>
</div>
<ul>
<li>데이터가 암호화되지 않음</li>
<li>80번 포트 사용</li>
<li>민감한 정보 전송 시 위험</li>
</ul>
</div>
<p><b>HTTPS (HTTP Secure)</b></p>
<div>
<div>
<pre class="angelscript" style="color: #abb2bf; text-align: left;"><code>클라이언트 &rarr; [암호화된 데이터] &rarr; 서버
           &uarr;
      SSL/TLS로 보호됨
      제3자가 해독 불가</code></pre>
</div>
</div>
<ul>
<li>SSL/TLS 프로토콜로 암호화</li>
<li>443번 포트 사용</li>
<li>데이터 무결성 보장</li>
<li>서버 신원 확인</li>
</ul>
<p>&nbsp;</p>
<h3>SSL 인증서, 왜 필수일까?</h3>
<p><b>SSL/TLS 인증서의 역할</b></p>
<ol>
<li><b>암호화</b>: 클라이언트와 서버 간 데이터를 제3자가 해독할 수 없게 암호화</li>
<li><b>인증</b>: 서버가 신뢰할 수 있는 주체임을 증명 (인증 기관 CA가 보증)</li>
<li><b>무결성</b>: 전송 중 데이터 변조를 감지하고 방지</li>
</ol>
<p><b>왜 배포 시 필수인가?</b></p>
<ul>
<li><b>브라우저 보안 정책</b>: 최신 브라우저는 HTTPS가 아닌 사이트에 "주의 요함" 경고 표시</li>
<li><b>데이터 보호</b>: 로그인 정보, API 토큰 등 민감한 데이터 전송 시 암호화 필수</li>
<li><b>최신 웹 API 요구사항</b>: Service Worker, Geolocation 등 많은 웹 API가 HTTPS 환경에서만 동작</li>
<li><b>SEO</b>: 구글 등 검색 엔진이 HTTPS 사이트를 우선 순위로 평가</li>
</ul>
<p><b>무료 배포 플랫폼의 SSL 지원</b></p>
<p>다행히 Koyeb, Railway, Render 같은 무료 배포 플랫폼은 Let's Encrypt를 사용해 SSL 인증서를 자동으로 발급하고 갱신해준다. 별도 설정 없이 배포만 하면 HTTPS가 활성화되는 것이 일반적이다.</p>
<hr contenteditable="false" />
<div>
<div>
<h2>3. Swagger는 잘 되는데 프론트엔드는 왜 안 될까?</h2>
</div>
</div>
<div>
<div>
<h3>배포 후 겪은 혼란</h3>
</div>
</div>
<div>
<div>
<p>백엔드를 배포하고 Swagger를 열어보니 모든 API가 정상 작동했다.</p>
</div>
</div>
<div>
<div>
<div>
<div>
<pre class="java" style="color: #abb2bf; text-align: left;"><code>Swagger에서 테스트: 완벽하게 동작
https://my-backend.koyeb.app/swagger-ui &rarr; API 호출 성공</code></pre>
</div>
</div>
</div>
</div>
<div>
<div>
<p>"오! 잘 되네?"라고 생각하며 프론트엔드 로컬 환경에서 같은 API를 호출했더니...</p>
</div>
</div>
<div>
<div>
<div>
<div>
<pre class="java" style="color: #abb2bf; text-align: left;"><code>로컬 프론트에서 호출: 빨간색 에러 폭격

Access to fetch at 'https://my-backend.koyeb.app/api/users' 
from origin 'http://localhost:3000' has been blocked by CORS policy</code></pre>
</div>
</div>
</div>
</div>
<div>
<p>"Swagger는 되는데 왜 프론트는 안 돼?" 이게 내가 며칠간 삽질한 핵심 질문이었다.</p>
<h3>원인: Same-Origin vs Cross-Origin</h3>
<p>문제는 <b>Origin(출처)</b> 개념에 있었다.</p>
<div>
<div>
<pre class="ini" style="color: #abb2bf; text-align: left;"><code>Origin = 프로토콜 + 도메인 + 포트</code></pre>
</div>
</div>
<p>&nbsp;</p>
<p><b>Swagger의 경우 (Same-Origin)</b></p>
<div>
<div>
<pre class="groovy" style="color: #abb2bf; text-align: left;"><code>Swagger UI:  https://my-backend.koyeb.app/swagger-ui
백엔드 API:  https://my-backend.koyeb.app/api/users

Origin: https://my-backend.koyeb.app (동일!)
&rarr; 같은 집 안에서 통신 &rarr; 제약 없음</code></pre>
</div>
</div>
<p>&nbsp;</p>
<p><b>로컬 프론트의 경우 (Cross-Origin)</b></p>
<div>
<div>
<pre class="groovy" style="color: #abb2bf; text-align: left;"><code>프론트엔드:  http://localhost:3000
백엔드 API:  https://my-backend.koyeb.app/api/users

프론트 Origin: http://localhost:3000
백엔드 Origin: https://my-backend.koyeb.app
&rarr; 서로 다른 집 &rarr; 보안 검문소(브라우저)를 거침!</code></pre>
</div>
</div>
<h3>브라우저의 Same-Origin Policy (동일 출처 정책)</h3>
<p>브라우저는 보안을 위해 기본적으로 <b>다른 출처 간의 리소스 공유를 차단</b>한다.</p>
<p>악의적인 사이트가 사용자 모르게 다른 사이트에 요청을 보내는 것을 막기 위해서다.</p>
<h3>Mixed Content와 쿠키 문제까지</h3>
<p>Origin이 다른 것만으로도 문제인데, 여기에 추가로:</p>
<p>&nbsp;</p>
<p><b>문제 1: Mixed Content</b></p>
<ul>
<li>HTTPS 페이지에서 HTTP 리소스 요청은 차단</li>
<li>다행히 내 경우는 HTTP(로컬) &rarr; HTTPS(배포)라서 허용됨</li>
</ul>
<p><b>문제 2: 쿠키 정책</b></p>
<ul>
<li>서로 다른 도메인 간 쿠키 전송은 SameSite=None 필요</li>
<li>SameSite=None은 반드시 Secure=true (HTTPS) 와 함께 사용</li>
<li>로컬은 HTTP인데 Secure 쿠키를 받을 수 있을까?</li>
</ul>
<h2>4. 해결의 실마리: Spring Security 설정의 필요성</h2>
<p>이 모든 문제는 <b>Spring Security에서 명시적으로 허용</b>해줘야 해결된다.</p>
<h3>필요한 설정들</h3>
<p><b>1. CORS 설정</b></p>
<div>
<div>
<pre class="awk" style="color: #abb2bf; text-align: left;"><code>// "이 출처들은 내 API 호출해도 돼!" 
configuration.setAllowedOrigins(List.of(
    "http://localhost:3000",
    "https://my-front.vercel.app"
));</code></pre>
</div>
</div>
<p>&nbsp;</p>
<p><b>2. 쿠키 설정(프론트와 쿠키로 TOKEN 이용하기로 했기 때문에 쿠키를 설정)</b></p>
<div>
<div>
<pre class="pgsql" style="color: #abb2bf; text-align: left;"><code>// SameSite=None, Secure=true 설정
ResponseCookie cookie = ResponseCookie.from("token", value)
    .sameSite("None")
    .secure(true)
    .build();</code></pre>
</div>
</div>
<p>&nbsp;</p>
<p><b>3. SecurityFilterChain 구성</b></p>
<div>
<div>
<pre class="xl" style="color: #abb2bf; text-align: left;"><code>// CORS 활성화, CSRF 비활성화 등
http.cors(cors -&gt; cors.configurationSource(corsConfigurationSource()))
    .csrf(csrf -&gt; csrf.disable());</code></pre>
</div>
</div>
<p>&nbsp;</p>
<p>이 모든 설정은 다음 포스팅에서 실전 코드와 함께 자세히 다룰 예정이다.</p>
<hr contenteditable="false" />
<h2>마치며</h2>
<p>백엔드 배포는 생각보다 고려할 게 많았다.</p>
<p>첫째, 백엔드와 프론트엔드는 근본적으로 다른 특성을 가지고 있고, 그에 따라 최적화된 플랫폼도 다르다는 것을 알게 되었다.</p>
<p>둘째, 대부분의 무료 배포 플랫폼이 자동으로 HTTPS를 제공하는 것은 큰 장점이지만, 이로 인해 로컬 개발 환경(HTTP)과의 연동에서 새로운 고려사항이 생긴다.</p>
<p>셋째, Swagger는 잘 되는데 프론트는 안 되는 이유가 바로 Origin 차이 때문이라는 것을 배웠다. Same-Origin과 Cross-Origin의 차이를 이해하는 것이 핵심이었다.</p>
<p>하지만 이론만으로는 부족했다. 실제로 로컬 프론트엔드에서 배포된 백엔드로 요청을 보내자마자 브라우저 콘솔은 빨간색 에러로 가득 찼다.</p>
<blockquote>
<p><span style="color: #ee2323;">"CORS Policy Error"</span><br /><span style="color: #ee2323;">"Cookie blocked due to SameSite policy"</span></p>
</blockquote>
<p>&nbsp;</p>
<p>다음 포스팅에서는 이 에러들을 하나씩 해결하며 완성한 Spring Security 설정 코드를 실전 중심으로 공유할 예정이다. 특히 CORS 설정, 쿠키의 SameSite와 Secure 속성, 그리고 SecurityFilterChain 구성까지 실제로 동작하는 코드와 함께 다뤄보겠다.</p>
</div>
<p>&nbsp;</p>