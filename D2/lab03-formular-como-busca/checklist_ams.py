"""AMS — o roteiro de segurança antes de uma intervenção, formulado como busca.

Adaptado do subproblema 3 do catálogo (roteiro de conformidade). A fatia
do AMS que é busca: em que ORDEM conferir as condições de segurança que as
NRs exigem e resolver as pendências encontradas, até liberar a intervenção
no menor tempo.

Item é uma CONDIÇÃO exigida pela norma ("bloqueio e etiquetagem
aplicados"); pendência é a CORREÇÃO quando a condição não é atendida
("aplicar cadeado e etiqueta"). Conferir é olhar se a condição vale;
resolver é fazer o que falta.

Duas instâncias, o mesmo caso de partida — o técnico chega à máquina sem
nada preparado; só a qualificação e autorização dele estão em ordem.
Verificar um item sempre abre as mesmas pendências (o caso é fixo).
  - OS_CHAO (NR-12 + NR-10): intervenção elétrica numa máquina no nível do
    chão. 7 itens, 6 pendências.
  - OS_ALTO (NR-12 + NR-10 + NR-35): a mesma intervenção, numa plataforma
    acima de 2 m. Soma os itens de altura; a análise de risco, a permissão
    de trabalho e a capacitação para altura já estão em ordem, o sistema de
    proteção contra quedas não. 10 itens, 7 pendências.

Granularidade: bloqueio e etiqueta são UM item (LOTO é um procedimento
só — a NR-12 exige os dois juntos), e análise de risco e permissão de
trabalho também (os dois documentos saem com o supervisor). Com eles
separados, a OS_ALTO passava de 50 000 estados.

Os cinco componentes:
  - Estado: o par (itens conferidos, pendências abertas), cada um como
    tupla ordenada — a situação no posto, não a ordem em que se chegou nela.
  - Estado inicial: nada conferido, nenhuma pendência aberta.
  - Ações: conferir um item ainda não conferido, ou resolver uma pendência
    aberta.
  - Transição: conferir soma o item aos conferidos e abre as pendências
    dele; resolver tira a pendência das abertas.
  - Objetivo: todos os itens conferidos E nenhuma pendência aberta — só
    então a intervenção é liberada.
  - Custo: minutos de cada ação (estimativas, não medições).

Por que a ordem importa: conferir um item com pendência aberta custa o
dobro (`fator_retrabalho` = 2.0) — enquanto a máquina ainda está
energizada ou sem bloqueio, a situação no posto vai mudar, e o que foi
conferido precisa ser reconfirmado depois. O caminho mais barato tende a
resolver cada pendência assim que ela abre, que é o que a prática de
segurança recomenda.

Simplificação declarada: a formulação torna a ordem errada mais cara, mas não impossível.
A NR-10 (item 10.13.1) exige a desenergização nesta sequência:
a) seccionamento ou desligamento;
b) constatação da ausência de tensão;
c) impedimento de reenergização;
d) constatação de ausência de tensão para a instalação de aterramento temporário com
equipotencialização dos condutores dos circuitos;
e) proteção dos elementos energizados existentes na zona controlada (Anexo II desta NR) e
proteção dos trabalhadores para os efeitos do arco elétrico;
f) instalação da sinalização de impedimento de reenergização; e
g) delimitação e sinalização da área de trabalho.

O que não é busca no AMS: classificar o risco de falha e escolher as NRs
aplicáveis — isso é classificação, não sequência de ações.

Fontes:
* NR-10: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/nr-10-atualizada-2026-1.pdf
* NR-12: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/arquivos/normas-regulamentadoras/nr-12-atualizada-2022-1.pdf
* NR-35: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/nr-35-atualizada-2025-1.pdf
"""

from __future__ import annotations

from dataclasses import dataclass

VERIFICAR = "verificar"
RESOLVER = "resolver"


@dataclass(frozen=True)
class Item:
    """Um item do roteiro de checagens."""

    nome: str
    esforco: float              # custo de verificar o item (minutos)
    abre: tuple[str, ...] = ()  # pendências que verificar este item abre


@dataclass(frozen=True)
class Pendencia:
    """Uma pendência que uma verificação pode abrir."""

    nome: str
    esforco: float              # custo de resolvê-la (minutos)

# NR-12 + NR-10: intervenção elétrica numa máquina no nível do chão
ITENS_NIVEL_CHAO: tuple[Item, ...] = (
    Item("técnico qualificado e autorizado", 2.0),
    Item("máquina parada e alimentação seccionada", 2.0, ("seccionar a alimentação",)),
    Item("bloqueio e etiquetagem aplicados", 2.0, ("aplicar cadeado e etiqueta",)),
    Item("ausência de tensão constatada", 2.5, ("medir com multímetro",)),
    Item("aterramento temporário instalado", 2.0, ("instalar o aterramento temporário",)),
    Item("energias residuais descarregadas (pneumática ou hidráulica)", 1.5, ("descarregar as energias residuais",)),
    Item("vestimenta e EPI adequados ao risco elétrico", 1.0, ("usar vestimenta e EPI adequados",)),
)
PENDENCIAS_NIVEL_CHAO: dict[str, float] = {
    "seccionar a alimentação": 3.0,
    "aplicar cadeado e etiqueta": 8.0,
    "medir com multímetro": 2.0,
    "instalar o aterramento temporário": 10.0,
    "descarregar as energias residuais": 7.0,
    "usar vestimenta e EPI adequados": 4.0,
}

