"""Testes do Laboratório 06 — a prova de que o baseline e a medição estão de pé.

Como usar (da pasta do laboratório):
    python -m pytest teste.py -q

Quatro famílias:

  1. AS REGRAS — cada condição de `decidir` dispara no caso que a define,
     e a ORDEM das condições importa (a primeira que casa decide);
  2. O ESTADO INTERNO — falhas contam dentro do ciclo de ferramenta e somem
     quando a ferramenta é trocada; sem desfecho, o estado não muda;
  3. O CONJUNTO E A MÉTRICA — os 30 casos do AMS, os custos das horas
     perdidas e os agentes simples;
  4. A TROCA — o mesmo medidor rodando sobre OUTRO arquivo de casos, sem
     tocar em código: a troca do conjunto é uma linha (slide 29).

O gabarito 25/30 da reserva saiu junto com as colunas do exemplo.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from collections import Counter
from pathlib import Path

from medir import agentes_simples, custo_da_decisao, medir

_AQUI = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location("esqueleto", _AQUI / "esqueleto.py")
esqueleto = importlib.util.module_from_spec(_spec)
sys.modules["esqueleto"] = esqueleto
_spec.loader.exec_module(esqueleto)  # type: ignore[union-attr]

_CASOS = _AQUI / esqueleto.CAMINHO_DOS_CASOS


def _registro(**mudancas) -> dict:
    base = {"udi": 1, "ciclo": 1, "tipo_maquina": "L",
            "desgaste_min": 100.0, "delta_temperatura_k": 10.0,
            "rotacao_rpm": 1500.0, "torque_nm": 40.0, "falhou_depois": 0}
    base.update(mudancas)
    return base


# --- 1. as regras -----------------------------------------------------------

def test_condicao_reativa_para_com_desgaste_alto():
    estado = esqueleto.EstadoDaFrota()
    decisao = esqueleto.decidir(_registro(desgaste_min=201.0), estado)
    assert decisao == "parar_para_manutencao"


def test_condicao_reativa_para_com_diferenca_de_temperatura_baixa():
    estado = esqueleto.EstadoDaFrota()
    decisao = esqueleto.decidir(_registro(delta_temperatura_k=8.5), estado)
    assert decisao == "parar_para_manutencao"


def test_os_limiares_exatos_nao_disparam():
    estado = esqueleto.EstadoDaFrota()
    decisao = esqueleto.decidir(
        _registro(desgaste_min=200.0, delta_temperatura_k=8.6), estado)
    assert decisao == "seguir_operando"


def test_estado_interno_inspeciona_apos_duas_falhas_no_ciclo():
    estado = esqueleto.EstadoDaFrota()
    estado.registrar_desfecho(_registro(falhou_depois=1))   # primeira falha
    assert esqueleto.decidir(_registro(), estado) == "seguir_operando"
    estado.registrar_desfecho(_registro(falhou_depois=1))
    decisao = esqueleto.decidir(_registro(), estado)
    assert decisao == "inspecionar_antes_de_operar"


def test_a_ordem_das_condicoes_importa():
    estado = esqueleto.EstadoDaFrota()
    for _ in range(2):
        estado.registrar_desfecho(_registro(falhou_depois=1))
    tudo_alto = _registro(desgaste_min=230.0, delta_temperatura_k=8.0)
    assert esqueleto.decidir(tudo_alto, estado) == "parar_para_manutencao", (
        "com leitura crítica, PARA — a condição reativa vem primeiro")


def test_a_decisao_nao_le_o_desfecho_nem_o_rotulo():
    estado = esqueleto.EstadoDaFrota()
    registro = _registro()
    del registro["falhou_depois"]
    assert esqueleto.decidir(registro, estado) == "seguir_operando"


# --- 2. o estado interno e o ciclo ------------------------------------------

def test_a_troca_de_ferramenta_zera_a_memoria():
    estado = esqueleto.EstadoDaFrota()
    for _ in range(2):
        estado.registrar_desfecho(_registro(ciclo=1, falhou_depois=1))
    decisao = esqueleto.decidir(_registro(ciclo=2), estado)
    assert decisao == "seguir_operando"


def test_sem_desfecho_o_estado_nao_muda():
    estado = esqueleto.EstadoDaFrota()
    estado.registrar_desfecho(_registro(falhou_depois=0))
    assert estado.falhas_no_ciclo(1) == 0


# --- 3. o conjunto e a métrica -----------------------------------------------

def test_os_custos_de_cada_decisao():
    assert custo_da_decisao("parar_para_manutencao", 1) == 0.0
    assert custo_da_decisao("parar_para_manutencao", 0) == 1.0
    assert custo_da_decisao("inspecionar_antes_de_operar", 1) == 1.5
    assert custo_da_decisao("inspecionar_antes_de_operar", 0) == 0.5
    assert custo_da_decisao("seguir_operando", 1) == 5.0
    assert custo_da_decisao("seguir_operando", 0) == 0.0


def test_o_conjunto_tem_30_casos_e_6_falhas():
    casos = esqueleto.carregar_casos(_CASOS)
    assert len(casos) == 30
    assert sum(r["falhou_depois"] for r in casos) == 6
    assert Counter(r["acao_correta"] for r in casos) == {
        "parar_para_manutencao": 6,
        "inspecionar_antes_de_operar": 4,
        "seguir_operando": 20,
    }


def test_agentes_simples_sobre_o_conjunto():
    assert agentes_simples(esqueleto.carregar_casos(_CASOS)) == {
        "sempre parar": 24.0,
        "sempre inspecionar": 21.0,
        "nunca parar": 30.0,
    }


def test_a_memoria_dispara_nos_dois_casos_da_sequencia_real():
    estado = esqueleto.EstadoDaFrota()
    decisoes = {}
    for registro in esqueleto.carregar_casos(_CASOS):
        decisoes[registro["grupo"]] = esqueleto.decidir(registro, estado)
        estado.registrar_desfecho(registro)
    assert decisoes["difícil: memória com falha"] == "inspecionar_antes_de_operar"
    assert decisoes["difícil: memória sem falha"] == "inspecionar_antes_de_operar"


def test_a_progressao_no_mesmo_ciclo_muda_a_decisao_no_fim():
    estado = esqueleto.EstadoDaFrota()
    decisoes = []
    for registro in esqueleto.carregar_casos(_CASOS):
        decisao = esqueleto.decidir(registro, estado)
        if registro["grupo"] == "fácil: progressão":
            decisoes.append(decisao)
        estado.registrar_desfecho(registro)
    assert decisoes == ["seguir_operando", "seguir_operando",
                        "parar_para_manutencao"]


# --- 4. a troca do conjunto é uma linha ---------------------------------------

def test_o_medidor_roda_sobre_outro_arquivo_sem_tocar_em_codigo(tmp_path):
    casos_novos = tmp_path / "meus_casos.csv"
    with casos_novos.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["id_caso", "udi", "ciclo", "tipo_maquina",
                           "desgaste_min", "delta_temperatura_k",
                           "rotacao_rpm", "torque_nm", "acao_correta",
                           "falhou_depois"])
        escritor.writerow(["M01", 1, 1, "L", 230, 10.0, 1500, 40.0,
                           "parar_para_manutencao", 1])
        escritor.writerow(["M02", 2, 2, "H", 100, 10.0, 1500, 40.0,
                           "seguir_operando", 0])
    resultado = medir(casos_novos)
    assert resultado["total"] == 2
    assert resultado["acertos"] == 2
    assert resultado["horas_perdidas"] == 0.0
