# Spring Boot JAR 배포 시 application.yml 설정 적용 우선순위

**발행일:** Wed, 19 Feb 2025 05:18:01 +0900

**링크:** https://hee-story6.tistory.com/219

---

<p><span>Spring Boot 프로젝트를 JAR 파일로 배포할 때 </span><span>application.yml</span><span> 설정이 어떻게 적용되는지 헷갈릴 수 있다. </span></p>
<p><span>이번에 개발망 JAR를 실행시키려 했는데 실행이 되지 않았고 JAR 내부에 </span><span>application.yml</span><span>이 포함되어 있는 경우, 또는 외부 설정 파일을 사용할 경우 Spring Boot는 특정 우선순위에 따라 설정을 로드한다는 걸 몰랐었다. 이번 글에서는 </span><span><b>Spring Boot의 설정 파일 적용 원리와 우선순위</b></span><span>를 정리해보았다.</span></p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<h2><span>1. Spring Boot에서 설정 파일 적용 원리</span></h2>
<p><span>Spring Boot는 </span><span>application.yml</span><span> 또는 </span><span>application.properties</span><span> 파일을 이용해 애플리케이션 설정을 관리한다. JAR 배포 시, Spring Boot는 설정 파일을 다음과 같은 우선순위에 따라 로드한다.</span></p>
<h3><span><b>  Spring Boot 설정 파일 우선순위 (높은 순서부터 적용됨)</b></span></h3>
<ol>
<li><span><b>실행 시 </b></span><span><b>--spring.config.location</b></span><span><b> 옵션으로 지정한 설정 파일</b></span></li>
<li><span><b>환경 변수 </b></span><span><b>SPRING_CONFIG_LOCATION</b></span><span><b>에 지정된 설정 파일</b></span></li>
<li><span><b>JAR 파일과 같은 디렉터리(</b></span><span><b>./application.yml</b></span><span><b> 또는 </b></span><span><b>./config/application.yml</b></span><span><b>)</b></span></li>
<li><span><b>JAR 내부 </b></span><span><b>BOOT-INF/classes/application.yml</b></span><span><b> (Spring Boot 프로젝트의 </b></span><span><b>src/main/resources/application.yml</b></span><span><b>)</b></span></li>
</ol>
<p><span>즉, </span><span><b>외부에 설정 파일이 존재하면 내부 설정보다 우선 적용되며</b></span><span>, 외부 설정이 없을 경우 JAR 내부 설정이 기본값으로 사용된다.</span></p>
<p>&nbsp;</p>
<h2><span>2. JAR 내부 설정만 있을 경우 (</span><span>application.yml</span><span> 포함됨)</span></h2>
<p><span>JAR 내부에 </span><span>application.yml</span><span>이 포함된 경우, 별다른 설정 없이도 Spring Boot는 내부 설정을 자동으로 인식한다.</span></p>
<h3><span><b>✅ 실행 방법</b></span></h3>
<pre class="mipsasm"><code>java -jar myapp.jar</code></pre>
<p><span>  이 경우, JAR 내부 </span><span>BOOT-INF/classes/application.yml</span><span>이 적용된다.</span></p>
<h3><span><b>  JAR 내부 설정 포함 여부 확인</b></span></h3>
<p><span>JAR 내부에 </span><span>application.yml</span><span>이 정상적으로 포함되었는지 확인하려면 아래 명령어를 실행하면 된다.</span></p>
<pre class="mipsasm"><code>jar tf myapp.jar | grep application.yml</code></pre>
<p><span>출력 예시:</span></p>
<pre class="stata"><code>BOOT-INF/classes/application.yml</code></pre>
<p><span>이처럼 </span><span>BOOT-INF/classes/application.yml</span><span>이 보이면 내부 설정이 정상적으로 포함된 것이다.</span></p>
<p>&nbsp;</p>
<h2><span>3. 외부 </span><span>application.yml</span><span> 설정을 적용하는 방법</span></h2>
<p><span>외부 설정을 적용하고 싶다면, 다음과 같은 방법을 사용할 수 있다.</span></p>
<h3><span><b>✅ 방법 1: 실행 시 </b></span><span><b>--spring.config.location</b></span><span><b> 옵션 사용</b></span></h3>
<p><span>실행할 때 명시적으로 외부 설정 파일을 지정하면, JAR 내부 설정보다 우선 적용된다.</span></p>
<pre class="jboss-cli"><code>java -jar myapp.jar --spring.config.location=/path/to/application.yml</code></pre>
<p><span>또는 설정 파일이 포함된 디렉터리를 지정할 수도 있다.</span></p>
<pre class="arduino"><code>java -jar myapp.jar --spring.config.location=/path/to/config/</code></pre>
<h3><span><b>✅ 방법 2: 환경 변수 </b></span><span><b>SPRING_CONFIG_LOCATION</b></span><span><b> 사용</b></span></h3>
<p><span>환경 변수로 설정 파일 경로를 지정할 수도 있다.</span></p>
<pre class="routeros"><code>export SPRING_CONFIG_LOCATION=/path/to/application.yml
java -jar myapp.jar</code></pre>
<p><span>이렇게 하면 JAR을 실행할 때마다 특정 설정 파일을 강제로 로드할 수 있다.</span></p>
<h3><span><b>✅ 방법 3: JAR과 같은 디렉터리 또는 </b></span><span><b>config/</b></span><span><b> 디렉터리에 </b></span><span><b>application.yml</b></span><span><b> 배치</b></span></h3>
<p><span>JAR 파일과 같은 디렉터리 또는 </span><span>config/</span><span> 디렉터리에 </span><span>application.yml</span><span>을 두면, Spring Boot는 이를 자동으로 인식하여 내부 설정보다 우선 적용한다.</span></p>
<p><span><b>디렉터리 구조 예시:</b></span></p>
<pre class="routeros"><code>/app/
 ├── myapp.jar
 ├── application.yml  # JAR과 같은 경로에 두면 자동 인식됨
 ├── config/
 │   ├── application.yml  # 또는 config 디렉터리에 두어도 인식됨</code></pre>
