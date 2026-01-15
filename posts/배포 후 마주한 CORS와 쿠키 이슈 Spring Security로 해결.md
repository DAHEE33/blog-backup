# 배포 후 마주한 CORS와 쿠키 이슈, Spring Security로 해결

**발행일:** Thu, 15 Jan 2026 08:00:41 +0900

**링크:** https://hee-story6.tistory.com/231

---

<p>지난 포스팅에서는 백엔드와 프론트엔드 플랫폼의 차이, HTTPS의 중요성, 그리고 "Swagger는 잘 되는데 왜 프론트는 안 될까?"라는 의문까지 다뤘다.</p>
<p>핵심은 <b>Origin(출처)의 차이</b>였다.</p>
<ul>
<li>Swagger: <a href="https://my-backend.koyeb.app">https://my-backend.koyeb.app</a> (Same-Origin) &rarr; 문제없음</li>
<li>로컬 프론트: http://localhost:3000 (Cross-Origin) &rarr; 브라우저가 차단</li>
</ul>
<p>이론적으로는 모든 준비가 끝났다고 생각했지만, 막상 로컬 프론트엔드에서 배포된 백엔드로 요청을 보내자 브라우저 콘솔은 빨간색 에러로 도배되었다.</p>
<div>
<div>
<pre class="java" style="color: #abb2bf; text-align: left;"><code>Access to fetch at 'https://api.myproject.koyeb.app/api/users' 
   from origin 'http://localhost:3000' has been blocked by CORS policy

Cookie "accessToken" has been rejected because it is in a cross-site 
   context and its "SameSite" is "Lax" or "Strict"</code></pre>
</div>
</div>
<p>&nbsp;</p>
<p>이번 글에서는 <b>이 에러들을 하나씩 해결하며 완성한 Spring Security 설정 코드</b>를 공유한다. 특히 HTTP(로컬)와 HTTPS(배포)가 혼재된 환경에서 인증을 처리해야 하는 분들에게 도움이 되길 바란다.</p>
<hr contenteditable="false" />
<h3 style="color: #000000; text-align: start;">1. 첫 번째 관문: CORS (Cross-Origin Resource Sharing)</h3>
<h3>CORS가 뭐길래?</h3>
<p>브라우저는 보안을 위해 <b>다른 출처(Origin) 간의 리소스 공유를 기본적으로 차단</b>한다. 이것이 바로 **Same-Origin Policy(동일 출처 정책)**이다.</p>
<ul>
<li><b>내 상황:</b>
<ul>
<li>Front: http://localhost:3000 (로컬)</li>
<li>Back: <a href="https://api.myproject.koyeb.app">https://api.myproject.koyeb.app</a> (배포)</li>
<li><b>결과:</b> 프로토콜(http/https)도 다르고 도메인도 다르므로 <b>Cross-Origin</b>으로 판단되어 차단된다.</li>
</ul>
</li>
</ul>
<h3>Preflight 요청 (OPTIONS)</h3>
<p>실제로는 브라우저가 본 요청을 보내기 전에 "이 요청 보내도 돼?"라고 서버에 먼저 물어본다.</p>
<div>
<div>
<div>
<pre class="routeros"><code>sequenceDiagram
    participant Browser
    participant Server

    Note over Browser, Server: 1. Preflight (간보기)
    Browser-&gt;&gt;Server: OPTIONS /api/users
    Server--&gt;&gt;Browser: 200 OK (Allowed-Origins, Methods, Credentials)

    Note over Browser, Server: 2. Actual Request (본 요청)
    Browser-&gt;&gt;Server: POST /api/users (with Cookie)
    Server--&gt;&gt;Browser: 200 OK (Data)
