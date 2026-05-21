# Phase 3C — Method 3: LLM-Hierarchical Clustering (k=4 finalized)

**Date:** 2026-05-21  
**Status: SUPERVISOR-APPROVED. k=4 locked. Phase 3D unblocked.**

**Approval notes (2026-05-21):**
- Section 6 non-financial-content rate **ran and is clean**: all four clusters well below the 40% artifact threshold (max M3-C1 = 4.1%; M3-C3 = 3.7%). No corpus-artifact cluster.
- M2-C1 verdict: **corroborated as a real cynical-reactive posture**, but **soft-edged**. Methods 2 and 3 independently recover the posture (M2-C1 is 2.0× / 1.91× overrepresented in M3-C3 and M3-C1 — the two cynical M3 clusters — and underrepresented in the earnest M3-C0). However, Method 3 disperses M2-C1 across cynical sub-flavors rather than producing a single crisp partner cluster. **Carried into Phase 3D as "real posture, fuzzy boundaries" — not promoted to "confirmed crisp cluster".** See `reports/decisions_log.md`.

---


## 1. Methodology

**Method:** k-medoids (PAM) on cosine distance of mpnet embeddings. k=4 selected by supervisor from candidates k=4..7 (interpretability, not silhouette). HDBSCAN+UMAP pipeline abandoned — see reports/decisions_log.md.

**Embedding:** paraphrase-multilingual-mpnet-base-v2, 768-dim, L2-normalised. Concatenation: perfil_em_uma_frase | postura_emocional | sinal_distintivo.

**Usable summaries:** 3586/3600. Parse failures dropped: 14 (0.4% of corpus — see decisions_log.md).

**k-medoids restarts:** 5. Silhouette score (cosine): 0.0785. Low silhouette (~0.05–0.08 range across all k) confirms continuum — no density structure. k selected on interpretability; silhouette used as tie-breaker only.


## 2. Cluster summary

Minimum viable cluster: 108 threads (3% of 3600).

| Cluster | n | % | Below 3% floor? |
|---------|---|---|-----------------|
| M3-C0 | 1333 | 37.0% | ok |
| M3-C1 | 413 | 11.5% | ok |
| M3-C2 | 1188 | 33.0% | ok |
| M3-C3 | 652 | 18.1% | ok |


## 3. Bootstrap stability

**Interpretation:** k-medoids on a continuum yields modest ARI — these are supervisor-interpretability partitions, not density clusters. Low ARI is expected and is reported honestly. ARI=1.0 from the old UMAP run was a topology artifact, NOT a real stability signal.

**Mean ARI: 0.618 ± 0.264** (STABLE ≥0.5)

| Cluster | Mean Jaccard | Stable? |
|---------|-------------|---------|
| M3-C0 | 0.808 | ok ≥0.5 |
| M3-C1 | 0.65 | ok ≥0.5 |
| M3-C2 | 0.657 | ok ≥0.5 |
| M3-C3 | 0.542 | ok ≥0.5 |


## 4. Missingness artifact check

Corpus median missing fields = 1.0. Artifact flag: >1.5.

| Cluster | Mean missing features | Flag? |
|---------|----------------------|-------|
| M3-C0 | 0.99 | ok |
| M3-C1 | 2.83 | ⚠️ ARTIFACT RISK |
| M3-C2 | 2.06 | ⚠️ ARTIFACT RISK |
| M3-C3 | 3.04 | ⚠️ ARTIFACT RISK |


## 5. Cluster exemplars (10 nearest to medoid)

First exemplar in each cluster is the medoid itself. Fields are Haiku-generated summaries — not raw thread text.


#### M3-C0  (n=1333, 37.0%)

**1g6jgt7** (d=-0.0) **[medoid]**
> **Perfil:** Investidor iniciante pragmático que prioriza construção de patrimônio de longo prazo sobre conhecimento técnico, aceitando sua própria limitação de tempo e expertise.  
> **Postura:** Ansiedade contida e racional. Não há desespero, mas há insegurança genuína mascarada por tom descontraído ('verdadeiro leigo'). Busca validação de que está 'fazendo certo' apesar de não entender. Registra coloquial, sem ironia defensiva.  
> **Sinal:** Explicitamente recusa a identidade de 'sábio de finanças' e a coloca como desnecessária para seu objetivo. Diferencia-se por aceitar ignorância como constraint permanente, não como fase transitória — investe apesar de, não para se tornar expert.  
> **Dor:** Incerteza sobre se está desperdiçando potencial de retorno por falta de conhecimento, combinada com falta de tempo/disposição para aprender — conflito entre FOMO intelectual e realismo sobre prioridades.  

**i04lng** (d=0.0861)
> **Perfil:** Investidor iniciante extremamente cauteloso e metódico, buscando construir patrimônio de longo prazo (30 anos) através de renda fixa, mas paralisado pela necessidade de compreender completamente cada mecanismo antes de agir.  
> **Postura:** Respeitosa, humilde, sem ironia — tom genuíno de quem se sente pequeno diante do sistema financeiro. Ansiedade real mascarada por formalidade ('Peço desculpas se for um incômodo'). Receptivo e grato com respostas, indicando insegurança sobre legitimidade de suas dúvidas.  
> **Sinal:** Horizonte de investimento extraordinariamente longo (30 anos) combinado com perfil ultra-conservador — sugere pessoa que planeja aposentadoria ou legado familiar, não especulação; a insistência em 'menor risco de alteração' revela trauma potencial com volatilidade ou experiência anterior negativa.  
> **Dor:** Medo de tomar decisão errada por falta de conhecimento completo — não quer perder dinheiro por ignorância. Confusão sobre qual modalidade realmente protege contra inflação e volatilidade de juros.  

**101x1e6** (d=0.0942)
> **Perfil:** Investidor iniciante, cauteloso e racional, que busca validação externa antes de tomar decisão de alto risco financeiro, mas está genuinamente preso entre oportunidade familiar e insegurança sobre sua capacidade de execução.  
> **Postura:** Ansiedade mascarada por racionalidade. Usa linguagem técnica ('investimento futuro', 'viabilidade') mas o tom revela insegurança profunda ('fico muito inseguro', 'não possuo experiência alguma'). Não há ironia genuína — há genuína dúvida. Busca permissão dos outros para validar o que já deseja emoci  
> **Sinal:** Propõe solução criativa e pragmática (deixar tios morarem enquanto paga, renegociar quando Selic cair) — não é ingênuo, mas também não é agressivo. Diferencia-se por estar disposto a esperar e estruturar, não apenas comprar. Isso sugere mentalidade de longo prazo, não especulativa.  
> **Dor:** Medo de overleverage — renda insuficiente (7 mil/mês para financiar 300+ mil) combinado com falta de entrada e necessidade de reforma. A dor não é falta de dinheiro, mas falta de margem de segurança para respirar durante 20-30 anos de financiamento.  