<p><span><b>실행:</b></span></p>
<pre class="mipsasm"><code>java -jar myapp.jar</code></pre>
<p><span>이렇게 하면 </span><span><b>JAR 내부 설정이 아닌 외부 </b></span><span><b>application.yml</b></span><span><b> 설정이 적용</b></span><span>된다.</span></p>
<div>
<h2 style="color: #000000; text-align: start;"><span>4.<span>&nbsp;</span></span><span>application.yml</span><span><span>&nbsp;</span>변경 시 적용 방법</span></h2>
</div>
<p><span><b>JAR이 실행된 상태에서 </b></span><span><b>application.yml</b></span><span><b>을 변경해도 즉시 반영되지 않는다.</b></span></p>
<p><span>  </span><span><b>변경 사항을 반영하려면 서버를 재시작해야 한다.</b></span></p>
<pre class="nginx"><code>systemctl restart myapp  # systemd 사용 시</code></pre>
<p><span>또는 수동으로 실행 중인 프로세스를 종료하고 다시 실행:</span></p>
<pre class="reasonml"><code>kill -9 $(ps -ef | grep myapp.jar | grep -v grep | awk '{print $2}')
nohup java -jar myapp.jar &amp;</code></pre>
<div>&nbsp;</div>
<h2><span>5. </span><span>spring.profiles.active</span><span>를 활용한 설정 관리 (추천)</span></h2>
<p><span>Spring Boot에서는 여러 개의 설정 파일을 </span><span>spring.profiles.active</span><span>를 이용해 쉽게 관리할 수 있다.</span></p>
<h3><span><b>  </b></span><span><b>application.yml</b></span><span><b>에서 기본 프로파일 지정</b></span></h3>
<pre class="less"><code>spring:
  profiles:
    active: dev  # 기본 프로파일을 'dev'로 설정</code></pre>
<h3><span><b>  각 환경별 설정 파일 분리</b></span></h3>
<p><span>  </span><span>application-dev.yml</span></p>
<pre class="yaml"><code>server:
  port: 8081</code></pre>
<p><span>  </span><span>application-prod.yml</span></p>
<pre class="yaml"><code>server:
  port: 8082</code></pre>
<p><span><b>실행 시 프로파일을 지정하면 해당 설정이 적용된다.</b></span></p>
<pre class="mipsasm"><code>java -jar myapp.jar --spring.profiles.active=prod</code></pre>
<p><span>이렇게 하면 </span><span>application-prod.yml</span><span>이 적용되며, </span><span>application.yml</span><span> 기본 설정보다 우선 적용된다.</span></p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<h2><span><b>  정리</b></span></h2>
<p>  적용 방법우선순위</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><span>--spring.config.location=/path/to/application.yml</span></td>
<td><span>✅ 최우선</span></td>
</tr>
<tr>
<td><span>환경 변수 </span><span>SPRING_CONFIG_LOCATION</span></td>
<td><span>✅ 높은 우선순위</span></td>
</tr>
<tr>
<td><span>JAR과 같은 디렉터리 </span><span>/application.yml</span><span> 또는 </span><span>config/application.yml</span></td>
<td><span>✅ 내부 설정보다 우선 적용됨</span></td>
</tr>
<tr>
<td><span>JAR 내부 </span><span>/BOOT-INF/classes/application.yml</span></td>
<td><span>  최후의 기본 설정</span></td>
</tr>
</tbody>
</table>
<p><span>✅ </span><span><b>외부 설정을 적용하려면 </b></span><span><b>--spring.config.location</b></span><span><b>을 지정하거나, JAR과 같은 디렉터리 또는 </b></span><span><b>config/</b></span><span><b> 디렉터리에 </b></span><span><b>application.yml</b></span><span><b>을 두는 것이 가장 간편한 방법이다.</b></span></p>
<p><span>✅ </span><span><b>여러 개의 설정 파일이 필요하다면 </b></span><span><b>spring.profiles.active</b></span><span><b>를 활용하는 것이 좋다.</b></span></p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<p><span>Spring Boot JAR 배포 시 설정 파일이 적용되는 원리를 이해하고, 필요에 맞게 적절한 설정 방식을 선택하자!</span></p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<div>&nbsp;</div>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>