# 로컬에서 CORS/Proxy를 다시 파본 이야기

**발행일:** Tue, 7 Jul 2026 23:16:17 +0900

**링크:** https://hee-story6.tistory.com/248

---

<h2>계기</h2>
<p>사실 이 부분을 진지하게 파본 적은 없었다. 2026년 상반기 초, 협업 프로젝트에서 프론트 쪽이 "API가 자꾸 안 붙는다"는 얘기를 했을 때 이것저것 찾아보며 시키는 대로 CORS 설정하고 프론트 담당자에게 proxy 설정을 요청 한 게 전부였다. 이해하려고 해도 완벽하게 되진 않고, 단순히 회사에서 해왔던 CORS 설정을 그대로 가져다 쓰는 정도였다. 그땐 "설정하니까 되네" 정도로 넘어갔다.</p>
<p>이번 공모전 프로젝트에서 프론트-백엔드를 혼자 처음부터 세팅하다 보니, 그때 왜 그런 설정을 했었는지가 뒤늦게 이해됐다. 이론보다 역시 체감하는 게 다르다.</p>
<p>겪었던 문제와 정리한 내용을 기록해본다.</p>
<h2>문제 상황</h2>
<div>
<div>
<pre class="groovy" style="color: #eaecf0;"><code>frontend : http://localhost:5173 (Vite)
backend  : http://localhost:8080 (Spring Boot, local profile)</code></pre>
</div>
</div>
<p>backend의 health check API(/api/health)는 브라우저로 직접 접근하면 정상 응답이 왔다.</p>
<div>
<div>
<pre class="json" style="color: #eaecf0;"><code>{
  "status": "OK",
  "service": "meet-or-solo-backend"
}</code></pre>
</div>
</div>
<p>하지만 frontend 화면에서 같은 API를 호출하면 처음엔 붙지 않았다.</p>
<p>&nbsp;</p>
<ul>
<li>Failed to fetch</li>
<li>또는 404 Not Found</li>
</ul>
<p>&nbsp;</p>
<h2>localhost라도 port가 다르면 다른 origin이다</h2>
<p>둘 다 localhost니까 같은 환경이라고 생각하기 쉽지만, 브라우저 기준 origin은 프로토콜 + 호스트 + 포트가 모두 같아야 한다.</p>
<p>포트가 다르면 서로 다른 origin이다.</p>
<p>&nbsp;</p>
<ul>
<li>frontend origin = http://localhost:5173</li>
<li>backend origin = http://localhost:8080</li>
</ul>
<p>&nbsp;</p>
<p>여기서 두 가지 선택지가 갈린다: <b>CORS 방식</b>과 <b>Proxy 방식</b>.</p>
<h2>방식 1. CORS &mdash; 직접 호출</h2>
<div>
<div>
<pre class="javascript" id="code_1783433273396"><code>fetch("http://localhost:8080/api/health");</code></pre>
</div>
</div>
<p>브라우저는 backend로 직접 요청을 보내고, backend가 200 OK를 반환해도 backend가 CORS를 허용하지 않으면 브라우저가 응답을 frontend JS 코드에 넘기지 않는다.</p>
<div>
<div>
<pre class="javascript" id="code_1783433288548"><code>Access to fetch at 'http://localhost:8080/api/health'
from origin 'http://localhost:5173'
has been blocked by CORS policy</code></pre>
</div>
</div>
<p>여기서 헷갈렸던 지점은, Chrome DevTools Network 탭에는 Status Code: 200 OK로 찍히는데 화면에는 Failed to fetch가 뜬다는 것이었다. <b>요청 자체는 성공했지만 브라우저가 응답 전달을 막은 상태</b>라는 걸 이해하지 못하면 "분명 200인데 왜 안 되지"에서 한참 헤맨다.</p>
<h2>방식 2. Vite Proxy &mdash; 상대 경로 호출</h2>
<p>frontend 코드는 backend 주소를 몰라도 된다.</p>
<div>
<div>
<pre class="javascript" id="code_1783433307374"><code>fetch("/api/health");</code></pre>
</div>
</div>
<p>vite.config.ts:</p>
<div>
<div>
<pre class="javascript" id="code_1783433320785"><code>server: {
  proxy: {
    "/api": {
      target: "http://localhost:8080",
      changeOrigin: true
    }
  }
}</code></pre>
</div>
</div>
<p>흐름은 이렇다.</p>
<div>
<div>
<pre class="javascript" id="code_1783433331666"><code>브라우저 &rarr; http://localhost:5173/api/health
        &rarr; Vite dev server
        &rarr; http://localhost:8080/api/health (proxy)
        &rarr; Spring Boot backend</code></pre>
