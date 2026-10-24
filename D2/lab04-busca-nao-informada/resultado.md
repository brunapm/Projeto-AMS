# Lab 04 — Busca não informada no checklist AMS

Formulação: `problemas.checklist_ams` (OS_CHAO e OS_ALTO).

## Comparação entre duas versões de checklist_ams.py (itens sem e com dependências)

- **Antes:** qualquer item podia ser verificado a qualquer momento. A ordem
  só influenciava o custo: verificar com pendência aberta custa o dobro
  (`fator_retrabalho = 2.0`). OS_CHAO: 7 itens, 6 pendências; OS_ALTO: 10 e 7.
- **Depois:** cada item pode declarar pré-requisitos (`requer`). A sequência
  de desenergização da NR-10 virou uma cadeia (EPI → seccionamento →
  ausência de tensão → bloqueio → aterramento), e as energias residuais
  dependem do bloqueio. Um item só fica disponível quando o anterior foi
  verificado **e** as pendências dele foram resolvidas. Entraram também dois
  itens independentes da cadeia (ferramentas isoladas, com pendência; pessoa
  de primeiros socorros, sem pendência), importantes nas NRs e para checar que
  `requer` não bloqueia o que não tem relação com a cadeia
  OS_CHAO: 9 itens, 7 pendências; OS_ALTO: 12 e 8.

## Resultados

### OS_CHAO — antes

| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| largura | 56.0 | 13 | 6556 | 6561 | 13 | 0.0151 |
| custo_uniforme | 47.0 | 13 | 6553 | 6561 | 13 | 0.0163 |
| profundidade_limitada(limite=32) | 56.0 | 13 | 14 | 13 | 13 | 0.0001 |
| aprofundamento_iterativo(limite=32) | 56.0 | 13 | 9491 | 39379 | 13 | 0.0755 |

### OS_CHAO — depois

| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| largura | 58.0 | 16 | 577 | 580 | 16 | 0.002 |
| custo_uniforme | 54.5 | 16 | 577 | 580 | 16 | 0.0017 |
| profundidade_limitada(limite=32) | 58.0 | 16 | 17 | 16 | 16 | 0.0001 |
| aprofundamento_iterativo(limite=32) | 58.0 | 16 | 1457 | 3662 | 16 | 0.0113 |

### OS_ALTO — antes

| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| largura | 87.0 | 17 | 107884 | 107892 | 17 | 0.2561 |
| custo_uniforme | 70.0 | 17 | 107875 | 107892 | 17 | 0.4074 |
| profundidade_limitada(limite=32) | 87.0 | 17 | 18 | 17 | 17 | 0.0001 |
| aprofundamento_iterativo(limite=32) | 87.0 | 17 | 148734 | 863153 | 17 | 2.1275 |

### OS_ALTO — depois

| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| largura | 89.0 | 20 | 11034 | 11040 | 20 | 0.033 |
| custo_uniforme | 77.5 | 20 | 11034 | 11040 | 20 | 0.0362 |
| profundidade_limitada(limite=32) | 89.0 | 20 | 21 | 20 | 20 | 0.0001 |
| aprofundamento_iterativo(limite=32) | 89.0 | 20 | 22197 | 92612 | 20 | 0.2581 |

## Antes × depois

O espaço de estados encolheu cerca de 10 vezes, mesmo com mais itens.
A largura expandiu 6556 → 577 nós na OS_CHAO e 107 884 → 11 034 na OS_ALTO.
Com o `requer`, `acoes()` oferece menos opções em cada estado (no estado
inicial da OS_CHAO, 4 ao invés de 7), e muitas combinações de "verificado /
aberto" deixam de ser alcançáveis. O aprofundamento iterativo, que reexpande
os níveis rasos a cada limite, foi o que mais ganhou: 2,1 s → 0,26 s na OS_ALTO.

### O custo ótimo subiu exatamente o valor dos itens novos.

47 → 54,5 e
70 → 77,5: a diferença é 1,5 + 5,0 + 1,0 (verificar ferramentas, substituir a
ferramenta, verificar primeiros socorros). Isso foi previsto antes de rodar e
confirma duas coisas: a ordem da NR-10 não impede o caminho ótimo (resolver
cada pendência logo que ela abre já respeita a cadeia), e os itens
independentes não foram bloqueados nem forçados a pagar retrabalho.

### A distância entre largura e custo uniforme diminuiu.

O retrabalho da largura caiu de 9 para 3,5 (OS_CHAO) e de 17 para 11,5 (OS_ALTO). Dentro da
cadeia NR-10, o `requer` obriga a resolver cada pendência antes de avançar,
então ali não há mais retrabalho possível. A largura agora só paga o dobro onde ainda há liberdade:
- nos itens livres do início: ela verifica as ferramentas (que abrem pendência)
  e, em seguida, primeiros socorros e EPI com a pendência ainda aberta
  (+1,0 +1,0); na OS_ALTO, também os três itens da NR-35 (+3 +2 +3);
- no ramo depois do bloqueio: aterramento e energias residuais ficam
  liberados juntos, e ela verifica os dois antes de resolver (+1,5).

## Por que o custo uniforme acha caminho mais barato que a largura

Pergunta: alguma busca achou caminho mais barato que a largura?
Resposta: sim, o custo uniforme, nas duas instâncias e nas duas versões.

1. **Todos os caminhos até o objetivo têm o mesmo número de ações.** Cada item
   é verificado uma vez e cada pendência é resolvida uma vez (16 ações na
   OS_CHAO, 20 na OS_ALTO). A largura garante o caminho com menos ações,
   e nesse critério todos empatam. O caminho que ela devolve é decidido pela
   ordem em que `acoes()` gera os sucessores (verificações antes de resoluções,
   na ordem da tupla de itens), não pelos minutos.
2. Os custos das ações não são uniformes. Verificar o mesmo item custa 1×
   ou 2× conforme haja pendência aberta, e as pendências custam de 2 a 15
   minutos. A largura só é ótima quando todo passo custa o mesmo. O custo
   uniforme expande sempre o nó de menor custo acumulado e testa o objetivo
   na retirada da fronteira, o que garante o caminho de menor custo total.
3. Nesse problema, a otimalidade sai de graça. Os nós expandidos são iguais, porque todos os
   objetivos estão na mesma profundidade e as duas buscas acabam varrendo
   quase todo o espaço antes de chegar lá. O custo uniforme gasta um pouco
   mais de tempo por nó (heap em vez de fila), mas a diferença é de milissegundos.

A profundidade limitada e o aprofundamento iterativo chegam ao mesmo caminho
da largura (58 e 89) pelo mesmo motivo: seguem a primeira ação gerada.

Vantagem aparente da profundidade limitada - `nos_expandidos` conta entradas na recursão, não os nós expandidos como as outras buscas, pois esse algoritmo não tem fronteira.