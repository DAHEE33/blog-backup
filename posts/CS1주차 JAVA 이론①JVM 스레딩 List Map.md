# [CS/1주차] JAVA 이론①(JVM, 스레딩, List, Map)

**발행일:** Mon, 12 Jan 2026 21:47:22 +0900

**링크:** https://hee-story6.tistory.com/229

---

<p>&nbsp;</p>
<hr />
<h3>1. JVM 메모리 구조와 GC (Garbage Collection)</h3>
<ul>
<li>JVM 메모리는 크게 여러 영역으로 나뉘지만, 면접에서는 <b>Stack, Heap, Method Area(Metaspace)</b> 이 세 가지의 역할과 차이를 명확히 구분하는 것이 핵심이다.<br />
<table border="1" style="background-color: #000000; color: #1f1f1f; border-collapse: collapse; width: 102.536%; height: 421px;">
<tbody>
<tr style="background-color: #000000; color: #1f1f1f;">
<td style="background-color: #efefef; color: #1f1f1f; width: 17.9103%; text-align: center;"><b>영역</b></td>
<td style="background-color: #efefef; color: #1f1f1f; width: 25.6738%; text-align: center;"><b>저장되는 것</b></td>
<td style="background-color: #efefef; color: #1f1f1f; width: 29.3629%; text-align: center;"><b>생명 주기 (Lifecycle)</b></td>
<td style="background-color: #efefef; color: #1f1f1f; width: 26.9323%; text-align: center;"><b>특징</b></td>
</tr>
</tbody>
<tbody style="background-color: #000000; color: #1f1f1f;">
<tr style="background-color: #000000; color: #1f1f1f;">
<td style="background-color: #000000; color: #1f1f1f; width: 17.9103%;"><span style="color: #ffffff;"><b>Method Area</b></span><br /><span style="color: #ffffff;">(Static 영역)</span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 25.6738%;"><span style="color: #ffffff;">클래스 정보(설계도),</span><br /><span style="color: #ffffff;"><b>Static 변수</b>, 상수</span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 29.3629%;"><span style="color: #ffffff;"><b>프로그램 시작(클래스 로</b><span style="background-color: #000000;"><b>딩) ~ 종료</b></span></span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 26.9323%;"><span style="color: #ffffff;">모든 스레드가 공유함.</span><br /><span style="color: #ffffff;">(Java 8부터는 Metaspace로 변경되어 Native Memory 사용)</span></td>
</tr>
<tr style="background-color: #000000; color: #1f1f1f;">
<td style="background-color: #000000; color: #1f1f1f; width: 17.9103%;"><span style="background-color: #000000; color: #ffffff;"><b>Heap</b></span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 25.6738%;"><span style="color: #ffffff;"><b>new로 생성된 객체(Instance)</b>,</span><span style="color: #ffffff;">Array</span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 29.3629%;"><span style="background-color: #000000; color: #ffffff;">객체 생성 ~ <b>GC가 수거할 때</b></span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 26.9323%;"><span style="color: #ffffff;">모든 스레드가 공유함.</span><br /><span style="color: #ffffff;">GC의 주 무대.</span></td>
</tr>
<tr style="background-color: #000000; color: #1f1f1f;">
<td style="background-color: #000000; color: #1f1f1f; width: 17.9103%;"><span style="background-color: #000000; color: #ffffff;"><b>Stack</b></span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 25.6738%;"><span style="color: #ffffff;"><b>메서드 실행 프레임</b>,</span><br /><span style="color: #ffffff;"><b>지역 변수</b>(Primitive),</span><br /><span style="color: #ffffff;">참조 변수(주소값)</span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 29.3629%;"><span style="background-color: #000000; color: #ffffff;">메서드 호출 ~ <b>메서드 종료(리턴)</b></span></td>
<td style="background-color: #000000; color: #1f1f1f; width: 26.9323%;"><span style="color: #ffffff;">스레드마다 별도로 생성됨.</span><br /><span style="color: #ffffff;">(동시성 문제 X)</span></td>
</tr>
</tbody>
</table>
아래 코드로 한 번 더 JVM 구조를 익혀보자.</li>
</ul>
<pre class="java" id="code_1768387426000"><code>public class MemoryLab {

    // [1. Method Area (Static 영역)]
    // 클래스가 로딩될 때 생성됨. 프로그램 종료 시까지 유지.
    // 모든 스레드가 공유함.
    static final String APP_NAME = "MyJavaApp"; // 상수
    static int userCount = 0; // 스태틱 변수

    public static void main(String[] args) {
        // [2. Stack 영역 (Main 스레드)]
        // main 메서드의 'Stack Frame'이 생성됨.
        // 메서드 안의 변수(지역변수)들은 이곳에 저장.
        int age = 30; // 기본형(Primitive) : 값 자체가 Stack에 저장됨.

        // [3. Heap 영역 &amp; Stack 영역의 참조]
        // new Person() : 실제 객체 데이터는 'Heap'에 생성.
        // Person p1    : 힙에 있는 객체의 주소값(Reference)을 가진 변수는 'Stack'에 생성.
        Person p1 = new Person("Kim"); 
        
        userCount++; // Static 변수 접근 (Method Area)

        // 메서드 호출 시 새로운 Stack Frame이 위로 쌓임 (Push)
        printWelcome(p1); 
        
        // [4. String Constant Pool 테스트]
        String str1 = "Hello";        // String Constant Pool (Heap 내부)
        String str2 = new String("Hello"); // 일반 Heap
        
        // str1과 str2는 저장 위치가 다름
    } // main 메서드 종료 -&gt; Stack Frame 삭제 -&gt; 지역변수(age, p1 등) 모두 소멸

    public static void printWelcome(Person person) {
        // [새로운 Stack Frame 생성]
        // 매개변수 person도 지역변수이므로 Stack에 주소값이 복사됨.
        String message = "Welcome, " + person.name; // message 변수도 Stack
        System.out.println(message);
    } // 메서드 종료 -&gt; printWelcome의 Stack Frame 삭제 (Pop)
}