**ipn9s4** (d=0.0978)
> **Perfil:** Investidor iniciante disciplinado que está construindo sua primeira reserva de emergência com método, mas ainda inseguro sobre onde alocar e se está fazendo certo.  
> **Postura:** Ansiedade contida e respeitosa — tom educado, agradecido, sem ironia. Busca validação mais que confronto. Há urgência subjacente ('sossego financeiro') mascarada por pergunta técnica aparentemente simples. Insegurança sobre decisão já tomada (Nubank) revela falta de confiança própria.  
> **Sinal:** Menciona 'sossego' duas vezes em contextos diferentes — não é sobre ganhar mais, é sobre parar de se preocupar. Isso diferencia de otimizadores de rendimento; é alguém em transição de 'sem colchão' para 'com colchão'.  
> **Dor:** Insegurança sobre segurança do Nubank (apesar de saber que é garantido) — medo latente de perder o dinheiro que custou 8 meses para juntar. Paralisia por análise: quer certeza antes de agir.  

**oan16o** (d=0.1042)
> **Perfil:** Investidor iniciante metódico e autodidata que busca construir carteira diversificada com disciplina, mas ainda está na fase de validar conceitos antes de comprometer capital real.  
> **Postura:** Ansiedade mascarada por metodologia. Tom respeitoso e educado, mas a obsessão por 'direcionamento correto' e a quantidade de dúvidas simultâneas revelam insegurança sobre estar fazendo 'certo'. Humor leve ('heheheh') funciona como amortecedor de tensão. Não há ironia genuína — há seriedade genuína d  
> **Sinal:** Distingue-se por pedir explicitamente 'direcionamento entre dúvidas e fontes' em vez de respostas prontas — sinaliza que quer ser educado, não alimentado. Isso é raro e revela maturidade intelectual, mas também revela que está em busca de um 'mapa' que não existe (cada fonte tem viés). Sua menção es  
> **Dor:** Paralisia por análise: muitas opções, muitas variáveis (liquidez vs. rendimento, IR regressivo, fundos vs. ativos diretos), medo de escolher errado com capital pequeno. A postagem fica incompleta ('Pensei em fazer uma planilha que me aju...') — sugestão de que está sobrecarregado.  

**1ga8vzx** (d=0.1046)
> **Perfil:** Investidor iniciante em situação de transição profissional, cauteloso e buscando validação antes de tomar decisão, sem clareza sobre seus próprios objetivos financeiros.  
> **Postura:** Ansiedade mascarada por pragmatismo. Tom respeitoso e aberto, mas a pergunta repetida ('vale a pena?') revela insegurança. Não há ironia ou cinismo — é genuína dúvida. Busca permissão/validação mais que orientação técnica.  
> **Sinal:** Menciona explicitamente que 'vai precisar usar parte do dinheiro a curto prazo' mas não quantifica — isso sugere que a verdadeira questão não é se investir, mas como separar o que é fundo de emergência do que é investimento. É um problema de alocação, não de decisão binária.  
> **Dor:** Falta de clareza sobre necessidade de liquidez e ausência de planejamento financeiro básico. Não sabe quanto precisa guardar vs. quanto pode investir, o que gera paralisia decisória.  

**wa7bjf** (d=0.1072)
> **Perfil:** Investidor cauteloso com capital significativo que busca otimização tática — quer segurança e rendimento simultâneos, mas está paralisado pela abundância de opções.  
> **Postura:** Pragmática e meticulosa, mas com ansiedade subjacente mascarada por perguntas técnicas. Não é impulsivo — quer 'deixar num canto' e 'ir mexendo aos poucos', sinalizando medo de decisão errada. Tom respeitoso, sem ironia; busca validação de especialistas.  
> **Sinal:** Obsessão com separação de contas ('não deixar atrelada ao saldo corrente') — sugere experiência negativa anterior com débitos automáticos ou falta de disciplina; busca estrutura externa para forçar comportamento.  
> **Dor:** Paralisia por excesso de opções (CDB, LCI, LCA, Tesouro SELIC, poupança) e medo de 'errar' com 400k. Quer liquidez diária mas também quer isenção de IR — demandas parcialmente conflitantes que a deixam confusa.  

**1figi79** (d=0.1073)
> **Perfil:** Investidor iniciante de renda alta recém-conquistada, cauteloso e autodidata, que busca construir patrimônio de forma independente mas carece de confiança técnica.  
> **Postura:** Ansiedade mascarada por pragmatismo. Tom respeitoso e humilde ('perdido', 'nunca imaginei'), não irônico. Há receio genuíno de ser enganado (assessores comissionados), sugerindo insegurança apesar do sucesso financeiro recente. Busca validação e segurança, não aventura.  
> **Sinal:** Menção explícita à esposa como beneficiária/dependente (não apenas 'família') e preocupação com seguro de vida — sugere mentalidade de provedor com dependentes, não apenas acumulador individual. Diferencia-o de investidores focados em retorno puro.  
> **Dor:** Lacuna de conhecimento técnico combinada com medo de cometer erros custosos. A renda alta criou oportunidade mas também responsabilidade que o deixa paralisado.  

**lvagj8** (d=0.1078)
> **Perfil:** Investidor iniciante com disciplina básica (reserva de emergência feita) mas sem clareza estratégica, buscando validação sobre onde estacionar capital ocioso.  
> **Postura:** Pragmática e cautelosa, sem dramaticidade. Tom é de dúvida genuína, não ansiedade mascarada. Busca resposta técnica, não validação emocional. Registra coloquial mas respeitoso.  
> **Sinal:** Menção explícita de 'não tenho objetivo de longo prazo' repetida duas vezes na mesma postagem — essa pessoa está confortável com incerteza temporal, o que é raro. Não quer forçar um objetivo fictício; quer uma solução que tolere indefinição.  
> **Dor:** Falta de objetivo claro paralisa a decisão. Não é medo de perder, é confusão sobre critério de escolha — 'para onde vai esse dinheiro se não sei quando vou usar?'  

