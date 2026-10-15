"""
Modelos de dados Pydantic para requisições e respostas da API de automação.
Alinhados com os contratos definidos na Seção 5 do CONTEXT.txt.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SolicitanteIdentificacao(BaseModel):
    """Dados de identificação horizontal do solicitante."""
    matricula: str = Field(..., description="Matrícula do solicitante")
    digito: str = Field(..., description="Dígito verificador do solicitante")
    sequencia: str = Field(..., description="Sequência da solicitação")


class ConsultaRegistrosRequest(BaseModel):
    """Corpo da requisição para listagem de registros da Fase 1."""
    matricula: str = Field(..., description="Matrícula do solicitante")
    digito: str = Field(..., description="Dígito verificador do solicitante")
    sequencia: str = Field(..., description="Sequência da solicitação")


class RegistroItem(BaseModel):
    """Item resumido retornado na listagem da Fase 1."""
    indice: int = Field(..., description="Índice ordinal de exibição no terminal")
    id: str = Field(..., description="Identificador único do registro no sistema legado")
    descricao: str = Field(..., description="Descrição ou tipo resumido do registro")


class ConsultaRegistrosResponse(BaseModel):
    """Resposta com a lista de registros encontrados na Fase 1."""
    solicitante: SolicitanteIdentificacao
    registros: List[RegistroItem]


class DetalhesRequest(BaseModel):
    """Corpo da requisição para extração de detalhes da Fase 2."""
    matricula: str = Field(..., description="Matrícula do solicitante")
    digito: str = Field(..., description="Dígito verificador do solicitante")
    sequencia: str = Field(..., description="Sequência da solicitação")
    indices_selecionados: List[int] = Field(
        ...,
        description="Lista de índices numéricos para marcar com 'X'",
    )


class RegistroDetalhe(BaseModel):
    """Campos detalhados de um registro extraído na Fase 2."""
    id: Optional[str] = Field(None, description="Identificador do registro")
    tipo: Optional[str] = Field(None, description="Tipo do registro")
    valor: Optional[str] = Field(None, description="Valor monetário formatado")
    status: Optional[str] = Field(None, description="Status de aprovação/tramitação")
    data: Optional[str] = Field(None, description="Data associada ao registro")


class DetalhesResponse(BaseModel):
    """Resposta consolidada com os dados extraídos na Fase 2."""
    status: str = Field("sucesso", description="Status da extração")
    dados: List[RegistroDetalhe]
