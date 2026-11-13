"""Módulo de conexão e factory para drivers de terminal IBM TN3270 (pw3270, py3270, mock)."""

# pylint: disable=broad-exception-caught,import-outside-toplevel,too-few-public-methods

import logging
import select
import socket
import ssl
import threading
import time
import warnings
from typing import List, Optional, Tuple

from automacao.core.config import Settings, settings
from automacao.driver.driver_3270_interface import Base3270Driver
from automacao.driver.mock_3270 import Mock3270Driver

logger = logging.getLogger("automacao.driver.3270")


class _TlsLegacyBridge:
    """
    Ponte local loopback (127.0.0.1 -> TLSv1/SECLEVEL=0 remoto).
    Permite que o binário s3270 conecte a mainframes IBM z/OS que exigem TLS 1.0 e cifras
    legadas (ex: AES256-SHA) bloqueadas pelas bibliotecas TLS modernas do sistema operacional.
    """

    def __init__(self, remote_host: str, remote_port: int, timeout: float = 15.0):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.timeout = timeout
        self._srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv_sock.bind(("127.0.0.1", 0))
        self._srv_sock.listen(1)
        self.local_port: int = self._srv_sock.getsockname()[1]
        self._running = True
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _create_tls_context(self) -> ssl.SSLContext:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            ctx.minimum_version = ssl.TLSVersion.TLSv1
        try:
            ctx.set_ciphers("ALL:@SECLEVEL=0")
        except ssl.SSLError:
            pass
        if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
            ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT")
        return ctx

    def _serve(self) -> None:
        client_sock: Optional[socket.socket] = None
        remote_ssl: Optional[ssl.SSLSocket] = None
        try:
            self._srv_sock.settimeout(self.timeout)
            client_sock, _ = self._srv_sock.accept()
            raw_remote = socket.create_connection(
                (self.remote_host, self.remote_port), timeout=self.timeout
            )
            ctx = self._create_tls_context()
            remote_ssl = ctx.wrap_socket(raw_remote, server_hostname=self.remote_host)

            sockets = [client_sock, remote_ssl]
            while self._running:
                rlist, _, _ = select.select(sockets, [], [], 0.5)
                for sock in rlist:
                    data = sock.recv(4096)
                    if not data:
                        return
                    destino = remote_ssl if sock is client_sock else client_sock
                    destino.sendall(data)
        except Exception as exc:
            logger.debug("Encerrando ponte TLS local: %s", exc)
        finally:
            for s in (client_sock, remote_ssl, self._srv_sock):
                if s is not None:
                    try:
                        s.close()
                    except Exception:
                        pass

    def close(self) -> None:
        """Encerra o socket e a thread da ponte TLS local."""
        self._running = False
        try:
            self._srv_sock.close()
        except Exception:
            pass


class Pw3270Driver(Base3270Driver):
    """Driver que utiliza as ligações Python nativas do pw3270 / lib3270 (python3-tn3270)."""

    def __init__(self, session_name: str = ":a"):
        try:
            import tn3270  # type: ignore[import-not-found]

            self.lib = tn3270
            self.session = tn3270.Session(session_name)
        except ImportError as exc:
            raise ImportError(
                "O módulo nativo 'tn3270' (python3-tn3270/lib3270) não está instalado no sistema."
            ) from exc

    def connect(
        self,
        host: str,
        port: int = 23,
        timeout: float = 15.0,
        secure: bool = False,
    ) -> None:
        scheme = "tn3270s" if secure else "tn3270"
        url = f"{scheme}://{host}:{port}"
        self.session.connect(url, int(timeout))
        if not self.is_connected():
            raise ConnectionError(f"Falha ao conectar via pw3270 ao host {url}")

    def disconnect(self) -> None:
        try:
            self.session.disconnect()
        except Exception:
            pass

    def is_connected(self) -> bool:
        return bool(getattr(self.session, "connected", False))

    def send_string(
        self, value: str, row: Optional[int] = None, col: Optional[int] = None
    ) -> None:
        if row is not None and col is not None:
            try:
                self.session.cursor = (row, col)
            except Exception:
                pass
        self.session.set(value)

    def send_enter(self) -> None:
        self.session.enter()
        self.wait_for_ready()

    def send_pf(self, key_number: int) -> None:
        if hasattr(self.session, "pfkey"):
            self.session.pfkey(key_number)
        else:
            self.session.enter()
        self.wait_for_ready()

    def send_clear(self) -> None:
        if hasattr(self.session, "clear"):
            self.session.clear()

    def get_string(self, row: int, col: int, length: int) -> str:
        return str(self.session.get(row, col, length))

    def get_screen_lines(self) -> List[str]:
        lines: List[str] = []
        for r in range(1, 25):
            lines.append(self.get_string(r, 1, 80))
        return lines

    def find_string(self, text: str) -> Optional[Tuple[int, int]]:
        res = self.session.find(text)
        if res:
            return (res[0], res[1]) if isinstance(res, (tuple, list)) else None
        return None

    def wait_for_string(
        self,
        text: str,
        row: Optional[int] = None,
        col: Optional[int] = None,
        timeout: float = 15.0,
    ) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            self.wait_for_ready(timeout)
            if row is not None and col is not None:
                if text in self.get_string(row, col, len(text)):
                    return True
            elif self.find_string(text) is not None:
                return True
            time.sleep(0.1)
        raise TimeoutError(
            f"Timeout ({timeout}s) aguardando texto '{text}' na tela TN3270."
        )

    def wait_for_ready(self, timeout: float = 15.0) -> None:
        if hasattr(self.session, "wait"):
            self.session.wait(int(timeout))


