# Swagger 사용 중 415 에러(application/octet-stream) 해결 과정

**발행일:** Mon, 5 Jan 2026 22:14:38 +0900

**링크:** https://hee-story6.tistory.com/225

---

<pre class="java" id="code_1767618055007"><code>{
    "timestamp": "2025-12-30T06:00:45.658Z",
    "status": 415,
    "error": "Unsupported Media Type",
    "trace": "org.springframework.web.HttpMediaTypeNotSupportedException: Content-Type 'application/octet-stream' is not supported\r\n\tat org.springframework.web.servlet.mvc.method.annotation.AbstractMessageConverterMethodArgumentResolver.readWithMessageConverters(AbstractMessageConverterMethodArgumentResolver.java:235)\r\n\tat org.springframework.web.servlet.mvc.method.annotation.RequestPartMethodArgumentResolver.resolveArgument(RequestPartMethodArgumentResolver.java:140)\r\n\tat org.springframework.web.method.support.HandlerMethodArgumentResolverComposite.resolveArgument(HandlerMethodArgumentResolverComposite.java:122)\r\n\tat org.springframework.web.method.support.InvocableHandlerMethod.getMethodArgumentValues(InvocableHandlerMethod.java:230)\r\n\tat org.springframework.web.method.support.InvocableHandlerMethod.invokeForRequest(InvocableHandlerMethod.java:180)\r\n\tat org.springframework.web.servlet.mvc.method.annotation.ServletInvocableHandlerMethod.invokeAndHandle(ServletInvocableHandlerMethod.java:117)..."
}</code></pre>
<h3 style="color: #000000; text-align: start;">문제 상황&nbsp;</h3>
<p>토이 프로젝트 개발 중 관리자 공연 등록 API를 개발하던 중, Swagger UI를 통한 테스트에서 <b>415 Unsupported Media Type</b> 에러가 발생했다.</p>
<p>API는 공연 정보(JSON)와 포스터 이미지, 상세 이미지들을 multipart/form-data 형식으로 함께 받아야 하는 구조였다. 그런데 요청을 보낼 때마다 다음과 같은 에러가 반복적으로 발생했다. 특히 이상한 점은, 분명 Swagger UI에서 JSON 데이터를 application/json으로 전송했는데, Spring 서버에서는 이를 <b>application/octet-stream(바이너리 데이터)으로 인식</b>한다는 것..!</p>
<p>&nbsp;</p>
<p><figure class="imageblock alignCenter"><span><img height="249" src="https://blog.kakaocdn.net/dn/cBXpsX/dJMcafZzvJZ/3z9E7FvADKJeey1avv6sk1/img.png" width="613" /></span></figure>
</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<h3 style="color: #000000; text-align: start;">초기코드</h3>
<pre class="java" id="code_1767618071092"><code>@PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public ResponseEntity&lt;ApiResponse&lt;ShowCreateResponse&gt;&gt; createShow(
        @RequestBody @Valid ShowCreateRequest request,  // 문제의 원인
        @RequestPart("poster") MultipartFile poster,
        @RequestPart(value = "detailImages", required = false) List&lt;MultipartFile&gt; detailImages) {
    // ...
}
```

### 에러 로그
```
Content-Type 'application/octet-stream' is not supported
415 Unsupported Media Type</code></pre>
<p>&nbsp;</p>
<hr contenteditable="false" />
<p>&nbsp;</p>
<h2 style="color: #000000; text-align: center;">문제 원인 분석</h2>
<h3>1. @RequestBody의 동작 방식 문제 상황</h3>
<p>@RequestBody는 <b>HTTP 요청 본문 전체</b>를 하나의 객체로 역직렬화</p>
<ul>
<li>일반적으로 application/json Content-Type과 함께 사용</li>
<li><b>전체 request body를 JSON으로 파싱</b>하려고 시도</li>
<li>Multipart 요청과는 <b>근본적으로 맞지 않는 구조</b></li>
</ul>
<h3 style="color: #000000; text-align: start;">2. Multipart 요청의 구조</h3>
<p><span style="color: #333333; text-align: start;"><span>&nbsp;</span>파트가<span>&nbsp;</span></span><b>독립적인 Content-Type</b>을 가지고 있습니다.</p>
<pre class="javascript" id="code_1767618184911"><code>POST /api/admin/shows HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="data"
Content-Type: application/json

{"title": "오페라의 유령", "genre": "MUSICAL"}
------WebKitFormBoundary
Content-Disposition: form-data; name="poster"; filename="poster.jpg"
Content-Type: image/jpeg