**1ey72ua** (d=0.1123)
> **Perfil:** Investidor iniciante e cauteloso que acumula pequenas quantias metodicamente, mas busca atalhos operacionais sem compreender as implicações fiscais e estruturais.  
> **Postura:** Pragmática e desconfiada — busca 'segurança' como justificativa, mas a ansiedade subjacente é sobre controle e compartimentalização. Tom coloquial e defensivo nos comentários ('bem mais prático'); resiste a crítica com argumentos frágeis, sinalizando insegurança sobre a decisão.  
> **Sinal:** Mentalidade de 'já tenho a ferramenta, por que não usar?' — típica de quem acumula contas/produtos sem propósito claro e depois tenta encaixá-los em necessidades que não resolvem; a ideia de logar em 'celular velho' revela confusão entre segurança física e segurança fiscal.  
> **Dor:** Confusão entre segurança operacional (isolamento de conta) e segurança fiscal/legal; resistência a aceitar que a solução 'mais prática' pode ser inadequada; medo de estar fazendo algo errado, mas relutância em investir tempo para aprender.  


#### M3-C1  (n=413, 11.5%)

**jcy0wu** (d=0.1786)
> **Perfil:** Investidor brasileiro cético e irônico que reconhece sinais de bolha especulativa através da banalização do marketing de investimentos.  
> **Postura:** Cinismo defensivo mascarando frustração real. Usa humor ácido ('foder os outros', 'cê loro') para processar medo de ser enganado novamente. Tom de quem já caiu em cilada antes.  
> **Sinal:** Usa referência histórica sofisticada (anedota Joe Kennedy) para fundamentar ceticismo — não é apenas reclame, é investidor que estuda padrões de bolha e reconhece quando o mercado ficou 'desesperado demais' em buscar autoridade.  
> **Dor:** Medo de estar em uma bolha especulativa sem saber quando sair. Frustração com a proliferação de 'gurus' vendendo esperança (Ports, agora Lana Rhoades) — sinal de que mercado está sobreaquecido e irracional.  

**uoz7u0** (d=0.1908)
> **Perfil:** Investidor de varejo cético e observador que acompanha movimentos de figuras públicas, mas mantém distância crítica e desconfiança do sistema.  
> **Postura:** Ceticismo irônico genuíno mascarando frustração com a volatilidade e manipulação de mercado; usa humor ('peraltices esculativas') para processar desconfiança legítima; tom é de quem observa o jogo mas se recusa a jogar.  
> **Sinal:** Usa linguagem coloquial brasileira ('trocados', 'peraltices esculativas') combinada com análise estruturada de padrão (compra-desiste-cria-larga), sugerindo alguém que acompanha mercado em português mas com visão crítica sistemática, não apenas emocional.  
> **Dor:** Sensação de impotência e exclusão — percebe oportunidades sendo criadas e destruídas por capricho de bilionários enquanto o varejo fica com migalhas ou perdas.  

**i8dx60** (d=0.2125)
> **Perfil:** Investidor de varejo em opções que segue influenciadores/gurus do mercado, oscila entre defesa cega de mentores e reconhecimento amargo de ter sido prejudicado em esquemas coletivos.  
> **Postura:** Cinismo defensivo mascarando frustração real. Usa ironia pesada ('vAi TeStA o PlAnO tRiAl') e caps aleatório para disfarçar raiva de ter perdido dinheiro. Simultaneamente defende o guru ('Ferri é bom') enquanto admite manipulação óbvia — contradição que revela desejo de acreditar que ainda pode lucr  
> **Sinal:** Defesa simultânea e crítica do mesmo guru (Ferri) na mesma thread — não consegue abandonar a esperança de lucro mesmo reconhecendo manipulação explícita. Típico de vítima de sunk cost em comunidade de trading.  
> **Dor:** Perda concreta em operações de opções coordenadas (Cogna, Vvar, Marfrig) onde preços foram manipulados; raiva de ter sido 'sardinha' em esquema coletivo; impotência porque sabe que é culpado por 'ir cegamente' mas continua fazendo.  

**ylzz0a** (d=0.2135)
> **Perfil:** Investidor cínico e politicamente engajado que vê oportunidades financeiras através de uma lente de crítica social e desconfiança institucional.  
> **Postura:** Ironia genuína mascarando frustração real com instabilidade macroeconômica. Tom de humor ácido e desencantado ('bolo de pote' como metáfora de consumo real vs. promessas vazias). Registra coloquial, desrespeitoso com autoridades, mas não é leviano — há cálculo por trás.  
> **Sinal:** Usa metáfora de 'bolo de pote' (consumo garantido vs. promessas vazias) para criticar tanto oportunidades de investimento quanto política — sugere pessoa que pensa em economia real, não apenas preços de ativos; rejeita tanto otimismo ingênuo quanto pessimismo paralisante.  
> **Dor:** Ciclos de esperança e desespero econômico ligados a mudanças políticas; ceticismo de que ganhos atuais (queda do dólar) sejam sustentáveis. Frustração com 'bolos de pote' (soluções cosméticas) em vez de reformas estruturais.  

**htop6r** (d=0.2182)
> **Perfil:** Investidor frustrado que reconhece a realidade dos limites da bolsa, mas mascara desespero com cinismo agressivo e tom de 'verdade incômoda'.  
> **Postura:** Cinismo defensivo com raiva subjacente. Tom é de 'verdade dura' e 'realismo', mas a agressividade (repetição de 'caralhada', 'fiquem no shape e quem quiser que se foda') revela ansiedade mascarada. Humor irônico usado como escudo contra a própria impotência.  
> **Sinal:** Menciona explicitamente 'fiquem no shape' como prioridade final — sugere que saúde/aparência é moeda de troca social/sexual em sua visão de mundo, revelando que vê mobilidade social também através de capital cultural/físico, não apenas financeiro. Isso diferencia de investidores que focam puramente   
> **Dor:** Sensação de armadilha: investimento em bolsa é lento demais, carreira é incerta, negócio é arriscado. Nenhuma via parece acessível com seu capital atual. A frustração é com a *velocidade* de enriquecimento, não com a impossibilidade.  