# NR-12 + NR-10 + NR-35: intervenção elétrica numa máquina em plataforma acima de 2m
ITENS_NIVEL_ALTO: tuple[Item, ...] = (
    Item("técnico qualificado e autorizado", 2.0),
    Item("máquina parada e alimentação seccionada", 2.0, ("seccionar a alimentação",)),
    Item("bloqueio e etiquetagem aplicados", 2.0, ("aplicar cadeado e etiqueta",)),
    Item("ausência de tensão constatada", 2.5, ("medir com multímetro",)),
    Item("aterramento temporário instalado", 2.0, ("instalar o aterramento temporário",)),
    Item("energias residuais descarregadas (pneumática ou hidráulica)", 1.5, ("descarregar as energias residuais",)),
    Item("vestimenta e EPI adequados ao risco elétrico", 1.0, ("usar vestimenta e EPI adequados",)),
    Item("análise de risco do trabalho em altura e permissão de trabalho emitidas", 3.0),
    Item("trabalhador capacitado para altura", 2.0),
    Item("sistema de proteção contra quedas inspecionado", 3.0, ("instalar a linha de vida",)),
)
PENDENCIAS_NIVEL_ALTO: dict[str, float] = {
    "seccionar a alimentação": 3.0,
    "aplicar cadeado e etiqueta": 8.0,
    "medir com multímetro": 2.0,
    "instalar o aterramento temporário": 10.0,
    "descarregar as energias residuais": 7.0,
    "usar vestimenta e EPI adequados": 4.0,
    "instalar a linha de vida": 15.0,
}

class Conformidade:
    """O problema de busca: em que ordem verificar e resolver.

    O estado é o par (itens verificados, pendências abertas), cada um como
    tupla ordenada. As ações têm verbo no nome — `"verificar:<item>"` e
    `"resolver:<pendência>"` — para o caminho do Resultado ser legível.
    """

    def __init__(
        self,
        itens: tuple[Item, ...],
        pendencias: dict[str, float],
        fator_retrabalho: float = 2.0,
    ):
        self.itens = itens
        self.pendencias = pendencias
        self.fator_retrabalho = fator_retrabalho
        self._item_por_nome = {i.nome: i for i in itens}
        self.estado_inicial: tuple[tuple[str, ...], tuple[str, ...]] = ((), ())

    @staticmethod
    def _partes(acao: str) -> tuple[str, str]:
        verbo, _, nome = acao.partition(":")
        return verbo, nome

    def acoes(self, estado: tuple[tuple[str, ...], tuple[str, ...]]) -> list[str]:
        verificados, abertas = estado
        disponiveis = [f"{VERIFICAR}:{i.nome}" for i in self.itens if i.nome not in verificados]
        return disponiveis + [f"{RESOLVER}:{p}" for p in abertas]

    def transicao(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]], acao: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        verificados, abertas = estado
        verbo, nome = self._partes(acao)
        if verbo == VERIFICAR:
            novos_verificados = tuple(sorted((*verificados, nome)))
            novas_abertas = tuple(sorted((*abertas,
                                          *(p for p in self._item_por_nome[nome].abre
                                            if p not in abertas))))
            return novos_verificados, novas_abertas
        if verbo == RESOLVER:
            return verificados, tuple(p for p in abertas if p != nome)
        raise ValueError(f"ação desconhecida: {acao}")

    def objetivo(self, estado: tuple[tuple[str, ...], tuple[str, ...]]) -> bool:
        verificados, abertas = estado
        return len(verificados) == len(self.itens) and not abertas

    def custo(
        self,
        estado: tuple[tuple[str, ...], tuple[str, ...]],
        acao: str,
        estado_seguinte: tuple[tuple[str, ...], tuple[str, ...]],
    ) -> float:
        verbo, nome = self._partes(acao)
        if verbo == VERIFICAR:
            esforco = self._item_por_nome[nome].esforco
            _, abertas = estado
            if abertas:  # auditar com pendência em aberto obriga a rever
                return esforco * self.fator_retrabalho
            return esforco
        return self.pendencias[nome]

    def _trabalho_basico(self, estado: tuple[tuple[str, ...], tuple[str, ...]]) -> float:
        verificados, abertas = estado
        faltar_itens = sum(i.esforco for i in self.itens if i.nome not in verificados)
        fechar_abertas = sum(self.pendencias[p] for p in abertas)
        return faltar_itens + fechar_abertas

    def heuristica_admissivel(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]],
    ) -> float:
        """Esforço base do que falta: itens por verificar + pendências em aberto.

        Admissível: todo item que falta será verificado, e custa no mínimo o
        seu esforço base (o re-trabalho só aumenta); toda pendência aberta
        AGORA terá de ser resolvida, e resolver é a única forma de fechá-la.
        Ignora as pendências que as verificações futuras ainda vão abrir.
        """
        return self._trabalho_basico(estado)

    def heuristica_inadmissivel(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]],
    ) -> float:
        """O dobro do trabalho que falta — a "folga de segurança".

        NÃO é admissível, e é tentadora por isso: estimar com folga para
        "não ser pego de surpresa" superestima o caminho sempre que a folga
        passar do custo real (o lab-05 mede o que isso faz com o A*).
        """
        return 2.0 * self._trabalho_basico(estado)


OS_CHAO = Conformidade(ITENS_NIVEL_CHAO, PENDENCIAS_NIVEL_CHAO)
OS_ALTO = Conformidade(ITENS_NIVEL_ALTO, PENDENCIAS_NIVEL_ALTO)
