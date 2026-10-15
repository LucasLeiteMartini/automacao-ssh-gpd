"""
Serviço de automação de terminal legado em duas fases.
Executa os fluxos de consulta e extração de detalhes sob proteção do operador_lock.
"""

import asyncio
import logging
from typing import Any, Dict, List

from automacao.core.config import settings
from automacao.core.security import operator_lock
from automacao.driver import parsers
from automacao.driver.terminal import TerminalDriver, conectar_terminal

logger = logging.getLogger("automacao.service")


def _navegar_ate_consulta_solicitante(
    term: TerminalDriver,
    solicitante_matricula: str,
    solicitante_digito: str,
    solicitante_sequencia: str,
) -> None:
    """Realiza o handshake de login e navega pelos menus até a tela de consulta do solicitante."""
    # 1. Tela Inicial
    term.esperar(parsers.PROMPT_INICIAL)
    term.send(f"{parsers.OPCAO_LOGIN}\n")

    # 2. Autenticação na Aplicação
    term.esperar(parsers.PROMPT_LOGIN_MATRICULA)
    term.send(f"{settings.APP_MATRICULA}\n")

    term.esperar(parsers.PROMPT_LOGIN_SENHA)
    term.send(f"{settings.APP_SENHA}\n")

    # 3. Menu Principal
    term.esperar(parsers.PROMPT_MENU_PRINCIPAL)
    term.send(f"{parsers.OPCAO_MENU_PRINCIPAL}\n")

    # 4. Submenu
    term.esperar(parsers.PROMPT_SUBMENU)
    term.send(f"{parsers.OPCAO_SUBMENU}\n")

    # 5. Entrada dos dados do solicitante
    term.esperar(parsers.PROMPT_SOLICITANTE_MATRICULA)
    term.send(f"{solicitante_matricula}\n")

    term.esperar(parsers.PROMPT_SOLICITANTE_DIGITO)
    term.send(f"{solicitante_digito}\n")

    term.esperar(parsers.PROMPT_SOLICITANTE_SEQUENCIA)
    term.send(f"{solicitante_sequencia}\n")


def _executar_busca_registros_sync(
    solicitante_matricula: str,
    solicitante_digito: str,
    solicitante_sequencia: str,
) -> Dict[str, Any]:
    """
    Fase 1 (Síncrona):
    Conecta, navega, lê os registros disponíveis e sai graciosamente sem marcar nada.
    """
    term = conectar_terminal()
    registros: List[Dict[str, Any]] = []

    try:
        _navegar_ate_consulta_solicitante(
            term, solicitante_matricula, solicitante_digito, solicitante_sequencia
        )

        buffer_tela_registros = ""
        while True:
            gatilho, tela = term.esperar_um_dos([
                parsers.PROMPT_ITEM_MARCAR,
                "Nenhum registro selecionado",
                parsers.PROMPT_ENCERRAMENTO_SESSAO,
            ])
            buffer_tela_registros += "\n" + tela
            if gatilho == parsers.PROMPT_ITEM_MARCAR:
                # Envia ENTER sem marcar com X para avançar
                term.send("\n")
            elif "Nenhum registro selecionado" in gatilho:
                term.send("\n")
                term.esperar(parsers.PROMPT_ENCERRAMENTO_SESSAO)
                break
            else:
                break

        # Extrai itens do buffer acumulado
        registros = parsers.parse_lista_registros(buffer_tela_registros)

    finally:
        term.close()

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
    Fase 2 (Síncrona):
    Conecta, navega até a listagem, seleciona os índices informados com 'X',
    e extrai os campos de cada tela de detalhe individual.
    """
    term = conectar_terminal()
    detalhes_extraidos: List[Dict[str, Any]] = []

    try:
        _navegar_ate_consulta_solicitante(
            term, solicitante_matricula, solicitante_digito, solicitante_sequencia
        )

        # Marcação dos registros
        item_atual = 1
        qtd_marcados = len(indices_selecionados)
        tela_detalhe_inicial = None

        while True:
            gatilho, tela = term.esperar_um_dos([
                parsers.PROMPT_ITEM_MARCAR,
                "DETALHE DO REGISTRO",
                "Nenhum registro selecionado",
                parsers.PROMPT_ENCERRAMENTO_SESSAO,
            ])

            if gatilho == parsers.PROMPT_ITEM_MARCAR:
                if item_atual in indices_selecionados:
                    term.send("X\n")
                else:
                    term.send("\n")
                item_atual += 1
            else:
                if gatilho == "DETALHE DO REGISTRO":
                    tela_detalhe_inicial = tela
                break

        # Leitura sequencial das telas de detalhes
        for idx in range(1, qtd_marcados + 1):
            if idx == 1 and tela_detalhe_inicial is not None:
                tela_detalhe = tela_detalhe_inicial
            else:
                tela_detalhe = term.esperar(f"DETALHE DO REGISTRO ({idx} de {qtd_marcados})")

            dados = parsers.parse_detalhe_registro(tela_detalhe)
            detalhes_extraidos.append(dados)
            # Envia ENTER para avançar para a próxima tela
            term.send("\n")

        # Aguarda encerramento
        try:
            term.esperar(parsers.PROMPT_ENCERRAMENTO_SESSAO, timeout=2.0)
        except Exception:
            pass

    finally:
        term.close()

    return detalhes_extraidos


class AutomacaoService:
    """Orquestrador assíncrono para os fluxos em duas fases sob mutex."""

    async def buscar_registros(
        self,
        matricula: str,
        digito: str,
        sequencia: str,
    ) -> Dict[str, Any]:
        """Fase 1: Adquire a trava do operador e obtém a lista de registros."""
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
        """Fase 2: Adquire a trava do operador e extrai detalhes dos itens marcados."""
        async with operator_lock.acquire():
            return await asyncio.to_thread(
                _executar_extracao_detalhes_sync,
                matricula,
                digito,
                sequencia,
                indices_selecionados,
            )


automacao_service = AutomacaoService()
