# HttpServletRequest, 구식 기술일까? - 현업에서 만난 진실

**발행일:** Tue, 6 Jan 2026 22:52:29 +0900

**링크:** https://hee-story6.tistory.com/226

---

<h3>고민의 시작: @Annotation vs HttpServletRequest</h3>
<p>최신 스프링 부트에선 HttpServletRequest를 직접 주입받아 사용하는 경우가 눈에 띄게 줄었다.<s><i>(레거시 프로젝트는 아직 대부분 HttpServletRequest를 쓰겠지만.. 예를 들면 지금 회사?)</i></s> 대부분 @RequestParam이나 @RequestBody로 데이터를 처리한다.</p>
<p>그렇다면 이제 HttpServletRequest는 아예 안 써도 되는 구식 기술일까?&nbsp;</p>
<pre class="java" id="code_1767707220768"><code>// 요즘 스타일
@PostMapping("/users")
public User createUser(@RequestBody UserDto userDto) {
    return userService.create(userDto);
}

// 옛날 스타일?
@PostMapping("/users")
public User createUser(HttpServletRequest request) {
    String name = request.getParameter("name");
    int age = Integer.parseInt(request.getParameter("age"));
    // ...
}</code></pre>
<div>
<div>
<h2>  왜 직접 쓰지 않게 되었나?</h2>
</div>
</div>
<div>
<p>과거에는 파라미터 하나 읽으려 해도 request.getParameter()를 쓰고, 직접 형변환까지 해야 했었다. 하지만 현대 스프링 개발에서 지양하는 이유는 명확하다.</p>
<h3 style="color: #000000; text-align: start;">1. 테스트의 어려움</h3>
<pre class="java" id="code_1767706617034"><code>@Test
void createUserTest() {
    // Mock 객체 생성이 복잡함
    HttpServletRequest request = mock(HttpServletRequest.class);
    when(request.getParameter("name")).thenReturn("KIM");
    when(request.getParameter("age")).thenReturn("25");
    // ...
}</code></pre>
<h3>2. 가독성 저하&nbsp;</h3>
<p>비즈니스 로직보다 데이터 추출/변환 코드가 더 길어지는 역설적 상황이 발생.</p>
<h3>3. 타입 안전성 부재</h3>
<p>@RequestParam은 스프링이 자동으로 타입 변환과 검증을 해주지만, request는 모두 수동 처리. 번거롭다</p>
<pre class="java" id="code_1767706632605"><code>// 스프링이 알아서 처리
@GetMapping("/search")
public List&lt;Item&gt; search(@RequestParam LocalDate startDate) { ... }

// 직접 파싱 필요
LocalDate startDate = LocalDate.parse(request.getParameter("startDate"));</code></pre>
</div>
<h2>✨ 여전히 '현역'인 이유: 시스템의 브릿지(Bridge)</h2>
<p>제가 최근 프로젝트에서 <b>외부 관리자 시스템에서 우리 서비스로 넘어오는 "브릿지" 상황</b>을 구현하면서 깨달았지.. 이런 저수준 제어가 필요한 순간에는 HttpServletRequest만한 것이 없다는 것을.</p>
<h3 style="color: #000000; text-align: start;">1. 외부 시스템과의 연동&nbsp;</h3>
<pre class="java" id="code_1767706772146"><code>@GetMapping("/admin/redirect")
public String handleAdminRedirect(HttpServletRequest request) {
    // Referer 헤더로 출처 검증
    String referer = request.getHeader("Referer");
    if (!referer.startsWith("https://admin.company.com")) {
        throw new UnauthorizedException();
    }
    
    // 특정 쿠키 확인
    Cookie[] cookies = request.getCookies();
    String adminToken = Arrays.stream(cookies)
        .filter(c -&gt; c.getName().equals("ADMIN_TOKEN"))
        .findFirst()
        .map(Cookie::getValue)
        .orElseThrow();
    
    return "redirect:/dashboard";
}</code></pre>
<h3 style="color: #000000; text-align: start;">2. 접속 환경 분석&nbsp;</h3>
<pre class="java" id="code_1767706795614"><code>public String getClientIP(HttpServletRequest request) {
    // 프록시 환경에서 실제 IP 추적
    String ip = request.getHeader("X-Forwarded-For");
    if (ip == null) {
        ip = request.getHeader("Proxy-Client-IP");
    }
    if (ip == null) {
        ip = request.getRemoteAddr();
    }
    return ip;
}</code></pre>
<h3 style="color: #000000; text-align: start;">3.통합 인증(SSO) 구현</h3>
<p>&nbsp;</p>
<h2>  필터와 인터셉터: 스프링 마법이 시작되기 전&nbsp;</h2>
<p>우리가 흔히 쓰는 @RequestBody나 @Valid는 스프링의 DispatcherServlet이 동작하면서 부리는 '마법'이다. 하지만 <b>이 마법이 시작되기 전</b>인 필터(Filter)나 인터셉터(Interceptor) 단계에서는 원본 그대로인 HttpServletRequest를 다룰 수밖에 없다..!</p>
<pre class="java" id="code_1767707027855"><code>@Component
public class RequestLoggingFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) {
        HttpServletRequest request = (HttpServletRequest) req;
        
