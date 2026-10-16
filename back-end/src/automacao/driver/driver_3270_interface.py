"""
Interface abstrata para drivers de terminal IBM TN3270.
Padroniza operações em matriz 24x80 e envio de teclas de ação AID (Enter, PF keys).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class Base3270Driver(ABC):
    """Contrato base para comunicação com emuladores e conexões TN3270."""

    @abstractmethod
    def connect(self, host: str, port: int = 23, timeout: float = 15.0) -> None:
        """Estabelece conexão TN3270 com o host e porta especificados."""

    @abstractmethod
    def disconnect(self) -> None:
        """Encerra a sessão TN3270 de forma limpa."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Informa se a sessão com o host está ativa."""

    @abstractmethod
    def send_string(self, value: str, row: Optional[int] = None, col: Optional[int] = None) -> None:
        """
        Escreve uma string no terminal.
        Se row e col forem informados (1-indexed), posiciona o cursor antes de escrever.
        """

    @abstractmethod
    def send_enter(self) -> None:
        """Envia a tecla de ação AID Enter para submissão do buffer de tela ao mainframe."""

    @abstractmethod
    def send_pf(self, key_number: int) -> None:
        """Envia uma tecla de função programável PF (1 a 24)."""

    @abstractmethod
    def send_clear(self) -> None:
        """Envia a tecla AID Clear para limpar a tela do terminal."""

    @abstractmethod
    def get_string(self, row: int, col: int, length: int) -> str:
        """Lê um trecho de texto da tela na linha e coluna especificadas (1-indexed)."""

    @abstractmethod
    def get_screen_lines(self) -> List[str]:
        """Retorna uma lista com todas as 24 linhas de 80 caracteres da tela atual."""

    @abstractmethod
    def find_string(self, text: str) -> Optional[Tuple[int, int]]:
        """Busca um texto na tela e retorna a primeira ocorrência (row, col) 1-indexed, ou None."""

    @abstractmethod
    def wait_for_string(
        self,
        text: str,
        row: Optional[int] = None,
        col: Optional[int] = None,
        timeout: float = 15.0,
    ) -> bool:
        """Aguarda até que o texto apareça na tela (ou na coordenada informada) até o timeout."""

    @abstractmethod
    def wait_for_ready(self, timeout: float = 15.0) -> None:
        """
        Aguarda o mainframe processar a transação e liberar o teclado (status READY).
        """

    def close(self) -> None:
        """Compatibilidade para encerramento seguro."""
        self.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
