"""
Endpoints REST da API de automação de terminal.
Expondo as duas fases stateless conforme contratos da Seção 5 do CONTEXT.txt.
"""

from fastapi import APIRouter, HTTPException, status

from automacao.core.security import (
    OperatorLockTimeoutError,
    TerminalTimeoutError,
    UsuarioJaConectadoError,
)
from automacao.schemas.solicitante import (
    ConsultaRegistrosRequest,
    ConsultaRegistrosResponse,
    DetalhesRequest,
    DetalhesResponse,
    RegistroDetalhe,
)
from automacao.services.automacao_service import automacao_service

router = APIRouter(prefix="/solicitante", tags=["Solicitante"])


@router.post(
    "/registros",
    response_model=ConsultaRegistrosResponse,
    summary="Fase 1: Consulta lista de registros disponíveis",
)
async def consultar_registros(payload: ConsultaRegistrosRequest):
    """
    Inicia uma sessão rápida no terminal, autentica o operador,
    preenche a busca do solicitante e extrai a lista de registros disponíveis.
    """
    try:
        resultado = await automacao_service.buscar_registros(
            matricula=payload.matricula,
            digito=payload.digito,
            sequencia=payload.sequencia,
        )
        return resultado
    except OperatorLockTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e),
        ) from e
    except UsuarioJaConectadoError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e),
        ) from e
    except TerminalTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na comunicação com o sistema legado: {str(e)}",
        ) from e


@router.post(
    "/detalhes",
    response_model=DetalhesResponse,
    summary="Fase 2: Extrai detalhes dos registros marcados",
)
async def extrair_detalhes(payload: DetalhesRequest):
    """
    Inicia uma nova sessão rápida no terminal, navega até a lista,
    marca com 'X' os índices selecionados pelo usuário e extrai os campos detalhados.
    """
    try:
        dados = await automacao_service.extrair_detalhes(
            matricula=payload.matricula,
            digito=payload.digito,
            sequencia=payload.sequencia,
            indices_selecionados=payload.indices_selecionados,
        )
        return DetalhesResponse(
            status="sucesso",
            dados=[RegistroDetalhe(**item) for item in dados],
        )
    except OperatorLockTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e),
        ) from e
    except UsuarioJaConectadoError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e),
        ) from e
    except TerminalTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na extração de detalhes do sistema legado: {str(e)}",
        ) from e
