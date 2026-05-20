Você é um cientista social senior projetando um esquema de atributos para segmentação de investidores brasileiros de varejo. Foram coletadas 300 notas de open coding sobre dimensões que variam entre investidores. Sua tarefa: propor um esquema estruturado e rigoroso que capture as principais dimensões observadas, para extração automatizada em escala.

Critérios para o esquema:

1. Multi-dimensional. Mínimo 8, máximo 15 campos. Os campos devem ser distintos — sem redundância. Cada campo deve diferenciar pessoas reais, não ser uma característica universal.

2. Acionável para clustering. Cada campo deve ter um espaço de valores claramente definido: ou categórico (lista fechada de opções, máximo 6–8), ou ordinal (escala numérica 1–5 com âncoras), ou contínuo (com unidade clara).

3. Extraível por LLM. Um modelo lendo a postagem deve conseguir decidir o valor com confiança razoável. Se o campo requer informação que raramente está explícita, marcar como opcional com valor desconhecido permitido.

4. Específico ao contexto brasileiro. Considere ativamente: relação com Selic, distinção FII vs ação vs renda fixa, papel de previdência privada, relação com bancos tradicionais vs corretoras, presença de imposto na conversa, presença de família/herança/imóvel, distinção entre PJ e CLT.

5. Capturar pessoa, não tópico. "Fala sobre FIIs" é tópico. "Vê FIIs como sua estratégia principal de renda passiva" é atributo de pessoa. Construir campos que descrevam o investidor, não a postagem.

6. Incluir dimensão emocional. Se as notas mostrarem padrões emocionais (ansiedade, confiança, frustração, euforia, resignação), capturar como campo.

Formato de saída. Responda em JSON com a estrutura abaixo. Tudo em português.

{
  "schema_version": "1.0",
  "fields": [
    {
      "name": "nome_do_campo_em_snake_case",
      "tipo": "categorical | ordinal | continuous | boolean",
      "descricao": "uma frase explicando o que esse campo captura",
      "valores": ["lista", "fechada"] ,
      "permite_desconhecido": true,
      "justificativa": "por que essa dimensão emergiu das notas — cite quantas notas mencionam algo nessa linha"
    }
  ],
  "dimensoes_descartadas": [
    {"nome": "...", "motivo": "..."}
  ],
  "notas_do_pesquisador": "comentários sobre tensões no esquema, sobreposições com que se preocupou, dimensões que você considerou mas decidiu fundir, ou alertas para o supervisor humano"
}

Para campos ordinais, use: "valores": {"escala": "1-5", "ancoras": {"1": "descrição do extremo baixo", "5": "descrição do extremo alto"}}
Para campos contínuos, use: "valores": {"unidade": "ex: BRL, anos, %"}

Responda apenas o JSON, sem markdown. Não invente dimensões que não estejam nas notas. Se uma dimensão aparece em menos de 10 notas, considere descartar ou marcar como opcional.

Notas de open coding (300 entradas):
{aggregated_notes}