class Person {
    String name; // 인스턴스 변수 -&gt; 객체가 생성될 때 'Heap'에 저장됨

    public Person(String name) {
        this.name = name;
    }
}</code></pre>
<ul>
<li>String Constant Pool (문자열 상수 풀) <br />: String을 생성하는 두 가지 방식(리터럴 vs new)의 차이는 "메모리 효율성"과 직결 <br />① String a = "aa"; (리터럴 방식)
<ul>
<li><b>저장 위치:</b> <b>Heap 영역 내부의 String Constant Pool</b></li>
<li><b>동작:</b>
<ol>
<li>String Constant Pool에 "aa"라는 문자열이 있는지 확인</li>
<li><b>있다면:</b> 그 주소값을 그대로 가져옴(재사용)</li>
<li><b>없다면:</b> 풀에 새로 만들고 그 주소를 반환</li>
</ol>
</li>
<li><b>결과:</b> 메모리를 절약</li>
</ul>
② String b = new String("aa"); (new 연산자 방식)
<ul>
<li><b>저장 위치:</b> <b>일반 Heap 영역</b></li>
<li><b>동작:</b> Constant Pool을 거치지 않고, 무조건 Heap 영역에 새로운 객체를 하나 생성</li>
<li><b>결과:</b> "aa"가 이미 풀에 있어도, 강제로 새로운 메모리를 할당(메모리 낭비)</li>
</ul>
</li>
</ul>
<pre class="java" id="code_1768387805191"><code>String a = "aa";
String b = "aa";
String c = new String("aa");

