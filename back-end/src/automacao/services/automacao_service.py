"""
Serviço de automação de terminal mainframe IBM TN3270 em duas fases.
Executa os fluxos de consulta e extração de detalhes em matriz 24x80 sob operator_lock.
"""

import asyncio
import logging
from typing import Any, Dict, List

from automacao.core.config import settings
from automacao.core.security import operator_lock
from automacao.driver import parsers
from automacao.driver.driver_3270_interface import Base3270Driver
from automacao.driver.terminal import conectar_terminal_3270

logger = logging.getLogger("automacao.service.3270")


# pylint: disable=too-many-locals
def _navegar_ate_consulta_solicitante(
    driver: Base3270Driver,
    solicitante_matricula: str,
    solicitante_digito: str,
    solicitante_sequencia: str,
) -> None:
    """Navega pelos painéis do mainframe até a tela de consulta de solicitante."""
    # 1. Tela de Login
    driver.wait_for_string(parsers.GATILHO_TELA_LOGIN)
    r_mat, c_mat = parsers.POS_LOGIN_MATRICULA
    r_sen, c_sen = parsers.POS_LOGIN_SENHA
    driver.send_string(settings.APP_MATRICULA, row=r_mat, col=c_mat)
    driver.send_string(settings.APP_SENHA, row=r_sen, col=c_sen)
    driver.send_enter()

    # 2. Menu Principal
    driver.wait_for_string(parsers.GATILHO_TELA_MENU)
    r_menu, c_menu = parsers.POS_MENU_OPCAO
    driver.send_string(parsers.VALOR_MENU_OPCAO, row=r_menu, col=c_menu)
    driver.send_enter()

    # 3. Submenu
    driver.wait_for_string(parsers.GATILHO_TELA_SUBMENU)
    r_sub, c_sub = parsers.POS_SUBMENU_OPCAO
    driver.send_string(parsers.VALOR_SUBMENU_OPCAO, row=r_sub, col=c_sub)
    driver.send_enter()

    # 4. Tela de Solicitante
    driver.wait_for_string(parsers.GATILHO_TELA_SOLICITANTE)
    r_smat, c_smat = parsers.POS_SOLICITANTE_MATRICULA
    r_sdig, c_sdig = parsers.POS_SOLICITANTE_DIGITO
    r_sseq, c_sseq = parsers.POS_SOLICITANTE_SEQUENCIA
    driver.send_string(solicitante_matricula, row=r_smat, col=c_smat)
    driver.send_string(solicitante_digito, row=r_sdig, col=c_sdig)
    driver.send_string(solicitante_sequencia, row=r_sseq, col=c_sseq)
    driver.send_enter()

    # 5. Aguarda tela de listagem
    driver.wait_for_string(parsers.GATILHO_TELA_LISTA)


def _executar_busca_registros_sync(
    solicitante_matricula: str,
    solicitante_digito: str,
    solicitante_sequencia: str,
) -> Dict[str, Any]:
    """
    Fase 1 (Síncrona TN3270):
    Conecta ao mainframe, navega até a listagem, lê a matriz de registros e desconecta com PF3.
    """
    driver = conectar_terminal_3270()
    try:
        _navegar_ate_consulta_solicitante(
            driver, solicitante_matricula, solicitante_digito, solicitante_sequencia
        )

        registros = parsers.parse_lista_registros_3270(driver)

        # Envia PF3 para sair graciosamente
        driver.send_pf(3)
    finally:
        driver.disconnect()

    return {
        "solicitante": {
            "matricula": solicitante_matricula,
            "digito": solicitante_digito,
            "sequencia": solicitante_sequencia,
        },
        "registros": registros,
    }


def _executar_extracao_detalhes_sync(
    solicitante_matricula: str,
    solicitante_digito: str,
    solicitante_sequencia: str,
    indices_selecionados: List[int],
) -> List[Dict[str, Any]]:
    """
    Fase 2 (Síncrona TN3270):
    Conecta, navega até a listagem, preenche 'X' nas coordenadas dos registros selecionados,
    envia AID Enter e lê as telas de detalhes sequenciais.
    """
    driver = conectar_terminal_3270()
    detalhes_extraidos: List[Dict[str, Any]] = []

    try:
        _navegar_ate_consulta_solicitante(
            driver, solicitante_matricula, solicitante_digito, solicitante_sequencia
        )

        itens_na_tela = parsers.parse_lista_registros_3270(driver)

        # Marca com 'X' as linhas correspondentes aos índices solicitados
        qtd_marcados = 0
        for item in itens_na_tela:
            if item["indice"] in indices_selecionados:
                driver.send_string("X", row=item["row"], col=item["check_col"])
                qtd_marcados += 1

        # Submete a tela com todos os registros marcados de uma só vez via Enter
        driver.send_enter()

        # Lê os detalhes de cada registro marcado
        for idx in range(1, qtd_marcados + 1):
            driver.wait_for_string(parsers.GATILHO_TELA_DETALHE)
            dados = parsers.parse_detalhe_registro_3270(driver)
            detalhes_extraidos.append(dados)

            if idx < qtd_marcados:
                driver.send_enter()

        # Encerramento seguro via PF3
        driver.send_pf(3)
    finally:
        driver.disconnect()

    return detalhes_extraidos


class AutomacaoService:
    """Orquestrador assíncrono para os fluxos TN3270 em duas fases sob mutex."""

    async def buscar_registros(
        self,
        matricula: str,
        digito: str,
        sequencia: str,
    ) -> Dict[str, Any]:
        """Fase 1: Adquire a trava do operador e obtém a lista de registros via TN3270."""
        async with operator_lock.acquire():
            return await asyncio.to_thread(
                _executar_busca_registros_sync, matricula, digito, sequencia
            )

    async def extrair_detalhes(
        self,
        matricula: str,
        digito: str,
        sequencia: str,
        indices_selecionados: List[int],
    ) -> List[Dict[str, Any]]:
        """Fase 2: Adquire a trava do operador e extrai detalhes marcados via TN3270."""
        async with operator_lock.acquire():
            return await asyncio.to_thread(
                _executar_extracao_detalhes_sync,
                matricula,
                digito,
                sequencia,
                indices_selecionados,
            )


automacao_service = AutomacaoService()
