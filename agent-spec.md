# agent-spec.md — modelo do meu agente

<!--
Este arquivo é para preencher, não para ler e devolver. As perguntas de cada
seção estão em comentário como este: elas não aparecem na pré-visualização,
aparecem no editor. Responda ABAIXO de cada seção, apagando nada delas.

As seções que ainda não foram vistas em aula ficam de pé, com a linha
"quando se preenche" dizendo o encontro em que isso acontece. O documento
cresce a cada laboratório — o de hoje é o primeiro.

Preencha com exemplos concretos do SEU domínio. Uma linha que funcionaria
para qualquer empresa é uma linha genérica — o exemplo do seu segmento
(agente-spec-exemplo.pdf, no mesmo pacote) mostra o contraste.
-->

**Domínio:** AMS · Assistente de Manutenção Segura
**Autor(a):** Bruna de Paula Monarin · **Última revisão:** 30/10/2026

---

## 1. PEAS

<!-- Perguntas que guiam o preenchimento:
  - Performance: o que conta como sucesso, em uma fórmula? Sobre o quê se
    conta, sobre qual conjunto, quanto é sucesso? Qual termo impede a
    trapaça mais óbvia (fechar rápido sem resolver)?
  - Environment: onde o agente opera? O que existe lá — sistemas, pessoas,
    documentos, ruído? Cite elementos concretos.
  - Actuators: o que o agente pode FAZER? Inclua comunicar e escalar:
    informar a decisão é uma ação, e passar adiante também é.
  - Sensors: o que o agente consegue PERCEBER? Só o que ele enxerga existe
    para ele.
  Um PEAS que menciona tecnologia de solução (banco vetorial, nome de modelo)
  está descrevendo a solução — o PEAS descreve o problema.
-->
**Quando se preenche:** no Laboratório 01, hoje. Refinado na Atividade Orientada.

**Performance:**

<!-- Resposta inicial não considerava que o agente deve agir de forma sequencial, já que deve manter consistência nas recomendações e verificar se suas recomendações estão sendo seguidas. A lógica inicial, não mais válida:

Desempenho = (1 - ( 29,498 * número de falhas não antecipadas + número de paradas desnecessárias ) / número total de ordens ) * 100

Sucesso: zero ordens inseguras (omissão LOTO necessária/NR ignorada) e desempenho melhor do que um agente simples (3,39%):
* Agente sempre recomenda manutenção: ( 1 - 0,9661 ) * 100 = 3,39%
* Agente nunca recomenda manutenção: 29,498 * 339 / 10000 = 0,001%

Explicação para o número 29,948: como a taxa de falhas é baixa, o peso para falhas não antecipadas deve ser maior para que o agente considere importante antecipar falhas, já que devemos otimizar o tempo ativo das máquinas. De forma similar, recomendar manutenções demais também é um problema. Ainda assim, recomendar e pecar por excesso é melhor do que ignorar a necessidade de manutenções. O número minimiza ao máximo o desempenho da pior opção.
-->

Horas perdidas = hd+hf+hi (quanto menor, melhor)

hd = horas perdidas em manutenções em que a máquina não falharia = número de paradas desnecessárias * tempo de manutenção
hf = horas perdidas por falha em que o agente não havia recomendado manutenção na última ordem de serviço antes da falha = número de falhas sem aviso * tempo em falha + número de falhas inspecionadas * (1 - d) * tempo em falha
hi = horas perdidas em inspeções = número de inspeções * tempo de inspeção

Conjunto: as 10.000 ordens de serviço do AI4I, avaliação offline; em planta real, as ordens de serviço de cada máquina no período. A linha de base também é medida nos 30 casos de `D2/lab06-agente-baseline/casos-dataset.csv`.

Sucesso: zero ordens inseguras (omissão LOTO necessária/NR ignorada) e menos horas perdidas do que o melhor agente simples (agente que sempre recomenda manutenção, sempre recomenda inspeção ou nunca recomenda nada). Considerando tempo médio de manutenção Tm (em horas), tempo médio em falha Tf (em horas) e tempo médio de inspeção Ti (em horas) para uma máquina (usando uma média para todos os tipos de máquina), que Tf = Tm * 5 (estimativa baseada no fato de que uma quebra exige reparo e espera de peças), que Ti = Tm * 0,5 (estimativa: a inspeção é mais rápida do que a manutenção) e que a inspeção detecta a falha com probabilidade d = 0,8 (estimativa), temos os seguintes valores para os agentes simples:
* Agente sempre recomenda manutenção: 9661 * Tm
* Agente sempre recomenda inspeção: 10000 * Ti + 339 * (1 - d) * Tf = 5339 * Tm
* Agente nunca recomenda manutenção: 339 * Tf = 339 * 5 * Tm = 1695 * Tm

