"""
Mapeamento de coordenadas (linhas e colunas) e parsers de tela 3270 (matriz 24x80).
Permite configurar as posições exatas dos campos do mainframe de forma desacoplada.
"""

import os
import re
from typing import Any, Dict, List

from automacao.driver.driver_3270_interface import Base3270Driver

# ==============================================================================
# GATILHOS DE IDENTIFICAÇÃO DE TELAS (TEXTOS ESPERADOS NA MATRIZ 24x80)
# ==============================================================================
GATILHO_TELA_LOGIN = os.getenv("GATILHO_TELA_LOGIN", "SISTEMA INTEGRADO LEGADO")
GATILHO_TELA_MENU = os.getenv("GATILHO_TELA_MENU", "MENU PRINCIPAL")
GATILHO_TELA_SUBMENU = os.getenv("GATILHO_TELA_SUBMENU", "SUBMENU DE SOLICITANTES")
GATILHO_TELA_SOLICITANTE = os.getenv(
    "GATILHO_TELA_SOLICITANTE", "CONSULTA DE REGISTROS DO SOLICITANTE"
)
GATILHO_TELA_LISTA = os.getenv("GATILHO_TELA_LISTA", "REGISTROS ENCONTRADOS")
GATILHO_TELA_DETALHE = os.getenv("GATILHO_TELA_DETALHE", "DETALHE DO REGISTRO")
GATILHO_FIM_SESSAO = os.getenv("GATILHO_FIM_SESSAO", "Sessao finalizada com sucesso.")

# Gatilhos de erro no mainframe
GATILHO_USUARIO_CONECTADO = os.getenv("GATILHO_USUARIO_CONECTADO", "usuario ja conectado")
GATILHO_ACESSO_NEGADO = os.getenv("GATILHO_ACESSO_NEGADO", "Acesso negado")

# ==============================================================================
# COORDENADAS DE INPUT (Linha, Coluna - 1-indexed)
# ==============================================================================
# Tela de Login
POS_LOGIN_MATRICULA = (8, 36)
POS_LOGIN_SENHA = (9, 36)

# Menu Principal
POS_MENU_OPCAO = (20, 43)
VALOR_MENU_OPCAO = os.getenv("OPCAO_MENU_PRINCIPAL", "5")

# Submenu
POS_SUBMENU_OPCAO = (20, 31)
VALOR_SUBMENU_OPCAO = os.getenv("OPCAO_SUBMENU", "10")

# Consulta Solicitante
POS_SOLICITANTE_MATRICULA = (8, 24)
POS_SOLICITANTE_DIGITO = (8, 48)
POS_SOLICITANTE_SEQUENCIA = (8, 67)

# Lista de Registros: Linhas onde os itens começam e coluna do checkbox
LINHA_INICIAL_REGISTROS = int(os.getenv("LINHA_INICIAL_REGISTROS", "8"))
LINHA_FINAL_REGISTROS = int(os.getenv("LINHA_FINAL_REGISTROS", "18"))
COLUNA_CHECKBOX_MARCAR = int(os.getenv("COLUNA_CHECKBOX_MARCAR", "9"))

# Regex para ler cada linha da lista 3270
REGEX_ITEM_LISTA_3270 = re.compile(
    r"\[(?P<indice>\d+)\]\s*\[\s*\]\s*ID:\s*(?P<id>[^\s|]+)\s*\|\s*Tipo:\s*(?P<descricao>[^\r\n]+)"
)

# Regex para campos da tela de detalhe
REGEX_DETALHE_ID = re.compile(r"ID REGISTRO\s*:\s*(.+)")
REGEX_DETALHE_TIPO = re.compile(r"TIPO\s*:\s*(.+)")
REGEX_DETALHE_VALOR = re.compile(r"VALOR\s*:\s*(.+)")
REGEX_DETALHE_STATUS = re.compile(r"STATUS\s*:\s*(.+)")
REGEX_DETALHE_DATA = re.compile(r"DATA\s*:\s*(.+)")


def parse_lista_registros_3270(driver: Base3270Driver) -> List[Dict[str, Any]]:
    """
    Percorre as linhas da matriz 24x80 da tela de listagem e extrai os itens encontrados.
    Retorna lista de {indice, id, descricao, row, check_col}.
    """
    registros: List[Dict[str, Any]] = []
    lines = driver.get_screen_lines()

    for row_idx, line_text in enumerate(lines, start=1):
        if LINHA_INICIAL_REGISTROS <= row_idx <= LINHA_FINAL_REGISTROS:
            match = REGEX_ITEM_LISTA_3270.search(line_text)
            if match:
                registros.append({
                    "indice": int(match.group("indice")),
                    "id": match.group("id").strip(),
                    "descricao": match.group("descricao").strip(),
                    "row": row_idx,
                    "check_col": COLUNA_CHECKBOX_MARCAR,
                })

    return registros


def parse_detalhe_registro_3270(driver: Base3270Driver) -> Dict[str, Any]:
    """
    Lê a tela de detalhe ativa na matriz 24x80 e extrai os valores dos campos.
    """
    lines = driver.get_screen_lines()
    screen_text = "\n".join(lines)

    match_id = REGEX_DETALHE_ID.search(screen_text)
    match_tipo = REGEX_DETALHE_TIPO.search(screen_text)
    match_valor = REGEX_DETALHE_VALOR.search(screen_text)
    match_status = REGEX_DETALHE_STATUS.search(screen_text)
    match_data = REGEX_DETALHE_DATA.search(screen_text)

    return {
        "id": match_id.group(1).strip() if match_id else None,
        "tipo": match_tipo.group(1).strip() if match_tipo else None,
        "valor": match_valor.group(1).strip() if match_valor else None,
        "status": match_status.group(1).strip() if match_status else None,
        "data": match_data.group(1).strip() if match_data else None,
    }
