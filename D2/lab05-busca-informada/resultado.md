# Lab 05 - Busca informada no checklist AMS

Formulação: `problemas.checklist_ams` (OS_CHAO e OS_ALTO).

## Resultados

### OS_CHAO

| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| largura | 58.0 | 16 | 577 | 580 | 16 | 0.002 |
| custo_uniforme | 54.5 | 16 | 577 | 580 | 16 | 0.0017 |
| profundidade_limitada(limite=32) | 58.0 | 16 | 17 | 16 | 16 | 0.0001 |
| aprofundamento_iterativo(limite=32) | 58.0 | 16 | 1457 | 3662 | 16 | 0.0113 |
| gulosa[admissivel] | 54.5 | 16 | 19 | 34 | 16 | 0.0003 |
| a_estrela[admissivel] | 54.5 | 16 | 469 | 528 | 16 | 0.0025 |
| gulosa[inadmissivel] | 54.5 | 16 | 19 | 34 | 16 | 0.0002 |
| a_estrela[inadmissivel] | 54.5 | 16 | 363 | 419 | 16 | 0.0019 |

### OS_ALTO

| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| largura | 89.0 | 20 | 11034 | 11040 | 20 | 0.033 |
| custo_uniforme | 77.5 | 20 | 11034 | 11040 | 20 | 0.0362 |
| profundidade_limitada(limite=32) | 89.0 | 20 | 21 | 20 | 20 | 0.0001 |
| aprofundamento_iterativo(limite=32) | 89.0 | 20 | 22197 | 92612 | 20 | 0.2581 |
| gulosa[admissivel] | 77.5 | 20 | 31 | 82 | 20 | 0.0005 |
| a_estrela[admissivel] | 77.5 | 20 | 9561 | 10240 | 20 | 0.0526 |
| gulosa[inadmissivel] | 77.5 | 20 | 31 | 82 | 20 | 0.0004 |
| a_estrela[inadmissivel] | 77.5 | 20 | 5635 | 6777 | 20 | 0.0345 |

### Comparação

A* e Gulosa encontraram o custo ótimo, assim como Custo Uniforme. Como o custo total é fixo (todos os itens e pendências são essenciais), esses três algoritmos foram capazes de encontrar caminhos que evitam verificar novos itens com pendências abertas. A* expandiu menos do que custo uniforme (469 contra 577 em OS_CHAO e 9561 contra 11034 em OS_ALTO). Isso era esperado, já que custo uniforme é um A* com h = 0 (ou seja, sem estimativa do que falta). A heurística admissível soma apenas os itens por verificar e as pendências já abertas, sem contar as pendências que esses itens ainda vão abrir. Por isso, ela estima baixo e a economia foi pequena (19% e 13%).

### Dominância

A heurística inadmissível domina a admissível, pois ela estima mais alto em todo estado (dobro do custo estimado pela admissível). O efeito da estimativa dobrada aparece no número de nós expandidos pelo A* - 363 contra 469 em OS_CHAO, e 5635 contra 9561 em OS_ALTO. Isso acontece porque com estimativa mais alta o algoritmo adia explorar certos nós. Essa superestimativa, porém, não garante o caminho de menor custo na busca, já que pode deixar de expandir nós que encontrariam um caminho melhor devido ao custo mais alto estimado. Como todos os itens e pendências são obrigatórios na definição do problema, diferentes ordens são ótimas.