**wo3ao0** (d=0.2211)
> **Perfil:** Investidor frustrado que usa humor cáustico e ironia para criticar oportunidades de investimento duvidosas ou esquemas fraudulentos no mercado brasileiro.  
> **Postura:** Cinismo defensivo mascarando desconfiança profunda. Tom sarcástico e irônico genuíno (não ansiedade), com registro coloquial que sugere familiaridade com comunidades online de investidores. A ironia é arma de crítica, não escape de medo.  
> **Sinal:** Usa humor absurdo escalonado ('alugando guardanapo usado') para desmontar propostas — não apenas critica, mas amplifica o ridículo até o ponto de exposição. Estratégia de comunicação muito específica de comunidades de investidores que se veem como 'acordadas'.  
> **Dor:** Exposição a ou conhecimento de esquemas duvidosos no mercado de investimentos brasileiro; frustração com a proliferação de oportunidades fraudulentas ou absurdas.  

**zk6z2s** (d=0.2237)
> **Perfil:** Investidor varejista cínico e desencantado que aprendeu a desconfiar de narrativas oficiais e prefere validação prática a credenciais institucionais.  
> **Postura:** Cinismo defensivo mascarando frustração real. Usa ironia e sarcasmo como armadura contra decepções — tom é de quem já perdeu dinheiro e agora questiona autoridades. Há raiva contida ('muita burrice mesmo', 'graças') misturada com resignação.  
> **Sinal:** Rejeição explícita de credencialismo institucional ('estagiário da FGV') em favor de aprendizado via perdas reais — sugere experiência de ter confiado em 'especialistas' e se arrependido.  
> **Dor:** Sensação de impotência diante de um sistema que não muda independentemente de quem está no poder; frustração com a ingenuidade de quem ainda acredita que ministros fazem diferença real.  

**vr5dc8** (d=0.2243)
> **Perfil:** Investidor/especulador que consome notícias financeiras com ceticismo performativo, usando humor como defesa contra a própria vulnerabilidade a esquemas.  
> **Postura:** Cinismo defensivo mascarando ansiedade. O humor excessivo ('papel em branco em dinheiro', 'NFT do dinheiro', 'Runescape') funciona como dessensibilização — rir do golpe é uma forma de negar que poderia cair nele. Há raiva subjacente (comentários sobre Banco Central e Roberto Campos Neto).  
> **Sinal:** Referência específica a 'Runescape' — indica pessoa jovem (millennial/Gen Z) que mistura cultura gamer com investimentos, sugerindo que aprendeu sobre risco e especulação em ambientes virtuais antes de aplicar em mercados reais.  
> **Dor:** Sensação de impotência diante de um sistema que parece simultaneamente fraudulento (golpistas) e legalmente corrupto (instituições oficiais). Possível histórico de perdas financeiras que alimenta o cinismo.  

**1c7znml** (d=0.2273)
> **Perfil:** Investidor iniciante que tenta fazer crítica social sobre decisões financeiras de pobres, mas expõe falta de compreensão básica de matemática ou lógica, gerando rejeição da comunidade.  
> **Postura:** Tom de superioridade moral mascarando insegurança; tenta fazer crítica 'inteligente' sobre comportamento financeiro alheio, mas é rapidamente desmascarado. Há frustração subjacente com a 'falta de inteligência' alheia que revela mais sobre suas próprias inseguranças.  
> **Sinal:** Escolheu criticar 'lógica do brasileiro médio' usando uma comparação matemática que não faz sentido (1500 ≠ 15x100 é uma tautologia vazia), sugerindo que a crítica é performativa, não fundamentada — típico de quem quer parecer investidor sofisticado sem ter base.  
> **Dor:** Incompetência em comunicar ideias (a postagem é confusa e a lógica falha) combinada com necessidade de parecer superior intelectualmente; rejeição brutal da comunidade amplifica essa dor.  

**xrgkzd** (d=0.2279)
> **Perfil:** Investidor/apostador brasileiro que domina análise de dados e odds, mas usa humor cáustico e ironia para processar uma relação ambígua com risco financeiro — entre a competência técnica e a autossabotagem deliberada.  
> **Postura:** Ironia genuína mascarando ansiedade e frustração. O tom é de quem ri da própria incompetência para evitar confrontar a realidade do risco. Usa humor agressivo ('bando de frouxo', 'quieta o cu') como defesa. A repetição de 'perder dinheiro' não é brincadeira leve — é confissão disfarçada.  
> **Sinal:** Cria conteúdo detalhado e bem estruturado (tabelas, análise de odds, referências a estratégias de trading) especificamente SOBRE como perder dinheiro, e a comunidade o valida ('isso que eu chamo de conteúdo'). Diferencia-se por transformar a própria falha em produto consumível.  
> **Dor:** Ciclo de perda financeira normalizado e ritualizado. A pessoa não está confusa — está resignada e a transforma em entretenimento/conteúdo. A dor é a incapacidade de parar, disfarçada de 'guia para perder dinheiro'.  


#### M3-C2  (n=1188, 33.0%)

**mdnsqv** (d=0.1862)
> **Perfil:** Investidor varejo que consome conteúdo de mercado financeiro com ceticismo bem-humorado, reconhecendo sorte e risco onde outros veem genialidade.  
> **Postura:** Ironia genuína como defesa contra FOMO e frustração. Tom é leve e auto-deprecativo ('dois erros fazem um acerto?'), mas subjacente há ceticismo sobre narrativas de sucesso fácil. Não há ansiedade mascarada — há desconfiança estruturada.  
> **Sinal:** Usa referência específica a IRBR como comparação — sinal de que acompanha ativos problemáticos/meme do mercado brasileiro, sugerindo investidor que consome comunidades online (Reddit, Discord) e não apenas mídia tradicional.  
> **Dor:** Frustração com narrativas de 'comprou na baixa, vendeu na alta' que circulam como se fossem replicáveis, quando na verdade são eventos únicos (um Bezos no mercado). Possível FOMO contido por humor.  

**maurcy** (d=0.1944)
> **Perfil:** Investidor cético e desiludido que usa humor corrosivo para processar a futilidade percebida da análise técnica e das previsões de mercado.  
> **Postura:** Cinismo defensivo mascarando desespero. O tom é irônico e absurdista (referências a Cthulhu, astrologia, Ronaldinho), mas o comentário final ('Estou depressivo por favor me deem um babaozinho') revela ansiedade genuína e possível burnout emocional com investimentos.  
> **Sinal:** A progressão do sarcasmo até o pedido explícito de consolo ('me deem um babaozinho') no final revela que essa pessoa usa comunidades de investimento menos para aprender e mais para encontrar validação emocional e camaradagem na desilusão compartilhada.  
> **Dor:** Sensação de que está perdendo tempo/dinheiro seguindo análises que são tautológicas ('se subir sobe, se cair cai') e que ninguém realmente sabe o que vai acontecer — combinado com depressão ou esgotamento emocional.  

