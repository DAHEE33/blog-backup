# [AWS 인프라 구축기] 극한의 비용 최적화로 완성한 대용량 예매 시스템 배포 아키텍처

**발행일:** Thu, 26 Mar 2026 08:00:55 +0900

**링크:** https://hee-story6.tistory.com/241

---

<p><figure class="imageblock alignCenter"><span><img height="164" src="https://blog.kakaocdn.net/dn/bcDvvq/dJMcagrmqaV/eIn5bddBnmN9KoydADeDlK/img.png" width="869" /></span></figure>
</p>
<p>또또또 부과됐다. AWS 해볼까 할 때마다 단기간에 이렇게까지 나올수있나 싶다.</p>
<p>이번에는 인강 들으면서 켜놨던 리소스를 제대로 종료하지 않았고 다음 날이라도 확인했었야했는데, root계정으로 로그인을 하지 않다보니 시간이 지나서 확인하여 생긴 문제 ㅠ ㅠ</p>
<p>재빨리 대시보드로 일정 예산 금액 넣으면 알림이 오게 해놨다.. 지금 이런 경험으로 AWS 구축에 오기가 생긴다!!</p>
<h2>01. 왜 이런 설계를 선택했나</h2>
<p><b>포트폴리오지만 실무처럼 &mdash; FinOps 마인드셋으로 설계한 이유</b></p>
<p>포트폴리오 프로젝트라도 AWS를 실무처럼 띄워놓고 방치하면 한 달에 수십만 원이 과금될 수 있다. 비용과 트레이드오프를 명확히 인지하고, 어떻게 비용을 억제하면서 실무급 아키텍처를 구성했는지 기록하는 과정이다.&nbsp;</p>
<blockquote>
<p><b>핵심 전략</b> Terraform IaC로 전체 인프라를 코드화하여 부하 테스트 시에만 terraform apply로 올리고, 완료 후 즉시 terraform destroy로 파기. <b>필요할 때만 켜는 구조</b>로 예산을 완벽하게 통제</p>
</blockquote>
<h3>전체 아키텍처 한눈에</h3>
<ul>
<li><b>사용자 브라우저</b> &rarr; Route 53 &rarr; CloudFront + S3 (React)</li>
<li><b>Public Subnet:</b> ALB (443/80) &rarr; ASG Spot Instance (Spring Boot)</li>
<li><b>Private Subnet:</b> RDS PostgreSQL | Infra EC2 (Redis + Kafka + Prometheus + Grafana)</li>
<li><b>인터넷 아웃바운드:</b> NAT Instance (t2.micro)를 통한 인터넷 연결</li>
</ul>
<p><figure class="imageblock alignCenter"><span><img height="407" src="https://blog.kakaocdn.net/dn/VQYUn/dJMcaibFHld/QJE6L4od3GXjkbzqGF0mh0/img.png" width="1145" /></span></figure>
</p>
<h2>02. 1주차 &mdash; VPC &amp; 네트워크 기반 구성</h2>
<p><b>main.tf : VPC / 서브넷 / IGW / 라우팅테이블 / NAT Instance</b></p>
<h3>VPC와 서브넷 설계 (퍼블릭/프라이빗 분리)</h3>
<p>AWS 내에 프로젝트만의 격리된 가상 네트워크를 만든다. 가장 신경 쓴 부분은 <b>'보안'과 '비용'의 균형</b>. DB와 핵심 백엔드 서버는 외부에서 직접 접근할 수 없도록 Private Subnet에 숨기고, 사용자 트래픽을 받는 로드밸런서(ALB)만 Public Subnet에 배치했다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>서브넷</b></td>
<td><b>CIDR</b></td>
<td><b>AZ (가용영역)</b></td>
<td><b>역할</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>public-a</b></span></td>
<td><span>10.0.1.0/24</span></td>
<td><span>ap-northeast-2a</span></td>
<td><span>ALB, NAT Instance</span></td>
</tr>
<tr>
<td><span><b>public-c</b></span></td>
<td><span>10.0.2.0/24</span></td>
<td><span>ap-northeast-2c</span></td>
<td><span>ALB (고가용성)</span></td>
</tr>
<tr>
<td><span><b>private-a</b></span></td>
<td><span>10.0.3.0/24</span></td>
<td><span>ap-northeast-2a</span></td>
<td><span>App Server, Infra EC2, RDS</span></td>
</tr>
<tr>
<td><span><b>private-c</b></span></td>
<td><span>10.0.4.0/24</span></td>
<td><span>ap-northeast-2c</span></td>
<td><span>RDS Multi-AZ</span></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<h3>NAT Instance &mdash; 핵심 비용 절감 포인트</h3>
<p>프라이빗 서브넷에 갇힌 서버들도 외부 API 호출이나 패키지 다운로드를 위해 인터넷이 필요하다. 이를 위해 AWS 관리형 <b>NAT Gateway를 쓰면 월 $45</b>라는 고정 비용이 발생하지만, 프리티어가 적용되는 <b>t2.micro EC2 한 대를 NAT 공유기처럼 활용</b>하기로 했다.</p>
<blockquote>
<p><b>NAT Instance 작동 원리 (source_dest_check)</b> 테라폼 코드에서 source_dest_check = false 설정이 핵심이다. 기본적으로 EC2는 목적지가 자신이 아닌 패킷은 버리도록 설계되어 있는데, 이 옵션을 꺼야만 프라이빗 서브넷에서 온 트래픽을 외부 인터넷으로 중계(포워딩)할 수 있다.</p>
</blockquote>
<pre class="html xml" id="code_1774427138670"><code>#!/bin/bash
# 1. iptables-services 먼저 설치 (설치 후 룰 저장해야 하므로 순서 중요)
dnf install -y iptables-services
systemctl enable iptables

