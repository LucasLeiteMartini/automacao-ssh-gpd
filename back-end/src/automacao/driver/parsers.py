"""
Mapeamento de prompts, gatilhos de navegação e parsers de tela.
Isola a estrutura do terminal legado para facilitar a adaptação do ambiente mock
para o ambiente de produção real sem alterar a camada de transporte SSH.
"""

import os
import re
from typing import Any, Dict, List

# ==============================================================================
# PROMPTS E GATILHOS DE TELA (CONFIGURÁVEIS VIA VARIÁVEIS DE AMBIENTE)
# ==============================================================================
PROMPT_INICIAL = os.getenv("PROMPT_INICIAL", "Escolha a opcao:")
OPCAO_LOGIN = os.getenv("OPCAO_LOGIN", "1")

PROMPT_LOGIN_MATRICULA = os.getenv("PROMPT_LOGIN_MATRICULA", "Matricula Operador:")
PROMPT_LOGIN_SENHA = os.getenv("PROMPT_LOGIN_SENHA", "Senha:")

PROMPT_MENU_PRINCIPAL = os.getenv("PROMPT_MENU_PRINCIPAL", "Selecione uma opcao (1-6):")
OPCAO_MENU_PRINCIPAL = os.getenv("OPCAO_MENU_PRINCIPAL", "5")

PROMPT_SUBMENU = os.getenv("PROMPT_SUBMENU", "Opcao desejada:")
OPCAO_SUBMENU = os.getenv("OPCAO_SUBMENU", "10")

PROMPT_SOLICITANTE_MATRICULA = os.getenv("PROMPT_SOLICITANTE_MATRICULA", "Matricula:")
PROMPT_SOLICITANTE_DIGITO = os.getenv("PROMPT_SOLICITANTE_DIGITO", "Digito:")
PROMPT_SOLICITANTE_SEQUENCIA = os.getenv("PROMPT_SOLICITANTE_SEQUENCIA", "Sequencia:")

PROMPT_ITEM_MARCAR = os.getenv("PROMPT_ITEM_MARCAR", "Marcar [X/ENTER pula]:")
PROMPT_ENCERRAMENTO_SESSAO = os.getenv("PROMPT_ENCERRAMENTO_SESSAO", "Sessao finalizada com sucesso.")

# Gatilhos de erro / bloqueio do legado
GATILHO_USUARIO_CONECTADO = os.getenv("GATILHO_USUARIO_CONECTADO", "usuario ja conectado")
GATILHO_ACESSO_NEGADO = os.getenv("GATILHO_ACESSO_NEGADO", "Acesso negado")

# ==============================================================================
# EXPRESSÕES REGULARES PARA PARSER DE REGISTROS
# ==============================================================================
# Mock atual: "[1] [ ] ID: REG-001 | Tipo: Solicitacao de Beneficio"
REGEX_ITEM_LISTA = re.compile(
    r"\[(?P<indice>\d+)\]\s*\[\s*\]\s*ID:\s*(?P<id>[^\s|]+)\s*\|\s*Tipo:\s*(?P<descricao>[^\r\n]+)"
)

# Mock detalhes:
# ID REGISTRO : REG-001
# TIPO        : Solicitacao de Beneficio
# VALOR       : R$ 1.500,00
# STATUS      : Aprovado
# DATA        : 10/10/2026
REGEX_DETALHE_ID = re.compile(r"ID REGISTRO\s*:\s*(.+)")
REGEX_DETALHE_TIPO = re.compile(r"TIPO\s*:\s*(.+)")
REGEX_DETALHE_VALOR = re.compile(r"VALOR\s*:\s*(.+)")
REGEX_DETALHE_STATUS = re.compile(r"STATUS\s*:\s*(.+)")
REGEX_DETALHE_DATA = re.compile(r"DATA\s*:\s*(.+)")


def parse_lista_registros(buffer_tela: str) -> List[Dict[str, Any]]:
    """
    Extrai a lista de registros apresentados na tela de listagem do legado.
    Retorna uma lista de dicionários com {indice, id, descricao}.
    """
    registros: List[Dict[str, Any]] = []
    for match in REGEX_ITEM_LISTA.finditer(buffer_tela):
        registros.append({
            "indice": int(match.group("indice")),
            "id": match.group("id").strip(),
            "descricao": match.group("descricao").strip(),
        })
    return registros


def parse_detalhe_registro(buffer_tela: str) -> Dict[str, Any]:
    """
    Extrai os campos estruturados da tela individual de detalhe do registro.
    Retorna um dicionário com os campos encontrados.
    """
    match_id = REGEX_DETALHE_ID.search(buffer_tela)
    match_tipo = REGEX_DETALHE_TIPO.search(buffer_tela)
    match_valor = REGEX_DETALHE_VALOR.search(buffer_tela)
    match_status = REGEX_DETALHE_STATUS.search(buffer_tela)
    match_data = REGEX_DETALHE_DATA.search(buffer_tela)

    return {
        "id": match_id.group(1).strip() if match_id else None,
        "tipo": match_tipo.group(1).strip() if match_tipo else None,
        "valor": match_valor.group(1).strip() if match_valor else None,
        "status": match_status.group(1).strip() if match_status else None,
        "data": match_data.group(1).strip() if match_data else None,
    }
