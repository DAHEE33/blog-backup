# 자주 쓰는 롬복(Lombok) 어노테이션과 패턴

**발행일:** Thu, 12 Jun 2025 14:28:11 +0900

**링크:** https://hee-story6.tistory.com/220

---

<p>&nbsp;</p>
<p>개인 프로젝트에 롬복을 쓰는데 습관처럼 쓰는데, 회사 직원이 물어보면서 다시 공부하게 된 롬복</p>
<p>여기서 다시 정리해봅니다</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<h2><b>Lombok 어노테이션 종류/역할</b></h2>
<div>
<p>&nbsp;</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="text-align: center;"><b>어노테이션</b></td>
<td style="text-align: center;"><b>역할/설명</b></td>
<td style="text-align: center;"><b>실무 사용 예</b></td>
</tr>
<tr>
<td>@Getter</td>
<td>모든 필드의 getter 자동 생성</td>
<td>거의 필수. DTO, Entity 모두에서 널리 사용</td>
</tr>
<tr>
<td>@Setter</td>
<td>모든 필드의 setter 자동 생성</td>
<td>Entity, DTO에서 <b>불변성 지키고 싶으면 지양</b></td>
</tr>
<tr>
<td>@NoArgsConstructor</td>
<td>파라미터 없는 기본 생성자 자동 생성</td>
<td>JPA Entity 필수 (보통 access=PROTECTED)</td>
</tr>
<tr>
<td>@AllArgsConstructor</td>
<td>모든 필드를 파라미터로 받는 생성자 자동 생성</td>
<td>빌더와 같이 쓰기 필수! (access=PRIVATE 추천)</td>
</tr>
<tr>
<td>@RequiredArgsConstructor</td>
<td>final/@NonNull 필드만 받는 생성자 자동 생성</td>
<td>서비스/컨트롤러 등 의존성 주입(DI)에서 가끔 사용</td>
</tr>
<tr>
<td>@Builder</td>
<td>빌더 패턴 자동 생성 (가장 많이 씀)</td>
<td>대부분 클래스 단위로 선언</td>
</tr>
<tr>
<td>@EqualsAndHashCode</td>
<td>equals, hashCode 메서드 자동 생성</td>
<td>엔티티 PK, VO에서 가끔 사용</td>
</tr>
<tr>
<td>@ToString</td>
<td>toString 메서드 자동 생성</td>
<td>로그/디버깅용, but 엔티티 연관관계 필드 주의!</td>
</tr>
<tr>
<td>@Data</td>
<td>Getter/Setter, toString, equals, hashCode, RequiredArgsConstructor 자동 생성</td>
<td>편하긴 하지만, <b>실무에서는 거의</b></td>
</tr>
</tbody>
</table>
</div>
<p>&nbsp;</p>
<hr contenteditable="false" />
<h2><b>@Data를 요즘 안 쓰는 이유?</b></h2>
<h3>1. <b>의도치 않은 setter/equals/hashCode 생성</b></h3>
<ul>
<li>@Data는 모든 필드에 <b>Setter, equals, hashCode, toString까지 다 만들어줌</b></li>
<li><b>Entity/DTO에서 불변성을 깨뜨리거나, 연관관계 필드의 순환 참조</b>(toString, equals 등)로 버그 발생 위험</li>
</ul>
<h3>2. <b>과도한 메서드 생성, 관리 어려움</b></h3>
<ul>
<li>내가 원치 않는 메서드까지 자동 생성 &rarr; 디버깅, 유지보수 때 혼란</li>
</ul>
<h3>3. <b>실무 표준은 "명확하게 필요한 것만!"</b></h3>
<ul>
<li>@Getter, @NoArgsConstructor, @AllArgsConstructor, @Builder<br />&rarr; 각 목적에 맞게 <b>명확하게</b> 조합해서 쓰는 게 실무 표준</li>
<li>Entity에는 Setter를 아예 안 쓰거나, <b>필요한 필드에만 개별로 붙임</b></li>
</ul>
<hr contenteditable="false" />
<h2><b>내가 사용한 조합</b></h2>
<pre class="java" id="code_1749705414213"><code>@Entity
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)  // JPA Entity 필수
@AllArgsConstructor(access = AccessLevel.PRIVATE)   // 빌더 생성자
@Builder                                            // 객체 생성 편의성
@Table(name = "survey")
public class Survey { ... }</code></pre>
<div>&nbsp;</div>
<p>&nbsp;</p>
<p>- 기본적으로 생성하는 파라미터 없는 생성자 생성한 뒤 AllArgsConstructor과 Builder를 쓴다.</p>
<p>처음 Builder만 써야한다고 생각했는데 에러가 나서 AllArgsConstructor과 Builder에 대해 더 공부했다.</p>
<p>&nbsp;</p>
<h2><b>Q. @AllArgsConstructor, @Builder의 차이는?</b></h2>
<h3><b>A. 전체 파라미터 생성자 vs. 빌더 패턴</b></h3>
<ul>
<li>@AllArgsConstructor<br />&rarr; <b>모든 필드를 파라미터로 받는 생성자</b>를 만들어줌<br />&rarr; 직접 new로 객체 생성<br />&rarr; 필드가 많으면 가독성 떨어지고, 순서 잘못 넣으면 에러</li>
</ul>
<pre class="java" id="code_1749705520041"><code>Survey s = new Survey(1L, "설문제목", ...);</code></pre>
<ul>
<li>@Builder<br />&rarr; <b>빌더 패턴</b>을 자동 생성<br />&rarr; <b>필요한 필드만 선택적으로</b> 할당, 순서 상관 없이 명확하게 객체 생성<br />&rarr; 내부적으로 &ldquo;모든 필드 생성자&rdquo;를 써서 객체를 만든다</li>
</ul>
<pre class="java" id="code_1749705490409"><code>Survey s = Survey.builder()
    .id(1L)
    .name("설문제목")
    .build();</code></pre>
