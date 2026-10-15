"""
Configurações da aplicação e credenciais parametrizadas.
Suporta variáveis de ambiente e arquivo .env com fallbacks seguros.
"""

import os
from dataclasses import dataclass
from pathlib import Path

# Carrega .env se existir
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    """Configurações centralizadas da aplicação."""
    # pylint: disable=invalid-name,too-many-instance-attributes
    # Modo de execução: True para socket direto contra o simulador, False para SSH real com Paramiko
    MODO_TESTE_LOCAL: bool = os.getenv("MODO_TESTE_LOCAL", "true").lower() in ("true", "1", "yes")

    # Servidor SSH / Host Real
    SSH_HOST: str = os.getenv("SSH_HOST", "172.16.5.13").strip('"\' ')
    SSH_PORT: int = int(os.getenv("SSH_PORT", "2222"))
    SSH_USER: str = os.getenv("SSH_USER", "root").strip('"\' ')
    SSH_PASS: str = os.getenv("SSH_PASS", "inforgpd2012*").strip('"\' ')

    # Host para modo de teste local (simulador)
    LOCAL_HOST: str = os.getenv("LOCAL_HOST", "127.0.0.1").strip('"\' ')

    # Credenciais do Operador no Terminal Legado
    APP_MATRICULA: str = os.getenv("APP_MATRICULA", "OP-9876")
    APP_SENHA: str = os.getenv("APP_SENHA", "SenhaForte@2026")

    # Timeouts e Controle de Concorrência
    LOCK_TIMEOUT_SECONDS: float = float(os.getenv("LOCK_TIMEOUT_SECONDS", "30.0"))
    TERMINAL_TIMEOUT_SECONDS: float = float(os.getenv("TERMINAL_TIMEOUT_SECONDS", "15.0"))
    CADENCIA_ENVIO_SEGUNDOS: float = float(os.getenv("CADENCIA_ENVIO_SEGUNDOS", "0.05"))

    # Servidor FastAPI
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))


settings = Settings()
