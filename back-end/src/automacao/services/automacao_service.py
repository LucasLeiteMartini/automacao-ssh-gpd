"""
Serviço de automação de terminal mainframe IBM TN3270 (PRODAM / SPPC - CONFER).
Executa os fluxos de consulta de férias e cálculo de saldo em matriz 24x80 sob operator_lock.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Tuple

from automacao.core.config import settings
from automacao.core.security import (
    CadastroInexistenteError,
    TerminalTimeoutError,
    operator_lock,
)
from automacao.driver import parsers
from automacao.driver.driver_3270_interface import Base3270Driver
from automacao.driver.terminal import conectar_terminal_3270

logger = logging.getLogger("automacao.service.3270")


def _aguardar_tela_solicitante(driver: Base3270Driver) -> None:
    """
    Aguarda o carregamento da 5ª tela (pedido de Matrícula, Dígito e Sequência),
    que é comum a todas as opções de consulta (4, 9, 10, 13 e 16).
    """
    inicio = time.time()
    timeout = settings.TERMINAL_TIMEOUT_SECONDS
    while time.time() - inicio < timeout:
        if (
            driver.find_string(parsers.GATILHO_TELA_SOLICITANTE) is not None
            or driver.find_string("Matric D") is not None
        ):
            return
        time.sleep(0.05)

    raise TerminalTimeoutError(
        "Tempo limite excedido aguardando a tela de identificação do servidor (Matric D Seq)."
    )


def _aguardar_lista_ou_erro_confer(driver: Base3270Driver) -> None:
    """
    Aguarda o retorno da consulta na 5ª tela:
    - Se a linha 1 apresentar erro ('>>> Matricula Inexiste no Cadastro' ou prefixo '>>>'),
      interrompe imediatamente lançando CadastroInexistenteError.
    - Se carregar a 6ª tela de listagem (gatilho de lista, Nome preenchido na linha 6 ou
      aviso 'Não existem ...' na linha 1), retorna normalmente.
    """
    inicio = time.time()
    timeout = settings.TERMINAL_TIMEOUT_SECONDS
    while time.time() - inicio < timeout:
        linha_erro = driver.get_string(1, 1, 80).strip()
        linha_lower = linha_erro.lower()
        if (
            parsers.GATILHO_MATRICULA_INEXISTENTE.lower() in linha_lower
            or linha_erro.startswith(parsers.PREFIXO_ERRO_TELA_SOLICITANTE)
        ):
            detalhe_limpo = linha_erro.lstrip("> ").strip()
            raise CadastroInexistenteError(
                f"Cadastro não encontrado ou inválido no SPPC/CONFER: {detalhe_limpo}"
            )

        cabecalho = parsers.parse_cabecalho_solicitante_3270(driver)
        if (
            driver.find_string(parsers.GATILHO_TELA_LISTA) is not None
            or cabecalho.get("nome") is not None
            or "não existem" in linha_lower
            or "nao existem" in linha_lower
        ):
            return

        time.sleep(0.05)

    raise TerminalTimeoutError(
        "Tempo limite excedido aguardando retorno da consulta na tela SPPC/CONFER."
    )


# pylint: disable=too-many-locals
def _navegar_ate_consulta_solicitante(
    driver: Base3270Driver,
    solicitante_matricula: str,
    solicitante_digito: str,
    solicitante_sequencia: str,
    opcao_consulta: str = "10",
) -> None:
    """
    Navega pelos 5 painéis reais do mainframe PRODAM/SPPC até carregar a listagem do servidor:
    1ª Tela (PRODAM) -> 2ª Tela (CICSCNTR) -> 3ª Tela (CEUSPL02) ->
    4ª Tela (SPPC/CONSULTA) -> 5ª Tela (Matric D Seq).
    """
    # 1ª Tela: Seleção de Aplicação PRODAM
    driver.wait_for_string(parsers.GATILHO_TELA_APLICACAO)
    r_app, c_app = parsers.POS_APLICACAO_OPCAO
    driver.send_string(parsers.VALOR_APLICACAO_OPCAO, row=r_app, col=c_app)
    driver.send_enter()

    # 2ª Tela: Login CICS (CICSCNTR - IDENT e SENHA)
    driver.wait_for_string(parsers.GATILHO_TELA_LOGIN)
    r_mat, c_mat = parsers.POS_LOGIN_MATRICULA
    r_sen, c_sen = parsers.POS_LOGIN_SENHA
    driver.send_string(settings.APP_MATRICULA, row=r_mat, col=c_mat)
    driver.send_string(settings.APP_SENHA, row=r_sen, col=c_sen)
    driver.send_enter()

    # 3ª Tela: Menu de Sistemas (CEUSPL02)
    driver.wait_for_string(parsers.GATILHO_TELA_MENU)
    r_menu, c_menu = parsers.POS_MENU_OPCAO
    driver.send_string(parsers.VALOR_MENU_OPCAO, row=r_menu, col=c_menu)
    driver.send_enter()

    # 4ª Tela: Menu de Consultas (SPPC/CONSULTA)
    driver.wait_for_string(parsers.GATILHO_TELA_SUBMENU)
    r_sub, c_sub = parsers.POS_SUBMENU_OPCAO
    opcao_submenu = (opcao_consulta or parsers.VALOR_SUBMENU_OPCAO).strip()
    driver.send_string(opcao_submenu, row=r_sub, col=c_sub)
    driver.send_enter()
    if driver.find_string(parsers.GATILHO_TELA_SUBMENU) is not None:
        driver.send_pf(parsers.TECLA_PF_AVANCAR_PAGINA)
        driver.send_string(opcao_submenu, row=r_sub, col=c_sub)
        driver.send_enter()

    # 5ª Tela: Identificação do Servidor (Matric D Seq é comum a todas as consultas)
    _aguardar_tela_solicitante(driver)
    chave_concatenada = (
        f"{solicitante_matricula}{solicitante_digito}{solicitante_sequencia.upper()}"
    )
    driver.send_string(chave_concatenada)
    if opcao_submenu == "10" and parsers.VALOR_SOLICITANTE_SITUACAO:
        r_sit, c_sit = parsers.POS_SOLICITANTE_SITUACAO
        driver.send_string(parsers.VALOR_SOLICITANTE_SITUACAO, row=r_sit, col=c_sit)
    driver.send_enter()

    # 6ª Tela: Verifica erro na linha 1 (ex: '>>> Matricula Inexiste no Cadastro') ou listagem
    _aguardar_lista_ou_erro_confer(driver)


def _encerrar_sessao_sppc(driver: Base3270Driver) -> None:
    """
    Executa logoff seguro do mainframe enviando a tecla PF configurada duas vezes:
    - 1º PF retorna de qualquer tela do SPPC diretamente para a 3ª tela (CEUSPL02)
    - 2º PF na 3ª tela encerra a sessão
    """
    driver.send_pf(parsers.TECLA_PF_ENCERRAR)
    driver.send_pf(parsers.TECLA_PF_ENCERRAR)


def _executar_busca_registros_sync(
    solicitante_matricula: str,
    solicitante_digito: str,
    solicitante_sequencia: str,
    opcao_consulta: str = "10",
) -> Dict[str, Any]:
    """
    Fase 1 (Síncrona TN3270):
    Conecta ao mainframe, navega pelas 5 telas, lê cabeçalho e todas as páginas da tabela
    de férias com saldo, e encerra a sessão com duplo PF3 sempre no bloco finally.
    """
    driver = conectar_terminal_3270()
    try:
        _navegar_ate_consulta_solicitante(
            driver,
            solicitante_matricula,
            solicitante_digito,
            solicitante_sequencia,
            opcao_consulta=opcao_consulta,
        )

        cabecalho = parsers.parse_cabecalho_solicitante_3270(driver)
        registros = parsers.parse_lista_registros_3270(
            driver,
            paginar=True,
            opcao_consulta=opcao_consulta,
        )
    finally:
        try:
            _encerrar_sessao_sppc(driver)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        driver.disconnect()

    return {
        "solicitante": {
            "matricula": solicitante_matricula,
            "digito": solicitante_digito,
            "sequencia": solicitante_sequencia.upper(),
            "opcao_consulta": opcao_consulta,
            "nome": cabecalho.get("nome"),
            "lotacao": cabecalho.get("lotacao"),
        },
        "registros": registros,
    }


def _extrair_detalhes_pagina_atual(
    driver: Base3270Driver,
    alvos_pagina: List[Tuple[int, int]],
    detalhes_extraidos: List[Dict[str, Any]],
) -> None:
    """Marca os registros selecionados na página atual, abre NC5F M13A e retorna à lista."""
    for row_num, check_col in alvos_pagina:
        driver.send_string(
            parsers.CARACTERE_MARCACAO_REGISTRO,
            row=row_num,
            col=check_col,
        )

    driver.send_enter()

    for _ in alvos_pagina:
        driver.wait_for_string(parsers.GATILHO_TELA_DETALHE)
        dados = parsers.parse_detalhe_registro_3270(driver)
        detalhes_extraidos.append(dados)
        driver.send_enter()


def _executar_extracao_detalhes_sync(
    solicitante_matricula: str,
    solicitante_digito: str,
    solicitante_sequencia: str,
    indices_selecionados: List[int],
    opcao_consulta: str = "10",
) -> List[Dict[str, Any]]:
    """
    Fase 2 (Síncrona TN3270):
    Conecta, navega até a listagem SPPC/CONFER e percorre as páginas em sentido único
    (usando ENTER na opção 10), marcando os períodos selecionados na página em que aparecem
    e lendo as telas NC5F M13A correspondentes.
    """
    driver = conectar_terminal_3270()
    detalhes_extraidos: List[Dict[str, Any]] = []

    try:
        _navegar_ate_consulta_solicitante(
            driver,
            solicitante_matricula,
            solicitante_digito,
            solicitante_sequencia,
            opcao_consulta=opcao_consulta,
        )

        acumulado_periodos: Dict[Tuple[str, str], Dict[str, Any]] = {}
        historico_fatias: set[Tuple[str, ...]] = set()
        num_pagina = 1

        while num_pagina <= 50:
            linhas_tela = driver.get_screen_lines()
            fatia_atual = tuple(
                linhas_tela[
                    parsers.LINHA_INICIAL_REGISTROS - 1 : parsers.LINHA_FINAL_REGISTROS
                ]
            )
            if not any(l.strip() for l in fatia_atual) or fatia_atual in historico_fatias:
                break
            historico_fatias.add(fatia_atual)

            encontrados = parsers.ler_linhas_ferias_pagina_3270(
                linhas_tela, acumulado_periodos, num_pagina
            )
            alvos_pagina = [
                (row_idx, parsers.COLUNA_CHECKBOX_MARCAR)
                for row_idx, idx_per in encontrados
                if idx_per in indices_selecionados
            ]
            if alvos_pagina:
                _extrair_detalhes_pagina_atual(driver, alvos_pagina, detalhes_extraidos)

            if not encontrados:
                break

            linhas_pos = driver.get_screen_lines()
            fatia_pos = tuple(
                linhas_pos[
                    parsers.LINHA_INICIAL_REGISTROS - 1 : parsers.LINHA_FINAL_REGISTROS
                ]
            )
            if fatia_pos == fatia_atual:
                parsers.avancar_pagina_3270(driver, opcao_consulta=opcao_consulta)

            num_pagina += 1
            if (
                driver.get_string(1, 1, 80)
                .strip()
                .startswith(parsers.PREFIXO_ERRO_TELA_SOLICITANTE)
            ):
                break
    finally:
        try:
            _encerrar_sessao_sppc(driver)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        driver.disconnect()

    return detalhes_extraidos


class AutomacaoService:
    """Orquestrador assíncrono para os fluxos TN3270 sob mutex."""

    async def buscar_registros(
        self,
        matricula: str,
        digito: str,
        sequencia: str,
        opcao_consulta: str = "10",
    ) -> Dict[str, Any]:
        """Fase 1: Adquire a trava do operador e obtém a lista e saldo de férias via TN3270."""
        async with operator_lock.acquire():
            return await asyncio.to_thread(
                _executar_busca_registros_sync,
                matricula,
                digito,
                solicitante_sequencia=sequencia,
                opcao_consulta=opcao_consulta,
            )

    async def extrair_detalhes(
        self,
        matricula: str,
        digito: str,
        sequencia: str,
        indices_selecionados: List[int],
        opcao_consulta: str = "10",
    ) -> List[Dict[str, Any]]:
        """Fase 2: Adquire a trava do operador e extrai detalhes marcados via TN3270."""
        async with operator_lock.acquire():
            return await asyncio.to_thread(
                _executar_extracao_detalhes_sync,
                matricula,
                digito,
                sequencia,
                indices_selecionados,
                opcao_consulta=opcao_consulta,
            )


automacao_service = AutomacaoService()
