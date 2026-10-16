"""
Configurações da aplicação e credenciais parametrizadas.
Suporta variáveis de ambiente e arquivo .env com fallbacks seguros.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# Carrega .env se existir (busca na raiz do projeto ou diretório corrente)
try:
    from dotenv import load_dotenv

    caminhos_env = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[3] / ".env",
    ]
    for p in caminhos_env:
        if p.exists():
            load_dotenv(dotenv_path=p)
            break
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    """Configurações centralizadas da aplicação."""
    # pylint: disable=invalid-name,too-many-instance-attributes
    # Modo de execução: True para simulador mock em memória, False para terminal/mainframe real
    MODO_TESTE_LOCAL: bool = os.getenv("MODO_TESTE_LOCAL", "true").lower() in ("true", "1", "yes")

    # Servidor SSH / Host Real (parametrizado via variáveis de ambiente)
    SSH_HOST: str = os.getenv("SSH_HOST", "127.0.0.1").strip('"\' ')
    SSH_PORT: int = int(os.getenv("SSH_PORT", "22"))
    SSH_USER: str = os.getenv("SSH_USER", "usuario").strip('"\' ')
    SSH_PASS: str = os.getenv("SSH_PASS", "senha").strip('"\' ')

    # Host para modo de teste local (simulador)
    LOCAL_HOST: str = os.getenv("LOCAL_HOST", "127.0.0.1").strip('"\' ')

    # Credenciais do Operador no Terminal Legado
    APP_MATRICULA: str = os.getenv("APP_MATRICULA", "OPERADOR").strip('"\' ')
    APP_SENHA: str = os.getenv("APP_SENHA", "SENHA").strip('"\' ')

    # Timeouts e Controle de Concorrência
    LOCK_TIMEOUT_SECONDS: float = float(os.getenv("LOCK_TIMEOUT_SECONDS", "30.0"))
    TERMINAL_TIMEOUT_SECONDS: float = float(os.getenv("TERMINAL_TIMEOUT_SECONDS", "15.0"))
    CADENCIA_ENVIO_SEGUNDOS: float = float(os.getenv("CADENCIA_ENVIO_SEGUNDOS", "0.05"))

    # Servidor FastAPI
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))


settings = Settings()
