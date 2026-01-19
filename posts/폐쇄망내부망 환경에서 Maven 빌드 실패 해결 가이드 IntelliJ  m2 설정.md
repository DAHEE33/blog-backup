# 폐쇄망/내부망 환경에서 Maven 빌드 실패 해결 가이드 (IntelliJ + .m2 설정)

**발행일:** Mon, 19 Jan 2026 13:42:22 +0900

**링크:** https://hee-story6.tistory.com/232

---

<p>보안이 철저한 금융권이나 공공기관 프로젝트를 하다 보면, <b>폐쇄망(내부망)</b> 환경에서 개발해야 하는 경우가 많다. 이때 가장 먼저 마주치는 난관이 바로 <b>Maven 빌드 실패</b>다.</p>
<p>인터넷이 차단되어 외부 리포지토리(Central Repository)에 접근할 수 없기 때문인데, 이를 해결하기 위해 IntelliJ와 Maven 설정에서 꼭 확인해야 할 핵심 2가지와 settings.xml의 의미를 정리한다.</p>
<hr contenteditable="false" />
<h3>1. IntelliJ 설정: 'Work offline' 활성화</h3>
<p>가장 먼저 IDE에게 "지금 인터넷 안 되니까 외부 요청 보내지 마"라고 알려줘야 한다.</p>
<ol>
<li><b>설정 진입</b>: Ctrl + Alt + S (Win/Linux) 또는 <b>File &gt; Settings</b></li>
</ol>
<p><figure class="imageblock alignCenter"><span><img height="455" src="https://blog.kakaocdn.net/dn/dGdjRz/dJMcaaD23F0/HMTiq89aZjPtE3c0wyzn91/img.png" width="375" /></span></figure>
</p>
<ol>
<li><b>메뉴 이동</b>: <b>Build, Execution, Deployment &gt; Build Tools &gt; Maven</b></li>
<li><b>옵션 체크</b>: <b>Work offline</b> 체크박스를 활성화</li>
</ol>
<blockquote>
<p><b>Note:</b> 이 설정을 켜면 Maven은 네트워크 통신을 시도하지 않고, 오직 로컬(PC)에 있는 라이브러리만 찾아 빌드함.</p>
</blockquote>
<p><figure class="imageblock alignCenter"><span><img height="724" src="https://blog.kakaocdn.net/dn/NMQcy/dJMcacBSn73/6PusXxoqJ2rrWdy9BGwDUK/img.png" width="980" /></span></figure>
</p>
<h3>2. 로컬 리포지토리(.m2) 경로 및 파일 확인</h3>
<p>'Work offline'을 켰는데도 빌드가 안 된다면, 십중팔구 <b>필요한 라이브러리 파일(.jar)이 로컬에 없기 때문</b>이다. 폐쇄망에서는 외부에서 다운로드받은 .m2 폴더를 통째로 반입해서 사용해야 한다. 또한 .m2 폴더 위치가 변동되었다면 Override 옵션을 켜고 경로를 다시 잡아줘야 한다.</p>
<h4>체크 포인트</h4>
<p><b> 반입 전 검증 필수</b> 반입 요청을 했음에도 파일이 깨지거나 누락되는 경우가 빈번하다. 가장 확실한 방법은 <b>외부망(인터넷 되는 PC)에서 랜선을 뽑고(인터넷 차단) 빌드를 돌려보는 것</b>이다. 이 상태에서 빌드가 성공해야 완벽한 .m2 폴더다. 이 '검증된 폴더'를 그대로 재반입 요청하자.</p>
<h3>3. settings.xml 설정과 HTTP 차단 이해하기</h3>
<p>.m2 파일도 완벽하고 경로도 맞는데 에러가 난다면, settings.xml 설정을 살펴봐야 한다. 보통 아래와 같은 미러링 설정이 포함되어 있다.</p>
<pre class="java" id="code_1768797487128"><code>&lt;settings&gt;
  &lt;mirrors&gt;
    &lt;mirror&gt;
      &lt;id&gt;maven-default-http-blocker&lt;/id&gt;
      &lt;mirrorOf&gt;external:http:*&lt;/mirrorOf&gt;
      &lt;name&gt;Pseudo repository to mirror external repositories initially using HTTP.&lt;/name&gt;
      &lt;url&gt;http://0.0.0.0/&lt;/url&gt;
    &lt;/mirror&gt;
  &lt;/mirrors&gt;
  &lt;/settings&gt;</code></pre>
<p>&nbsp;</p>
<p><b>왜 이런 설정을 할까?</b></p>
<ol>
<li><b>"인터넷 연결이 제한된 환경" 대응:</b> 폐쇄망에서는 외부 라이브러리 다운로드가 불가능하다. 따라서 외부 요청을 차단하거나 로컬/사내 서버로 돌리기 위해 mirror 설정을 사용한다.</li>
<li><b>보안 규정 준수 (HTTP 차단):</b> maven-default-http-blocker는 암호화되지 않은 HTTP 사이트 접속을 강제로 막는 설정이다. 최신 Maven은 보안을 위해 HTTPS가 아니면 통신을 차단한다. url을 0.0.0.0으로 설정한 것은 HTTP 요청을 아예 무효화시키겠다는 뜻이다.</li>
<li><b>빌드 속도 및 안정성:</b> 매번 외부망을 타지 않고 로컬 복사본을 쓰면 빌드 속도가 훨씬 빠르고, 외부 서버 장애의 영향을 받지 않는다.</li>
<li>&nbsp;</li>
</ol>
<hr contenteditable="false" />
<p>폐쇄망에서 빌드 에러가 뜨면 당황하지 말고 <b>1. Work offline 체크, 2. .m2 파일 및 경로 확인, 3. settings.xml 설정</b> 순서로 점검하면 대부분 해결된다.</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>