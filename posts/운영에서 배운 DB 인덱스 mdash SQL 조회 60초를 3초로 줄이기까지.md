# 운영에서 배운 DB 인덱스 &mdash; SQL 조회 60초를 3초로 줄이기까지

**발행일:** Tue, 30 Jun 2026 16:42:27 +0900

**링크:** https://hee-story6.tistory.com/247

---

<p>백엔드 개발을 하다 보면 처음엔 "기능이 돌아가면 됐지"라고 생각하게 된다. 그러다 운영 환경에서 데이터가 쌓이고, 어느 날 조회 하나가 60초씩 걸리기 시작했다.</p>
<p>이 글은 그 경험에서 시작해서, 인덱스를 이해하고 실제로 적용하기까지의 과정을 정리한 글이다.</p>
<h2>인덱스란?</h2>
<p>인덱스는 <b>테이블 데이터와 별도로 관리되는 정렬된 색인 구조</b>다.</p>
<p>책의 목차를 생각하면 이해하기 쉽다. 책에서 특정 내용을 찾을 때 처음부터 끝까지 읽지 않고 목차에서 페이지 번호를 먼저 찾듯이, DB도 인덱스에서 위치를 먼저 찾고 해당 row로 바로 이동한다.</p>
<p><b>PK나 자주 검색하는 컬럼에 인덱스를 걸면 DB는 해당 컬럼 값과 실제 데이터 위치를 별도로 저장한다.</b> 조회할 때는 테이블 전체를 훑지 않고 인덱스에서 값을 먼저 찾은 뒤 실제 row 위치로 이동하기 때문에 빠르다.</p>
<p><span style="color: #006dd7;">단, 인덱스는 읽기를 빠르게 하는 대신 쓰기 비용이 생긴다. INSERT, UPDATE, DELETE가 발생하면 테이블뿐 아니라 인덱스도 함께 갱신해야 한다. 쓰기가 많은 테이블에 인덱스를 과도하게 걸면 오히려 전체 성능이 낮아질 수 있다.</span></p>
<h2>인덱스 스캔 종류</h2>
<div>
<table border="1" style="border-collapse: collapse; width: 100%; height: 73px;">
<tbody>
<tr>
<td>타입</td>
<td>설명</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">Full Table Scan</td>
<td style="height: 21px;">테이블 전체를 처음부터 끝까지 읽음</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">Index Range Scan</td>
<td style="height: 21px;">인덱스에서 범위 조건으로 일부만 탐색</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">Index Unique Scan</td>
<td style="height: 21px;">인덱스에서 단 1건만 조회 (PK, UNIQUE)</td>
</tr>
</tbody>
</table>
</div>
<p>Full Scan이 무조건 나쁜 건 아니다. 데이터가 적은 테이블에서는 Full Scan이 오히려 빠를 수 있다. 중요한 건 <b>데이터가 많고 자주 조회되는 테이블</b>에서 Full Scan이 발생하고 있는지를 파악하는 것이다.</p>
<h2>Full Scan이 발생하는 경우</h2>
<p>인덱스를 걸었는데도 Full Scan이 나는 경우가 있다.</p>
<h3>1. 인덱스 컬럼에 함수를 적용한 경우</h3>
<pre class="java" id="code_1782803148370"><code>--  Full Scan 발생 &mdash; created_at 컬럼을 함수로 변환
WHERE TO_CHAR(created_at, 'YYYY-MM-DD') = '2024-01-01'

--  인덱스 사용 가능 &mdash; 컬럼은 그대로, 비교값에 함수 적용
WHERE created_at &gt;= TO_DATE('2024-01-01', 'YYYY-MM-DD')
  AND created_at &lt;  TO_DATE('2024-01-02', 'YYYY-MM-DD')</code></pre>
<p>핵심은 <b>인덱스가 걸린 컬럼 자체는 건드리지 않는 것</b>이다. 변환이 필요하다면 비교 대상 값에 적용하면 된다.</p>
<h3>2. LIKE 앞 와일드카드</h3>
<pre class="java" id="code_1782803177758"><code>--  Full Scan &mdash; 어디서 시작하는지 알 수 없어 전체를 읽어야 함
WHERE name LIKE '%철수'

