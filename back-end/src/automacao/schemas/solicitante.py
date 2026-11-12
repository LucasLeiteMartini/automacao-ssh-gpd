"""
Modelos de dados Pydantic para requisições e respostas da API de automação.
Alinhados com o módulo SPPC/CONFER (Consulta Férias) do mainframe PRODAM.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SolicitanteIdentificacao(BaseModel):
    """Dados de identificação e cabeçalho do servidor/solicitante."""
    matricula: str = Field(
        ..., pattern=r"^\d{6}$", description="Matrícula com 6 dígitos numéricos"
    )
    digito: str = Field(
        ..., pattern=r"^\d{1}$", description="Dígito verificador numérico de 1 dígito"
    )
    sequencia: str = Field(
        ..., pattern=r"^[a-zA-Z]{1}$", description="Sequência com 1 letra"
    )
    opcao_consulta: str = Field(
        ...,
        pattern=r"^(4|9|10|13|16)$",
        description="Código da consulta no menu SPPC/CONSULTA (4, 9, 10, 13 ou 16)",
    )
    nome: Optional[str] = Field(None, description="Nome completo do servidor no SPPC")
    lotacao: Optional[str] = Field(None, description="Lotação do servidor no SPPC")


class ConsultaRegistrosRequest(BaseModel):
    """Corpo da requisição para listagem de registros da Fase 1."""
    matricula: str = Field(
        ..., pattern=r"^\d{6}$", description="Matrícula com 6 dígitos numéricos"
    )
    digito: str = Field(
        ..., pattern=r"^\d{1}$", description="Dígito verificador numérico de 1 dígito"
    )
    sequencia: str = Field(
        ..., pattern=r"^[a-zA-Z]{1}$", description="Sequência com 1 letra"
    )
    opcao_consulta: str = Field(
        ...,
        pattern=r"^(4|9|10|13|16)$",
        description="Código da consulta no menu SPPC/CONSULTA (4, 9, 10, 13 ou 16)",
    )


class RegistroItem(BaseModel):
    """Item de férias retornado na listagem da Fase 1 (SPPC/CONFER)."""
    indice: int = Field(..., description="Índice ordinal de exibição no terminal (1 a 10)")
    id: str = Field(..., description="Período aquisitivo identificador")
    descricao: str = Field(..., description="Resumo legível do registro e saldo")
    aquisicao_inicio: Optional[str] = Field(None, description="Data inicial do período aquisitivo")
    aquisicao_fim: Optional[str] = Field(None, description="Data final do período aquisitivo")
    dias_adquiridos: int = Field(0, description="Total de dias adquiridos no período (Adq.)")
    status: Optional[str] = Field(None, description="Status do período: 'P' (Pendente) ou 'NP'")
    utilizacao_inicio: Optional[str] = Field(None, description="Data inicial de utilização")
    dias_utilizados: int = Field(0, description="Dias utilizados nesta parcela/linha")
    dias_utilizados_periodo: int = Field(
        0, description="Soma dos dias utilizados em todas as parcelas do mesmo período aquisitivo"
    )
    saldo_disponivel: int = Field(
        0,
        description="Saldo disponível calculado para o período (dias_adquiridos - soma utilizados)",
    )
    doc_tipo: Optional[str] = Field(None, description="Tipo do documento (ex: MEM)")
    doc_numero: Optional[str] = Field(None, description="Número do documento (ex: 001510)")
    doc_data: Optional[str] = Field(None, description="Data do documento")


class ConsultaRegistrosResponse(BaseModel):
    """Resposta com o cabeçalho do servidor e a lista de registros de férias da Fase 1."""
    solicitante: SolicitanteIdentificacao
    registros: List[RegistroItem]


class DetalhesRequest(BaseModel):
    """Corpo da requisição para extração de detalhes da Fase 2 (em stand-by)."""
    matricula: str = Field(
        ..., pattern=r"^\d{6}$", description="Matrícula com 6 dígitos numéricos"
    )
    digito: str = Field(
        ..., pattern=r"^\d{1}$", description="Dígito verificador numérico de 1 dígito"
    )
    sequencia: str = Field(
        ..., pattern=r"^[a-zA-Z]{1}$", description="Sequência com 1 letra"
    )
    opcao_consulta: str = Field(
        ...,
        pattern=r"^(4|9|10|13|16)$",
        description="Código da consulta no menu SPPC/CONSULTA (4, 9, 10, 13 ou 16)",
    )
    indices_selecionados: List[int] = Field(
        ...,
        description="Lista de índices numéricos para marcar com 'X'",
    )


class RegistroDetalhe(BaseModel):
    """Campos detalhados de um registro extraído na Fase 2 (Tela NC5F M13A da PRODAM)."""
    id: Optional[str] = Field(None, description="Período aquisitivo do registro")
    aquisicao: Optional[str] = Field(None, description="Período de aquisição formatado")
    dias_adquiridos: int = Field(0, description="Dias adquiridos no período")
    dias_utilizados: int = Field(0, description="Dias utilizados no registro")
    dias_restantes: int = Field(0, description="Saldo restante (Adquiridos - Utilizados)")
    situacao: Optional[str] = Field(None, description="Situação (Pendente / Nao Pendente)")
    previsao: Optional[str] = Field(None, description="Período de previsão (Inicial a Final)")
    utilizacao: Optional[str] = Field(None, description="Período de utilização (Inicial a Final)")
    dias_gozados: int = Field(0, description="Quantidade de dias gozados na utilização")
    doc_tipo: Optional[str] = Field(None, description="Tipo do documento (ex: MEM)")
    doc_numero: Optional[str] = Field(None, description="Número do documento (ex: 001510)")
    doc_data: Optional[str] = Field(None, description="Data do documento (ex: 01/06/2012)")
    observacao: Optional[str] = Field(None, description="Observação registrada no documento")
    tipo: Optional[str] = Field(None, description="Tipo e número do documento")
    valor: Optional[str] = Field(
        None, description="Resumo de dias adquiridos, utilizados e restantes"
    )
    status: Optional[str] = Field(None, description="Status detalhado")
    data: Optional[str] = Field(None, description="Data do documento")


class DetalhesResponse(BaseModel):
    """Resposta consolidada com os dados extraídos na Fase 2."""
    status: str = Field("sucesso", description="Status da extração")
    dados: List[RegistroDetalhe]