</code></pre>
</div>
</div>
</div>
<p>만약 1번 단계(Preflight)에서 적절한 CORS 헤더를 받지 못하면, 2번(본 요청)은 아예 전송되지도 않는다.</p>
<h3>해결 코드: SecurityConfig.java</h3>
<p>Spring Security 설정 파일(SecurityConfig.java)에서 CORS를 명시적으로 허용해줘야 한다.</p>
<p>기본 구조</p>
<pre class="java" id="code_1768049795213"><code>@Bean
public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration configuration = new CorsConfiguration();

    // 1. 허용할 프론트엔드 도메인
    configuration.setAllowedOrigins(List.of(
            "http://localhost:3000",
            "https://my-front.vercel.app"
    ));

    // 2. 허용할 HTTP 메서드
    configuration.setAllowedMethods(List.of(
            "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"
    ));

    // 3. 허용할 헤더
    configuration.setAllowedHeaders(List.of("*"));

    // 4. ⭐ 자격 증명 허용 (쿠키 전송 필수!)
    configuration.setAllowCredentials(true);

    // 5. Preflight 요청 캐싱 시간
    configuration.setMaxAge(3600L);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", configuration);
    return source;
}</code></pre>
<h3>실전 코드: 환경변수로 관리하기</h3>
<p>하지만 위처럼 하드코딩하면 배포 환경마다 코드를 수정해야 한다. 실전에서는 환경변수로 관리하는 것이 좋다. application.yml이나 application.properties에 넣고 나서 설정 파일로 수정한다.</p>
<pre class="java" id="code_1768049711525"><code>  @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        // 허용할 Origin (환경변수에서 주입)
        configuration.setAllowedOrigins(allowedOrigins);

        // 허용할 HTTP 메서드
        configuration.setAllowedMethods(allowedMethods);

        // 허용할 헤더
        configuration.setAllowedHeaders(allowedHeaders);

        // 쿠키 전송 허용
        configuration.setAllowCredentials(allowCredentials);

        // 브라우저가 응답 헤더를 읽을 수 있도록 노출
        configuration.setExposedHeaders(exposedHeaders);

        // Preflight 요청 캐싱 시간
        configuration.setMaxAge(maxAge);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }</code></pre>
<h2>2. 두 번째 관문: 쿠키 정책 (SameSite &amp; Secure)</h2>
<h3>마주한 에러</h3>
<p>CORS를 해결하고 나니 로그인은 성공한 것 같은데, 다음 요청부터 로그인이 풀리는(쿠키 미전송) 문제가 발생했다.</p>
<h3>SameSite 속성이란?</h3>
<p>쿠키의 SameSite 속성은 <b>서로 다른 사이트 간에 쿠키를 전송할 것인지</b>를 제어한다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>값</b></td>
<td><b>의미</b></td>
<td><b>사용 시나리오</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>Strict</b></span></td>
<td><span>같은 사이트에서만 쿠키 전송</span></td>
<td><span>보안 최우선 (은행 등)</span></td>
</tr>
<tr>
<td><span><b>Lax</b> (기본)</span></td>
<td><span>같은 사이트 + 안전한 요청(GET)</span></td>
<td><span>일반적인 웹사이트</span></td>
</tr>
<tr>
<td><span><b>None</b></span></td>
<td><span>모든 사이트에서 쿠키 전송</span></td>
<td><span>Cross-Site 통신 필요 시</span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<h3>내가 마주한 딜레마</h3>
<ol>
<li>서로 다른 도메인(로컬 Front &harr; 배포 Back) 간에 쿠키를 공유하려면 SameSite=None이 필요하다.</li>
<li>SameSite=None을 쓰려면 반드시 <b>Secure=true (HTTPS)</b> 속성이 함께 설정되어야 한다.</li>
<li>"그런데 내 로컬 프론트는 HTTP인데?"</li>
</ol>
<h3>localhost는 예외!&nbsp;</h3>
<p>천만다행히도 최신 브라우저들은 개발 편의를 위해 localhost에 한해서는 HTTP 환경이라도 Secure 쿠키를 허용해준다.</p>
<ul>
<li>localhost (HTTP) + Secure 쿠키 = 허용 (개발 편의)</li>
<li>다른 도메인 (HTTP) + Secure 쿠키 = 차단</li>
</ul>
<h3>해결 코드: ResponseCookie 설정</h3>
<p>구 버전의 Cookie 클래스 대신 ResponseCookie 빌더를 사용하면 속성을 섬세하게 조절할 수 있다.</p>
<div>
<div>
<div>
<pre class="java"><code>public ResponseCookie createTokenCookie(String token) {
    return ResponseCookie.from("accessToken", token)
            .httpOnly(true)      // JavaScript에서 접근 불가 (XSS 방지)
            .secure(true)        // HTTPS에서만 전송 (SameSite=None 시 필수)
            .path("/")           // 모든 경로에서 유효
            .maxAge(60 * 60)     // 1시간
            .sameSite("None")    // Cross-Site 요청에서도 전송 허용
            .build();
}