--  인덱스 사용 가능
WHERE name LIKE '김%'</code></pre>
<h3>3. 선택도가 낮은 컬럼</h3>
<p>값의 종류가 너무 적은 컬럼(예: 성별 M/F)은 인덱스를 타도 절반을 읽어야 한다. 이 경우 옵티마이저가 Full Scan을 선택한다.</p>
<blockquote>
<p><b>옵티마이저</b>란 SQL을 실행하기 전에 "어떻게 실행하면 가장 빠를까?"를 자동으로 판단하는 DB 내부 엔진이다. 인덱스가 있어도 옵티마이저가 Full Scan이 더 빠르다고 판단하면 인덱스를 무시한다.</p>
</blockquote>
<h2>복합 인덱스 (Composite Index)</h2>
<p>두 개 이상의 컬럼을 묶어서 만드는 인덱스다.</p>
<p>복합 인덱스는 <b>왼쪽 컬럼부터 순서대로 정렬</b>된다. (이름, 나이) 인덱스라면 이름 기준으로 먼저 정렬되고, 같은 이름 안에서만 나이순으로 정렬된다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="width: 100%;">김아름 - 20 <br />김루나 - 25 <br />박철수&nbsp;-&nbsp;30 <br />이영희&nbsp;-&nbsp;22</td>
</tr>
</tbody>
</table>
<div><br />
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td>조건인덱스</td>
<td>사용여부</td>
</tr>
<tr>
<td>WHERE 이름 = '김루나'</td>
<td>OK</td>
</tr>
<tr>
<td>WHERE 이름 = '김루나' AND 나이 = 25</td>
<td>OK</td>
</tr>
<tr>
<td>WHERE 나이 = 25</td>
<td>X (나이는 전체적으로 정렬되어 있지 않음)</td>
</tr>
</tbody>
</table>
</div>
<p>나이만 조건으로 넣으면 나이가 전체적으로 정렬된 상태가 아니기 때문에 결국 인덱스 전체를 읽어야 한다. 옵티마이저가 Full Scan을 선택하게 된다.</p>
<h3>컬럼 순서 설계 원칙</h3>
<ul>
<li>선택도가 높은 컬럼을 앞에 (user_id, order_id처럼 값 종류가 많은 것)</li>
<li>자주 쓰는 WHERE 조건 컬럼을 앞에</li>
<li>동등 조건(=)을 범위 조건(&gt;, BETWEEN)보다 앞에</li>
</ul>
<h2>EXPLAIN으로 실행 계획 확인하기</h2>
<p>쿼리가 느릴 때 가장 먼저 해야 할 일은 EXPLAIN으로 실행 계획을 확인하는 것이다.</p>
<p>MySQL/MariaDB 기준 주요 컬럼:</p>
<p><b>type</b> &mdash; 가장 중요한 컬럼이다.</p>
<div>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td>값</td>
<td>의미</td>
</tr>
<tr>
<td>ALL</td>
<td>Full Table Scan&nbsp;</td>
</tr>
<tr>
<td>range</td>
<td>인덱스 범위 탐색</td>
</tr>
<tr>
<td>ref</td>
<td>비고유 인덱스로 조회</td>
</tr>
<tr>
<td>const</td>
<td>PK/UNIQUE로 1건 조회&nbsp;</td>
</tr>
</tbody>
</table>
</div>
<p><b>key</b> &mdash; 실제 사용된 인덱스 이름. NULL이면 인덱스 미사용.</p>
<p><b>rows</b> &mdash; 예상 스캔 행 수. 작을수록 좋다.</p>
<p><b>Extra</b> &mdash; 추가 정보.</p>
<div>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td>값</td>
<td>의미</td>
</tr>
<tr>
<td>Using index</td>
<td>인덱스만으로 처리 완료 (빠름)</td>
</tr>
<tr>
<td>Using filesort</td>
<td>추가 정렬 발생 (느림)</td>
</tr>
<tr>
<td>Using temporary</td>
<td>임시 테이블 생성 (느림)</td>
</tr>
</tbody>
</table>
</div>
<p>확인 순서: type &rarr; key &rarr; rows &rarr; Extra</p>
<h2>실무 경험 &mdash; 조회 60초 &rarr; 3초</h2>
<p>운영 중인 발송 시스템에서 특정 조회 화면의 응답이 점점 느려지다가 60초를 넘기 시작했다.</p>
<h3>원인 파악</h3>
<p>EXPLAIN으로 실행 계획을 확인했을 때 type: ALL이 확인됐다.</p>
<p>기존 쿼리를 보니 구조적인 문제가 있었다.</p>
<pre class="sql" id="code_1782805240634"><code>-- 기존 구조 (문제)
SELECT * FROM (
    SELECT * FROM table_a
    UNION ALL
    SELECT * FROM table_b
) t
WHERE t.status = 'DONE'
  AND t.created_at &gt;= ...</code></pre>
