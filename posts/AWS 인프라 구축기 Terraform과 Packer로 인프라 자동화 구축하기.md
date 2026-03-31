# [AWS 인프라 구축기] Terraform과 Packer로 인프라 자동화 구축하기

**발행일:** Wed, 1 Apr 2026 07:04:23 +0900

**링크:** https://hee-story6.tistory.com/242

---

<p>토이 프로젝트를 활용해 Terraform과 Packer를 이용한 인프라 자동화를 구축하며 겪은 시행착오와 '비싼' 배움의 기록을 정리했다. 단순히 기술을 나열하는 것이 아니라, 이 과정이 얼마나 정교한 설계와 책임감을 요하는지 깨달은 시간이었다.&nbsp;</p>
<hr contenteditable="false" />
<h2>1. Packer와 Terraform, 이 둘은 뭐가 다를까?</h2>
<p>가장 먼저 두 도구의 역할을 명확히 이해하는 게 중요했다.</p>
<ul>
<li id="p-rc_7033361708178780-165"><span><b><span>Packer (The Baker):</span></b><span> 서버의 '원형'인 AMI(Amazon Machine Image)를 만드는 도구다</span></span><span><span></span></span><span>. </span><span></span><span><span>운영체제 위에 필요한 소프트웨어(Java)를 설치하고, 애플리케이션(</span><span>app.jar</span><span>)을 미리 담아 언제든 바로 실행 가능한 '밀키트' 상태로 포장하는 역할을 한다</span></span><span><span></span></span><span>.</span></li>
<li id="p-rc_7033361708178780-166"><span><b><span>Terraform (The Architect):</span></b><span> Packer가 만든 이미지를 어디에, 몇 대나 배치할지 설계하는 </span><span>인프라 구성 도구</span><span>다</span></span><span><span></span></span><span>. </span><span></span><span><span>VPC, 보안 그룹, 데이터베이스(RDS) 등 클라우드의 모든 자원을 코드로 정의하고 생성한다</span></span><span><span></span></span><span>.</span></li>
</ul>
<p>요약하면 Packer가 재료를 준비하고, Terraform이 그 재료로 집을 짓는 느낌이다.</p>
<h2>2. 48달러의 교훈: 인프라 관리의 무게</h2>
<p><figure class="imageblock alignCenter"><span><img height="596" src="https://blog.kakaocdn.net/dn/QHrGC/dJMcacJnpsZ/7ZhhFPO332V444pVlK22TK/img.png" width="1635" /></span></figure>
</p>
<p>테라폼의 편리함을 체감하기도 전에, 인프라 관리의 무서움을 먼저 맛보았다.</p>
<p>인강을 보며 실습하던 중 terraform destroy가 제대로 동작하지 않아 수동으로 AWS 리소스를 삭제한 적이 있었다. 나름 꼼꼼하게 지웠다고 생각했는데, IAM 테스트 계정으로만 확인하고 Root 계정의 비용 현황을 확인하지 않은 게 문제였다. 뒤늦게 확인한 청구서에는 <b>48달러</b>가 찍혀 있었다.</p>
<p>알고 보니 수동 삭제 과정에서 WAF(Web Application Firewall)를 놓쳤고, SQS 등 몇몇 리소스가 매일 비용을 발생시키고 있었다. 이 사건 이후 두 가지 철칙을 세웠다.</p>
<ol>
<li><b>예산 알림 설정:</b> 일정 금액 이상 발생 시 즉시 알림이 오도록 설정했다.</li>
<li><b>매일의 Destroy:</b> 아직은 인스턴스 중지(Stop)보다 삭제(Destroy)가 더 안전하다고 판단하여, 매일 테스트 종료 후 인프라를 완전히 허문다. 아침마다 Root 계정으로 들어가 비용을 확인하는 습관도 생겼다. 비싼 수업료였지만, 직접 겪어보니 인프라 관리의 정교함이 왜 필요한지 뼈저리게 느꼈다.</li>
</ol>
<p>비싼 수업료였지만, 직접 겪어보니 인프라 관리의 정교함이 왜 필요한지 뼈저리게 느꼈다. 그리고 오기도 생겼다. <b>무조건 프리티어 안에서, 최소한의 비용으로 구축하겠다!</b></p>
<p><figure class="imageblock alignCenter"><span><img height="651" src="https://blog.kakaocdn.net/dn/blkHUb/dJMcafswXmF/TGDlXUKf6FOWy9Vlr1dpK0/img.png" width="416" /></span></figure>
</p>
<h2>3. 인프라 설계: 역할에 따른 파일 분리</h2>
<p>인프라의 성격에 따라 파일을 분리하여 관리 효율성을 높였다.</p>
<ul>
<li><b>main.tf (기반 공사):</b> VPC, 서브넷, 인터넷 게이트웨이 등 한 번 구축하면 변하지 않는 네트워크의 뼈대를 설정했다.</li>
<li><b>infra.tf (고정형 시설):</b> Redis, Kafka와 같이 상시 가동되어야 하는 고정형 서버들을 정의했다.<br />
<div>&rarr; 이부분은 현재 Redis, Kafka를 Avien에서 쓰고 있으며, 내 목표는 프리티어 내에서 혹은 최소한의 비용으로 해결하는게 목표이기 때문에 Paas를 이용하기로 하였고, 초기 구성에서 추후 제외하였다.(현재 주석처리)</div>
</li>
<li id="p-rc_7033361708178780-167"><span><b><span>app.tf</span><span> (유동형 공장):</span></b><span> 트래픽에 따라 서버가 늘어나는 Auto Scaling Group(ASG)과 그 거푸집인 </span><span>Launch Template</span><span>을 설정했다</span></span><span><span></span></span><span>.<br />&rarr; Launch Template(시작템플릿)란? EC2 인스턴스를 띄울 때 필요한 모든 설정(AMI ID, 인스턴스 유형, 보안 그룹 등)을 미리 저장해둔 '설계도'<br /></span></li>
<li><b>terraform.tfstate (상태 기록):</b> GitHub Actions와의 협업을 위해 S3와 DynamoDB를 활용한 Remote Backend를 구축하여 인프라의 현재 상태를 동기화했다.</li>
</ul>
<h2 style="color: #000000; text-align: start;">4. Packer의 설계도</h2>
<p style="color: #000000; text-align: start;">상세 코드를 나열하기보다, 이미지 빌드를 위해 구성한 파일들의 역할을 정의했다.</p>
<ul>
<li><b>aws-ami.pkr.hcl</b>: 어떤 기반 이미지(AMI)를 사용하고, 어떤 인스턴스 타입으로 빌드할지 정의하는 핵심 설계도다.</li>
<li><b>variables.pkr.hcl</b>: 리전 정보나 JAR 파일 경로 등 가변적인 설정을 변수로 분리하여 관리했다.</li>
<li><b>setup.sh &amp; configure-service.sh</b>: 인스턴스 내부에 Java를 설치하고, 앱을 systemd 서비스로 등록하는 실질적인 설치 스크립트다.</li>
<li><b>moa-backend.service</b>: 앱의 실행 명령어와 재시작 정책 등을 담은 서비스 설정 파일이다.</li>
</ul>
<h2>5. 처음이기에 겪었던 시행착오와 해결 (Troubleshooting)</h2>
<p>단순히 소스 코드를 업로드하는 수준을 넘어, 초기 환경 구성을 '무(無)'에서 '유(有)'로 만드는 과정은 생각보다 복잡했다.</p>
<h3>① "단순 업로드"가 아닌 "환경 구축"의 어려움</h3>
<p id="p-rc_7033361708178780-177"><span>처음에는 파일을 올리면 끝날 줄 알았으나, 실제로는 Key Pair 관리, IAM 권한 설정, 보안 그룹(Security Group) 간의 연동 등 고려할 것이 너무 많았다. </span><span></span><span><span>특히 DB나 Redis가 실행되지 않았던 이유는 대부분 </span><span>보안 그룹에서 포트가 막혀 있거나</span><span>, 환경 변수가 제대로 주입되지 않았기 때문이었다</span></span><span><span></span></span><span>.</span></p>
<h3>② JAR 이름 통일과 경로의 지옥</h3>
<p>빌드할 때마다 달라지는 JAR 파일 이름과 Packer/Terraform 간 경로 불일치로 서버가 앱을 찾지 못하는 현상이 발생했다. 빌드 결과물 이름을 app.jar로 고정하고, Packer에서 임시로 올리는 경로(/tmp)와 최종 실행 경로(/opt/moa/backend/)를 명확히 구분해서 해결했다.</p>
<h3>③ 비밀값 관리 (Secrets &amp; Variables)</h3>
<p>DB 비밀번호나 AWS 키를 코드에 노출할 수 없으니, variables.tf에 변수를 선언하고 실제 값은 GitHub Actions의 Secrets에 저장했다. Terraform 실행 시 TF_VAR_ 접두어를 사용해 안전하게 값을 주입하는 방식을 이번에 제대로 익혔다.</p>
<h3>④ "닭이 먼저냐, 달걀이 먼저냐" - 생성 순서(Dependency) 이슈</h3>
<p>아마 이게 가장 많이 겪은 에러였던 것 같다. app.tf에서 보안 그룹이나 RDS를 생성할 때, A 리소스가 B 리소스의 ID를 참조해야 하는데 B가 아직 생성되지 않아 터지는 문제다. depends_on으로 명시적으로 순서를 지정하거나, 보안 그룹 규칙을 별도 리소스(aws_security_group_rule)로 분리해서 의존성 스파게티를 풀어냈다.</p>
<hr contenteditable="false" />
<p>이번 작업을 돌아보면, 기술 자체보다 인프라를 다루는 태도를 배웠다는 게 더 크다.</p>
<p>코드 몇 줄로 수십 개의 리소스가 생겨나는 건 분명 편리하다. 그런데 그만큼 잘못됐을 때의 파급력도 크다. 48달러짜리 실수가 준 교훈이 바로 그것이었다. 자동화는 편의를 위한 도구이지, 책임을 대신해주는 도구가 아니라는 것.</p>
<p>앞으로는 지금 구축한 기반 위에 GitHub Actions와의 CI/CD 파이프라인을 좀 더 단단하게 연결하고, 모니터링과 로깅 쪽도 손볼 계획이다. 여전히 프리티어 안에서.  </p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>