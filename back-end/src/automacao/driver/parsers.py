"""
Mapeamento de coordenadas (linhas e colunas) e parsers de tela 3270 (matriz 24x80).
Todas as constantes de gatilhos, coordenadas e opções são lidas diretamente do environment (.env).
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import automacao.core.config  # pylint: disable=unused-import
from automacao.driver.driver_3270_interface import Base3270Driver


def _env_str(key: str) -> str:
    """Obtém uma string diretamente do environment removendo aspas externas."""
    return os.environ[key].strip('"\' ')


def _env_int(key: str) -> int:
    """Obtém um inteiro diretamente do environment."""
    return int(_env_str(key))


# ==============================================================================
# GATILHOS DE IDENTIFICAÇÃO DE TELAS (LIDOS DO ENVIRONMENT)
# ==============================================================================
GATILHO_TELA_APLICACAO = _env_str("GATILHO_TELA_APLICACAO")
GATILHO_TELA_LOGIN = _env_str("GATILHO_TELA_LOGIN")
GATILHO_TELA_MENU = _env_str("GATILHO_TELA_MENU")
GATILHO_TELA_SUBMENU = _env_str("GATILHO_TELA_SUBMENU")
GATILHO_TELA_SOLICITANTE = _env_str("GATILHO_TELA_SOLICITANTE")
GATILHO_TELA_LISTA = _env_str("GATILHO_TELA_LISTA")
GATILHO_TELA_DETALHE = _env_str("GATILHO_TELA_DETALHE")
GATILHO_FIM_SESSAO = _env_str("GATILHO_FIM_SESSAO")

# Gatilhos de erro no mainframe
GATILHO_USUARIO_CONECTADO = _env_str("GATILHO_USUARIO_CONECTADO")
GATILHO_ACESSO_NEGADO = _env_str("GATILHO_ACESSO_NEGADO")
GATILHO_MATRICULA_INEXISTENTE = _env_str("GATILHO_MATRICULA_INEXISTENTE")
PREFIXO_ERRO_TELA_SOLICITANTE = _env_str("PREFIXO_ERRO_TELA_SOLICITANTE")

# ==============================================================================
# COORDENADAS DE INPUT E OPÇÕES (LIDAS DO ENVIRONMENT)
# ==============================================================================
# 1ª Tela: Seleção de Aplicação (PRODAM)
POS_APLICACAO_OPCAO = (_env_int("POS_APLICACAO_LINHA"), _env_int("POS_APLICACAO_COLUNA"))
VALOR_APLICACAO_OPCAO = _env_str("OPCAO_APLICACAO")

# 2ª Tela: Login CICS (CICSCNTR)
POS_LOGIN_MATRICULA = (
    _env_int("POS_LOGIN_MATRICULA_LINHA"),
    _env_int("POS_LOGIN_MATRICULA_COLUNA"),
)
POS_LOGIN_SENHA = (
    _env_int("POS_LOGIN_SENHA_LINHA"),
    _env_int("POS_LOGIN_SENHA_COLUNA"),
)

# 3ª Tela: Menu de Sistemas (CEUSPL02)
POS_MENU_OPCAO = (_env_int("POS_MENU_LINHA"), _env_int("POS_MENU_COLUNA"))
VALOR_MENU_OPCAO = _env_str("OPCAO_MENU_PRINCIPAL")

# 4ª Tela: Menu de Consultas (SPPC/CONSULTA)
POS_SUBMENU_OPCAO = (_env_int("POS_SUBMENU_LINHA"), _env_int("POS_SUBMENU_COLUNA"))
VALOR_SUBMENU_OPCAO = _env_str("OPCAO_SUBMENU")

# 5ª Tela: Consulta Férias do Servidor (SPPC/CONFER - PC05 M05A)
POS_SOLICITANTE_MATRICULA = (
    _env_int("POS_SOLICITANTE_MATRICULA_LINHA"),
    _env_int("POS_SOLICITANTE_MATRICULA_COLUNA"),
)
POS_SOLICITANTE_DIGITO = (
    _env_int("POS_SOLICITANTE_DIGITO_LINHA"),
    _env_int("POS_SOLICITANTE_DIGITO_COLUNA"),
)
POS_SOLICITANTE_SEQUENCIA = (
    _env_int("POS_SOLICITANTE_SEQUENCIA_LINHA"),
    _env_int("POS_SOLICITANTE_SEQUENCIA_COLUNA"),
)
POS_SOLICITANTE_SITUACAO = (
    _env_int("POS_SOLICITANTE_SITUACAO_LINHA"),
    _env_int("POS_SOLICITANTE_SITUACAO_COLUNA"),
)
VALOR_SOLICITANTE_SITUACAO = _env_str("OPCAO_SOLICITANTE_SITUACAO")

# 6ª Tela: Linhas da tabela de férias, coluna de seleção e teclas de ação
LINHA_INICIAL_REGISTROS = _env_int("LINHA_INICIAL_REGISTROS")
LINHA_FINAL_REGISTROS = _env_int("LINHA_FINAL_REGISTROS")
COLUNA_CHECKBOX_MARCAR = _env_int("COLUNA_CHECKBOX_MARCAR")
CARACTERE_MARCACAO_REGISTRO = _env_str("CARACTERE_MARCACAO_REGISTRO")
TECLA_PF_ENCERRAR = _env_int("TECLA_PF_ENCERRAR")
TECLA_PF_AVANCAR_PAGINA = _env_int("TECLA_PF_AVANCAR_PAGINA")

# Regex de cabeçalho do servidor (Linhas 6 e 7 da tela SPPC/CONFER)
REGEX_CABECALHO_NOME = re.compile(
    r"^\s*\d{6}\s*\d\s*[A-Za-z0-9]\s+(?P<nome>.+?)\s*$"
)
REGEX_CABECALHO_LOTACAO = re.compile(
    r"Lotacao:\s*(?P<lotacao>.+?)\s*$", re.IGNORECASE
)

# Regex para cada linha da listagem de férias (SPPC/CONFER - Linhas 11 a 20)
REGEX_ITEM_LISTA_3270 = re.compile(
    r"(?P<aquisicao_inicio>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<aquisicao_fim>\d{2}/\d{2}/\d{2})\s+"
    r"(?:(?P<previsao_inicio>\d{2}/\d{2}/\d{2})\s+)?"
    r"(?P<abono>[A-Z])\s+"
    r"(?P<adiantamento_13>[A-Z])\s+"
    r"(?P<dias_adquiridos>\d+)\s+"
    r"(?P<status>NP|P)\b"
    r"(?:\s+(?P<utilizacao_inicio>\d{2}/\d{2}/\d{2})\s+(?P<dias_utilizados>\d+))?"
    r"(?:\s+(?P<doc_tipo>[A-Z0-9]{2,4})\s+(?P<doc_numero>\S+)\s+(?P<doc_data>\d{2}/\d{2}/\d{2}))?"
)

# Regex para campos da tela de detalhe NC5F M13A (formato real PRODAM)
REGEX_DETALHE_AQUISICAO = re.compile(
    r"Aquisic[^:]*:\s*(\d{2}[/\s]\d{2}[/\s]\d{4})\s+a\s+(\d{2}[/\s]\d{2}[/\s]\d{4})",
    re.IGNORECASE,
)
REGEX_DETALHE_ADQUIRIDOS = re.compile(
    r"Adquiridos\.?:[ \t]*(\d+)",
    re.IGNORECASE,
)
REGEX_DETALHE_UTILIZADOS = re.compile(
    r"Utilizados\.?:[ \t]*(\d+)",
    re.IGNORECASE,
)
REGEX_DETALHE_SITUACAO = re.compile(
    r"Adquiridos\.?:[ \t]*\d+(?:[ \t]+Utilizados\.?:[ \t]*\d*)?[ \t]+(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
REGEX_DETALHE_PENDENTE_DIAS = re.compile(
    r"Pendente\.?:[ \t]*(\d+)",
    re.IGNORECASE,
)
REGEX_DETALHE_PREVISAO = re.compile(
    r"Previs[^:]*:\s*(?:(\d{2}[/\s]\d{2}[/\s]\d{4})\s+a\s+(\d{2}[/\s]\d{2}[/\s]\d{4}))?",
    re.IGNORECASE,
)
REGEX_DETALHE_UTILIZACAO = re.compile(
    r"^\s*Utiliza(?:cao|ção)[^:]*:\s*"
    r"(?:(\d{2}[/\s]\d{2}[/\s]\d{4})\s+a\s+(\d{2}[/\s]\d{2}[/\s]\d{4}))?"
    r"(?:\s+(\d+)\s*Dias)?",
    re.IGNORECASE | re.MULTILINE,
)
REGEX_DETALHE_DOC_TABELA = re.compile(
    r"TP\s+Numero\s+Data\s+Observa[^\n]*\n\s*"
    r"([A-Z0-9]{2,4})?\s*(\d{3,10})?\s*(\d{2}[/\s]\d{2}[/\s]\d{4})?\s*(.*)$",
    re.IGNORECASE | re.MULTILINE,
)
REGEX_DETALHE_DOC_LINHA = re.compile(
    r"TP:\s*([A-Z0-9]+)\s+Numero:\s*(\S+)\s+Data:\s*(\d{2}[/\s]\d{2}[/\s]\d{4})",
    re.IGNORECASE,
)


def _formatar_data_3270(raw: Optional[str]) -> Optional[str]:
    """Normaliza datas 'DD MM AAAA' do terminal 3270 para 'DD/MM/AAAA'."""
    if not raw:
        return None
    limpo = "/".join(raw.strip().split())
    return limpo if limpo else None


def parse_cabecalho_solicitante_3270(driver: Base3270Driver) -> Dict[str, Optional[str]]:
    """
    Extrai o Nome (linha 6) e a Lotação (linha 7) do servidor na tela SPPC/CONFER.
    """
    lines = driver.get_screen_lines()
    nome: Optional[str] = None
    lotacao: Optional[str] = None

    if len(lines) >= 6:
        match_nome = REGEX_CABECALHO_NOME.search(lines[5])
        if match_nome:
            nome_extraido = match_nome.group("nome").strip()
            if nome_extraido:
                nome = nome_extraido

    if len(lines) >= 7:
        match_lot = REGEX_CABECALHO_LOTACAO.search(lines[6])
        if match_lot:
            lot_extraida = " ".join(match_lot.group("lotacao").split())
            if lot_extraida:
                lotacao = lot_extraida

    return {"nome": nome, "lotacao": lotacao}


def _acumular_linha_ferias(
    por_periodo: Dict[Tuple[str, str], Dict[str, Any]],
    match: re.Match[str],
    pagina_atual: int,
    row_idx: int,
) -> None:
    """Consolida uma linha da tabela de férias (MC5A NC5A) por período aquisitivo."""
    aq_ini = match.group("aquisicao_inicio")
    aq_fim = match.group("aquisicao_fim")
    dias_adq = int(match.group("dias_adquiridos"))
    status = match.group("status")
    util_ini = match.group("utilizacao_inicio") or None
    dias_util = int(match.group("dias_utilizados") or "0")
    doc_tipo = match.group("doc_tipo") or None
    doc_num = match.group("doc_numero") or None
    doc_data = match.group("doc_data") or None

    chave = (aq_ini, aq_fim)
    if chave not in por_periodo:
        por_periodo[chave] = {
            "indice": len(por_periodo) + 1,
            "id": f"{aq_ini} a {aq_fim}",
            "descricao": "",
            "aquisicao_inicio": aq_ini,
            "aquisicao_fim": aq_fim,
            "dias_adquiridos": dias_adq,
            "status": status,
            "utilizacao_inicio": util_ini,
            "dias_utilizados": dias_util,
            "dias_utilizados_periodo": dias_util,
            "saldo_disponivel": 0,
            "doc_tipo": doc_tipo,
            "doc_numero": doc_num,
            "doc_data": doc_data,
            "row": row_idx,
            "rows": [row_idx] if pagina_atual == 1 else [],
            "targets": [{"page": pagina_atual, "row": row_idx}],
            "check_col": COLUNA_CHECKBOX_MARCAR,
        }
    else:
        existente = por_periodo[chave]
        existente["dias_utilizados"] += dias_util
        existente["dias_utilizados_periodo"] += dias_util
        if pagina_atual == 1:
            existente["rows"].append(row_idx)
        existente["targets"].append({"page": pagina_atual, "row": row_idx})
        if util_ini:
            existente["utilizacao_inicio"] = util_ini
        if doc_num:
            existente["doc_tipo"] = doc_tipo
            existente["doc_numero"] = doc_num
            existente["doc_data"] = doc_data


# pylint: disable=too-many-locals
def parse_lista_registros_3270(
    driver: Base3270Driver,
    paginar: bool = True,
) -> List[Dict[str, Any]]:
    """
    Percorre as linhas da matriz 24x80 na tela SPPC/CONFER (paginando com PF8 quando necessário)
    e consolida períodos aquisitivos repetidos em uma única linha por período,
    exibindo Adq, Util (soma no período) e Saldo.
    """
    por_periodo: Dict[Tuple[str, str], Dict[str, Any]] = {}
    paginas_vistas: set[Tuple[str, ...]] = set()
    pagina_atual = 1
    max_paginas = 20

    while pagina_atual <= max_paginas:
        lines = driver.get_screen_lines()
        fatia_tabela = tuple(
            lines[LINHA_INICIAL_REGISTROS - 1 : LINHA_FINAL_REGISTROS]
        )
        if not any(l.strip() for l in fatia_tabela) or fatia_tabela in paginas_vistas:
            break
        paginas_vistas.add(fatia_tabela)

        ultima_linha_preenchida = False
        for row_idx in range(LINHA_INICIAL_REGISTROS, LINHA_FINAL_REGISTROS + 1):
            if row_idx <= len(lines):
                match = REGEX_ITEM_LISTA_3270.search(lines[row_idx - 1])
                if match:
                    if row_idx == LINHA_FINAL_REGISTROS:
                        ultima_linha_preenchida = True
                    _acumular_linha_ferias(por_periodo, match, pagina_atual, row_idx)

        if not paginar or not ultima_linha_preenchida:
            break

        driver.send_pf(TECLA_PF_AVANCAR_PAGINA)
        pagina_atual += 1
        linha_topo = driver.get_string(1, 1, 80).strip()
        if linha_topo.startswith(PREFIXO_ERRO_TELA_SOLICITANTE):
            break

    registros = list(por_periodo.values())
    for item in registros:
        util_total = item["dias_utilizados_periodo"]
        saldo = max(0, item["dias_adquiridos"] - util_total)
        item["saldo_disponivel"] = saldo
        item["descricao"] = (
            f"Adq: {item['dias_adquiridos']}d | Util: {util_total}d | Saldo: {saldo}d"
        )

    return registros


def _formatar_intervalo_3270(match_obj: Optional[re.Match[str]]) -> Optional[str]:
    """Formata um intervalo 'DD MM AAAA a DD MM AAAA' a partir de grupos 1 e 2."""
    if match_obj and match_obj.group(1) and match_obj.group(2):
        ini = _formatar_data_3270(match_obj.group(1))
        fim = _formatar_data_3270(match_obj.group(2))
        return f"{ini} a {fim}"
    return None


# pylint: disable=too-many-locals
def parse_detalhe_registro_3270(driver: Base3270Driver) -> Dict[str, Any]:
    """
    Lê a 7ª tela de detalhe NC5F M13A da PRODAM na matriz 24x80 e retorna
    todos os campos estruturados (Aquisição, Dias, Previsão, Utilização e Documento).
    """
    screen_text = "\n".join(driver.get_screen_lines())

    match_aq = REGEX_DETALHE_AQUISICAO.search(screen_text)
    match_adq = REGEX_DETALHE_ADQUIRIDOS.search(screen_text)
    match_util_num = REGEX_DETALHE_UTILIZADOS.search(screen_text)
    match_sit = REGEX_DETALHE_SITUACAO.search(screen_text)
    match_pend_dias = REGEX_DETALHE_PENDENTE_DIAS.search(screen_text)
    match_prev = REGEX_DETALHE_PREVISAO.search(screen_text)
    match_util = REGEX_DETALHE_UTILIZACAO.search(screen_text)
    match_doc_tab = REGEX_DETALHE_DOC_TABELA.search(screen_text)
    match_doc_lin = REGEX_DETALHE_DOC_LINHA.search(screen_text)

    aquisicao = _formatar_intervalo_3270(match_aq)
    previsao = _formatar_intervalo_3270(match_prev)
    utilizacao = _formatar_intervalo_3270(match_util)

    dias_adq = int(match_adq.group(1)) if match_adq else 0
    dias_util = int(match_util_num.group(1)) if match_util_num else 0
    situacao = (
        (" ".join(match_sit.group(1).split()).strip() or None) if match_sit else None
    )
    dias_rest = (
        int(match_pend_dias.group(1))
        if match_pend_dias
        else max(0, dias_adq - dias_util)
    )
    dias_gozados = (
        int(match_util.group(3))
        if (match_util and match_util.group(3))
        else dias_util
    )

    doc_tipo: Optional[str] = None
    doc_numero: Optional[str] = None
    doc_data: Optional[str] = None
    observacao: Optional[str] = None

    if match_doc_tab:
        doc_tipo = (match_doc_tab.group(1) or "").strip() or None
        doc_numero = (match_doc_tab.group(2) or "").strip() or None
        doc_data = _formatar_data_3270(match_doc_tab.group(3))
        obs_bruta = (match_doc_tab.group(4) or "").replace("_", " ").strip()
        observacao = " ".join(obs_bruta.split()) or None
    elif match_doc_lin:
        doc_tipo = match_doc_lin.group(1).strip()
        doc_numero = match_doc_lin.group(2).strip()
        doc_data = _formatar_data_3270(match_doc_lin.group(3))

    tipo_legado = f"{doc_tipo} {doc_numero}".strip() if (doc_tipo or doc_numero) else None
    valor_legado = (
        f"Adquiridos: {dias_adq:02d} | Utilizados: {dias_util:02d} | Restantes: {dias_rest:02d}"
        if match_adq
        else None
    )

    return {
        "id": aquisicao,
        "aquisicao": aquisicao,
        "dias_adquiridos": dias_adq,
        "dias_utilizados": dias_util,
        "dias_restantes": dias_rest,
        "situacao": situacao,
        "previsao": previsao,
        "utilizacao": utilizacao,
        "dias_gozados": dias_gozados,
        "doc_tipo": doc_tipo,
        "doc_numero": doc_numero,
        "doc_data": doc_data,
        "observacao": observacao,
        "tipo": tipo_legado,
        "valor": valor_legado,
        "status": situacao,
        "data": doc_data,
    }