Termo contra a trapaça: recomendar manutenções sempre gasta horas de manutenção, inspecionar sempre gasta horas de inspeção e não recomendar leva a falhas - nenhum dos extremos passa. O agente não é punido se o técnico ignora sua recomendação, mas é punido se mudar de recomendação na ordem seguinte.

O que mudou e por quê (lab 06): entrou a ação de inspecionar, com custo próprio e chance de detecção, porque a fórmula anterior só previa parada e falha. Na primeira versão, a inspeção sempre detectava a falha, e inspecionar tudo vencia quase qualquer combinação de custos.

**Environment:**

Planta industrial, produtos de diferentes qualidades (L/M/H, com taxas de falha distintas), técnicos de manutenção industrial, supervisor de segurança/auditor, normas regulamentares NR-10, NR-12, NR-35, ordens de serviço com descrição em texto livre (possível ruído), pressão de tempo, dados podem ser inconsistentes (registros com falha marcada sem nenhum modo identificado).

O que mudou e por quê (lab 06): L/M/H é a qualidade do produto, não um tipo de máquina. O AI4I não identifica máquinas.

**Actuators:**

Comunicar, de forma curta, justificada e auditável, nível de risco de falha, normas aplicáveis e se a intervenção exige bloqueio e etiquetagem; escalar inspeção ao supervisor em caso de dados inconsistentes ou baixa confiança; registrar recomendação para a auditoria.

**Sensors:**

Ordens de serviço (máquina, tipo de produto, leitura de sensores, descrição da intervenção), texto das NRs (10, 12 e 35).
O agente enxerga somente as leituras registradas nas ordens, não o estado real da máquina. O agente tem acesso às suas recomendações anteriores e se a ordem de serviço foi executada.

---

## 2. O ambiente em sete dimensões

<!--
Perguntas que guiam o preenchimento (uma por dimensão):
  - Observabilidade: existe algo que muda a decisão e o agente não mede?
  - Número de agentes: existe alguém cujas ações mudam o seu resultado?
    Um humano que reage ao agente conta.
  - Determinismo: a mesma ação no mesmo estado dá sempre o mesmo efeito?
  - Episódico ou sequencial: a decisão de agora afeta as decisões seguintes?
  - Estático ou dinâmico: o ambiente muda enquanto o agente delibera?
  - Discreto ou contínuo: estados e ações são contáveis?
  - Conhecido ou desconhecido: o agente sabe de antemão as regras? (Trata do
    que ele SABE, não do que ele VÊ.)
  Cada classificação vem com uma frase de justificativa — a etiqueta sozinha
  não vale nada.
-->
**Quando se preenche:** no Laboratório 02, no sábado (encontro 2).

- Parcialmente observável: Existem variáveis não medidas que mudam a decisão correta, como histórico da máquina específica e condições do ambiente.
- Multiagente: O técnico reage à recomendação e decide segui-la ou não.
- Estocástico: O agente lê texto usando um LLM (ação estocástica) e sua recomendação pode ser seguida ou ignorada pelo técnico.
- Sequencial: A recomendação atual pode mudar o estado futuro da máquina e a confiança do técnico nas recomendações seguintes.
- Dinâmico: As máquinas podem falhar depois da criação da ordem de serviço, e a demora na resposta impacta a experiência dos técnicos.
- Discreto e contínuo: Ações são discretas (recomendações), mas os estados das máquinas são contínuos.
- Conhecido: O agente sabe que tipos de máquina existem e quais normas deve seguir.

---

## 3. Tipo de agente pretendido

<!--
Perguntas que guiam o preenchimento:
  - O tipo mais simples que resolve: reativo simples, baseado em modelo,
    baseado em objetivos, baseado em utilidade, ou um deles com aprendizagem?
  - A caracterização do ambiente (seção 2) é que decide — parcialmente
    observável elimina o reativo simples.
  - Justifique com a dimensão do ambiente que obriga a escolha.
-->
**Quando se preenche:** no sábado (encontro 2, manhã).

Baseado em utilidade, com memória ligada à máquina.

O ambiente parcialmente observável elimina o reativo simples: nem toda falha aparece na leitura do instante, então o agente precisa de estado interno. O estado interno sozinho não basta: como o custo de cada erro é diferente, a decisão precisa pesar a chance de falha contra esse custo. Com os custos da seção 1, parar compensa acima de 16,7% de chance de falha, e inspecionar, acima de 12,5%.

