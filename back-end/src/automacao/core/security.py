"""
Gerenciador de concorrência e sessão única para a credencial do operador.
Utiliza asyncio.Lock com timeout para proteger o terminal legado contra acessos simultâneos.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator


class OperatorLockTimeoutError(Exception):
    """Lançado quando uma requisição aguarda na fila além do tempo limite permitido."""


class UsuarioJaConectadoError(Exception):
    """Lançado quando o sistema legado relata que a matrícula do operador já está em uso."""


class TerminalTimeoutError(Exception):
    """Lançado quando o terminal legado não responde a âncora esperada no tempo limite."""


class OperatorConcurrencyManager:
    """Controla o acesso exclusivo à credencial única do operador."""

    def __init__(self, timeout_seconds: float = 30.0):
        self._lock = asyncio.Lock()
        self.timeout_seconds = timeout_seconds

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[None, None]:
        """Adquire o lock assíncrono com timeout configurado."""
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=self.timeout_seconds)
        except asyncio.TimeoutError as exc:
            msg = (
                "A credencial do operador está ocupada por outra operação. "
                "Tente novamente em alguns segundos."
            )
            raise OperatorLockTimeoutError(msg) from exc

        try:
            yield
        finally:
            self._lock.release()

    @property
    def is_locked(self) -> bool:
        """Informa se a trava está retida por alguma operação."""
        return self._lock.locked()


# Instância global do gerenciador de concorrência
operator_lock = OperatorConcurrencyManager()
