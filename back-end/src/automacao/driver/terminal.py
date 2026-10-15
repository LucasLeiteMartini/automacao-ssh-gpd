"""
Driver de baixo nível para comunicação com o terminal interativo (Paramiko VT100 ou Raw Socket).
Garante fechamento seguro, cadência de digitação e tratamento de timeouts e erros de sessão.
"""

import socket
import time
from typing import Optional

import paramiko

from automacao.core.config import Settings, settings
from automacao.core.security import TerminalTimeoutError, UsuarioJaConectadoError
from automacao.driver.ansi import limpar_ansi
from automacao.driver.parsers import GATILHO_ACESSO_NEGADO, GATILHO_USUARIO_CONECTADO


class TerminalDriver:
    """Wrapper para padronizar o envio e leitura via Paramiko Channel ou Raw Socket."""

    def __init__(self, stream, ssh_client: Optional[paramiko.SSHClient] = None):
        self.stream = stream
        self.ssh_client = ssh_client
        self.buffer_acumulado = ""

    def send(self, data: str, delay: Optional[float] = None) -> None:
        """Envia comandos para o terminal com pequena cadência para evitar buffer overflow no legado."""
        pausa = delay if delay is not None else settings.CADENCIA_ENVIO_SEGUNDOS
        if pausa > 0:
            time.sleep(pausa)

        payload = data.encode("utf-8")
        if hasattr(self.stream, "sendall"):
            self.stream.sendall(payload)
        else:
            self.stream.send(payload)

    def esperar(self, texto_gatilho: str, timeout: Optional[float] = None) -> str:
        """Lê o buffer até encontrar o texto_gatilho ou atingir o timeout."""
        tempo_limite = timeout if timeout is not None else settings.TERMINAL_TIMEOUT_SECONDS
        inicio = time.time()
        buffer = ""

        while time.time() - inicio < tempo_limite:
            chunk = ""
            if hasattr(self.stream, "recv_ready"):
                if self.stream.recv_ready():
                    chunk = self.stream.recv(1024).decode("utf-8", errors="ignore")
            else:
                self.stream.settimeout(0.5)
                try:
                    chunk = self.stream.recv(1024).decode("utf-8", errors="ignore")
                except socket.timeout:
                    chunk = ""

            if chunk:
                buffer += chunk
                buffer_limpo = limpar_ansi(buffer)

                # Checagem de mensagens de erro críticas do sistema legado
                if GATILHO_USUARIO_CONECTADO.lower() in buffer_limpo.lower():
                    raise UsuarioJaConectadoError(
                        "Operador já conectado no sistema legado. Aguarde encerramento da sessão."
                    )
                if GATILHO_ACESSO_NEGADO.lower() in buffer_limpo.lower():
                    raise PermissionError("Acesso negado no sistema legado.")

                if texto_gatilho in buffer_limpo:
                    self.buffer_acumulado += buffer
                    return buffer_limpo

            time.sleep(0.05)

        raise TerminalTimeoutError(
            f"Timeout ({tempo_limite}s) aguardando por '{texto_gatilho}'. "
            f"Buffer recebido:\n{limpar_ansi(buffer)}"
        )

    def esperar_um_dos(self, gatilhos: list[str], timeout: Optional[float] = None) -> tuple[str, str]:
        """Lê o buffer até encontrar qualquer um dos gatilhos especificados. Retorna (gatilho_encontrado, buffer_limpo)."""
        tempo_limite = timeout if timeout is not None else settings.TERMINAL_TIMEOUT_SECONDS
        inicio = time.time()
        buffer = ""

        while time.time() - inicio < tempo_limite:
            chunk = ""
            if hasattr(self.stream, "recv_ready"):
                if self.stream.recv_ready():
                    chunk = self.stream.recv(1024).decode("utf-8", errors="ignore")
            else:
                self.stream.settimeout(0.5)
                try:
                    chunk = self.stream.recv(1024).decode("utf-8", errors="ignore")
                except socket.timeout:
                    chunk = ""

            if chunk:
                buffer += chunk
                buffer_limpo = limpar_ansi(buffer)

                # Checagem de mensagens de erro críticas do sistema legado
                if GATILHO_USUARIO_CONECTADO.lower() in buffer_limpo.lower():
                    raise UsuarioJaConectadoError(
                        "Operador já conectado no sistema legado. Aguarde encerramento da sessão."
                    )
                if GATILHO_ACESSO_NEGADO.lower() in buffer_limpo.lower():
                    raise PermissionError("Acesso negado no sistema legado.")

                for g in gatilhos:
                    if g in buffer_limpo:
                        self.buffer_acumulado += buffer
                        return g, buffer_limpo

            time.sleep(0.05)

        raise TerminalTimeoutError(
            f"Timeout ({tempo_limite}s) aguardando por qualquer um dos gatilhos {gatilhos}. "
            f"Buffer recebido:\n{limpar_ansi(buffer)}"
        )

    def close(self) -> None:
        """Encerra com segurança o canal e o cliente SSH/socket associados."""
        try:
            if hasattr(self.stream, "close"):
                self.stream.close()
        except Exception:
            pass

        if self.ssh_client is not None:
            try:
                self.ssh_client.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def conectar_terminal(config: Optional[Settings] = None) -> TerminalDriver:
    """Cria e retorna uma conexão com o terminal legado baseada nas configurações."""
    cfg = config or settings

    if cfg.MODO_TESTE_LOCAL:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(cfg.TERMINAL_TIMEOUT_SECONDS)
        sock.connect((cfg.LOCAL_HOST, cfg.SSH_PORT))
        return TerminalDriver(stream=sock)

    cliente_ssh = paramiko.SSHClient()
    cliente_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente_ssh.connect(
        cfg.SSH_HOST,
        port=cfg.SSH_PORT,
        username=cfg.SSH_USER,
        password=cfg.SSH_PASS,
        timeout=cfg.TERMINAL_TIMEOUT_SECONDS,
    )
    canal = cliente_ssh.invoke_shell(term="vt100", width=80, height=24)
    return TerminalDriver(stream=canal, ssh_client=cliente_ssh)
