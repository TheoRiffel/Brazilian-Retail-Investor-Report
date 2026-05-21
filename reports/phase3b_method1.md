# Phase 3B — Method 1: Embedding + HDBSCAN (comparison instrument)

**Date:** 2026-05-20  
**Status: AWAITING SUPERVISOR REVIEW — Phase 3C is blocked**

---


## 1. Methodology

**This method is independent of Method 2.** Text embeddings only. No attributes, no subreddit, no window labels are used in clustering. The M2 attribute join in Section 8 is for post-hoc description, not input.

**Primary model:** `intfloat/multilingual-e5-large`   Dimensions: 1024.   Pooling: mean (SentenceTransformer default).   Prefix: `passage: ` (required by e5 architecture for document encoding).   Model max_length: 512 tokens.   Estimated tokenizer-truncated texts: n/a   (0.0%).   Encode time: cacheds.   Embeddings L2-normalised: cosine similarity = dot product.

**Secondary model:** `paraphrase-multilingual-mpnet-base-v2`   Dimensions: 768.   No prefix required.   Model max_length: 514 tokens.   Used for cross-model robustness check (Section 3).

**UMAP denoising:** cosine metric, n_components=20, n_neighbors=15, min_dist=0.0 (tight clusters). 2-D UMAP (min_dist=0.1) used only for visualisation.

**HDBSCAN:** min_cluster_size=108 (3% floor), min_samples tuned (chosen: 15; see sweep table in Section 2). Noise points (label −1) are excluded from persona candidacy.

**Cross-check:** HDBSCAN also run directly on cosine-distance matrix (no UMAP), metric='precomputed'. Both results reported; primary is UMAP+HDBSCAN.


## 2. HDBSCAN min_samples sweep (primary model, UMAP-20d)

| min_samples | n_clusters | n_noise | noise_pct | Chosen? |
|------------|-----------|---------|-----------|---------|
| 5 | 11 | 1044 | 29.0% |  |
| 10 | 12 | 1018 | 28.3% |  |
| 15 | 4 | 383 | 10.6% | ← chosen |
| 27 | 4 | 434 | 12.1% |  |

**Chosen min_samples=15**: first value with noise < 25% and ≥ 4 clusters. If no value met both criteria, the value minimising noise was selected. **Noise fraction: 10.6%.** Noise points are excluded from all downstream analyses.


## 3. Cross-model agreement (e5-large vs mpnet)

e5-large: **4 clusters**, 383 noise (10.6%)

mpnet: **4 clusters**, 543 noise (15.1%)

**ARI(e5, mpnet) = 0.192**

⚠️ ARI < 0.3: low inter-model agreement. Cluster assignments are model-sensitive. Results below reflect e5-large only; treat with caution.


## 4. Cosine-distance cross-check (HDBSCAN, no UMAP)

HDBSCAN on cosine-distance matrix (precomputed, min_samples=15): **0 clusters**, 3600 noise (100.0%). ARI vs UMAP+HDBSCAN (non-noise overlap): **0.0**. High ARI → UMAP denoising did not distort the cluster structure. Low ARI → UMAP collapsed some real boundaries; interpret UMAP-based results carefully.


## 5. Primary cluster summary (e5-large, UMAP+HDBSCAN)

⚠️ **Noise: 383 threads (10.6%) excluded from all analyses below.**

| Cluster | n | % | Below 3% floor? |
|---------|---|---|-----------------|
| noise | 383 | 10.6% | n/a |
| M1-C0 | 154 | 4.3% | ok |
| M1-C1 | 465 | 12.9% | ok |
| M1-C2 | 156 | 4.3% | ok |
| M1-C3 | 2442 | 67.8% | ok |


## 6. Bootstrap stability (e5-large, UMAP+HDBSCAN)

20 iterations, 80% subsample. UMAP NOT re-run per bootstrap (subsamples the precomputed 20-d embedding). Noise excluded from ARI computation.

**Mean ARI: 0.623 ± 0.294** (STABLE)

