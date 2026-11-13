"""
Configurações da aplicação e credenciais carregadas diretamente das variáveis de ambiente (.env).
"""

import os
from dataclasses import dataclass
from pathlib import Path

# Carrega .env da raiz do projeto ou diretório corrente (com fallback para .env.example em CI)
try:
    from dotenv import load_dotenv

    raiz_repo = Path(__file__).resolve().parents[4]
    dir_backend = Path(__file__).resolve().parents[3]
    caminhos_env = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        dir_backend / ".env",
        raiz_repo / ".env",
        raiz_repo / ".env.example",
    ]
    for caminho in caminhos_env:
        if caminho.exists():
            load_dotenv(dotenv_path=caminho)
            break
except ImportError:
    pass


def _env_str(key: str) -> str:
    """Obtém uma string diretamente do environment removendo aspas/espaços."""
    return os.environ[key].strip("\"' ")


@dataclass(frozen=True)
class Settings:
    """Configurações centralizadas da aplicação lidas diretamente do environment."""

    # pylint: disable=invalid-name,too-many-instance-attributes
    MODO_TESTE_LOCAL: bool = _env_str("MODO_TESTE_LOCAL").lower() in (
        "true",
        "1",
        "yes",
    )

    # Host Real TN3270
    HOST: str = _env_str("HOST")
    PORT: int = int(_env_str("PORT"))
    SECURE_CONNECTION: bool = _env_str("SECURE_CONNECTION").lower() in (
        "true",
        "1",
        "yes",
    )

    # Host para modo de teste local (simulador)
    LOCAL_HOST: str = _env_str("LOCAL_HOST")

    # Credenciais do Operador no Terminal Legado
    APP_MATRICULA: str = _env_str("APP_MATRICULA")
    APP_SENHA: str = _env_str("APP_SENHA")

    # Timeouts e Controle de Concorrência
    LOCK_TIMEOUT_SECONDS: float = float(_env_str("LOCK_TIMEOUT_SECONDS"))
    TERMINAL_TIMEOUT_SECONDS: float = float(_env_str("TERMINAL_TIMEOUT_SECONDS"))
    CADENCIA_ENVIO_SEGUNDOS: float = float(_env_str("CADENCIA_ENVIO_SEGUNDOS"))

    # Servidor FastAPI
    API_HOST: str = _env_str("API_HOST")
    API_PORT: int = int(_env_str("API_PORT"))

    # Cache em Memória (TTL e Limite LRU)
    CACHE_TTL_SEGUNDOS: int = int(
        os.environ.get("CACHE_TTL_SEGUNDOS", "3600").strip("\"' ")
    )
    CACHE_MAX_ENTRADAS: int = int(
        os.environ.get("CACHE_MAX_ENTRADAS", "200").strip("\"' ")
    )


settings = Settings()
