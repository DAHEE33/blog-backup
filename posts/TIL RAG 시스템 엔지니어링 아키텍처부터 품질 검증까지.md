# [TIL] RAG 시스템 엔지니어링: 아키텍처부터 품질 검증까지

**발행일:** Wed, 18 Mar 2026 20:09:13 +0900

**링크:** https://hee-story6.tistory.com/239

---

<p>국비 무제한 강의권이 끝나가는 시점, 진행하던 토이 프로젝트(티켓팅 시스템)를 마무리하며 평소 관심 있던 RAG(Retrieval-Augmented Generation)를 제대로 파보았다. 단순히 AI 모델을 호출하는 것을 넘어, 데이터 인프라를 설계하고 검증하는 과정이 백엔드 엔지니어링과 닮아 있어 흥미로운 공부였다.</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<h3>1. 데이터 인프라: 의미를 숫자로 저장하기</h3>
<ul>
<li><b>Chunking (청킹):</b> 방대한 문서를 AI가 소화하기 좋은 크기로 쪼개는 작업.</li>
<li><b>Embedding (임베딩):</b> 텍스트를 고차원 공간의 좌표(Vector)로 변환. 단순 키워드가 아닌 '의미적 유사도'를 계산하기 위함.
<ul>
<li><i>OpenAI Embedding:</i> 시장 표준으로 쓰이는 고성능 임베딩 전용 모델 서비스.</li>
</ul>
</li>
<li><b>Vector DB:</b> 좌표값들을 저장하고, 질문과 가장 가까운 데이터를 찾는 전용 저장소.
<ul>
<li><b>ANN (Approximate Nearest Neighbor):</b> 수백만 개의 데이터 중 가장 비슷한 것을 초고속으로 찾아내는 인덱싱 알고리즘.</li>
<li><b>RDB vs Vector DB:</b> '똑같은 글자(Exact Match)'를 찾는가, '비슷한 의미(Similarity Search)'를 찾는가의 차이.</li>
</ul>
</li>
</ul>
<p><b>결론:</b> 일반 DB가 데이터의 정합성을 지키는 데 목숨을 건다면, <b>벡터 DB는 사용자의 의도(Intent)를 찾는 데 목숨을 건다.</b> 쇼핑몰에서 '빨간 옷'을 검색했을 때 '진홍색 원피스'를 보여줄 수 있는 힘이 여기서 나온다.</p>
<p>이 부분이 공부할 때 제일 흥미로웠다. 어떻게 유사한 데이터를 보낼 수 있는지, Vector DB에 대해 더 공부하고 적용해보고 싶다.</p>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td><b>구분</b></td>
<td><b>일반 RDB (MySQL, PostgreSQL 등)</b></td>
<td><b>벡터 DB (Pinecone, Milvus 등)</b></td>
</tr>
</tbody>
<tbody>
<tr>
<td><span><b>검색 방식</b></span></td>
<td><span><b>Exact Match</b> (정확한 일치)</span></td>
<td><span><b>Similarity Search</b> (의미적 유사도)</span></td>
</tr>
<tr>
<td><span><b>핵심 로직</b></span></td>
<td><span>"이 데이터가 존재해? (Binary: 0 or 1)"</span></td>
<td><span>"이거랑 얼마나 비슷해? (Probability: 유사도 %)"</span></td>
</tr>
<tr>
<td><span><b>인덱싱</b></span></td>
<td><span>B-Tree, Hash Index</span></td>
<td><span>ANN Index (HNSW, IVF 등)</span></td>
</tr>
<tr>
<td><span><b>한계</b></span></td>
<td><span>1,536차원 같은 고차원 데이터를 LIKE나 Full Scan으로 처리 시 서버 과부하 발생</span></td>
<td><span>고차원 공간에서의 '거리 계산'에 최적화되어 초고속 검색 가능</span></td>
</tr>
</tbody>
</table>
<h3>2. RAG 파이프라인 엔지니어링</h3>
<p>RAG는 단순히 DB를 뒤지는 게 아니라 전/후처리가 포함된 시스템 아키텍처</p>
<ul>
<li><b>Pre-processing (프리 프로세싱):</b>
<ul>
<li>사용자의 모호한 질문을 검색 시스템이 이해하기 좋게 다듬는 과정 (Query Rewriting)..&nbsp;</li>
<li>마치 백엔드의 Security Filter나 Interceptor와 역할. 보안 엔지니어랑&nbsp;</li>
<li><b>Moderation (보안 필터링):</b> AI가 생성한 답변이 사용자에게 나가기 직전에 "이 답변에 개인정보가 포함됐나?", "공격적인 언어가 있나?"를 체크. 부적절하면 즉시 차단하거나 Error Response를 내보내는 실시간 방화벽 역할</li>
<li><b>RAI (Responsible AI - 윤리):</b> AI가 특정 집단에 편향된 답변을 하지 않는지, 기업의 윤리 가이드라인을 벗어나지 않는지 검수</li>
</ul>
</li>
<li><b>Retrieval (검색):</b> <b>Ranking:</b> 유사도 점수순으로 정렬.
<ul>
<li><b>Cutoff (Top-K / Threshold):</b> 답변 근거로 쓸 데이터의 개수나 최소 점수 기준을 정해 자르는 작업.</li>
</ul>
</li>
<li><b>Post-processing (포스트 프로세싱):</b>
<ul>
<li><b>Reranking:</b> 검색 결과를 다시 한번 정교하게 재정렬.</li>
<li><b>Moderation &amp; RAI:</b> 답변의 욕설, 위험성, 윤리적 편향성을 검사하는 보안 필터링.</li>
</ul>
</li>
</ul>
<h3>3. 품질 검증 및 모니터링: Ragas</h3>
<p>AI 시스템은 결과가 매번 달라지므로 Unit Test와 같은 객관적 지표가 필수.</p>
<ul>
<li><b>Faithfulness (충실도):</b> 답변이 주어진 근거 문서(Context)에만 기반했는가? (지어내지 않았나?)</li>
<li><b>Answer Relevancy (관련성):</b> 질문 의도에 딱 맞는 답변인가?</li>
<li><b>Context Precision &amp; Recall:</b> 검색해 온 문서들이 정말 질문과 관련 있고 필요한 내용을 다 포함하고 있는가?</li>
<li><b>Answer Correctness:</b> 최종 답변이 실제 정답과 얼마나 일치하는가?</li>
</ul>
<p>내가 이해한 바로는 Regas가 AI 가 거짓말을 하지 않는 감사 시스템이라 생각했는데, 이것도.. 요즘 AI가 거짓말(?)을 하는 이유였나.. 이것이! 더 공부해보고 싶은 시간들이다.</p>
<p>&nbsp;</p>
<hr contenteditable="false" />
<p>"데이터가 존재하느냐"를 묻던 RDB의 세계에서 "얼마나 비슷하느냐"를 계산하는 벡터 DB의 세계로 넘어온 기분이다. 특히 Ragas를 통해 AI의 정직함을 수치화하는 과정은 마치 복잡한 버그를 잡아낼 때와 같은 짜릿함을 주었다. 어서 남은 것도 빨리 마무리해야지비 무제한 강의권이 끝나가는 시점, 진행하던 토이 프로젝트(티켓팅 시스템)를 마무리하며 평소 관심 있던 RAG(Retrieval-Augmented Generation)를 제대로 파보았다. 단순히 AI 모델을 호출하는 것을 넘어, 데이터 인프라를 설계하고 검증하는 과정이 백엔드 엔지니어링과 닮아 있어 흥미로운 공부였다.</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>1. 데이터 인프라: 의미를 숫자로 저장하기</p>
<p>Chunking (청킹): 방대한 문서를 AI가 소화하기 좋은 크기로 쪼개는 작업.</p>
<p>Embedding (임베딩): 텍스트를 고차원 공간의 좌표(Vector)로 변환. 단순 키워드가 아닌 '의미적 유사도'를 계산하기 위함.</p>
<p>OpenAI Embedding: 시장 표준으로 쓰이는 고성능 임베딩 전용 모델 서비스.</p>
<p>Vector DB: 좌표값들을 저장하고, 질문과 가장 가까운 데이터를 찾는 전용 저장소.</p>
<p>ANN (Approximate Nearest Neighbor): 수백만 개의 데이터 중 가장 비슷한 것을 초고속으로 찾아내는 인덱싱 알고리즘.</p>
<p>RDB vs Vector DB: '똑같은 글자(Exact Match)'를 찾는가, '비슷한 의미(Similarity Search)'를 찾는가의 차이.</p>
<p>결론: 일반 DB가 데이터의 정합성을 지키는 데 목숨을 건다면, 벡터 DB는 사용자의 의도(Intent)를 찾는 데 목숨을 건다. 쇼핑몰에서 '빨간 옷'을 검색했을 때 '진홍색 원피스'를 보여줄 수 있는 힘이 여기서 나온다.</p>
<p>&nbsp;</p>
<p>이 부분이 공부할 때 제일 흥미로웠다. 어떻게 유사한 데이터를 보낼 수 있는지, Vector DB에 대해 더 공부하고 적용해보고 싶다.</p>
<p>&nbsp;</p>
<p>구분 일반 RDB (MySQL, PostgreSQL 등) 벡터 DB (Pinecone, Milvus 등)</p>
<p>검색 방식 Exact Match (정확한 일치) Similarity Search (의미적 유사도)</p>
<p>핵심 로직 "이 데이터가 존재해? (Binary: 0 or 1)" "이거랑 얼마나 비슷해? (Probability: 유사도 %)"</p>
<p>인덱싱 B-Tree, Hash Index ANN Index (HNSW, IVF 등)</p>
<p>한계 1,536차원 같은 고차원 데이터를 LIKE나 Full Scan으로 처리 시 서버 과부하 발생 고차원 공간에서의 '거리 계산'에 최적화되어 초고속 검색 가능</p>
<p>2. RAG 파이프라인 엔지니어링</p>
<p>RAG는 단순히 DB를 뒤지는 게 아니라 전/후처리가 포함된 시스템 아키텍처</p>
<p>&nbsp;</p>
<p>Pre-processing (프리 프로세싱):</p>
<p>사용자의 모호한 질문을 검색 시스템이 이해하기 좋게 다듬는 과정 (Query Rewriting)..&nbsp;</p>
<p>마치 백엔드의 Security Filter나 Interceptor와 역할. 보안 엔지니어랑&nbsp;</p>
<p>Moderation (보안 필터링): AI가 생성한 답변이 사용자에게 나가기 직전에 "이 답변에 개인정보가 포함됐나?", "공격적인 언어가 있나?"를 체크. 부적절하면 즉시 차단하거나 Error Response를 내보내는 실시간 방화벽 역할</p>
<p>RAI (Responsible AI - 윤리): AI가 특정 집단에 편향된 답변을 하지 않는지, 기업의 윤리 가이드라인을 벗어나지 않는지 검수</p>
<p>Retrieval (검색): Ranking: 유사도 점수순으로 정렬.</p>
<p>Cutoff (Top-K / Threshold): 답변 근거로 쓸 데이터의 개수나 최소 점수 기준을 정해 자르는 작업.</p>
<p>Post-processing (포스트 프로세싱):</p>
<p>Reranking: 검색 결과를 다시 한번 정교하게 재정렬.</p>
<p>Moderation &amp; RAI: 답변의 욕설, 위험성, 윤리적 편향성을 검사하는 보안 필터링.</p>
<p>3. 품질 검증 및 모니터링: Ragas</p>
<p>AI 시스템은 결과가 매번 달라지므로 Unit Test와 같은 객관적 지표가 필수.</p>
<p>&nbsp;</p>
<p>Faithfulness (충실도): 답변이 주어진 근거 문서(Context)에만 기반했는가? (지어내지 않았나?)</p>
<p>Answer Relevancy (관련성): 질문 의도에 딱 맞는 답변인가?</p>
<p>Context Precision &amp; Recall: 검색해 온 문서들이 정말 질문과 관련 있고 필요한 내용을 다 포함하고 있는가?</p>
<p>Answer Correctness: 최종 답변이 실제 정답과 얼마나 일치하는가?</p>
<p>내가 이해한 바로는 Regas가 AI 가 거짓말을 하지 않는 감사 시스템이라 생각했는데, 이것도.. 요즘 AI가 거짓말(?)을 하는 이유였나.. 이것이! 더 공부해보고 싶은 시간들이다.</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p>"데이터가 존재하느냐"를 묻던 RDB의 세계에서 "얼마나 비슷하느냐"를 계산하는 벡터 DB의 세계로 넘어온 기분이다. 특히 Ragas를 통해 AI의 정직함을 수치화하는 과정은 마치 복잡한 버그를 잡아낼 때와 같은 짜릿함을 주었다. 어서 남은 것도 빨리 마무리해야지</p>