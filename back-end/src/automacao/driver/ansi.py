"""
Sanitização de sequências de escape ANSI e formatação de cursor/cores VT100.
"""

import re

ANSI_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def limpar_ansi(texto: str) -> str:
    """Remove caracteres de controle ANSI e sequências de formatação do buffer."""
    if not texto:
        return ""
    return ANSI_REGEX.sub("", texto)
