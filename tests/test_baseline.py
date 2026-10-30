"""Testes do agente de linha de base: as regras, o estado interno, a medição e a troca."""

import csv
from collections import Counter

from ams import baseline
from ams.baseline import EstadoDaFrota, decidir


def _registro(**mudancas) -> dict:
    base = {
        "udi": 1,
        "ciclo": 1,
        "tipo_maquina": "L",
        "desgaste_min": 100.0,
        "delta_temperatura_k": 10.0,
        "rotacao_rpm": 1500.0,
        "torque_nm": 40.0,
        "falhou_depois": 0,
    }
    base.update(mudancas)
    return base


# --- as regras ------------------------------------------------------------------


def test_condicao_reativa_para_com_desgaste_alto():
    assert decidir(_registro(desgaste_min=201.0), EstadoDaFrota()) == baseline.PARAR


def test_condicao_reativa_para_com_diferenca_de_temperatura_baixa():
    assert decidir(_registro(delta_temperatura_k=8.5), EstadoDaFrota()) == baseline.PARAR


def test_os_limiares_exatos_nao_disparam():
    registro = _registro(desgaste_min=200.0, delta_temperatura_k=8.6)
    assert decidir(registro, EstadoDaFrota()) == baseline.SEGUIR


def test_estado_interno_inspeciona_apos_duas_falhas_no_ciclo():
    estado = EstadoDaFrota()
    estado.registrar_desfecho(_registro(falhou_depois=1))
    assert decidir(_registro(), estado) == baseline.SEGUIR
    estado.registrar_desfecho(_registro(falhou_depois=1))
    assert decidir(_registro(), estado) == baseline.INSPECIONAR


def test_a_ordem_das_condicoes_importa():
    estado = EstadoDaFrota()
    for _ in range(2):
        estado.registrar_desfecho(_registro(falhou_depois=1))
    tudo_alto = _registro(desgaste_min=230.0, delta_temperatura_k=8.0)
    assert decidir(tudo_alto, estado) == baseline.PARAR


def test_a_decisao_nao_le_o_desfecho_nem_o_rotulo():
    registro = _registro()
    del registro["falhou_depois"]
    assert decidir(registro, EstadoDaFrota()) == baseline.SEGUIR


# --- o estado interno -----------------------------------------------------------


def test_a_troca_de_ferramenta_zera_a_memoria():
    estado = EstadoDaFrota()
    for _ in range(2):
        estado.registrar_desfecho(_registro(ciclo=1, falhou_depois=1))
    assert decidir(_registro(ciclo=2), estado) == baseline.SEGUIR


def test_sem_desfecho_o_estado_nao_muda():
    estado = EstadoDaFrota()
    estado.registrar_desfecho(_registro(falhou_depois=0))
    assert estado.falhas_no_ciclo(1) == 0


# --- o conjunto e a métrica -----------------------------------------------------


def test_os_custos_de_cada_decisao():
    assert baseline.custo_da_decisao(baseline.PARAR, 1) == 0.0
    assert baseline.custo_da_decisao(baseline.PARAR, 0) == 1.0
    assert baseline.custo_da_decisao(baseline.INSPECIONAR, 1) == 1.5
    assert baseline.custo_da_decisao(baseline.INSPECIONAR, 0) == 0.5
    assert baseline.custo_da_decisao(baseline.SEGUIR, 1) == 5.0
    assert baseline.custo_da_decisao(baseline.SEGUIR, 0) == 0.0


def test_o_conjunto_tem_30_casos_e_6_falhas():
    casos = baseline.carregar_casos(baseline.CAMINHO_DOS_CASOS)
    assert len(casos) == 30
    assert sum(r["falhou_depois"] for r in casos) == 6
    assert Counter(r["acao_correta"] for r in casos) == {
        baseline.PARAR: 6,
        baseline.INSPECIONAR: 4,
        baseline.SEGUIR: 20,
    }


def test_a_medicao_devolve_a_linha_de_base():
    resultado = baseline.medir()
    assert resultado["horas_perdidas"] == 10.0
    assert resultado["acertos"] == 23
    assert resultado["agentes_simples"] == {
        "sempre parar": 24.0,
        "sempre inspecionar": 21.0,
        "nunca parar": 30.0,
    }


def test_a_memoria_dispara_nos_dois_casos_da_sequencia_real():
    estado = EstadoDaFrota()
    decisoes = {}
    for registro in baseline.carregar_casos(baseline.CAMINHO_DOS_CASOS):
        decisoes[registro["grupo"]] = decidir(registro, estado)
        estado.registrar_desfecho(registro)
    assert decisoes["difícil: memória com falha"] == baseline.INSPECIONAR
    assert decisoes["difícil: memória sem falha"] == baseline.INSPECIONAR


def test_a_progressao_no_mesmo_ciclo_muda_a_decisao_no_fim():
    estado = EstadoDaFrota()
    decisoes = []
    for registro in baseline.carregar_casos(baseline.CAMINHO_DOS_CASOS):
        decisao = decidir(registro, estado)
        if registro["grupo"] == "fácil: progressão":
            decisoes.append(decisao)
        estado.registrar_desfecho(registro)
    assert decisoes == [baseline.SEGUIR, baseline.SEGUIR, baseline.PARAR]


# --- a troca do conjunto --------------------------------------------------------


def test_o_medidor_roda_sobre_outro_arquivo_sem_tocar_em_codigo(tmp_path):
    casos_novos = tmp_path / "meus_casos.csv"
    with casos_novos.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow([
            "id_caso", "udi", "ciclo", "tipo_maquina", "desgaste_min",
            "delta_temperatura_k", "rotacao_rpm", "torque_nm", "acao_correta",
            "falhou_depois",
        ])
        escritor.writerow(["M01", 1, 1, "L", 230, 10.0, 1500, 40.0, baseline.PARAR, 1])
        escritor.writerow(["M02", 2, 2, "H", 100, 10.0, 1500, 40.0, baseline.SEGUIR, 0])
    resultado = baseline.medir(casos_novos)
    assert resultado["total"] == 2
    assert resultado["acertos"] == 2
    assert resultado["horas_perdidas"] == 0.0
