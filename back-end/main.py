"""
Ponto de entrada para execução direta do backend via python/uvicorn.
"""

import uvicorn
from automacao.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "automacao.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