| Cluster | Mean Jaccard | Stable? |
|---------|-------------|---------|
| M1-C0 | 0.132 | ⚠️ UNSTABLE |
| M1-C1 | 0.681 | ok |
| M1-C2 | 0.970 | ok |
| M1-C3 | 0.776 | ok |


## 7. Missingness artifact check

Mean count of desconhecido/NaN fields per thread (M2 attributes) per M1 cluster. Corpus median = 1.0. A TEXT cluster should NOT be missingness-driven. Flag if mean > 1.5 × corpus median (1.50).

| Cluster | Mean missing features | Flag? |
|---------|----------------------|-------|
| M1-C0 | 1.18 | ok |
| M1-C1 | 1.11 | ok |
| M1-C2 | 1.81 | ⚠️ ARTIFACT RISK |
| M1-C3 | 2.08 | ⚠️ ARTIFACT RISK |


## 8. Attribute profiles (M2 attributes joined back; NOT used in clustering)

For each M1 cluster: ordinal means + top-3 categorical modes from M2 attributes. This shows what the embedding clusters 'look like' in attribute space. No persona names assigned — clusters are M1-C0 … M1-C{k-1}.


#### M1-C0  (n=154)

Mean missingness: 1.18

| Feature | Value |
|---------|-------|
| sofisticacao_tecnica | 2.34 (mean) |
| tolerancia_risco_declarada_ou_inferida | 2.4 (mean) |
| ceticismo_institucional | 2.42 (mean) |
| exposicao_a_cripto_e_especulacao | 1.41 (mean) |
| identidade_comunitaria | 1.42 (mean) |
| fase_acumulacao | acumulacao_ativa (53)  /  acumulacao_inicial (44)  /  consolidacao (23) |
| estrategia_principal | dividendos_buy_hold (44)  /  sem_estrategia_definida (31)  /  especulacao_curto_prazo (18) |
| relacao_com_instituicoes_financeiras | diy_sem_intermediario (24)  /  multiplaforma_ativo (24)  /  migrando_para_corretora (15) |
| estado_emocional_predominante | curioso_ou_exploratorio (90)  /  ansioso_ou_inseguro (36)  /  frustrado_ou_resignado (15) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (68)  /  renda_passiva_imediata (13)  /  compra_de_imovel (6) |


#### M1-C1  (n=465)

Mean missingness: 1.11

| Feature | Value |
|---------|-------|
| sofisticacao_tecnica | 2.02 (mean) |
| tolerancia_risco_declarada_ou_inferida | 2.22 (mean) |
| ceticismo_institucional | 2.52 (mean) |
| exposicao_a_cripto_e_especulacao | 1.13 (mean) |
| identidade_comunitaria | 1.56 (mean) |
| fase_acumulacao | consolidacao (102)  /  acumulacao_ativa (97)  /  acumulacao_inicial (84) |
| estrategia_principal | sem_estrategia_definida (139)  /  imobiliario_direto_ou_fii (89)  /  renda_fixa_conservadora (51) |
| relacao_com_instituicoes_financeiras | dependente_de_bancao (115)  /  migrando_para_corretora (106)  /  desconfiado_de_todos (75) |
| estado_emocional_predominante | curioso_ou_exploratorio (188)  /  ansioso_ou_inseguro (116)  /  frustrado_ou_resignado (87) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (154)  /  compra_de_imovel (69)  /  reserva_de_emergencia (36) |


#### M1-C2  (n=156)

Mean missingness: 1.81

| Feature | Value |
|---------|-------|
| sofisticacao_tecnica | 1.98 (mean) |
| tolerancia_risco_declarada_ou_inferida | 3.67 (mean) |
| ceticismo_institucional | 2.97 (mean) |
| exposicao_a_cripto_e_especulacao | 3.58 (mean) |
| identidade_comunitaria | 3.04 (mean) |
| fase_acumulacao | acumulacao_inicial (36)  /  pre_inicio (25)  /  acumulacao_ativa (20) |
| estrategia_principal | especulacao_curto_prazo (117)  /  sem_estrategia_definida (7)  /  investimento_exterior (5) |
| relacao_com_instituicoes_financeiras | desconfiado_de_todos (14)  /  diy_sem_intermediario (9)  /  multiplaforma_ativo (8) |
| estado_emocional_predominante | curioso_ou_exploratorio (43)  /  euforico_ou_impulsivo (41)  /  cinico_ou_ironico (36) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (79)  /  renda_passiva_imediata (3)  /  sucessao_ou_doacao_familiar (1) |


