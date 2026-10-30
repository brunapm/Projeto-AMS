"""Agente de linha de base do AMS: regras explícitas, sem modelo de linguagem.

Percepção (o registro), decisão (regras), ação (a recomendação) e medida (as
horas perdidas do `agent-spec.md`, sobre 30 casos). O número que sai daqui é a
linha de base contra a qual o agente de D10 vai ser comparado.

As funções vêm do laboratório D2-06, em `D2/lab06-agente-baseline/`, e os casos
são gerados em `notebooks/casos-d2-lab06.ipynb`.

Uso:  python -m ams.baseline
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from ams.dados import RAIZ_DO_PACOTE

CAMINHO_DOS_CASOS = RAIZ_DO_PACOTE / "D2" / "lab06-agente-baseline" / "casos-dataset.csv"

PARAR = "parar_para_manutencao"
INSPECIONAR = "inspecionar_antes_de_operar"
SEGUIR = "seguir_operando"

# Os limiares vêm do `notebooks/01-eda.ipynb`. As regras exatas dos modos de falha
# ficam de fora: o AI4I foi gerado com elas, e copiá-las daria um número artificial.
LIMITE_DESGASTE = 200.0  # min: acima disso, para (pergunta 2)
DELTA_MINIMO = 8.6  # K: abaixo disso, para (pergunta 4)
FALHAS_PARA_INSPECAO = 2  # falhas observadas no ciclo: inspecionar

# Custos em múltiplos de Tm: estimativas, não medições. A falha custa mais que a
# manutenção porque é reativa: é preciso detectar, inspecionar, achar a causa e
# consertar. A manutenção é proativa, e a inspeção é mais rápida que ela.
TF = 5.0
TI = 0.5
# A inspeção detecta a falha em 80% das vezes (d = 0,8). Guardar a chance de
# escapar evita o erro de arredondamento de 1 − 0,8.
ESCAPE_DA_INSPECAO = 0.2


class EstadoDaFrota:
    """O que o agente já observou: falhas por ciclo de ferramenta.

    O ciclo é o que o AI4I tem de mais próximo de uma identidade de máquina. A
    política de esquecimento vem dos dados: a troca da ferramenta começa um ciclo novo.
    """

    def __init__(self) -> None:
        self._falhas: Counter[int] = Counter()

    def falhas_no_ciclo(self, ciclo: int) -> int:
        """Quantas falhas o agente viu neste ciclo de ferramenta."""
        return self._falhas[ciclo]

    def registrar_desfecho(self, registro: dict) -> None:
        """Guarda o desfecho que o ambiente revelou depois da decisão."""
        if int(registro.get("falhou_depois", 0)) == 1:
            self._falhas[registro["ciclo"]] += 1


def decidir(registro: dict, estado: EstadoDaFrota) -> str:
    """Uma rodada: percepção entra, ação sai.

    Primeiro a condição reativa, depois a condição com estado interno, mantida
    porque o ambiente é parcialmente observável. A primeira que casar decide.
    """
    if (
        registro["desgaste_min"] > LIMITE_DESGASTE
        or registro["delta_temperatura_k"] < DELTA_MINIMO
    ):
        return PARAR
    if estado.falhas_no_ciclo(registro["ciclo"]) >= FALHAS_PARA_INSPECAO:
        return INSPECIONAR
    return SEGUIR


def carregar_casos(caminho: str | Path) -> list[dict]:
    """Lê o CSV de casos rotulados na ordem do `udi`.

    A ordem importa, porque o estado interno se acumula caso a caso.
    """
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


def custo_da_decisao(decisao: str, falhou: int) -> float:
    """As horas perdidas numa decisão, em múltiplos de Tm.

    Parar antes de uma falha não custa, porque a manutenção era necessária.
    Inspecionar custa Ti sempre, e numa falha soma o custo esperado de ela
    escapar: Ti + (1 − d) × Tf.
    """
    if decisao == PARAR:
        return 0.0 if falhou else 1.0
    if decisao == INSPECIONAR:
        return TI + ESCAPE_DA_INSPECAO * TF if falhou else TI
    return TF if falhou else 0.0


def agentes_simples(casos: list[dict]) -> dict[str, float]:
    """As horas perdidas dos agentes simples, que o baseline precisa vencer."""
    return {
        nome: sum(custo_da_decisao(decisao, r["falhou_depois"]) for r in casos)
        for nome, decisao in (
            ("sempre parar", PARAR),
            ("sempre inspecionar", INSPECIONAR),
            ("nunca parar", SEGUIR),
        )
    }


def medir(caminho: str | Path = CAMINHO_DOS_CASOS) -> dict:
    """Roda o agente sobre os casos, um a um, e devolve o resultado da medição."""
    casos = carregar_casos(caminho)
    estado = EstadoDaFrota()
    acertos = 0
    horas = 0.0
    erros: list[dict] = []
    for registro in casos:
        decisao = decidir(registro, estado)
        correta = registro["acao_correta"]
        horas += custo_da_decisao(decisao, registro["falhou_depois"])
        if decisao == correta:
            acertos += 1
        else:
            erros.append({
                "id_caso": registro["id_caso"],
                "decidiu": decisao,
                "correta": correta,
                "grupo": registro.get("grupo", ""),
            })
        estado.registrar_desfecho(registro)
    total = len(casos)
    return {
        "caminho": str(caminho),
        "total": total,
        "horas_perdidas": horas,
        "agentes_simples": agentes_simples(casos),
        "acertos": acertos,
        "valor": acertos / total if total else 0.0,
        "distribuicao": dict(Counter(registro["acao_correta"] for registro in casos)),
        "erros": erros,
    }


def imprimir(resultado: dict) -> None:
    """Imprime a métrica, o valor, o conjunto e a lista de onde o agente erra."""
    print(
        "Métrica primária: horas perdidas (hd + hf + hi), em múltiplos de Tm, "
        "com Tf = 5 Tm, Ti = 0,5 Tm e d = 0,8; menor é melhor"
    )
    print(f"Valor: {resultado['horas_perdidas']} Tm")
    print(
        f"Conjunto: {resultado['caminho']} — {resultado['total']} casos "
        f"rotulados {resultado['distribuicao']}"
    )
    simples = ", ".join(
        f"{nome} = {horas} Tm" for nome, horas in resultado["agentes_simples"].items()
    )
    print(f"Agentes simples (a vencer): {simples}")
    print(
        f"Métrica secundária: acerto da decisão = {resultado['acertos']}/"
        f"{resultado['total']} = {round(resultado['valor'], 4)}"
    )
    print("Onde erra (o rótulo que o agente não deu):")
    for erro in resultado["erros"]:
        print(
            f"  caso {erro['id_caso']} ({erro['grupo']}): decidiu "
            f"{erro['decidiu']}, correto era {erro['correta']}"
        )


if __name__ == "__main__":
    imprimir(medir())
