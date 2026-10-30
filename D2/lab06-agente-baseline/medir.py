"""medir.py — a medição da linha de base sobre os casos rotulados.

Roda o agente (a função `decidir` e o estado do `esqueleto.py`) sobre o
conjunto de casos, caso a caso, na ordem do `udi`, e imprime as três
informações que o slide 28 cobra que o aluno traga:

  1. A MÉTRICA — horas perdidas, a primária do `agent-spec.md`;
  2. O VALOR — quanto deu, em múltiplos do tempo médio de manutenção (Tm);
  3. O CONJUNTO — sobre quais casos, quantos são e como se distribuem.

E acrescenta a leitura mais valiosa (slide 30): ONDE o agente erra — a
lista dos casos com decisão diferente do rótulo, que é a matéria-prima da
análise escrita da entrega final.

As horas perdidas dependem da decisão e do desfecho (`falhou_depois`). O
rótulo `acao_correta` alimenta só o acerto, a métrica secundária, e a lista
de erros.

Uso:  python medir.py            (usa o CAMINHO_DOS_CASOS do esqueleto)
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import esqueleto

PARAR = "parar_para_manutencao"
INSPECIONAR = "inspecionar_antes_de_operar"
SEGUIR = "seguir_operando"

# Custos em múltiplos de Tm: estimativas, não medições. A falha custa mais que a
# manutenção porque é reativa: é preciso detectar, inspecionar, achar a causa e
# consertar. A manutenção é proativa, e a inspeção é mais rápida que ela.
TF = 5.0
TI = 0.5
# A inspeção detecta a falha em 80% das vezes (d = 0,8). Guardar a chance de
# escapar evita o erro de arredondamento de 1 − 0,8.
ESCAPE_DA_INSPECAO = 0.2


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
        for nome, decisao in (("sempre parar", PARAR),
                              ("sempre inspecionar", INSPECIONAR),
                              ("nunca parar", SEGUIR))
    }


def medir(caminho: str | Path, decidir=None, classe_estado=None) -> dict:
    """Roda o agente sobre os casos e devolve o resultado da medição.

    O agente decide caso a caso, na ordem do `udi`; depois de cada
    decisão, o ambiente revela o desfecho e o estado interno se atualiza —
    é o ciclo percepção → decisão → ação → observação do agente
    baseado em modelo. O caminho vem por parâmetro (a troca do conjunto é
    uma linha, slide 29); sem parâmetro, o configurado no esqueleto.
    """
    decidir = decidir or esqueleto.decidir
    classe_estado = classe_estado or esqueleto.EstadoDaFrota
    casos = esqueleto.carregar_casos(caminho)
    estado = classe_estado()
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
            erros.append({"id_caso": registro["id_caso"],
                          "decidiu": decisao, "correta": correta,
                          "grupo": registro.get("grupo", "")})
        estado.registrar_desfecho(registro)
    total = len(casos)
    rotulos = Counter(registro["acao_correta"] for registro in casos)
    return {
        "caminho": str(caminho),
        "total": total,
        "horas_perdidas": horas,
        "agentes_simples": agentes_simples(casos),
        "acertos": acertos,
        "valor": acertos / total if total else 0.0,
        "distribuicao": dict(rotulos),
        "erros": erros,
    }


def imprimir(resultado: dict, nome_da_metrica: str) -> None:
    """As três informações do slide 28, e a lista de onde erra (slide 30)."""
    print(f"Métrica primária: {nome_da_metrica}")
    print(f"Valor: {resultado['horas_perdidas']} Tm")
    print(f"Conjunto: {resultado['caminho']} — {resultado['total']} casos "
          f"rotulados {resultado['distribuicao']}")
    print("Agentes simples (a vencer): " + ", ".join(
        f"{nome} = {horas} Tm"
        for nome, horas in resultado["agentes_simples"].items()))
    print(f"Métrica secundária: acerto da decisão = {resultado['acertos']}/"
          f"{resultado['total']} = {round(resultado['valor'], 4)}")
    if resultado["erros"]:
        print("Onde erra (o rótulo que o agente não deu):")
        for erro in resultado["erros"]:
            print(f"  caso {erro['id_caso']} ({erro['grupo']}): decidiu "
                  f"{erro['decidiu']}, correto era {erro['correta']}")
    else:
        print("Onde erra: em nenhum dos casos — cuidado com um conjunto só "
              "de casos fáceis (slide 24: número bonito e inútil).")


def medir_e_imprimir(caminho: str | Path, decidir, classe_estado) -> None:
    resultado = medir(caminho, decidir, classe_estado)
    imprimir(resultado, "horas perdidas (hd + hf + hi), em múltiplos de Tm, "
                        "com Tf = 5 Tm, Ti = 0,5 Tm e d = 0,8; menor é melhor")


if __name__ == "__main__":
    medir_e_imprimir(esqueleto.CAMINHO_DOS_CASOS,
                     esqueleto.decidir, esqueleto.EstadoDaFrota)