# 2. IP 포워딩 활성화 &mdash; 다른 서버의 패킷을 중계할 수 있게 함
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" &gt;&gt; /etc/sysctl.conf

# 3. 네트워크 인터페이스 자동 추출
ETH=$(ip route show default | awk '/default/ {print $5}')

# 4. iptables NAT 룰 &mdash; 나가는 트래픽의 출발지 IP를 NAT Instance IP로 변환
iptables -t nat -A POSTROUTING -o $ETH -j MASQUERADE

# 5. 재부팅 시에도 룰 유지 (설치 완료 후 저장)
iptables-save &gt; /etc/sysconfig/iptables</code></pre>
<p>&nbsp;</p>
<h2>03. 2주차 &mdash; Infra EC2 구성</h2>
<p><b>infra.tf : Redis + Kafka + Prometheus + Grafana를 단일 EC2에</b></p>
<h3>왜 단일 EC2에 다 올리나? (Docker 도입 이유)</h3>
<p>Redis, Kafka, 모니터링 툴을 AWS 관리형 서비스(ElastiCache, MSK 등)로 분리해서 쓰면 비용이 감당 안 될 정도로 커져서, 깡통 인스턴스(t3.micro) 한 대를 빌리고, 그 안에서 <b>Docker Compose를 활용하여 각 프로그램들을 컨테이너로 격리 실행</b>해 비용을 $0으로 하고자 했다.</p>
<h3>Swap 4GB &mdash; 1GB RAM의 한계 극복</h3>
<p>t3.micro는 저렴하지만 <b>RAM이 딱 1GB</b>뿐입니다. 무거운 Kafka와 여러 컨테이너를 동시에 띄우면 메모리 부족(OOM)으로 인스턴스가 다운된다. 이를 해결하기 위해 SSD 공간 4GB를 가상 RAM으로 속여서 사용하는 <b>Swap 메모리 설정</b>을 추가했다. 속도 트레이드오프는 존재하지만, 포트폴리오 트래픽을 처리하기 위한 최선의 선택이라고 생각했다.</p>
<pre class="html xml" id="code_1774427166212"><code># Swap 4GB 설정
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile swap swap defaults 0 0' &gt;&gt; /etc/fstab

# Docker 설치 및 실행
dnf install -y docker
systemctl enable docker
systemctl start docker</code></pre>
<h3>Kafka KRaft 모드 &amp; JVM Heap 튜닝 (Stop-the-World 방지)</h3>
<p>메모리를 아끼기 위해 Zookeeper 없이 자체적으로 메타데이터를 관리하는 <b>KRaft 모드</b>를 적용했다. 더 중요한 것은 <b>JVM Heap 튜닝.</b></p>
<pre class="html xml" id="code_1774427178252"><code># docker-compose.yml 중 kafka 부분 발췌
kafka:
  image: apache/kafka:latest
  environment:
    KAFKA_PROCESS_ROLES: broker,controller   # KRaft 모드
    KAFKA_HEAP_OPTS: "-Xms512m -Xmx512m"     # ★핵심: 최소=최대로 튜닝 고정</code></pre>
<blockquote>
<p><b>JVM Heap을 왜 최소=최대로 고정할까?</b> Java는 메모리가 부족해지면 최소 힙(-Xms)에서 최대 힙(-Xmx)까지 메모리를 동적으로 늘린다. 이때 디스크(Swap)에 접근하며 엄청난 I/O가 발생하면, 수 초간 시스템이 완전히 멈추는 <b>Stop-the-World (Full GC)</b> 현상이 발생한다. 이를 예방하기 위해 "처음부터 512MB만 잡고 절대 늘리지 마!"라고 크기를 고정해둔 것이다.</p>
</blockquote>
<h3>SSM Session Manager &mdash; 키페어 없는 안전한 접속</h3>
<p>Private Subnet의 EC2는 공개 IP가 없어 SSH 직접 접속이 불가하다. 포트(22번)를 여는 것은 보안상 취약점이 될 수 있으므로, 테라폼으로 <b>AWS SSM 권한이 포함된 IAM Role</b>을 부여했다. 이를 통해 키페어 없이 AWS 콘솔에서 안전하게 인스턴스 내부에 접근한다.</p>
<pre class="html xml" id="code_1774427194529"><code>resource "aws_iam_role_policy_attachment" "infra_ssm_policy" {
  role       = aws_iam_role.infra_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}</code></pre>
<h3>EBS 용량 관리 (프리티어 30GB 한도)</h3>
<ul>
<li><b>NAT Instance:</b> 8GB</li>
<li><b>Infra EC2:</b> 15GB (이후 추가될 DB 및 App 서버를 위해 20GB가 아닌 15GB로 타이트하게 설정)</li>
<li><b>합계:</b> 23GB (30GB 한도 내 안전하게 관리)</li>
</ul>
<h2>04. 배포 검증 &mdash; docker ps</h2>
<p><b>SSM으로 Infra EC2 접속 후 컨테이너 정상 구동 확인</b></p>
<ol>
<li>AWS 콘솔 &rarr; Systems Manager &rarr; Session Manager 이동</li>
<li>moa-v2-infra-instance 인스턴스 접속</li>
<li>docker ps 명령어로 4개의 컨테이너(redis, kafka, prometheus, grafana)가 모두 정상 작동(Up)하는지 확인.</li>
<li>확인 완료 후 과금 방지를 위해 즉시 terraform destroy를 실행</li>
</ol>
<p>&nbsp;</p>