System.out.println(a == b); // true (둘 다 Constant Pool의 같은 주소를 가리킴)
System.out.println(a == c); // false (a는 Pool, c는 일반 Heap의 다른 주소)
System.out.println(a.equals(c)); // true (주소는 다르지만 '내용'은 같음)</code></pre>
<p>&nbsp;</p>
<p><b>2) GC &amp; 역할</b></p>
<ul>
<li>프로그래밍에서&nbsp;더 이상 사용되지 않는 객체가 점유한 메모리를 자동으로 찾아 해제하는 메모리 관리 기술. 개발자가 수동으로 메모리를 관리하는 대신, 시스템(런타임 환경)이 자동으로 쓸모없어진 데이터를 정리하여 메모리 누수와 같은 문제를 방지하고 프로그램 효율을 높이는 역할</li>
</ul>
<p>&nbsp;</p>
<p>❓ JVM의 GC는 메모리를 어떻게 정리할까?</p>
<p>GC는 지금 실행 중인 코드가 쓰는 변수부터 시작해서, 거기서 줄줄이 연결된 객체들을 다 찾아냅니다. 그리고 연결 안 된 것을 쓰레기로 판단해서 지웁니다. 예를 들어, 메서드 안의 지역 변수나 클래스의 static 변수 같은 것들이 출발점이 되고, 거기서 참조하는 객체들을 따라가면서 살아있는 객체를 구분합니다.</p>
<p>&nbsp;</p>
<p> Static 변수는 언제 메모리에 올라가고 언제 내려가나요?</p>
<p>Static 변수는 JVM이 클래스를 로딩(Class Loading)하는 시점에 Method Area(메타스페이스)에 올라갑니다. 그리고 프로그램이 종료되거나, 드물게 클래스 로더가 언로드(Unload)될 때 메모리에서 내려갑니다</p>
<p>&nbsp;</p>
<h3>2. 운영체제(OS): 프로세스와 스레드</h3>
<p><b>1) 프로세스 (Process)</b></p>
<ul>
<li><b>정의:</b> 운영체제로부터 자원을 할당받아 실행 중인 <b>프로그램의 단위</b>.</li>
<li><b>특징:</b> 각각 독립된 메모리 공간(Code, Data, Heap, Stack)을 가진다. 따라서 A 프로세스가 B 프로세스의 메모리를 침범할 수 없다.</li>
</ul>
<p><b>2) 스레드 (Thread)</b></p>
<ul>
<li><b>정의:</b> 프로세스 내에서 실행되는 <b>작업의 흐름 단위</b>.</li>
<li><b>특징:</b>
<ul>
<li>프로세스 하나에 여러 스레드가 존재할 수 있다.</li>
<li><b>메모리 공유:</b> 스레드끼리는 <b>Stack을 제외한 Heap(데이터) 영역을 공유</b>한다.</li>
<li><b>장점:</b> 데이터를 공유하므로 통신 속도가 빠르고 자원 효율이 좋다.</li>
<li><b>단점:</b> 여러 스레드가 동시에 같은 데이터를 수정할 때 동시성 문제(데이터 꼬임)가 발생할 수 있다.</li>
</ul>
</li>
</ul>
<p>❓ 프로세스와 스레드의 차이를 메모리 관점에서 설명해 주세요.</p>
<p>가장 큰 차이는 <b>메모리 공유 여부</b>입니다. <b>프로세스</b>는 OS로부터 독립된 메모리를 할당받아 서로 침범할 수 없습니다. 반면, <b>스레드</b>는 하나의 프로세스 안에서 <b>Heap(데이터) 영역을 공유</b>합니다. (Stack만 따로 가짐) 이 때문에 스레드 간 데이터 통신은 빠르지만, 동시에 같은 자원을 건드리는 동시성 이슈(Concurrency Issue)에 주의해야 합니다</p>
<h3>2-1. 멀티스레딩 (Multi-threading)</h3>
<p>하나의 프로세스 안에서 <b>여러 개의 스레드가 동시에 작업을 수행</b>하는 것.</p>
<h4>1) 정의 및 비유</h4>
<ul>
<li><b>정의:</b> CPU의 최대 활용을 위해, 하나의 프로그램(프로세스) 안에서 둘 이상의 스레드를 동시에 실행시키는 기술.</li>
<li><b>비유:</b>
<ul>
<li><b>싱글 스레드:</b> 요리사 1명이 주문 3개를 순서대로 처리함. (하나 끝나야 다음 거 시작)</li>
<li><b>멀티 스레드:</b> 요리사 3명이 한 주방(Process Memory)에서 동시에 주문 3개를 처리함.</li>
</ul>
</li>
</ul>
<h4>2) 핵심 개념: 동시성(Concurrency) vs 병렬성(Parallelism), 2-2에서 더 자세히</h4>
<ul>
<li><b>동시성 (Concurrency):</b> 싱글 코어에서 여러 스레드를 <b>아주 빠르게 번갈아 가며 실행</b>해서 동시에 실행되는 것처럼 보이게 하는 것. (논리적 동시)</li>
<li><b>병렬성 (Parallelism):</b> 멀티 코어에서 실제로 여러 스레드가 <b>물리적으로 동시에</b> 실행되는 것.</li>
</ul>
<h4>3) 컨텍스트 스위칭 (Context Switching) - 멀티스레딩의 비용&nbsp;</h4>
<ul>
<li><b>정의:</b> CPU가 실행 중인 스레드를 멈추고, 다른 스레드를 실행하기 위해 <b>상태(Context)를 저장하고 교체하는 작업</b>.</li>
<li><b>문제점:</b> 스레드가 너무 많으면, 실제 일하는 시간보다 교체하는 시간(Overhead)이 더 커져서 성능이 오히려 떨어질 수 있다.</li>
</ul>
<h4>4) 장단점 요약</h4>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>구분</b></td>
<td><b>내용</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>장점</b></span></td>
<td><span>1. <b>응답성:</b> 긴 작업(파일 다운로드) 중에도 화면이 멈추지 않음.</span><br /><br /><span>2. <b>자원 효율:</b> CPU가 노는 시간(Idle time)을 줄일 수 있음.</span></td>
</tr>
<tr>
<td><span><b>단점</b></span></td>
<td><span>1. <b>동기화 문제:</b> 여러 스레드가 동시에 같은 데이터를 고치면 값이 꼬임 (Thread-Safe 필요).</span><br /><br /><span>2. <b>디버깅 어려움:</b> 버그가 발생했을 때 재현하기가 매우 까다로움.</span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<p>❓ 스레드가 많으면 무조건 좋은가요? <br />스레드가 너무 많으면 컨텍스트 스위칭(Context Switching) 비용이 커져서 CPU가 일은 안 하고 스레드 교체만 하느라 바빠집니다따라서 적절한 스레드 풀(Thread Pool) 사이즈를 설정하는 것이 중요합니다.</p>
<h3>2-2. 싱글 코어 vs 멀티 코어 (동시성 vs 병렬성)</h3>
<p><figure class="imageblock alignCenter"><span><img height="106" src="https://blog.kakaocdn.net/dn/qmo7r/dJMcaiIMRPN/qiua9OpgLC6G9CvDESWUP0/img.png" width="967" /></span></figure>
</p>
<p>멀티스레딩이 실제 하드웨어(CPU)에서 어떻게 돌아가는지 이해하는 것이 핵심.</p>
<h4>1) 싱글 코어 (Single Core) - "동시성 (Concurrency)"</h4>
<ul>
<li><b>상황:</b> 직원은 1명(Core)인데, 처리해야 할 주문(Thread)이 3개인 상황.</li>
<li><b>동작 방식 (시분할, Time Slicing):</b>
<ul>
<li>직원이 엄청나게 빠른 속도로 주문 A를 0.01초 하고, 주문 B를 0.01초 하고, 다시 A로 돌아오는 식.</li>
<li><b>핵심:</b> 실제로 동시에 하는 게 아니라, <b>번갈아 가며 실행</b>하는데 그 속도가 너무 빨라서 사용자 눈에는 동시에 실행되는 것처럼 보임.</li>
<li><b>키워드:</b> <b>논리적 동시 실행</b>, <b>컨텍스트 스위칭(Context Switching)</b> 발생.</li>
</ul>
</li>
</ul>
<h4>2) 멀티 코어 (Multi Core) - "병렬성 (Parallelism)"</h4>
<ul>
<li><b>상황:</b> 직원이 2명(Dual Core) 이상이고, 주문(Thread)도 여러 개인 상황.</li>
<li><b>동작 방식:</b>
<ul>
<li>직원 A는 주문 1을 처리하고, 직원 B는 주문 2를 처리함.</li>
<li><b>핵심:</b> 실제로 물리적으로 <b>동시에</b> 작업이 수행됨.</li>
<li><b>키워드:</b> <b>물리적 동시 실행</b>, 성능 극대화.</li>
</ul>
</li>
</ul>
<h4>동시성 vs 병렬성 비교표</h4>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>구분</b></td>
<td><b>싱글 코어 (Single Core)</b></td>
<td><b>멀티 코어 (Multi Core)</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>개념</b></span></td>
<td><span><b>동시성 (Concurrency)</b></span></td>
<td><span><b>병렬성 (Parallelism)</b></span></td>
</tr>
<tr>
<td><span><b>실행 방식</b></span></td>
<td><span>하나의 CPU가 시간을 쪼개서 번갈아 실행</span></td>
<td><span>여러 CPU가 실제로 동시에 실행</span></td>
</tr>
<tr>
<td><span><b>비유</b></span></td>
<td><span>요리사 1명이 칼질하다가 냄비 젓다가 왔다 갔다 함</span></td>
<td><span>요리사 2명이 한 명은 칼질, 한 명은 냄비 저음</span></td>
</tr>
<tr>
<td><span><b>특징</b></span></td>
<td><span>Context Switching 비용이 큼</span></td>
<td><span>멀티스레드 효율이 좋지만, 동기화(Lock) 문제 주의 필요</span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<h3>2-3. Java에서의 동시성(Concurrency)과 스레드 제어</h3>
<p>OS 이론인 스레드를 넘어, 실제 자바 개발에서 <b>"여러 스레드가 동시에 자원에 접근할 때(Multi-thread)"</b> 발생하는 문제와 해결책.</p>
<h4>1) Thread-Safe (스레드 안전)란?</h4>
<ul>
<li><b>정의:</b> 멀티 스레드 환경에서 여러 스레드가 동시에 하나의 객체나 변수에 접근해도, 프로그램의 실행 결과가 올바르게 유지되는 상태.</li>
<li><b>구현 방법:</b>
<ul>
<li><b>Lock 사용:</b> synchronized 키워드 등을 사용해 한 번에 한 스레드만 접근하게 막음.</li>
<li><b>동시성 컬렉션 사용:</b> ConcurrentHashMap, AtomicInteger 등 내부적으로 안전하게 설계된 클래스 사용.</li>
</ul>
</li>
</ul>
<h4>2) Map 구현체의 차이 (Hashtable vs ConcurrentHashMap)</h4>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>구분</b></td>
<td><b>Hashtable (구형)</b></td>
<td><b>ConcurrentHashMap (신형)</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>동기화 방식</b></span></td>
<td><span>메서드 전체에 synchronized가 걸려있음.</span></td>
<td><span><b>Lock Striping</b> (데이터를 여러 구역으로 나눠 필요한 구역만 잠금)</span></td>
</tr>
<tr>
<td><span><b>성능</b></span></td>
<td><span>한 스레드가 쓰고 있으면 다른 모든 스레드가 대기해야 함 (느림).</span></td>
<td><span>여러 스레드가 동시에 읽거나, 서로 다른 구역에 쓸 수 있음 (빠름).</span></td>
</tr>
<tr>
<td><span><b>Null 허용</b></span></td>
<td><span>Key, Value 모두 Null 불가</span></td>
<td><span>Key, Value 모두 Null 불가</span></td>
</tr>
</tbody>
</table>
<h4>3) 스레드 풀 (Thread Pool)</h4>
<ul>
<li><b>정의:</b> 스레드를 미리 만들어두고(Pool), 작업이 들어오면 대기 중인 스레드를 재사용하는 기법.</li>
<li><b>왜 쓰는가?:</b> 스레드 생성(new Thread)은 OS 리소스를 많이 소모하는 비싼 작업이다. 요청마다 스레드를 만들면 서버가 뻗을 수 있다.</li>
<li><b>동작원리</b></li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="1486" src="https://blog.kakaocdn.net/dn/weLEk/dJMcajt88nc/aECVOiA9ZyvciRrKYM1GzK/img.png" width="3099" /></span></figure>
</p>
<p><b>❓ </b>ConcurrentHashMap은 어떻게 락을 덜 걸면서 안전한가요?&nbsp;</p>
<p>Hashtable은 식당 문 전체를 잠그고 한 명만 밥을 먹게 하는 방식이라면, ConcurrentHashMap은 식탁(Bucket)별로만 잠금을 겁니다. 1번 테이블에서 밥을 먹어도 2번 테이블 손님은 기다릴 필요가 없습니다. 또한, 값을 읽을(Read) 때는 아예 락을 걸지 않고, 쓸(Write) 때만 CAS(Compare And Swap) 알고리즘 등을 사용해 성능을 극대화했습니다.</p>
<p>&nbsp;</p>
<h3>3. 자료구조: ArrayList와 LinkedList</h3>
<p>데이터를 저장하는 방식(메모리 구조)에 따라 성능 차이가 발생한다.</p>
<p><b>1) ArrayList (배열 리스트)</b></p>
<ul>
<li><b>구조:</b> 데이터가 메모리 상에 <b>연속적으로 나열</b>되어 있다.</li>
<li><b>특징:</b>
<ul>
<li>데이터의 위치(Index)를 알면 즉시 접근할 수 있다. (<b>조회 속도 빠름</b>)</li>
<li>중간에 데이터를 넣거나 빼려면, 뒤의 데이터를 한 칸씩 다 밀어야 한다. (<b>삽입/삭제 느림</b>)</li>
</ul>
</li>
</ul>
<p><b>2) LinkedList (연결 리스트)</b></p>
<ul>
<li><b>구조:</b> 데이터가 메모리 여기저기에 흩어져 있고, '다음 데이터의 주소(Reference)'를 들고 연결되어 있다.</li>
<li><b>특징:</b>
<ul>
<li>N번째 데이터를 찾으려면 첫 번째부터 주소를 따라가야 한다. (<b>조회 속도 느림</b>)</li>
<li>중간에 데이터를 넣거나 뺄 때, 연결된 주소만 바꿔주면 된다. (<b>삽입/삭제 빠름</b> - <i>단, 탐색 시간 제외</i>)</li>
</ul>
</li>
</ul>
<p>❓ ArrayList와 LinkedList의 차이점과, 본인은 무엇을 선호하는지 말해주세요.</p>
<p>데이터가 메모리에 저장되는 <b>구조</b>가 다릅니다. <b>ArrayList</b>는 데이터가 아파트 호수처럼 <b>연속적으로 저장</b>되어 있어 인덱스로 한 번에 조회할 수 있습니다. 반면 <b>LinkedList</b>는 데이터가 여기저기 흩어져 있고, <b>주소(Reference)로 연결</b>된 보물찾기 쪽지 같은 형태라 조회가 느립니다. 현업에서는 조회가 훨씬 빈번하게 일어나므로, 저는 대부분 <b>ArrayList</b>를 사용합니다.</p>
<h3>3-1. HashMap의 동작 원리</h3>
<h4>1) HashMap 구조</h4>
<ul>
<li><b>정의:</b> Key-Value 쌍으로 데이터를 저장하며, Key의 해시(Hash)값을 이용해 저장 위치를 결정하는 자료구조.</li>
<li><b>내부 동작:</b>
<ol>
<li>Key.hashCode()를 호출해 해시값을 얻음.</li>
<li>해시값을 배열(Bucket)의 크기로 나눈 나머지(인덱스) 위치에 저장.</li>
<li>검색 속도: O(1) (상수 시간). 키만 알면 계산해서 바로 찾아감.</li>
</ol>
</li>
</ul>
<h4>2) 해시 충돌(Hash Collision)과 해결</h4>
<ul>
<li><b>문제:</b> 서로 다른 Key가 우연히 같은 해시값을 가지거나, 같은 인덱스에 배정되는 경우.</li>
<li><b>해결책 (Java의 방식 - Seperate Chaining):</b>
<ul>
<li>같은 칸에 데이터가 들어오면 <b>LinkedList</b>로 줄줄이 연결함.</li>
<li><b>Java 8 이후의 최적화:</b> 하나의 버킷에 데이터가 8개 이상 쌓이면, LinkedList 대신 <b>Red-Black Tree</b>로 변환하여 조회 속도를 O(N)에서 O(log N)으로 획기적으로 줄임.</li>
</ul>
</li>
</ul>
<p><b>❓ </b>equals()와 hashCode()는 왜 같이 재정의해야 하나요?</p>
<p>HashMap에서 Key를 찾을 때 두 단계를 거치기 때문입니다.</p>
<ol>
<li>hashCode()로 어느 방(Bucket)에 있는지 찾습니다.</li>
<li>그 방 안에 있는 객체들 중 equals()가 true인 것을 최종적으로 꺼냅니다. 만약 hashCode만 재정의하고 equals를 안 하면, 같은 방까지는 갔는데 "이게 내 거 맞나?" 확인을 못 해서 null을 반환하거나 엉뚱한 값을 가져오는 오류가 발생합니다.</li>
</ol>