A linha de base do lab 06 é baseada em modelo, com duas regras reativas e memória por ciclo de ferramenta. Seus erros mostram o que falta: ela olha uma variável por vez, e a memória indica risco na ferramenta, mas não separa o caso que vai falhar do que não vai.

---

## 4. Medida de desempenho

<!--
Perguntas que guiam o preenchimento:
  - A fórmula do campo Performance, agora em definição operacional: como se
    calcula, passo a passo, sem ambiguidade?
  - Métrica primária e duas secundárias. As secundárias pegam o que a
    primária deixa passar (custo, latência, reabertura).
  - O conjunto de casos: de onde vêm, quantos são, de que período.
  - O limiar de sucesso e o valor de hoje.
-->
**Quando se preenche:** a fórmula começa no Laboratório 01; a definição
operacional completa — primária, secundárias, conjunto e limiar — é item da
Atividade Orientada.

Valores de hoje: linha de base do lab 06 (`python -m ams.baseline`).

| Métrica | Como se calcula | Limiar de sucesso | Hoje (30 casos) | Hoje (AI4I inteiro) |
|---|---|---|---:|---:|
| Primária: horas perdidas | hd + hf + hi, em múltiplos de Tm (seção 1) | Menos que o melhor agente simples: 21 Tm nos 30 casos e 1695 Tm no AI4I inteiro | 10,0 Tm | 2044 Tm |
| Secundária: acerto da decisão | Casos com decisão igual à `acao_correta`, sobre o total | Mais que a linha de base | 23/30 | Não se aplica: o AI4I não tem esse rótulo |
| Secundária: falhas sem aviso | Falhas em que o agente decidiu seguir operando, sobre o total de falhas | Menos que a linha de base | 1/6 | 102/339 |

Conjuntos: 30 casos do AI4I (`casos-dataset.csv`), com 6 falhas (20%), e as 10.000 ordens do AI4I (3,4% de falhas). Os 30 casos foram escolhidos para testar o agente e mostram onde ele erra. O AI4I inteiro mostra quanto ele vale: a linha de base vence nos 30 casos, mas perde para "nunca recomendar" no AI4I inteiro.

---

## 5. Restrições

<!--
Perguntas que guiam o preenchimento:
  - Latência aceitável: a partir de quantos segundos a resposta perde valor?
  - Custo aceitável: quanto pode custar cada resolução?
  - O que o agente jamais pode fazer: a ação irreversível que ele não executa
    sozinho. Esta linha vira política em D12.
  - A troca que você aceita: quanto de qualidade por quanto de custo?
    Um exemplo numérico vale mais que a fórmula.
-->
**Quando se preenche:** na Atividade Orientada.

[latência aceitável, custo aceitável, o que o agente jamais
pode fazer sozinho, e a troca qualidade × custo que você
aceita — com um exemplo numérico]

---

## 6. Catálogo de ações

<!--
Perguntas que guiam o preenchimento:
  - Para cada ação: nome, entrada, saída, é reversível?, qual o risco se
    errar? As quatro colunas são obrigatórias — "baixo" não é descrição de
    risco.
  - Ações de leitura E de escrita: as que alteram o mundo são as que exigem
    cuidado, e são justamente as que mais ficam de fora.
  - Este catálogo é, literalmente, a lista de ferramentas que você vai
    implementar em D10.
-->
**Quando se preenche:** na Atividade Orientada — o pacote `D2-07` traz o
modelo da tabela e dois exemplos preenchidos.

[tabela: nome · entrada · saída · é reversível? · risco se
errar — ações de leitura e de escrita]

---

## 7. Formulação por busca

<!--
Perguntas que guiam o preenchimento:
  - Qual fatia do problema é um espaço de estados? (Nem toda fatia é — e
    reconhecer a que não é vale tanto quanto formular a que é.)
  - Os cinco componentes: estado inicial, ações, modelo de transição, teste
    de objetivo, custo de caminho. Comece pelo teste de objetivo.
  - O estado descreve a SITUAÇÃO, não a história de como se chegou nela.
-->
**Quando se preenche:** no Laboratório 03, sábado à tarde (encontro 2).

  - Estado: o par (itens conferidos, pendências abertas), cada um como tupla ordenada — a situação no posto, não a ordem em que se chegou nela.
  - Estado inicial: nada conferido, nenhuma pendência aberta.
  - Ações: conferir um item ainda não conferido e liberado (pré-requisitos concluídos), ou resolver uma pendência aberta.
  - Transição: conferir soma o item aos conferidos e abre as pendências dele; resolver tira a pendência das abertas.
  - Objetivo: todos os itens conferidos E nenhuma pendência aberta — só então a intervenção é liberada.
  - Custo: minutos de cada ação (estimativas, não medições).