**1fhderl** (d=0.2002)
> **Perfil:** Investidor desencantado que questiona ídolos financeiros populares e desconfia de narrativas simplistas sobre enriquecimento.  
> **Postura:** Cínica e defensiva, com humor ácido que mascara frustração real. Usa ironia pesada ('herói de vocês?') e sarcasmo para deslegitimar figuras públicas. Tom de quem se sente enganado por promessas fáceis.  
> **Sinal:** Combina ceticismo inteligente (questiona marca d'água, pede contexto) com tática prática de sobrevivência (burla cupons), sugerindo alguém que não apenas critica, mas age contra o sistema — diferente de críticos passivos.  
> **Dor:** Sensação de estar sendo enganado por figuras públicas que vendem esperança fácil enquanto a realidade financeira permanece apertada. Raiva de narrativas que simplificam pobreza.  

**10lt9c6** (d=0.202)
> **Perfil:** Investidor de varejo que acompanha crises corporativas com ceticismo e humor defensivo, buscando validar suas escolhas de investimento seguro contra riscos sistêmicos.  
> **Postura:** Ironia genuína mascarando ansiedade sobre confiabilidade do sistema financeiro. O tom é de 'eu avisei' — não é humor leve, é alívio de ter escapado de um calote. Registra coloquial ('caralhos', 'coitado'), sugerindo descontração, mas o conteúdo revela preocupação real com risco sistêmico.  
> **Sinal:** Compara Americanas com Argentina (calote soberano) — sinal de que essa pessoa pensa em risco sistêmico e default em escala macro, não apenas em uma empresa. Não é um trader focado em oportunidades, é alguém que teme contágio.  
> **Dor:** Medo de que até instituições 'seguras' (bancos, governo via BNDES) cometam erros de alocação que afetam o sistema como um todo. Frustração com falta de transparência ou lógica nas decisões de crédito corporativo.  

**ncunu1** (d=0.205)
> **Perfil:** Investidor cético e desencantado que questiona a viabilidade real de estratégias de renda passiva, usando humor corrosivo para mascarar frustração com promessas irrealistas do mercado.  
> **Postura:** Cinismo defensivo com tom de humor negro. Usa ironia afiada ('basta ter 1 milhão') não como leveza, mas como arma contra ilusões. Há frustração genuína disfarçada de brincadeira — o tipo que ri para não chorar.  
> **Sinal:** Usa referências muito específicas (Ambev, Brahma, Heineken, Warren Buffett) para desconstruir narrativas — não reclama genericamente, mas aponta a hipocrisia de ricos que fingem ser modestos. Isso sugere alguém que estuda o comportamento de investidores bem-sucedidos com ressentimento inteligente.  
> **Dor:** Sensação de estar fora do jogo — observa outros gerando renda passiva real (acionistas Ambev) enquanto sabe que não tem capital para replicar. Frustração com a mentira de que é 'fácil' ou 'para todos'.  

**1dbsukk** (d=0.2067)
> **Perfil:** Investidor experiente e cético que busca validação de sua estratégia contrária ao hype, mas com sinais de fadiga emocional com o ciclo de narrativas do mercado.  
> **Postura:** Cinismo defensivo mascarando frustração genuína. Tom irônico e sarcástico ('tigrinho', 'me divertindo enquanto perco dinheiro') que funciona como válvula de escape para irritação com o ruído do mercado. Não é ansiedade aguda, mas desgaste crônico.  
> **Sinal:** Rejeição ativa de 'market timing' combinada com humor autodepreciativo sobre perdas — sugere investidor que já passou por ciclos múltiplos e desenvolveu imunidade a FOMO, mas não a irritação com quem ainda cai nele.  
> **Dor:** Saturação por narrativas cíclicas e previsões falsas do mercado; sensação de estar cercado por ruído enquanto tenta manter foco em estratégia de longo prazo.  

**mw76sp** (d=0.2101)
> **Perfil:** Investidor de varejo que segue influenciadores do mercado financeiro, oscila entre ceticismo e FOMO, e usa humor como defesa contra a própria insegurança sobre decisões de investimento.  
> **Postura:** Cinismo defensivo mascarando ansiedade real. Usa ironia pesada ('manual de cabeça para baixo', 'Mercado Financeiro Quântico') para processar frustração de ver outros ganharem enquanto ele perde. Tom é de quem ri para não chorar.  
> **Sinal:** Foco obsessivo no tamanho do capital investido ('meio milho', '1bi a menos') como explicação para resultados — não questiona a estratégia, questiona se a aposta foi grande o suficiente, revelando crença de que volume resolve tudo.  
> **Dor:** Sensação de estar fora do jogo — vê outros ganhando 'absurdamente' enquanto ele perde, e suspeita que o conhecimento vendido online é fraude ou que a sorte/capital inicial é o verdadeiro fator.  

**sxybkd** (d=0.2107)
> **Perfil:** Investidor iniciante que confunde volatilidade de curto prazo com sinais fundamentais, buscando validação para uma tese que ele próprio não acredita.  
> **Postura:** Ceticismo defensivo mascarando ansiedade real. Usa tom de pergunta retórica ('investidor estrangeiro é inocente assim mesmo?') para expressar desconfiança, mas a própria pergunta revela que ele está procurando razões para acreditar no Brasil — e não consegue encontrá-las sozinho. Frustração com a pr  
> **Sinal:** Usa a palavra 'inocente' três vezes em contextos diferentes (título, corpo, resposta implícita aos comentários), revelando que a questão central não é sobre investidores estrangeiros, mas sobre sua própria ingenuidade — ele está testando se merece confiar em seu próprio julgamento.  
> **Dor:** Paralisia por falta de convicção — vê sinais técnicos positivos (dólar caindo) mas não consegue reconciliar com ceticismo político (populismo, instabilidade). Medo de ser 'inocente' como os comentários sugerem.  

**npebdq** (d=0.2192)
> **Perfil:** Investidor cético e desencantado que reconhece esquemas de enriquecimento rápido como fraude, mas permanece preso à ansiedade de estar perdendo oportunidades.  
> **Postura:** Cinismo defensivo mascarando frustração real. Usa humor ácido e sarcasmo (ironia sobre brownies, maldições a 'Wendell Carvalho') para processar raiva de ter sido ou quase ter sido enganado. Tom é de quem 'acordou' mas ainda dói.  
> **Sinal:** Menciona explicitamente 'pena da galera que cai nessa' — não é apenas cético, é moralmente afetado pelo dano alheio. Diferencia-se por empatia com vítimas, não apenas por ceticismo próprio.  
> **Dor:** Sensação de estar sendo enganado sistematicamente por influenciadores; impotência diante da proliferação de esquemas que atraem pessoas desesperadas; culpa/pena pelos que 'caem nessa'.  

**wh3ok6** (d=0.2217)
> **Perfil:** Investidor de varejo com postura cínica que observa o sistema financeiro como máquina de transferência de renda, mais interessado em criticar comportamentos alheios do que em sua própria estratégia.  
> **Postura:** Cinismo estruturado mascarando desconfiança profunda. Humor ácido e irônico ('quem quer dinheiro ooooeeee') cobre frustração com a 'ingenuidade' alheia. Registra tom de superioridade moral — julga quem 'cai na ratoeira' enquanto se posiciona como observador lúcido do sistema.  
> **Sinal:** Postura de 'trader observador moral' — critica comportamento de risco alheio (antecipações, empréstimos predatórios) enquanto simultaneamente aposta em ações de bancos que lucram exatamente com isso. Contradição reveladora entre discurso crítico e posicionamento financeiro.  
> **Dor:** Frustração com a 'falta de consciência' alheia e possível ressentimento de que beneficiários 'não merecem' — sugere conflito não resolvido sobre justiça distributiva ou inveja mascarada de acesso a programas.  


#### M3-C3  (n=652, 18.1%)

**1dn0ppy** (d=-0.0) **[medoid]**
> **Perfil:** Investidor iniciante ou amador que compartilha posições perdedoras ou decisões financeiras questionáveis em redes sociais, buscando validação ou humor em vez de conselho genuíno.  
> **Postura:** Ironia defensiva mascarando frustração real com perdas. Usa humor para lidar com constrangimento financeiro. Tom descontraído superficialmente, mas a reação dos comentários sugere que a postagem foi percebida como genuinamente ruim ou ingênua — não apenas brincadeira.  
> **Sinal:** Postou algo tão inadequado que foi removido até de comunidades de varejo especulativo (notoriamente tolerantes) — sugere falta de filtro, impulsividade ou desespero emocional, não apenas ingenuidade.  
> **Dor:** Perda financeira concreta e humilhação pública associada; exclusão de comunidades online onde buscava pertencimento; incapacidade de distinguir entre brincadeira e conselho sério.  

**nmbw3e** (d=0.0781)
> **Perfil:** Investidor iniciante ou amador que observa erros alheios com ironia, mas que provavelmente comete os mesmos — compra na alta, vende na baixa, e busca validação em comunidades online.  
> **Postura:** Ironia defensiva mascarando frustração real. O tom é de 'eu vejo o erro dos outros' mas a frequência de postagem e engajamento sugerem ansiedade sobre próprias decisões. Humor como mecanismo de lidar com perdas ou indecisão.  
> **Sinal:** Usa ironia como ferramenta de observação social — posta para comentar erro alheio, não para pedir ajuda. Isso sugere que já perdeu dinheiro e agora se posiciona como observador crítico para recuperar sensação de controle.  
> **Dor:** Perda ou indecisão em operações cambiais; sensação de estar sempre um passo atrás (compra na alta, vende na baixa); impotência diante de variáveis macroeconômicas (câmbio, eleições) que não controla.  

**y84zjk** (d=0.1058)
> **Perfil:** Investidor iniciante ou observador periférico que consome conteúdo financeiro em comunidades online, mas não demonstra engajamento ativo com sua própria estratégia.  
> **Postura:** Ironia defensiva e desapego performático. O tom é de quem ri da situação financeira alheia (e implicitamente da própria) como mecanismo de distanciamento. Não há ansiedade explícita — há cinismo confortável.  
> **Sinal:** Não comenta sobre a postagem original (que parece ser sobre um investidor específico chamado Pestana) — apenas reforça a narrativa coletiva de fracasso/dívida como identidade compartilhada. É um espectador que se vê no espelho.  
> **Dor:** Invisibilidade financeira — estar fora do jogo de investimentos/crédito formal, observando de fora. A ironia mascara exclusão, não ansiedade de ganho.  

**10kdurc** (d=0.1137)
> **Perfil:** Investidor amador que sofreu perda significativa e busca validação/ajuda em comunidade de varejo, mas é alvo de ridicularização sistemática por decisões de timing ruim.  
> **Postura:** Frustração genuína mascarada por tom irônico/sarcástico na postagem ('Lord Punheteiro'); comunidade responde com cinismo cruel e sarcasmo agressivo que sugere a pessoa está em estado de vulnerabilidade real — o humor é defesa, não leveza.  
> **Sinal:** Escolheu postar em r/farialimabeta (comunidade de sátira sobre investimentos ruins) em vez de r/investimentos, sinalizando que já internalizou o fracasso como 'meme' — busca ajuda onde sabe que será ridicularizado, sugerindo resignação ou masoquismo financeiro.  
> **Dor:** Perda material de 90% em ativo específico + humilhação pública em comunidade que transforma fracasso em entretenimento; sensação de estar preso em decisão ruim sem saída clara.  

**nnrgwf** (d=0.1168)
> **Perfil:** Investidor iniciante que perdeu dinheiro em aplicações de risco e agora processa a experiência através de humor autodepreciativo  
> **Postura:** Ironia defensiva mascarando frustração e arrependimento genuíno; tom de humor negro para lidar com perda real; registro descontraído mas com ressentimento subjacente  
> **Sinal:** Uso de foto com batata na postagem sobre perda de dinheiro — sugestão de que está literalmente sem recursos ou fazendo crítica visual absurda sobre pobreza; diferencia-se por usar absurdo visual em vez de apenas texto  
> **Dor:** Perda financeira concreta e recente; sensação de ter sido enganado ou de que o sistema trabalha contra o pequeno investidor  

**hjjq7c** (d=0.1238)
> **Perfil:** Investidor iniciante em renda fixa que busca validação social para decisões financeiras pequenas, mas está inserido em comunidade que trivializa ganhos modestos.  
> **Postura:** Ironia defensiva mascarando frustração real com ganhos ínfimos. Tom de brincadeira ('que pó vcs me recomendam') é mecanismo de proteção contra a realidade de que seu retorno é negligenciável. Busca validação através do humor, não genuinamente despreocupado.  
> **Sinal:** Único na thread que menciona TD (Tesouro Direto) especificamente — sinal de que tentou educação financeira formal, mas está em comunidade que desvaloriza essa escolha. Contraste entre comportamento 'correto' e ambiente que o ridiculariza.  
> **Dor:** Impotência financeira — ganho tão pequeno que a comunidade o trivializa imediatamente. Frustração com velocidade de acumulação em renda fixa. Sensação de estar 'fazendo algo certo' (investindo) mas recebendo retorno que não justifica o esforço.  

**1eykafw** (d=0.1249)
> **Perfil:** Investidor que buscava comunidade séria sobre mercado financeiro, mas se vê frustrado com a degradação do grupo em conteúdo de day trade superficial e sexualizado.  
> **Postura:** Decepção genuína mascarada por tom irônico e sarcástico. Não é humor puro — há ressentimento real com a qualidade das discussões. Usa ironia defensiva ('Essa foi a principal lição') para expressar desaprovação sem confronto direto.  
> **Sinal:** É um dos poucos no thread que critica a postagem original em vez de apenas ridicularizá-la — sua reclamação inicial ('Eu gostava desse grupo quando...') revela nostalgia por padrão anterior, não apenas rejeição ao absurdo presente.  
> **Dor:** Erosão de um espaço que era valioso — o grupo perdeu credibilidade ao permitir conteúdo de day trade irresponsável e sexualizado. Sente-se sozinho em buscar seriedade.  

**wtnlgj** (d=0.126)
> **Perfil:** Investidor iniciante ou leigo que caiu em golpe de robô de trading/PIX e agora busca validação cínica da comunidade em vez de admitir o erro  
> **Postura:** Ironia defensiva mascarando humilhação e arrependimento real; tom de auto-deprecação que busca controlar a narrativa antes que outros o façam; ansiedade convertida em humor amargo  
> **Sinal:** A postagem é um meme/provérbio ('todo dia sai de casa um esperto') aplicado a si mesmo — indicador de que a pessoa está processando o golpe através de humor coletivo, buscando pertencimento ao grupo de 'vítimas' em vez de isolamento da vergonha  
> **Dor:** Perda financeira concreta em golpe de robô/PIX; humilhação social por ter caído em armadilha óbvia; desamparo diante de promessas falsas que pareciam plausíveis no momento  

**ud08su** (d=0.1289)
> **Perfil:** Investidor iniciante ou amador que consome conteúdo de comunidades especulativas online e trata oportunidades financeiras duvidosas com ironia defensiva.  
> **Postura:** Ironia como mecanismo de defesa contra frustração financeira real. O tom é cínico e auto-deprecativo ('Como um bom Farialimer, vejo que esta é uma ótima maneira de garantir nosso loss diário'), mascarando ansiedade sobre oportunidades reais vs. golpes. Há desespero subjacente disfarçado de humor.  
> **Sinal:** Referência específica a 'Farialimer' (comunidade de traders/especuladores brasileiros) e familiaridade com memes de golpes clássicos (príncipe da Nigéria, agiota), sugerindo que essa pessoa consome regularmente conteúdo de comunidades especulativas online como forma de lidar com frustração financeir  
> **Dor:** Impossibilidade de ganhar o suficiente com trabalho convencional; sensação de estar preso em um sistema que não oferece mobilidade financeira real. A ironia é uma resposta à impotência.  

**1arjltt** (d=0.1296)
> **Perfil:** Investidor iniciante que confunde análise macroeconômica com competência financeira e busca validação em comunidades online após sofrer consequências por comportamento inadequado.  
> **Postura:** Frustração mascarada por ironia defensiva ('Chegou minha vez =\'); tom de vítima incompreendida; usa humor para processar rejeição social; há ressentimento genuíno sob a leveza aparente.  
> **Sinal:** Traz uma observação macroeconômica (PIB global dividido igualmente) como defesa intelectual para um banimento — sugere que confunde pensamento econômico abstrato com argumentação válida em contexto social, e usa isso como escudo contra crítica.  
> **Dor:** Banimento de comunidade (provavelmente r/investimentos ou similar) interpretado como rejeição pessoal; sensação de injustiça ('esse não vale, pô'); isolamento relativo em espaços onde buscava aprender.  


## 6. Non-financial content rate per cluster

Overall non-financial rate: **3.0%** (109/3586 threads). Clusters >40% non-financial are corpus-artifact candidates.


**By subreddit:**

  r/farialimabets: 59/1789 = 3.3%
  r/investimentos: 50/1797 = 2.8%

| Cluster | n | n non-financial | rate % | Flag? |
|---------|---|-----------------|--------|-------|
| M3-C0 | 1333 | 34 | 2.6% | ok |
| M3-C1 | 413 | 17 | 4.1% | ok |
| M3-C2 | 1188 | 34 | 2.9% | ok |
| M3-C3 | 652 | 24 | 3.7% | ok |


## 7. M3–M2 ARI and cluster correspondence

**ARI (M3 k=4 vs M2 k=7) on shared threads:** actual agreement between the two independent clusterings. Computed on threads present in both parquets. ARI=0 means no agreement beyond chance; ARI=1 means perfect agreement. For independent methods with different k, modest ARI (~0.1–0.3) is a positive signal.

**ARI(M3, M2) = 0.2120** on 3586 shared threads.

**M3→M2 correspondence table** (which M2 cluster is most overrepresented in each M3 cluster?). Overrepresentation = (share of M2-Cx within M3-Cc) / (corpus base rate of M2-Cx). >1.5× = meaningful signal. Supervisor's predicted mapping shown for comparison.

| M3 cluster | n | Best M2 match | Overrep | Best M1 match | Overrep |
|------------|---|---------------|---------|---------------|---------|
| M3-C0 | 1333 | M2-C3 | 2.34× | M1-C0 | 1.9× |
| M3-C1 | 413 | M2-C1 | 1.91× | M1-noise | 1.39× |
| M3-C2 | 1188 | M2-C5 | 1.81× | M1-C2 | 2.06× |
| M3-C3 | 652 | M2-C6 | 5.5× | M1-noise | 1.37× |

Full M2 overrepresentation per M3 cluster:

  M3-C0: M2-C3:2.34×, M2-C2:1.71×, M2-C4:1.3×, M2-C0:0.79×
  M3-C1: M2-C1:1.91×, M2-C4:1.58×, M2-C5:0.65×, M2-C2:0.59×
  M3-C2: M2-C5:1.81×, M2-C0:1.24×, M2-C4:1.01×, M2-C1:0.93×, M2-C2:0.78×
  M3-C3: M2-C6:5.5×, M2-C1:2.0×, M2-C0:1.62×, M2-C5:1.59×


## 8. Adjudication — five pre-specified tests (M2→M3 direction)

Complement to Section 7: for each M2/M1 reference cluster, where do its threads land in M3? Overrepresentation = pct_in_top / cluster_base_rate. >1.5× and concentrated = methods independently recover the same group.


####   M2-C1 (cynical-reactive — decisive test)

Reference threads: 1073. Base rate: 30.0%. Top M3 cluster: **M3-C3** (36.4% of ref threads). That cluster's corpus share: 18.2%. Overrepresentation: **2.0×**. Entropy: 1.883. Threshold: 40%.

Distribution:
  M3-C0: 117
  M3-C1: 236
  M3-C2: 329
  M3-C3: 391

**Verdict:** — DISPERSED (36.4% < 40% threshold)


####   M2-C2 (earnest learner)

Reference threads: 1711. Base rate: 47.6%. Top M3 cluster: **M3-C0** (63.6% of ref threads). That cluster's corpus share: 37.2%. Overrepresentation: **1.71×**. Entropy: 1.361. Threshold: 55%.

Distribution:
  M3-C0: 1089
  M3-C1: 117
  M3-C2: 441
  M3-C3: 64

**Verdict:** ✓ CONCENTRATED — 1.71× overrepresented in M3-C0 (63.6% ≥ 55%)


####   M2-C5 (speculator)

Reference threads: 658. Base rate: 18.4%. Top M3 cluster: **M3-C2** (59.9% of ref threads). That cluster's corpus share: 33.1%. Overrepresentation: **1.81×**. Entropy: 1.419. Threshold: 30%.

Distribution:
  M3-C0: 25
  M3-C1: 49
  M3-C2: 394
  M3-C3: 190

**Verdict:** ✓ CONCENTRATED — 1.81× overrepresented in M3-C2 (59.9% ≥ 30%)


####   M1-C1 (property/banking/debt)

Reference threads: 464. Base rate: 12.9%. Top M3 cluster: **M3-C0** (63.6% of ref threads). That cluster's corpus share: 37.2%. Overrepresentation: **1.71×**. Entropy: 1.393. Threshold: 25%.

Distribution:
  M3-C0: 295
  M3-C1: 16
  M3-C2: 110
  M3-C3: 43

**Verdict:** ✓ CONCENTRATED — 1.71× overrepresented in M3-C0 (63.6% ≥ 25%)


####   M1-C0 (tax/IR)

Reference threads: 154. Base rate: 4.3%. Top M3 cluster: **M3-C0** (70.8% of ref threads). That cluster's corpus share: 37.2%. Overrepresentation: **1.9×**. Entropy: 1.284. Threshold: 15%.

Distribution:
  M3-C0: 109
  M3-C1: 16
  M3-C2: 23
  M3-C3: 6

**Verdict:** ✓ CONCENTRATED — 1.9× overrepresented in M3-C0 (70.8% ≥ 15%)


## 9. M3 × M2 cross-tabulation

| row_0   |   M2-C0 |   M2-C1 |   M2-C2 |   M2-C3 |   M2-C4 |   M2-C5 |   M2-C6 |
|:--------|--------:|--------:|--------:|--------:|--------:|--------:|--------:|
| M3-C0   |       5 |     117 |    1089 |      81 |      16 |      25 |       0 |
| M3-C1   |       0 |     236 |     117 |       5 |       6 |      49 |       0 |
| M3-C2   |       7 |     329 |     441 |       6 |      11 |     394 |       0 |
| M3-C3   |       5 |     391 |      64 |       1 |       0 |     190 |       1 |


## 10. M3 × M1 cross-tabulation

| row_0   |   M1-C0 |   M1-C1 |   M1-C2 |   M1-C3 |   M1-noise |
|:--------|--------:|--------:|--------:|--------:|-----------:|
| M3-C0   |     109 |     295 |      20 |     823 |         86 |
| M3-C1   |      16 |      16 |       6 |     314 |         61 |
| M3-C2   |      23 |     110 |     105 |     810 |        140 |
| M3-C3   |       6 |      43 |      23 |     485 |         95 |


## 11. Figures

- `reports/figures/m3_kmedoids_k4.png` — 2-D UMAP coloured by M3 clusters
- `reports/figures/m3_crosstab_m2.png` — M3 × M2 heatmap
- `reports/figures/m3_crosstab_m1.png` — M3 × M1 heatmap

---

## Review outcome (2026-05-21)

Phase 3C **APPROVED**. k=4 locked. Phase 3D unblocked.

Resolved review questions:
1. M3→M2 correspondence — CONFIRMED with one nuance:
   - M3-C0 earnest-learner ↔ M2-C2 (concentrated, 63.6% of M2-C2 → M3-C0; 1.71×). ✓
   - M3-C2 speculator ↔ M2-C5 (concentrated, 59.9% → M3-C2; 1.81×). ✓
   - M2-C1 cynical-reactive is **distributed across BOTH M3-C1 and M3-C3** (1.91× and 2.0× respectively). Real posture, fuzzy boundaries — see Section 1 status note and decisions_log.
2. M3×M1 — CONFIRMED: M3-C2 speculator aligns with M1-C2 crypto (2.06×).
3. No artifact clusters. Section 6 non-financial rates ≤ 4.1% (all clusters); Section 4 missingness flags on C1/C2/C3 are a known farialimabets thin-text effect handled by holistic summaries, not a corpus pollutant.
4. Bootstrap stability acceptable (mean ARI 0.618±0.264; all per-cluster Jaccard ≥ 0.5) given continuum-partition context.