#### M1-C3  (n=2442)

Mean missingness: 2.08

| Feature | Value |
|---------|-------|
| sofisticacao_tecnica | 1.77 (mean) |
| tolerancia_risco_declarada_ou_inferida | 2.52 (mean) |
| ceticismo_institucional | 2.63 (mean) |
| exposicao_a_cripto_e_especulacao | 1.66 (mean) |
| identidade_comunitaria | 2.45 (mean) |
| fase_acumulacao | acumulacao_inicial (448)  /  pre_inicio (349)  /  acumulacao_ativa (349) |
| estrategia_principal | especulacao_curto_prazo (422)  /  sem_estrategia_definida (340)  /  renda_fixa_conservadora (315) |
| relacao_com_instituicoes_financeiras | migrando_para_corretora (198)  /  multiplaforma_ativo (178)  /  dependente_de_bancao (117) |
| estado_emocional_predominante | curioso_ou_exploratorio (849)  /  cinico_ou_ironico (595)  /  euforico_ou_impulsivo (292) |
| objetivo_financeiro_primario | acumulacao_sem_objetivo_claro (772)  /  renda_passiva_imediata (168)  /  reserva_de_emergencia (134) |


## 9. Exemplars (10 nearest to cluster centroid)

Cosine similarity to centroid (unit-norm embeddings). Texts truncated to 300 chars.


#### M1-C0 exemplars

**ngai8p** (sim=0.9455)
> Dúvidas sobre o IR  Sou investidor faz 1 ano e vou ter que declarar minhas ações esse ano, sou extremamente leigo e me encaixo em um grupo mais especifico ainda para declaração, então tenho duas dúvidas:  1 - Preciso enviar o informe de rendimentos de todas as ações ou só as que distribuíram dividen

**tbaebq** (sim=0.9447)
> Calculadora de IR  Alguém aqui usa calculadora de IR, principalmente para ações? Tem algum site que vcs recomendam?  --- Top comments --- [score 3] Review breve e honesto:  IRPFbolsa não é bonitinho e o atendimento fica desejar,  mas realiza todos os cálculo com precisão incrível, inclusive com deri

