# Lab 06 - Agente de linha de base no AMS

**Linha de base:** 10,0 Tm de horas perdidas em 30 casos do AI4I.

**Tipo de agente:** baseado em modelo, com duas regras reativas e estado interno. A segunda condição foi mantida porque o ambiente é parcialmente observável (`agent-spec.md`, seção 2).

## Medição

Saída de `medir.py`:

```text
Métrica primária: horas perdidas (hd + hf + hi), em múltiplos de Tm, com Tf = 5 Tm, Ti = 0,5 Tm e d = 0,8; menor é melhor
Valor: 10.0 Tm
Conjunto: casos-dataset.csv — 30 casos rotulados {'seguir_operando': 20, 'parar_para_manutencao': 6, 'inspecionar_antes_de_operar': 4}
Agentes simples (a vencer): sempre parar = 24.0 Tm, sempre inspecionar = 21.0 Tm, nunca parar = 30.0 Tm
Métrica secundária: acerto da decisão = 23/30 = 0.7667
Onde erra (o rótulo que o agente não deu):
  caso C05 (difícil: potência fora da faixa): decidiu seguir_operando, correto era parar_para_manutencao
  caso C10 (atípico: RNF): decidiu seguir_operando, correto era inspecionar_antes_de_operar
  caso C14 (difícil: memória com falha): decidiu inspecionar_antes_de_operar, correto era parar_para_manutencao
  caso C15 (difícil: memória sem falha): decidiu inspecionar_antes_de_operar, correto era seguir_operando
  caso C16 (difícil: desgaste alto sem falha): decidiu parar_para_manutencao, correto era inspecionar_antes_de_operar
  caso C25 (difícil: desgaste alto sem falha): decidiu parar_para_manutencao, correto era inspecionar_antes_de_operar
  caso C26 (difícil: desgaste alto sem falha): decidiu parar_para_manutencao, correto era inspecionar_antes_de_operar
```

## Análise

O agente erra em sua recomendação em 7 dos 30 casos (5, 10, 14, 15, 16, 25, 26). No caso 5, enquanto as variáveis observadas estavam dentro do esperado, a potência estava fora da faixa e o agente decidiu seguir operando (correto era parar para manutenção). O caso 10 é atípico: o registro está inconsistente, mas não houve falha, e nenhuma variável indica esse problema. Os casos 14 e 15 são relacionados à memória: no caso 14 havia uma falha e o agente decidiu inspecionar devido à memória enquanto o correto era parar (cauteloso de menos, apesar do erro aqui ser parcial); no caso 15 o agente decide inspecionar - aqui a memória atrapalhou, pois o correto era seguir (cauteloso demais). A memória indica risco, mas não separa o caso que vai falhar do que não vai. Os casos 16, 25 e 26 falham devido ao limite estabelecido para desgaste: como o desgaste estava alto, o agente decide parar para manutenção, mas o correto era inspecionar antes de operar.
Esses erros são sistemáticos: o agente olha uma variável por vez e conta falhas por ferramenta, sem combinar sinais nem pesar a chance de falha contra o custo de cada ação. Por isso, o problema exige um agente baseado em utilidade, com memória ligada à máquina.

### Onde cada erro acontece

| Casos | Decisão | Correto | Por quê |
|---|---|---|---|
| C05 | Seguir | Parar | Desgaste e diferença de temperatura estavam normais, mas a potência estava fora da faixa (9049 W), e o agente não observa potência. |
| C10 | Seguir | Inspecionar | O registro está marcado como RNF sem falha, um dado inconsistente. Nenhuma leitura indica o problema, e o agente não vê essa marcação. |
| C14 | Inspecionar | Parar | Havia uma falha, e a memória fez o agente inspecionar, mas o correto era parar (cauteloso de menos). Ainda assim, ela reduziu o custo de 5 para 1,5 Tm. |
| C15 | Inspecionar | Seguir | Não havia falha, e a memória gerou uma inspeção desnecessária de 0,5 Tm (cauteloso demais). |
| C16, C25 e C26 | Parar | Inspecionar | O desgaste passou do limite de 200 min, mas não houve falha: um limiar fixo não separa risco de falha. |

C14 e C15 mostram que a memória indica risco na ferramenta, mas não separa o caso que vai falhar do que não vai: os dois têm 2 falhas anteriores no ciclo, e as leituras deles só seriam separadas por uma combinação de sinais.

## Declarações

**Conjunto.** Usei 30 casos próprios do AI4I, não a reserva, gerados em `notebooks/casos-d2-lab06.ipynb` com semente fixa.

- O conjunto tem 6 falhas (20%), contra 3,4% no AI4I. Uma proporção real deixaria só 1 falha, sem casos difíceis.
- Duas sequências reais foram escolhidas de propósito: o ciclo 56, para testar a memória, e o ciclo 114, para mostrar a mesma ferramenta ao longo do tempo.
- Por isso, os 30 casos mostram se o mecanismo funciona, e não quanto ele vale em operação.

**Estimativas.** `Tf = 5 Tm`, `Ti = 0,5 Tm` e `d = 0,8` são suposições, não medições. Só a ordem falha > manutenção > inspeção vem do domínio: a falha é reativa e exige detectar, inspecionar, achar a causa e consertar, enquanto a manutenção é proativa e a inspeção é mais rápida que ela.

**Adaptações do esqueleto.** O AI4I não tem vibração, idade da máquina, horas desde a manutenção, data nem identificação de máquina.

- A memória usa o ciclo de ferramenta, que aproxima uma identidade de máquina. Os casos seguem a ordem do `udi`.
- `tipo_maquina` guarda a qualidade do produto (L, M ou H).
- A métrica primária é horas perdidas, a do `agent-spec.md`, e não o acerto da decisão.