</div>
</div>
<p>브라우저는 5173에만 요청을 보내고, Vite dev server가 서버 입장에서 backend로 대신 요청하기 때문에 브라우저의 CORS 제한 자체를 우회하게 된다.</p>
<h2>CORS 에러 vs Proxy 미설정 에러, 어떻게 구분하나</h2>
<p>이게 이번에 제일 명확하게 정리된 부분이다. <b>기준은 Network 탭의 Request URL 하나다.</b></p>
<div>
<table border="1" style="border-collapse: collapse; width: 100%; height: 105px;">
<tbody>
<tr style="height: 21px;">
<td style="height: 21px;">상황</td>
<td style="height: 21px;">호출 코드</td>
<td style="height: 21px;">Request URL</td>
<td style="height: 21px;">Backend 도착 여부</td>
<td style="height: 21px;">에러</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">proxy 없음</td>
<td style="height: 21px;">fetch("/api/health")</td>
<td style="height: 21px;">localhost:5173/...</td>
<td style="height: 21px;">X</td>
<td style="height: 21px;">404</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">CORS 없음</td>
<td style="height: 21px;">fetch("http://localhost:8080/...")</td>
<td style="height: 21px;">localhost:8080/...</td>
<td style="height: 21px;">O</td>
<td style="height: 21px;">CORS error</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">backend 미실행</td>
<td style="height: 21px;">직접 호출 or proxy</td>
<td style="height: 21px;">localhost:8080</td>
<td style="height: 21px;">X</td>
<td style="height: 21px;">connection refused</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">proxy 정상</td>
<td style="height: 21px;">fetch("/api/health")</td>
<td style="height: 21px;">localhost:5173/...</td>
<td style="height: 21px;">O</td>
<td style="height: 21px;">200 OK</td>
</tr>
</tbody>
</table>
</div>
<ul>
<li>Request URL이 5173 &rarr; 요청이 Vite dev server에서 끝난 것. backend CORS를 아무리 만져도 소용없다. proxy 설정 문제다.</li>
<li>Request URL이 8080인데 화면은 실패 &rarr; 요청은 backend까지 갔고 응답도 받았는데 브라우저가 막은 것. CORS 문제다.</li>
</ul>
<p>이 기준을 잡기 전엔 "프론트에서 API가 안 된다"는 말을 들으면 막연히 backend 로그부터 뒤졌는데, 사실 Network 탭 Request URL 한 줄로 원인이 갈린다는 걸 알고 나니 디버깅 순서 자체가 달라졌다.</p>
<h2>협업/운영에서는 왜 proxy(reverse proxy) 방식을 쓰는가</h2>
<ol>
<li><b>frontend 코드가 환경에 덜 의존한다</b> &mdash; /api 상대경로 하나로 로컬/개발/운영을 통일할 수 있다. backend 주소를 직접 박으면 환경별로 관리 포인트가 늘어난다.</li>
<li><b>CORS 이슈 자체가 줄어든다</b> &mdash; 브라우저 입장에서 같은 origin으로 보이기 때문.</li>
<li><b>운영 nginx 구조와 대응된다</b> &mdash; 로컬 Vite proxy가 하는 역할을, 운영에서는 nginx가 이어받는다.</li>
</ol>
<div>
<div>
<pre class="javascript" id="code_1783433406834"><code>로컬 개발: 브라우저 &rarr; Vite dev server &rarr; backend
운영 배포: 브라우저 &rarr; nginx        &rarr; backend</code></pre>
<p>nginx는 정적 파일 서빙, API 라우팅, HTTPS(SSL termination), 로드밸런싱까지 맡는다. HTTPS 인증서는 Certbot(Let's Encrypt)이 발급/갱신을 담당하는데, 실제 요청을 받아서 처리하는 건 nginx이고 Certbot은 그 앞단에서 인증서를 관리해주는 역할만 한다. 즉 Certbot 자체가 프록시로서 트래픽을 넘겨주는 게 아니라, nginx가 그 인증서를 가져다 쓰는 구조라는 점이 헷갈렸던 부분이다.</p>
<h2><span style="color: #000000;">있는 줄 몰랐던 "개발용 proxy"</span></h2>
<p><span style="color: #000000;">nginx가 운영 환경에서 리버스 프록시 역할을 한다는 건 알고 있었다. 그런데 이번에 처음 알게 된 건, 운영에만 프록시가 있는 게 아니라 </span><span style="color: #000000;">로컬 개발 환경에도 그 역할을 하는 게 따로 존재한다</span><span style="color: #000000;">는 점이었다.</span><b></b></p>
<ul>
<li>로컬 개발: 브라우저 &rarr; Vite dev server &rarr; backend</li>
<li>운영 배포: 브라우저 &rarr; nginx&nbsp; &nbsp; &nbsp; &nbsp; &rarr; backend</li>
</ul>
<p><span style="color: #000000;">지금까지는 nginx = 리버스 프록시라고만 생각했는데, Vite dev server도 </span><span style="color: #188038;">server.proxy</span><span style="color: #000000;"> 설정만 있으면 로컬에서 똑같은 역할(요청을 받아서 대신 backend로 넘겨주는 것)을 한다는 걸 이번에 직접 세팅해보면서 알았다. 운영 환경의 nginx와 개발 환경의 Vite proxy는 등장하는 계층도 쓰이는 목적도 다르지만, "브라우저 대신 요청을 받아 backend로 넘겨준다"는 구조 자체는 동일하다.</span></p>
</div>
</div>
<h2>결론</h2>
<p><span style="color: #000000;">로컬에서 frontend/backend를 나눠 실행할 때, 둘 다 localhost라고 같은 서버처럼 동작하지 않는다. 포트가 다르면 다른 origin이고, 여기서 CORS를 허용하거나 proxy를 태우는 두 갈래로 나뉜다.</span></p>
<p><b>&nbsp;</b></p>
<p><span style="color: #000000;">이번 프로젝트에서는 협업&middot;운영 구조를 고려해 Vite proxy 방식을 선택했다. 예전엔 이 설정을 왜 하는지 모르고 따라 했지만, 이번엔 원리를 이해하고 직접 구성했다는 점에서 차이가 있다. 예전엔 에러가 나면 그때그때 원인을 찾아서 땜질하는 식이었다면, 이제는 CORS와 proxy가 각각 어떤 계층에서 무슨 역할을 하고 서로 어떻게 연결되는지 전체 그림이 그려진다. 다음에 "API가 안 붙는다"는 이슈를 마주치면, Network 탭의 Request URL부터 확인하는 게 가장 빠른 진단 순서라는 걸 이제는 안다.</span></p>
<p>&nbsp;</p>