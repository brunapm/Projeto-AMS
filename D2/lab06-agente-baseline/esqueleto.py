"""Laboratório 06 — o agente de linha de base do seu domínio.

O agente mais simples que resolve uma fatia do problema, SEM modelo de
linguagem: percepção (o registro), decisão (regras explícitas), ação (a
recomendação) e medida (a métrica primária do `agent-spec.md`, sobre 30
casos). O número que sai daqui é a linha de base contra a qual o agente de
D10 vai ser comparado — sem ela, "melhorou" é opinião.

Estrutura do slide 22 do D2-E4: uma função `decidir(registro, estado)` com
duas condições — a primeira REATIVA (só a percepção do instante) e a
segunda consultando ESTADO INTERNO (o que o agente já observou do mundo).
Quem caracterizou o ambiente como totalmente observável pode APAGAR a
segunda condição e ficar com um reativo simples — e registra a escolha na
análise, porque o tipo de agente é parte do que a rubrica avalia.

Como usar:
    1. rode:  python medir.py
    2. quando o baseline estiver pronto, copie as funções para
       `src/<projeto>/baseline.py` — é o caminho que a entrega final cobra.

Adaptado ao AMS: os 30 casos vêm do AI4I (`casos-dataset.csv`, gerado em
`notebooks/casos-d2-lab06.ipynb`). As variáveis do exemplo que não existem
no AI4I saíram (vibração, idade, horas desde a manutenção), e a temperatura
virou a diferença processo − ar. O conjunto de reserva usa as colunas antigas
e não roda mais neste módulo.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

# --------------------------------------------------------------------------
# Configuração — a troca do dataset é UMA LINHA aqui (slide 29).
# --------------------------------------------------------------------------
CAMINHO_DOS_CASOS = "casos-dataset.csv"

# --------------------------------------------------------------------------
# Os limiares das regras — os do `notebooks/01-eda.ipynb`. As regras exatas
# dos modos de falha do AI4I ficam de fora: copiá-las daria um número alto
# e artificial, porque o dataset sintético foi gerado com elas.
# --------------------------------------------------------------------------
LIMITE_DESGASTE = 200.0        # min — acima disso, para (pergunta 2)
DELTA_MINIMO = 8.6             # K   — abaixo disso, para (pergunta 4)
FALHAS_PARA_INSPECAO = 2       # falhas observadas no ciclo → inspecionar

# --------------------------------------------------------------------------
# Estado interno — a memória do que o agente JÁ OBSERVOU do ambiente.
# O agente não sabe o futuro: ele acumula os desfechos que o ambiente
# revelou até agora. A memória é por ciclo de ferramenta, o que o AI4I tem de
# mais próximo de uma identidade de máquina. A política de esquecimento vem
# dos dados: a troca da ferramenta começa um ciclo novo, sem falhas.
# --------------------------------------------------------------------------


class EstadoDaFrota:
    """O que o agente já observou: falhas por ciclo de ferramenta."""

    def __init__(self) -> None:
        self._falhas: Counter[int] = Counter()

    def falhas_no_ciclo(self, ciclo: int) -> int:
        """Quantas falhas o agente viu neste ciclo de ferramenta."""
        return self._falhas[ciclo]

    def registrar_desfecho(self, registro: dict) -> None:
        """O ambiente revela o desfecho do caso — a percepção do próximo
        ciclo é maior do que a do anterior (parcialmente observável). Sem
        desfecho observado, não há o que registrar."""
        if int(registro.get("falhou_depois", 0)) == 1:
            self._falhas[registro["ciclo"]] += 1


# --------------------------------------------------------------------------
# A decisão — o coração do agente, em oito linhas (slide 22)
# --------------------------------------------------------------------------

def decidir(registro: dict, estado: EstadoDaFrota) -> str:
    """Uma rodada: percepção entra, ação sai.

    Primeiro a condição reativa, com os limiares sobre o REGISTRO atual.
    Depois a condição com estado interno, mantida porque o ambiente é
    parcialmente observável (`agent-spec.md`, seção 2). `ciclo` identifica a
    ferramenta em uso: o AI4I não identifica máquinas.
    A ordem importa: a primeira que casar decide.
    """
    if registro["desgaste_min"] > LIMITE_DESGASTE or \
            registro["delta_temperatura_k"] < DELTA_MINIMO:
        return "parar_para_manutencao"
    if estado.falhas_no_ciclo(registro["ciclo"]) >= FALHAS_PARA_INSPECAO:
        return "inspecionar_antes_de_operar"
    return "seguir_operando"


def carregar_casos(caminho: str | Path) -> list[dict]:
    """Lê o CSV de casos rotulados, na ordem do `udi` — a ordem importa,
    porque o estado interno se acumula caso a caso. encoding utf-8-sig:
    tolera o BOM que o Excel costuma gravar."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        casos = list(csv.DictReader(arquivo))
    casos.sort(key=lambda registro: int(registro["udi"]))
    for registro in casos:
        registro["udi"] = int(registro["udi"])
        registro["ciclo"] = int(registro["ciclo"])
        registro["desgaste_min"] = float(registro["desgaste_min"])
        registro["delta_temperatura_k"] = float(registro["delta_temperatura_k"])
        registro["rotacao_rpm"] = float(registro["rotacao_rpm"])
        registro["torque_nm"] = float(registro["torque_nm"])
        registro["falhou_depois"] = int(registro["falhou_depois"])
    return casos


if __name__ == "__main__":
    from medir import medir_e_imprimir

    medir_e_imprimir(CAMINHO_DOS_CASOS, decidir, EstadoDaFrota)