[바이너리 데이터]
------WebKitFormBoundary--</code></pre>
<h3>3. 왜 application/octet-stream으로 인식되었나?</h3>
<p>Swagger UI에서 JSON 파트를 전송할 때:</p>
<ul>
<li>Swagger는 data 파트를 application/json으로 명시</li>
<li>하지만 Spring의 @RequestBody는 <b>multipart의 개별 파트를 처리할 수 없음</b></li>
<li>Spring이 해당 파트를 <b>바이너리 데이터(octet-stream)로 오해석</b></li>
<li>Jackson이 octet-stream을 JSON으로 파싱 시도 &rarr; 실패</li>
</ul>
<hr contenteditable="false" />
<h2 style="text-align: center;">해결 과정</h2>
<h3>시도 1: ObjectMapper를 이용한 수동 파싱</h3>
<pre class="java" id="code_1767618320942"><code>@PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public ResponseEntity&lt;ApiResponse&lt;ShowCreateResponse&gt;&gt; createShow(
        @RequestPart("data") String dataJson,  // String으로 받기
        @RequestPart("poster") MultipartFile poster,
        @RequestPart(value = "detailImages", required = false) List&lt;MultipartFile&gt; detailImages) 
        throws JsonProcessingException {
    
    ObjectMapper objectMapper = new ObjectMapper();
    ShowCreateRequest request = objectMapper.readValue(dataJson, ShowCreateRequest.class);
    
    // Validation 수동 처리 필요
    // ...
}</code></pre>
<p>&nbsp;</p>
<p><b>문제점:</b></p>
<p>&nbsp;</p>
<ul>
<li>@Valid 자동 검증 불가</li>
<li>수동으로 Validator 호출 필요</li>
<li>코드 복잡도 증가</li>
<li>에러 처리 로직 추가 필요</li>
</ul>
<h3 style="color: #000000; text-align: start;">시도 2: HttpMessageConverter 커스터마이징</h3>
<pre class="java" id="code_1767618376881"><code>@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureMessageConverters(List&lt;HttpMessageConverter&lt;?&gt;&gt; converters) {
        MappingJackson2HttpMessageConverter converter = new MappingJackson2HttpMessageConverter();
        converter.setSupportedMediaTypes(Arrays.asList(
            MediaType.APPLICATION_JSON,
            MediaType.APPLICATION_OCTET_STREAM  // 추가
        ));
        converters.add(converter);
    }
}</code></pre>
<p><b>문제점:</b></p>
<ul>
<li>전역 설정 변경으로 다른 API에 영향 가능</li>
<li>근본적인 해결책이 아님</li>
<li>octet-stream을 JSON으로 파싱하는 것은 의미론적으로 부적절</li>
</ul>
<hr contenteditable="false" />
<h2 style="color: #000000; text-align: center;">최종 해결책: @RequestPart 사용</h2>
<pre class="java" id="code_1767618404278"><code>@Operation(
    summary = "공연 등록", 
    description = "새로운 공연을 등록합니다.\n\n" +
                 "**요청 형식:** multipart/form-data\n\n" +
                 "**필수 필드:**\n" +
                 "- `data`: 공연 정보 (JSON)\n" +
                 "- `poster`: 포스터 이미지 파일\n\n" +
                 "**선택 필드:**\n" +
                 "- `detailImages`: 상세 이미지 파일 목록 (여러 개 가능)\n\n" +
                 "**장르 (genre):** MUSICAL, CONCERT, THEATER, CLASSIC, DANCE"
)
@PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public ResponseEntity&lt;ApiResponse&lt;ShowCreateResponse&gt;&gt; createShow(
        @Parameter(
            description = "공연 정보 (JSON)",
            required = true,
            schema = @Schema(implementation = ShowCreateRequest.class)
        )
        @RequestPart(value = "data", required = true) @Valid ShowCreateRequest request,
        
        @Parameter(
            description = "포스터 이미지 파일 (jpg, jpeg, png, gif, webp, 최대 10MB)", 
            required = true
        )
        @RequestPart("poster") MultipartFile poster,
        
        @Parameter(description = "상세 이미지 파일 목록 (선택, 여러 개 가능)")
        @RequestPart(value = "detailImages", required = false) List&lt;MultipartFile&gt; detailImages) {
    
    ShowCreateResponse result = adminShowService.createShow(request, poster, detailImages);
    return ResponseEntity.status(HttpStatus.CREATED)
        .body(ApiResponse.success(result, result.getMessage()));
}</code></pre>
<h3>핵심 포인트</h3>
<ol>
<li><b>@RequestPart 사용</b>
<ul>
<li>Multipart 요청의 <b>각 파트를 개별적으로 처리</b></li>
<li>각 파트의 Content-Type에 맞게 자동 변환</li>
<li>JSON 파트는 자동으로 Jackson이 역직렬화</li>
</ul>
</li>
<li><b>@Valid 검증 지원</b>
<ul>
<li>Spring의 표준 Validation 기능 사용 가능</li>
<li>별도의 Validator 호출 불필요</li>
</ul>
</li>
<li><b>Swagger 문서화</b>
<ul>
<li>@Schema(implementation = ...) 로 명확한 스키마 정의</li>
<li>Swagger UI에서 정확한 예시 표시</li>
</ul>
</li>
</ol>
<hr contenteditable="false" />
<h3>배운 점</h3>
<ol>
<li>@RequestBody는 전체 request body를 처리하므로 Multipart와 <b>구조적으로 불일치</b></li>
<li>@RequestPart는 각 파트의 Content-Type을 존중하며 적절히 변환</li>
<li>Spring은 <b>올바른 어노테이션 사용 시</b> 복잡한 설정 없이도 잘 동작</li>
</ol>