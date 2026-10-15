"""
Aplicação FastAPI para a API de Automação de Terminal Legado.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from automacao.api.endpoints import router as api_router
from automacao.core.config import settings
from automacao.core.security import operator_lock

app = FastAPI(
    title="Automação Terminal Legado SSH",
    description="API REST intermediária para automação de terminal legado com sessão monousuário.",
    version="1.0.0",
)

# Habilita CORS para permitir conexão direta a partir do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Status"])
async def health_check():
    """Verifica se o backend está ativo e o estado do lock da credencial."""
    return {
        "status": "online",
        "operador_ocupado": operator_lock.is_locked,
    }


def main() -> None:
    """Inicia o servidor uvicorn."""
    uvicorn.run("automacao.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
