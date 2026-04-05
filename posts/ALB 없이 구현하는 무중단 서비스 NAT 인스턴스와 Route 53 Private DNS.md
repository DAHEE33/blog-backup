# ALB 없이 구현하는 무중단 서비스: NAT 인스턴스와 Route 53 Private DNS 조합

**발행일:** Mon, 6 Apr 2026 07:16:06 +0900

**링크:** https://hee-story6.tistory.com/243

---

<p>이전에 RDS로 띄우고 5일만에 7만원정도 비용이 나온적이 있었다. 그땐 급하기도 했고, 내가 뭔가 잘못 설정했었겠지 란 생각에 이번 프로젝트에서 최소 비용으로 도전하고 싶었다. 연결 자체는 AWS는 참 쉬운 듯 보였으나 보안을 위해 RDS를 프라이빗 서브넷(Private Subnet)에 넣었더니, 로컬 IntelliJ에서 DB 연결하는 과정이 거의 첩보 작전 수준이었다. SSH 터널링 설정하랴, 보안 그룹(Security Group) 열어주랴 그 외 2일 정도를 이것저것 도전하는 사이 비용이 누가봐도 이대로라면 10만원 넘겠더라.&nbsp;</p>
<p>"이럴 거면 차라리 가성비로 가자." RDS를 과감히 정리하고, 기존에 이용하던 외부 DB 서비스인 Aiven을 이용하는 걸로 변경했다.</p>
<h3>1.가성비 아키텍처: ALB 없이 NAT 인스턴스로 버티기</h3>
<p>ALB(Application Load Balancer)는 사용하면 기본적으로 나가는 요금이 있다. 때문에 NAT 인스턴스에 Nginx를 올려서 리버스 프록시로 활용하는 전략을 택했다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="text-align: center;"><b>항목</b></td>
<td style="text-align: center;"><b>Before (RDS + ALB)</b></td>
<td style="text-align: center;"><b>After (Aiven + NAT Proxy)</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td style="text-align: center;"><span><b>DB</b></span></td>
<td style="text-align: center;"><span>AWS RDS (프라이빗)</span></td>
<td style="text-align: center;"><span>Aiven (외부 매니지드)</span></td>
</tr>
<tr>
<td style="text-align: center;"><span><b>로드밸런서</b></span></td>
<td style="text-align: center;"><span>ALB (~$20/월+)</span></td>
<td style="text-align: center;"><span>Nginx 리버스 프록시</span></td>
</tr>
<tr>
<td style="text-align: center;"><span><b>로컬 DB 접근</b></span></td>
<td style="text-align: center;"><span>SSH 터널링 지옥</span></td>
<td style="text-align: center;"><span>직접 연결 가능</span></td>
</tr>
<tr>
<td style="text-align: center;"><span><b>운영 비용</b></span></td>
<td style="text-align: center;"><span>High</span></td>
<td style="text-align: center;"><span>Low&nbsp;</span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<h3>2. 주요 장애 포인트와 해결 과정</h3>
<h4>장애 1: "왜 DB 연결이 안 돼?" (The Config Trap)</h4>
<p><b>현상:</b> 앱은 정상적으로 기동됐으나, The connection attempt failed 에러를 뱉으며 바로 종료됐다. <br /><b>원인:</b> GitHub Actions에서 TF_VAR로 넘겨준 변수가 EC2의 .service 파일까지 전달되지 않았다.</p>
<ul>
<li><b>오타의 저주:</b> 변수 일부를 넣는 과정에서 소문자 l(엘)이 i(아이)로 바뀌어 들어갔다. 폰트 차이 때문에 눈으로는 절대 구분이 안 됐다. <b>절대 작은 것이라도 복붙 활용을 해야한다..</b></li>
<li><b>쌍따옴표 함정:</b> systemd 환경변수 값에 ""가 함께 들어가면서 스프링 부트가 문자열을 그대로 인식해 버렸다.</li>
</ul>
<p><b>해결:</b> Terraform 템플릿(.tftpl)을 수정해 변수를 직접 주입하고, 특수문자 이스케이프 처리를 추가해 자동화했다.</p>
<h4>장애 2: "죽은 서버의 IP를 붙잡고 있는 Nginx" (The Ghost IP)</h4>
<p><b>현상:</b> 외부 도메인 접속 시 504 Gateway Time-out 발생.</p>
<p><b>원인:</b> ASG(Auto Scaling Group) 특성상 인스턴스가 교체되면 Private IP가 바뀌는데, Nginx는 옛날 IP(10.0.4.119)를 고집스럽게 찾아가고 있었다.</p>
<p><b>해결:</b> 처음엔 sed로 IP를 직접 갈아끼우고 reload를 시도했으나, Nginx가 기존 커넥션을 끊지 못하는 문제가 발생했다.</p>
<p>restart를 해야만 IP를 인식했는데 이럴 경우 무중단 서비스를 고려할 경우 비적합한거 같아, cron으로 IP를 가져오려 했으나 어찌된 일인지 먹히지 않았다. 그래서 Route 53 Private Hosted Zone을 구축했다.</p>
<p>&nbsp;</p>
<ol>
<li><b>내부 전용 도메인 생성:</b> app.internal.moa라는 내부용 주소를 할당한다.</li>
<li><b>Nginx Resolver 설정:</b> Nginx가 10초마다(valid=10s) 이 도메인의 IP를 새로 조회하게 만든다.</li>
<li><b>무중단 갱신:</b> 스크립트가 앱 서버 IP를 감지하면 Route 53의 A 레코드만 업데이트(UPSERT)한다. Nginx는 재시작 없이 자연스럽게 새 IP를 바라본다.</li>
</ol>
<h3>3. 최종 아키텍처 흐름</h3>
<ol>
<li><b>배포 단계:</b> GitHub Actions &rarr; Terraform &rarr; App Instance에 tftpl로 정확한 환경변수 주입.</li>
<li><b>추적 단계:</b> NAT 인스턴스의 Cron Job(1분 주기)이 ASG에서 InService인 앱 서버 IP를 탈취.</li>
<li><b>등기 단계:</b> 탈취한 IP를 Route 53 Private DNS 레코드에 등기(UPSERT).</li>
<li><b>라우팅 단계:</b> 외부 사용자가 접속하면 Nginx가 DNS를 통해 최신 앱 서버로 안내.</li>
</ol>
<p>이번 프로젝트를 통해 처음 해보는 기술적 도전이 많았다. AI의 도움을 많이 받았지만, 결국 무한 반복되는 에러의 실타래를 푸는 것은 로그를 직접 확인하고 원인을 분석하는 '나의 눈'이었다.</p>
<p>비용을 아끼기 위해 시작한 '가성비' 전략이었지만, 결과적으로는 AWS 인프라의 깊은 곳(Private DNS, Resolver, ASG 스크립트 등)을 직접 만져보며 성장할 수 있었던 소중한 시간이었다.</p>
<p>&nbsp;</p>