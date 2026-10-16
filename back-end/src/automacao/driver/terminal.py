"""Módulo de conexão e factory para drivers de terminal IBM TN3270 (pw3270, py3270, mock)."""
# pylint: disable=broad-exception-caught,import-outside-toplevel

import logging
from typing import List, Optional, Tuple

from automacao.core.config import Settings, settings
from automacao.driver.driver_3270_interface import Base3270Driver
from automacao.driver.mock_3270 import Mock3270Driver

logger = logging.getLogger("automacao.driver.3270")


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

    def connect(self, host: str, port: int = 23, timeout: float = 15.0) -> None:
        url = f"tn3270://{host}:{port}"
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

    def send_string(self, value: str, row: Optional[int] = None, col: Optional[int] = None) -> None:
        if row is not None and col is not None:
            # pw3270 get/set usa linha e coluna
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
        # pw3270 get(row, col, length)
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
        try:
            if hasattr(self.session, "wait_for_string"):
                return bool(self.session.wait_for_string(text, int(timeout)))
        except Exception:
            pass
        return True

    def wait_for_ready(self, timeout: float = 15.0) -> None:
        if hasattr(self.session, "wait"):
            self.session.wait(int(timeout))


class Py3270Driver(Base3270Driver):
    """Driver alternativo que utiliza py3270 / s3270 headless."""

    def __init__(self):
        try:
            from py3270 import Emulator  # type: ignore[import-untyped]
            self.em = Emulator(visible=False)
        except Exception as exc:
            raise ImportError(
                "O pacote py3270 requer o binário 's3270' instalado no sistema operacional."
            ) from exc

    def connect(self, host: str, port: int = 23, timeout: float = 15.0) -> None:
        target = f"{host}:{port}" if port != 23 else host
        self.em.connect(target)
        self.wait_for_ready(timeout)

    def disconnect(self) -> None:
        try:
            self.em.terminate()
        except Exception:
            pass

    def is_connected(self) -> bool:
        return self.em.is_connected()

    def send_string(self, value: str, row: Optional[int] = None, col: Optional[int] = None) -> None:
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
        return self.em.string_get(row, col, length)

    def get_screen_lines(self) -> List[str]:
        lines: List[str] = []
        for r in range(1, 25):
            lines.append(self.em.string_get(r, 1, 80))
        return lines

    def find_string(self, text: str) -> Optional[Tuple[int, int]]:
        for r in range(1, 25):
            line = self.em.string_get(r, 1, 80)
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
        if row is not None and col is not None:
            return self.em.string_found(row, col, text)
        return self.find_string(text) is not None

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
        driver.connect(cfg.LOCAL_HOST, cfg.SSH_PORT, cfg.TERMINAL_TIMEOUT_SECONDS)
        return driver

    # Tenta pw3270 nativo primeiro
    try:
        pw_driver = Pw3270Driver()
        pw_driver.connect(cfg.SSH_HOST, cfg.SSH_PORT, cfg.TERMINAL_TIMEOUT_SECONDS)
        return pw_driver
    except Exception as e_pw:
        logger.warning("pw3270 nativo não disponível: %s. Tentando py3270 (s3270)...", e_pw)

    # Fallback para py3270 / s3270
    try:
        py_driver = Py3270Driver()
        py_driver.connect(cfg.SSH_HOST, cfg.SSH_PORT, cfg.TERMINAL_TIMEOUT_SECONDS)
        return py_driver
    except Exception as e_py:
        logger.error("Nenhum emulador 3270 disponível no sistema: %s", e_py)
        msg_erro = (
            f"Não foi possível conectar ao host TN3270 {cfg.SSH_HOST}:{cfg.SSH_PORT}. "
            "Certifique-se de ter o python3-tn3270 ou s3270 instalados."
        )
        raise RuntimeError(msg_erro) from e_py