// 컨트롤러 적용 예시
@PostMapping("/login")
public ResponseEntity&lt;?&gt; login(@RequestBody LoginDto dto, HttpServletResponse response) {
    String token = jwtService.generateToken(dto);
    ResponseCookie cookie = createTokenCookie(token);
    
    response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString());
    
    return ResponseEntity.ok("로그인 성공");
}</code></pre>
</div>
</div>
</div>
<p>&nbsp;</p>
<h2>3. 최종 보스: Spring Security FilterChain</h2>
<p>위에서 만든 CORS 설정과 보안 정책을 Spring Security에 적용하는 최종 코드다. (Spring Security 6.x 기준)</p>
<div>
<div>
<div>
<pre class="less"><code>@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // 1. CSRF 비활성화 (REST API + JWT 토큰 방식)
            .csrf(AbstractHttpConfigurer::disable)
            
            // 2. CORS 설정 적용 (위에서 만든 Bean 주입)
            .cors(cors -&gt; cors.configurationSource(corsConfigurationSource()))
            
            // 3. 세션 관리: Stateless (서버에 세션을 저장하지 않음)
            .sessionManagement(session -&gt; 
                 session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            
            // 4. 보안 헤더 설정 (HSTS, XSS 방지 등)
            .headers(headers -&gt; headers
                .frameOptions(HeadersConfigurer.FrameOptionsConfig::deny)
                .httpStrictTransportSecurity(hsts -&gt; hsts
                    .includeSubDomains(true)
                    .maxAgeInSeconds(31536000) // 1년
                )
            )
            
            // 5. 요청 경로별 권한 설정
            .authorizeHttpRequests(auth -&gt; auth
                .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll() // Preflight 허용
                .anyRequest().authenticated()
            );

        return http.build();
    }
    
    // ... corsConfigurationSource Bean 코드는 상단 참조 ...
}
</code></pre>
</div>
</div>
</div>
<h3>설정 포인트</h3>
<ol>
<li><b>.csrf(disable)</b>: JWT를 사용하고 SessionCreationPolicy.STATELESS를 설정했으므로 CSRF 보호를 비활성화했다. (단, 쿠키를 사용할 경우 CSRF 공격 가능성이 완전히 0은 아니므로, 매우 민감한 정보 변경 시에는 별도의 CSRF 토큰이나 Referer 검증을 추가하는 것이 좋다.)</li>
<li><b>.requestMatchers(HttpMethod.OPTIONS, "/**")</b>: Spring Security 필터 단계에서 Preflight 요청이 차단되지 않도록 OPTIONS 메서드를 명시적으로 허용해주는 것이 안전하다.</li>
</ol>
<h2>4. 트러블슈팅: 자주 마주치는 에러 체크리스트</h2>
<p>혹시 아직도 빨간 에러가 뜬다면 아래 체크리스트를 확인해보자.</p>
<h3><span style="color: #ee2323;">에러 1: "CORS policy: No 'Access-Control-Allow-Origin'..."</span></h3>
<ul>
<li>SecurityConfig의 setAllowedOrigins에 프론트 도메인이 프로토콜, 포트까지 정확한가? (예: http://localhost:3000)</li>
<li>setAllowCredentials(true)를 설정하고 allowedOrigins에 "*"를 쓰진 않았는가?</li>
<li>requestMatchers에서 HttpMethod.OPTIONS를 허용했는가?</li>
</ul>
<h3><span style="color: #ee2323;">에러 2: "This Set-Cookie was blocked... SameSite..."</span></h3>
<ul>
<li>ResponseCookie 생성 시 .sameSite("None")을 설정했는가?</li>
<li>.secure(true)를 설정했는가? (None 설정 시 필수)</li>
<li>백엔드 서버가 HTTPS로 배포되었는가? (HTTP 배포 환경에서는 Secure 쿠키 동작 안 함)</li>
</ul>
<h3>에러 3: 로그인은 되는데 다음 요청부터 <span style="color: #ee2323;">401 에러</span></h3>
<ul>
<li>프론트엔드 요청 코드에 credentials: 'include' (Fetch) 혹은 withCredentials: true (Axios)가 빠지지 않았는가?</li>
</ul>
<hr contenteditable="false" />
<p>이렇게 1편의 환경 이해부터 시작해 오늘 다룬 CORS와 쿠키 설정까지, 로컬 프론트엔드와 배포된 백엔드를 연결하는 긴 여정이 끝났다.</p>
<p>처음에는 "그냥 배포하면 되는 거 아니야?"라고 가볍게 생각했지만, 웹 브라우저가 우리의 보안을 위해 얼마나 깐깐하게 구는지 몸소 체험할 수 있었다. 이 설정들은 프로젝트가 커지거나 실제 도메인(mysite.com)을 연결하게 되면 또 달라질 수 있겠지만, 현재의 [로컬 개발 - 배포 서버] 하이브리드 환경에서는 가장 확실한 해결책이 될 것이다.</p>