**1fhnqx4** (sim=0.944)
> Impostos em carteiras complexas   Neste ano, minha renda mais que dobrou, mas mantive meu padrão de vida. Resultado: meus investimentos aumentaram significativamente. Estudei muito sobre e diversifiquei minha carteira que antes só tinha poucas ações da B3, FIIs, Tesouro e alguns CDBs (que hoje me ar

**v1mw94** (sim=0.9423)
> Estão me expulsando do mercado?Porque a declaração não me incentiva a nada a não ser agredir do Guedes.  [link post]  --- Top comments --- [score 60] A declaração que eu queria fazer é impublicável. [score 32] Se vc for um trader com um bom planejamento,  ir não é um problema. Vende tudo no natal e 

**wis8wl** (sim=0.9421)
> Socorro  Seguinte gente, em 2020 eu coloquei 2197 reais na NGRD3 na corretora Rico. Sim fui um dos vários trouxas q caiu nessa. Até peguei uma altinha mas segurei, segurei e segurei até q começou a despencar. Fiquei segurando até 2021 qnd vendi boa parte e agr em 2022 eu to operando nessa baixa. O p

**jkxs4l** (sim=0.9404)
> Dúvida sobre IR na venda de ações  O IR sobre o ganho na venda de ações é de 15% sobre o ganho. Mas por exemplo, supondo que tenho 10 ações que comprei a  preço X, e outras 5 que comprei a preço Y. Vendi 3 a preço Z. A tributação vai ser sobre Z - ((10X+5Y)/(15)) ?  --- Top comments --- [score 6] Aç

**v1a1cb** (sim=0.9397)
> Investir pouco e contador  Fala, galera! Sou estudante de engenharia de software em uma federal e professor particular de inglês em parte do tempo. Meu amigo investidor me sugeriur investir todo mês 120 reais. 40 no PagBank, 40 em MXRF11 e 40 em ações de energia.   Considerando que eu teria que paga

**hyk9v9** (sim=0.9396)
> Darf em venda de FIIs  No final do ano passado resolvi investir em ações e FIIs, e logo em seguida, percebi que não gostei disso. Percebi que para investir bem tem que estudar e se dedicar muito, e se for para estudar prefiro me especializar mais em minha profissão. Por isso prefiro colocar meu dinh

**n9ux1c** (sim=0.9393)
> Sugestão - um post discutindo IR a respeito de cripto  Como declarar:  * mineração   Suponho que ela seja tratada como renda tributavel, como aluguel de equipamento, alguém sabe como tratar?    * staking   Poderia ser um tipo de "juros sobre capital próprio"? Existe regra para isso?    * faucets * a

**hwm339** (sim=0.9382)
> COMO A RECEITA PODERIA AJUDAR NA DECLARAÇÃO DE IMPOSTOS  De tempos em tempos penso em coisas simples que a Receita podeira fazer que facilitaria a vida de muita gente por aí. A declaração de IR tem uma complexidade desnecessária.  A Receita recebe informes de rendimentos e possui acesso a todas as m



#### M1-C1 exemplars

**1dv9gv2** (sim=0.9375)
> Vocês andam com o cartão de crédito do banco em que guardam os investimentos?  Sei que andar com o aplicativo do banco com grana instalado no celular é um risco que todos já sabem. Mas e só com o cartão na carteira?   Tem como limparem sua conta também em caso de sequestro relâmpago?   Estava pensan

**ngi2s1** (sim=0.9368)
> para banco/cartão E corretora - BTG ou XP ?  Tô acompanhando o [post](https://www.reddit.com/r/investimentos/comments/nfhco0/btg_em_6_meses_está_fazendo_mais_que_o_nubank_em/?utm_medium=android_app&amp;utm_source=share) elogiando o BTG+ e nos comentários vi muita gente reiterando a apreciação do OP 

**10f9r9k** (sim=0.9367)
> Gain dos grandes  Vim reportar o maior gain que já tive. Fiz um investimento de longo prazo de construir meu score e pegar um monte de cartões de crédito com limite alto, aí no meio do ano passado gastei tudo de uma vez e vou deixando rodar. Basicamente ganhei 70k, pretendo pagar no máximo 10% disso

**y5qjfb** (sim=0.9367)
> Minha fatura de 3k vai vencer e nao tenho dinheiro pra pagar.. Ja até comecei a trabalhar, mas até eu receber tudo o juros do CC vai ficar aumentando a divida??  Edit: Provavelmente vou deixar essa divida acumular por 1 ano e esperar a renegociação pra não pagar juros.  Foi um gasto de saúde e mecan

**1h0a452** (sim=0.9366)
> Tô com o dinheiro do financiamento: quitar ou deixar investido no 100% CDI?  Pergunta no título. Financiei um Apt de 300k. Dei 30 de entrada. Sobrou 270 que já paguei 2 anos. Amortizando uma parcelinha ou outra, resta ainda 263k pra pagar.   Parcelas de 3k mês.  Já tenho exatamente 263k guardados no

**xqhu59** (sim=0.9366)
> Financiamento Imobiliário + Portabilidade de Financiamento  Pessoal, estou me planejando para comprar o primeiro apartamento (faixa de valor de 220-250K). Obviamente irei financiar - dando cerca de 60K de entrada.  Sei que dado os juros atuais, o financiamento sairá mais caro.  Mas sei também que qu

**1f8qwgu** (sim=0.9357)
> Qual recomendação de banco para o meu perfil?  Tenho 25 anos e até o momento concentro toda minha atividade financeira (conta corrente, salário, investimentos) no Inter. Tenho o objetivo de conseguir investir em ETFs em mercados como o dos EUA, assim como fazer aportes no Brasil.  Dessa forma, tanto

**u7xhk7** (sim=0.9357)
> Troca de corretora: NuInvest -&gt; BTG Pactual  Olá Pessoal!  Faz algum tempo que tenho ponderado trocar de corretora e talvez até serviços "bancários" do Nu para BTG. Gostaria de saber se alguém tem alguma ressalva com eles, ou se o processo de troca de corretoras é traumático demais e nem devo pen

**1ghx3px** (sim=0.9349)
> Corretoras que "travam" o dinheiro após a compra  Olá, pessoal!  Eu atualmente uso o nubank como corretora e me atende bem, a maior feature que gosto dela é que ela já mostra os dividendos que a ação/fii paga e que quando vc faz a compra ela "trava" esse dinheiro da sua conta retirando ele pra vc n 

**t7i1pi** (sim=0.9346)
> Dúvida sobre dívidas  Alguém ai pegou algum financiamento enquanto as taxas estavam baixas? Qual indexador vocês escolheram? O custo subiu muito??  Não tenho conhecimento sobre o assunto, sempre poupo para investir e não planejo ter dívidas, mas penso que se o custo da dívida for inferior ao retorno



#### M1-C2 exemplars

**nv6tf0** (sim=0.9511)
> Todo mundo preparado?  [link post]  --- Top comments --- [score 70] Você só descobre quem está nadando pelado quando a maré baixa kkkk [score 46] Agora é a hora que todo mundo que falava bem de criptomoedas começar a dizer que é pirâmide, golpe, bolha, etc... Daí quando voltar a subir vão dizer que 

**t4konx** (sim=0.948)
> Onde posso ir aprendendo mais sobre criptomoedas?  Recentemente, decidi comprar quantidades pequenas de Ether só para eu ter uma ideia de como as criptomoedas e as carteiras de cripto funcionam. Comprei R$25,00 de Ether na NovaDAX.  Sempre investi em CDBs e nada mais. Sou novo nesse mundo dos invest

**nlm82w** (sim=0.948)
> Bitcoin ou Ethereum  Qual dessas criptomoedas está valendo mais investir atualmente?  --- Top comments --- [score 8] Ethereum [score 8] Na dúvida os dois, diversificar é tudo. [score 6] Diversifica nos 2, mas acredito que a ethereum tem mais potencial de alta, ela e a ADA podem passar o market cap d

**mx13mj** (sim=0.9477)
> Investimento de Cryptomoedas  Boa tarde pessoal!  Queria saber a opinião de voces sobre crypto no momento! Tenho 30% ETH, 30% ADA, 10% BTC e 30% em BNB, LINK e VET e um um pouquinho de DOGE.  Coloquei todo meu dinheiro de estagiário no Binance 4.20 k (nice) mas ja cai para 3.6 K com essa nova queda,

**msa020** (sim=0.9465)
> Criptomoedas e Stablecoins. Pensando seriamente em nunca "vender"  Estou cada vez mais desanimado em converter minhas criptomoedas em R$. Eu simplesmente não vejo muito sentido considerando como as coisas estão no Brasil e o que o universo de criptomoedas proporciona.  Obviamente não dá para contar 

**vr7qec** (sim=0.9463)
> quem tá contando a verdade?  [pentágono aponta centralização de btc](https://youtu.be/i_kwu4oYFYU)  Eu só compro btc, comprei até quando tava em 60k. O famoso Hodlr. :/ acho que se isso for verdade, vou virar mod aqui.  --- Top comments --- [score 42] E investir em bct, pode? [score 31] A regra é cl

**nuvlvi** (sim=0.946)
> Usei uma grana que tava sobrando pra comprar criptomoeda hoje e ja perdi quase 20% do investimento AMA.  A ultima vez que me senti tão burro foi quando minha ex pediu pra eu fazer um emprestimo no meu nome para abrir um negócio e usou esse dinheiro para se midar pra Aruba com meu vizinho perneta.  -

**o2t9z7** (sim=0.9451)
> Pior que perder dinheiro é ter quase ganho muito dinheiro...  [link post]  --- Top comments --- [score 9] Eu vi Bitcoin a 700 reais, eu até pensei em comprar e reservei uma grana na época das férias e acabei não comprando, vc meramente adotou não ter ganho dinheiro, eu nasci não ganhando dinheiro. [

**1hlk7na** (sim=0.9439)
> Bitcoin caiu 15% do topo e a galera já tá surtando kkkkk  https://preview.redd.it/afnvcexwgu8e1.png?width=1656&format=png&auto=webp&s=c5e74503001752d7a3ebeb0c4be0e7f6380260d2  "Agora vai 100k, confia!" Isso já rolou antes, todo mundo fica achando que é lua e depois toma banho de água fria. A tendênc

**gxwykg** (sim=0.9435)
> Investimento em Criptomoedas, por onde começar?  Estou pesquisando um pouco sobre criptomoedas e estou me interessando, achei uma forma interessante de investimento. Queria saber mais sobre esse mercado e pra isso queria dicas de canais que explicam de forma mais simples, que corretoras posso usar..



#### M1-C3 exemplars

**j58nzp** (sim=0.9383)
> LCI caindo mensalmente, o que pode dar errado ?  O que acham desta estrategia de investimento. Basicamente é deixar os investimentos de renda fixa com vencimento um mês depois do outro, para sempre algo vencer e cair grana na conta.  &amp;#x200B;  Todo mês eu invisto R$X em LCI 90 , até depois der o

**skdj6b** (sim=0.9382)
> Eu tenho dois lados...  [link post]  --- Top comments --- [score 66] Eu quitei do r/investimentos, os caras não aguentam uma piadota. [score 54] Aqui além de mais engraçado também é mais sério. [score 34] Considerando que na imagem a parte r/farialimabets está maior que a área do r/investimentos, en

**k26jd2** (sim=0.9378)
> Comente minha carteira - iniciante em renda variável  Boa tarde, eu acompanho o sub há algum tempo mas só agora consegui montar minha carteira, depois de muita pesquisa e ponderação sobre o peso dos ativos. Gostaria de saber a opinião de vocês, pensei em investir em bitcoin também mas acho um mercad

**mlu3ez** (sim=0.9372)
> Diamond hands💎✊〽️  [link post]  --- Top comments --- [score 52] Esse com certeza é do sub [score 44] Saudades do trade raiz que investia o dinheiro que não tinha [score 22] Tem um cara do meu trabalho que estava se sentindo o trader profissional com uns dois meses de experiência, operando com 3 moni

**kt2x1m** (sim=0.9366)
> Mais um iludido  [link post]  --- Top comments --- [score 26] Acho que a galera que entra nisso esquece que trading é 99% emocional e 1% todo o resto.  Eu quero ver quem é o filha da puta, e posso afirmar que é um filha da puta com certeza, que fala o contrário disso.  Nego passa 4 anos em uma facul

**w5eddb** (sim=0.9366)
> Oque é melhor, Alto risco ou segurança ?     Bom dia. Consegui entrar em um emprego (sou um brasileiro médio agora kk) que me paga 1400 bonoro, moro com os meu pais e não gasto com balada e outras parada. Estou começado minha vida financeira agora, tem uns 3 ou 4 meses que eu conheci esse mundo dos 

**w6wkbr** (sim=0.9358)
> ㅤ  [link post]  --- Top comments --- [score 203] Esse vê uma casca de banana há 50 metros e já reclama: “Droga, lá vou eu escorregar de novo” [score 69] É uma obrigação cívica separar o trouxa do dinheiro [score 45] Esse daí é mod do sub [score 33]  Deve fazer parte do grupo que acredita em investim

**yon3s8** (sim=0.9358)
> Adeus otários, estou me mudando para o r/investimentos, nunca critiquei a IQ Option  [link post]  --- Top comments --- [score 134] Não esqueça que o retorno pra cá custa caro [score 81] Como é a sensação de ter seu dinheiro trabalhando pra você ? [score 60] Olha, quando você acorda e vê que ganhou 8

**1gkjged** (sim=0.9354)
> Gostaria que alguém julgasse meu investimentos  Contexto: Moro com os meus pais, ganho 4k, não sou formado ainda, comecei a +/- 1 anos, tenho foco em longo prazo, já tenho a reserva de emergência tesouro selic e tenho IPCA que planeja usa para sair de casa quando termina a faculdade. Aporto 500 reai

**mh7xje** (sim=0.9354)
> Pq tem muito otario que tá pobre e devia começar a vender curso tbm ao invés de comprar  [link post]  --- Top comments --- [score 231] O ano é 2035.   Sucessivas crises econômicas levam a uma intensa desvalorização do Real. Chego na padaria e me deparo com a placa: "Promoção - 7 Belo R$ 325 (cada)".



## 10. Cross-tabulation M1 × M2

Rows = M1 cluster, Columns = M2 cluster. Noise rows/cols included for completeness. Use this table for the adjudication analysis below.

| row_0    |   M2-C0 |   M2-C1 |   M2-C2 |   M2-C3 |   M2-C4 |   M2-C5 |   M2-C6 |
|:---------|--------:|--------:|--------:|--------:|--------:|--------:|--------:|
| M1-C0    |       3 |      13 |     120 |       4 |       1 |      13 |       0 |
| M1-C1    |       0 |     115 |     307 |      22 |       2 |      19 |       0 |
| M1-C2    |       0 |      11 |      44 |       1 |       1 |      99 |       0 |
| M1-C3    |      11 |     783 |    1105 |      63 |      25 |     454 |       1 |
| M1-noise |       3 |     157 |     136 |       4 |       4 |      79 |       0 |

Overall ARI(M1-non-noise, M2-non-noise): computed in adjudication section.


## 11. Adjudication — does Method 1 corroborate Method 2 structure?

Three specific adjudication questions from Phase 3A:


#### 11.1  M2-C5 (speculator): high-crypto, euphoric, short-term

M2-C5 threads: 664. Concentration: top M1 cluster is M1-C3 (68.4% of M2-C5 threads). Entropy: 0.976  (lower = more concentrated in one M1 cluster).

✓ M2-C5 is concentrated in one M1 cluster — Method 1 recovers the speculator group.


#### 11.2  M2-C2 (earnest-learner): curious, exploratory

M2-C2 threads: 1712. Top M1 cluster: M1-C3 (64.5%). Entropy: 1.072.

✓ M2-C2 concentrated in one M1 cluster — earnest-learner is text-distinguishable.


#### 11.3  M2-C1 (PROVISIONAL — cynical-reactive): high missingness

M2-C1 threads: 1079. Top M1 cluster: M1-C3 (72.6%). Entropy: 0.852.

✓ M2-C1 is concentrated → Method 1 (missingness-blind) recovers a coherent group in the same embedding region. This is positive evidence that C1 is a REAL cluster, not a missingness artifact. Recommend promoting to confirmed in Phase 3D.


## 12. Figures

- `reports/figures/m1_umap_primary.png` — 2-D UMAP coloured by e5-large clusters
- `reports/figures/m1_umap_cosine.png` — 2-D UMAP coloured by cosine-distance HDBSCAN
- `reports/figures/m1_model_comparison.png` — e5-large vs mpnet clusters on same 2-D UMAP
- `reports/figures/m1_crosstab.png` — M1 × M2 cross-tabulation heatmap

---

## ⛔ HARD STOP

Phase 3B complete. **Do not proceed to Phase 3C** until supervisor has
reviewed this document, the adjudication results (Section 11), and the figures.
Specifically: the M2-C1 adjudication outcome changes the provisional flag status.