<p>UNION ALL로 두 테이블을 전부 합친 뒤 WHERE로 필터링하는 구조였다. 합치는 시점에는 인덱스를 탈 수 없어서 대량 데이터를 메모리에 올린 후 필터링하게 된다.</p>
<h3>개선</h3>
<p>중심 테이블 기준으로 WHERE 조건을 먼저 적용한 뒤 JOIN하는 구조로 전환했다.</p>
<pre class="sql" id="code_1782805256963"><code>-- 개선 구조
SELECT t.*, d.detail_col
FROM table_a t
LEFT JOIN table_b d ON t.id = d.ref_id
WHERE t.status = 'DONE'
  AND t.created_at &gt;= TO_DATE('2024-01-01', 'YYYY-MM-DD')</code></pre>
<p>WHERE 조건 컬럼(status, created_at)에 복합 인덱스도 재설계했다.</p>
<p>EXPLAIN 재확인 결과 type: ALL &rarr; type: range로 변경됐고, 조회 시간은 60초 &rarr; 3초로 개선됐다.</p>
<h2>인덱스를 쓰면 오히려 안 좋은 경우</h2>
<ul>
<li>쓰기가 매우 많은 테이블 &mdash; 갱신 비용이 커져 전체 처리량 감소</li>
<li>데이터가 적은 테이블 &mdash; Full Scan이 오히려 빠름</li>
<li>선택도가 낮은 컬럼 &mdash; 값 종류가 2~3개뿐이면 효과 없음</li>
</ul>
<h2>정리</h2>
<div>
<table border="1" style="border-collapse: collapse; width: 100%; height: 143px;">
<tbody>
<tr style="height: 21px;">
<td style="height: 21px;">개념</td>
<td style="height: 21px;">핵심</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">인덱스</td>
<td style="height: 21px;">정렬된 별도 색인. 읽기 빠름, 쓰기 비용 발생</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">복합 인덱스</td>
<td style="height: 21px;">왼쪽 컬럼부터 순서대로 유효</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">Full Scan 원인</td>
<td style="height: 21px;">컬럼에 함수 적용, 앞 와일드카드 LIKE, 선택도 낮은 컬럼</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">옵티마이저</td>
<td style="height: 21px;">비용 계산 후 실행 계획 자동 선택. 인덱스가 있어도 무시할 수 있음</td>
</tr>
<tr style="height: 21px;">
<td style="height: 21px;">EXPLAIN</td>
<td style="height: 21px;">type &rarr; key &rarr; rows &rarr; Extra 순서로 확인</td>
</tr>
</tbody>
</table>
</div>
<p>성능 문제는 처음부터 완벽하게 설계하기 어렵다. 운영 데이터가 쌓이고 나서야 보이는 병목이 많다. 중요한 건 느려졌을 때 원인을 찾고 개선하는 흐름을 아는 것이라고 생각한다.</p>
<p>&nbsp;</p>