class Py3270Driver(Base3270Driver):
    """Driver que utiliza py3270 / s3270 headless com suporte a ponte TLSv1 legada."""

    def __init__(self):
        self._tls_bridge: Optional[_TlsLegacyBridge] = None
        try:
            from py3270 import Emulator  # type: ignore[import-untyped]

            self.em = Emulator(
                visible=False,
                args=["-xrm", "s3270.verifyHostCert: false"],
            )
        except Exception as exc:
            raise ImportError(
                "O pacote py3270 requer o binário 's3270' instalado no sistema operacional."
            ) from exc

    def connect(
        self,
        host: str,
        port: int = 23,
        timeout: float = 15.0,
        secure: bool = False,
    ) -> None:
        if secure:
            self._tls_bridge = _TlsLegacyBridge(host, port, timeout=timeout)
            target = f"127.0.0.1:{self._tls_bridge.local_port}"
        else:
            target = f"{host}:{port}"
        self.em.connect(target)
        self.wait_for_ready(timeout)

    def disconnect(self) -> None:
        try:
            self.em.terminate()
        except Exception:
            pass
        if self._tls_bridge is not None:
            self._tls_bridge.close()
            self._tls_bridge = None

    def is_connected(self) -> bool:
        return self.em.is_connected()

    def send_string(
        self, value: str, row: Optional[int] = None, col: Optional[int] = None
    ) -> None:
        self.em.send_string(value, ypos=row, xpos=col)

    def send_enter(self) -> None:
        self.em.send_enter()
        self.wait_for_ready()

    def send_pf(self, key_number: int) -> None:
        self.em.send_pf(key_number)
        self.wait_for_ready()

    def send_clear(self) -> None:
        if hasattr(self.em, "send_clear"):
            getattr(self.em, "send_clear")()
        elif hasattr(self.em, "exec_command"):
            getattr(self.em, "exec_command")(b"Clear")

    def get_string(self, row: int, col: int, length: int) -> str:
        cmd = self.em.exec_command(
            f"Ascii({row - 1},{col - 1},{length})".encode("ascii")
        )
        if cmd.data:
            return cmd.data[0].decode("utf-8", errors="replace")
        return ""

    def get_screen_lines(self) -> List[str]:
        lines: List[str] = []
        for r in range(1, 25):
            lines.append(self.get_string(r, 1, 80))
        return lines

    def find_string(self, text: str) -> Optional[Tuple[int, int]]:
        for r in range(1, 25):
            line = self.get_string(r, 1, 80)
            c = line.find(text)
            if c != -1:
                return (r, c + 1)
        return None

    def wait_for_string(
        self,
        text: str,
        row: Optional[int] = None,
        col: Optional[int] = None,
        timeout: float = 15.0,
    ) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            self.wait_for_ready(timeout)
            if row is not None and col is not None:
                if text in self.get_string(row, col, len(text)):
                    return True
            elif self.find_string(text) is not None:
                return True
            time.sleep(0.1)
        raise TimeoutError(
            f"Timeout ({timeout}s) aguardando texto '{text}' na tela TN3270."
        )

    def wait_for_ready(self, timeout: float = 15.0) -> None:
        try:
            self.em.wait_for_field()
        except Exception:
            pass


def conectar_terminal_3270(config: Optional[Settings] = None) -> Base3270Driver:
    """
    Factory que instancia o driver TN3270 adequado.
    Em MODO_TESTE_LOCAL retorna Mock3270Driver.
    Em produção, tenta carregar o driver nativo pw3270 ou py3270 (s3270).
    """
    cfg = config or settings

    if cfg.MODO_TESTE_LOCAL:
        driver = Mock3270Driver()
        driver.connect(
            cfg.LOCAL_HOST,
            cfg.PORT,
            cfg.TERMINAL_TIMEOUT_SECONDS,
            secure=cfg.SECURE_CONNECTION,
        )
        return driver

    # Tenta pw3270 nativo primeiro
    try:
        pw_driver = Pw3270Driver()
        pw_driver.connect(
            cfg.HOST,
            cfg.PORT,
            cfg.TERMINAL_TIMEOUT_SECONDS,
            secure=cfg.SECURE_CONNECTION,
        )
        return pw_driver
    except Exception as e_pw:
        logger.warning(
            "pw3270 nativo não disponível: %s. Tentando py3270 (s3270)...", e_pw
        )

    # Fallback para py3270 / s3270
    try:
        py_driver = Py3270Driver()
        py_driver.connect(
            cfg.HOST,
            cfg.PORT,
            cfg.TERMINAL_TIMEOUT_SECONDS,
            secure=cfg.SECURE_CONNECTION,
        )
        return py_driver
    except Exception as e_py:
        logger.error("Nenhum emulador 3270 disponível no sistema: %s", e_py)
        msg_erro = "Não foi possível conectar ao sistema"
        raise RuntimeError(msg_erro) from e_py