<p>&nbsp;</p>
<p>&nbsp;</p>
<h3><b>B. 빌더는 '모든 필드 생성자'가 필수!</b></h3>
<ul>
<li>빌더 패턴이 정상적으로 동작하려면<br /><b>모든 필드를 받는 생성자</b>가 필요함</li>
<li>@NoArgsConstructor만 있으면, 이 생성자가 없어 에러 발생</li>
<li><b>특정 생성자에만 붙이기도 가능:</b><br />일부 파라미터만 빌더로 만들고 싶으면, 생성자에 직접 붙일 수도 있지만<br />&rarr; 잘 안 씀 (유지보수 불리, 코드 일관성 떨어짐)</li>
<li><b>해결:</b><br />@AllArgsConstructor도 같이 선언하면 해결<br />(실무에서는 @NoArgsConstructor + @AllArgsConstructor + @Builder 조합이 표준)</li>
</ul>
<pre class="java" id="code_1749705587332"><code>@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor(access = AccessLevel.PRIVATE) // 실수로 new 못하게!
@Builder
public class Survey { ... }</code></pre>
<p>&nbsp;</p>
<p>&nbsp;</p>
<h3 style="color: #000000; text-align: start;"><b>C. 두 어노테이션의 &ldquo;핵심 차이점</b><b></b></h3>
<div><br />
<table border="1" style="border-collapse: collapse; width: 100%; height: 122px;">
<tbody>
<tr style="height: 17px;">
<td style="height: 17px;">&nbsp;</td>
<td style="height: 17px;"><b>@AllArgsConstructor</b></td>
<td style="height: 17px;"><b>@Builder</b></td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;"><b>생성 방법</b></td>
<td style="height: 21px;">new Survey(1L, "이름")</td>
<td style="height: 21px;">Survey.builder().id(1L).name("이름").build()</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;"><b>파라미터 순서</b></td>
<td style="height: 21px;">반드시 지켜야 함</td>
<td style="height: 21px;">순서 상관 없음, 일부 필드만 선택 가능</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;"><b>가독성</b></td>
<td style="height: 21px;">낮음 (필드 많으면 헷갈림)</td>
<td style="height: 21px;">높음, 명확하게 필드별로 할당</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;"><b>유지보수</b></td>
<td style="height: 21px;">힘듦 (필드 추가/삭제 시 생성자 수정 필요)</td>
<td style="height: 21px;">쉬움 (필드 추가/삭제에도 코드 영향 적음)</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;"><b>필드 생략</b></td>
<td style="height: 21px;">불가 (모든 필드 값 필수)</td>
<td style="height: 21px;">가능 (필요한 것만 채워서 build 가능)</td>
</tr>
</tbody>
</table>
</div>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<p>&nbsp;</p>
<p>아직 실무에서 써본적은 없지만 앞으로를 위해 제대로 알아두면 좋을 거 같아 정리한 롬복</p>
<p>어노테이션이나 의존성을 필요할까봐 막 넣었다면 요즘은 최대한 사용하는 것 위주로 넣으려고 한다.(그래도 어려움)</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>