        log.info("Request URI: {}", request.getRequestURI());
        log.info("Method: {}", request.getMethod());
        log.info("Client IP: {}", getClientIP(request));
        log.info("User-Agent: {}", request.getHeader("User-Agent"));
        
        chain.doFilter(req, res);
    }
}</code></pre>
<p>&nbsp;</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<h2 style="color: #000000; text-align: start;">  실전에서 배운 교훈</h2>
<p>개발자라면 누구나 최신 기술, 최신 방식을 사용하고 싶어한다(혹시 나만?).</p>
<p>@RequestParam, @RequestBody 같은 편리한 어노테이션을 쓰면서 HttpServletRequest를 거의 쓰지 않는다. 개인 프로젝트에서는.. 회사에서 레거시이기 때문에 쓰더라도 그냥 습관적으로?</p>
<p>하지만 외부 시스템과의 연동 작업을 하면서 깨달았다. <b>"어떤 기술을 쓰느냐"보다 "왜 이 기술을 써야 하는지"를 아는 것이 진짜 실력</b>이라는 것을.. 내 실력을 반성했다.</p>
<h3>기본기의 중요성</h3>
<p>관리자 페이지 A에서 관리자 페이지 B로 사용자를 넘기는 브릿지를 구현하면서:</p>
<ul>
<li>"어느 페이지에서 왔는지" 확인하려니 &rarr; Referer 헤더가 필요했고</li>
<li>"인증 정보를 어떻게 전달할지" 고민하다 &rarr; 쿠키와 세션을 다뤄야 했고</li>
<li>"보안을 어떻게 검증할지" 생각하니 &rarr; 필터 단계에서 원본 request가 필요했다</li>
</ul>
<p>이 모든 것이 @RequestParam으로는 불가능한 영역이었다.</p>
<h3>옛것과 새것의 조화</h3>
<p><span style="color: #006dd7;"><b>결국 중요한 건 "무엇이 최신 기술인가"가 아니라 "이 상황에 가장 적합한 기술이 무엇인가"를 판단하는 능력이다.</b></span></p>
<ul>
<li>비즈니스 데이터를 다룰 때는 &rarr; 스프링이 제공하는 편리한 어노테이션을</li>
<li>시스템의 뼈대를 다룰 때는 &rarr; 기본에 충실한 HttpServletRequest를</li>
</ul>
<p>최신 기술의 편리함을 누리되, 그 밑바탕을 이루는 기본 원리를 이해하고 있어야 한다. 그래야 막상 필요한 순간에 당황하지 않고 적절한 도구를 선택할 수 있다.</p>
<p>&nbsp;</p>