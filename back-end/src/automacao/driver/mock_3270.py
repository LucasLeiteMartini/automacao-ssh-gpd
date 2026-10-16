"""
Simulador em memória da matriz 24x80 do terminal IBM TN3270 (Mock3270Driver).
Permite testar e validar toda a navegação e regras de tela sem conexão com mainframe real.
"""

import time
from typing import List, Optional, Tuple

from automacao.driver.driver_3270_interface import Base3270Driver
from automacao.driver import parsers


# pylint: disable=too-many-instance-attributes
class Mock3270Driver(Base3270Driver):
    """Driver mock que simula uma tela 3270 de 24 linhas por 80 colunas."""

    CATALOGO_SOLICITANTES = {
        ("123456", "0", "1"): [
            {
                "id": "REG-001",
                "tipo": "Solicitacao de Beneficio",
                "valor": "R$ 1.500,00",
                "status": "Aprovado",
                "data": "10/10/2026",
                "row": 8,
                "check_col": 9,
            },
            {
                "id": "REG-002",
                "tipo": "Reembolso Deslocamento",
                "valor": "R$ 340,50",
                "status": "Em Analise",
                "data": "12/10/2026",
                "row": 9,
                "check_col": 9,
            },
            {
                "id": "REG-003",
                "tipo": "Adiantamento Salarial",
                "valor": "R$ 800,00",
                "status": "Pendente",
                "data": "14/10/2026",
                "row": 10,
                "check_col": 9,
            },
        ],
        ("123456", "0", "01"): [
            {
                "id": "REG-001",
                "tipo": "Solicitacao de Beneficio",
                "valor": "R$ 1.500,00",
                "status": "Aprovado",
                "data": "10/10/2026",
                "row": 8,
                "check_col": 9,
            },
            {
                "id": "REG-002",
                "tipo": "Reembolso Deslocamento",
                "valor": "R$ 340,50",
                "status": "Em Analise",
                "data": "12/10/2026",
                "row": 9,
                "check_col": 9,
            },
            {
                "id": "REG-003",
                "tipo": "Adiantamento Salarial",
                "valor": "R$ 800,00",
                "status": "Pendente",
                "data": "14/10/2026",
                "row": 10,
                "check_col": 9,
            },
        ],
        ("654321", "9", "A"): [
            {
                "id": "REG-101",
                "tipo": "Auxilio Transporte",
                "valor": "R$ 450,00",
                "status": "Aprovado",
                "data": "01/10/2026",
                "row": 8,
                "check_col": 9,
            },
            {
                "id": "REG-102",
                "tipo": "Gratificacao por Funcao",
                "valor": "R$ 1.200,00",
                "status": "Pendente",
                "data": "05/10/2026",
                "row": 9,
                "check_col": 9,
            },
        ],
    }

    def __init__(self):
        self.connected = False
        self.cursor_row = 1
        self.cursor_col = 1
        self.current_screen = "LOGIN"
        self.marked_indices: List[int] = []
        self.detail_index = 0
        self.current_records: List[dict] = []
        self.grid: List[List[str]] = [[" " for _ in range(80)] for _ in range(24)]

    def connect(self, host: str, port: int = 23, timeout: float = 15.0) -> None:
        self.connected = True
        self._render_login_screen()

    def disconnect(self) -> None:
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def send_string(self, value: str, row: Optional[int] = None, col: Optional[int] = None) -> None:
        if not self.connected:
            raise ConnectionError("Terminal TN3270 não conectado.")

        r = row if row is not None else self.cursor_row
        c = col if col is not None else self.cursor_col

        # 1-indexed para 0-indexed
        r_idx = r - 1
        c_idx = c - 1

        for i, ch in enumerate(value):
            if c_idx + i < 80 and r_idx < 24:
                self.grid[r_idx][c_idx + i] = ch

        self.cursor_row = r
        self.cursor_col = min(80, c + len(value))

    def send_enter(self) -> None:  # pylint: disable=too-many-branches
        """Processa a transação correspondente à tela ativa."""
        if not self.connected:
            raise ConnectionError("Terminal TN3270 não conectado.")

        if self.current_screen == "LOGIN":
            self.current_screen = "MENU_PRINCIPAL"
            self._render_menu_principal()

        elif self.current_screen == "MENU_PRINCIPAL":
            self.current_screen = "SUBMENU"
            self._render_submenu()

        elif self.current_screen == "SUBMENU":
            self.current_screen = "SOLICITANTE"
            self._render_solicitante_screen()

        elif self.current_screen == "SOLICITANTE":
            mat = self.get_string(
                parsers.POS_SOLICITANTE_MATRICULA[0],
                parsers.POS_SOLICITANTE_MATRICULA[1],
                6,
            ).strip(" ]")
            dig = self.get_string(
                parsers.POS_SOLICITANTE_DIGITO[0],
                parsers.POS_SOLICITANTE_DIGITO[1],
                1,
            ).strip(" ]")
            seq = self.get_string(
                parsers.POS_SOLICITANTE_SEQUENCIA[0],
                parsers.POS_SOLICITANTE_SEQUENCIA[1],
                1,
            ).strip(" ]")

            chave = (mat, dig, seq)
            self.current_records = self.CATALOGO_SOLICITANTES.get(chave, [])
            self.current_screen = "LISTA"
            self._render_lista_screen()

        elif self.current_screen == "LISTA":
            # Lê quais checkboxes foram marcados com 'X'
            self.marked_indices = []
            for idx, rec in enumerate(self.current_records, start=1):
                r_pos = int(str(rec["row"]))
                c_pos = int(str(rec["check_col"]))
                val = self.get_string(r_pos, c_pos, 1)
                if val.upper() == "X":
                    self.marked_indices.append(idx)

            if not self.marked_indices:
                self.current_screen = "FIM"
                self._render_fim_screen("Nenhum registro selecionado.")
            else:
                self.detail_index = 0
                self.current_screen = "DETALHES"
                self._render_detalhe_screen()

        elif self.current_screen == "DETALHES":
            self.detail_index += 1
            if self.detail_index < len(self.marked_indices):
                self._render_detalhe_screen()
            else:
                self.current_screen = "FIM"
                self._render_fim_screen("Sessao finalizada com sucesso.")

    def send_pf(self, key_number: int) -> None:
        """Emula teclas PF (ex: PF3 para voltar/sair)."""
        if key_number == 3:
            self.current_screen = "FIM"
            self._render_fim_screen("Sessao finalizada com sucesso.")

    def send_clear(self) -> None:
        self.grid = [[" " for _ in range(80)] for _ in range(24)]

    def get_string(self, row: int, col: int, length: int) -> str:
        r_idx = row - 1
        c_idx = col - 1
        if 0 <= r_idx < 24 and 0 <= c_idx < 80:
            slice_chars = self.grid[r_idx][c_idx : min(80, c_idx + length)]
            return "".join(slice_chars)
        return ""

    def get_screen_lines(self) -> List[str]:
        return ["".join(row) for row in self.grid]

    def find_string(self, text: str) -> Optional[Tuple[int, int]]:
        for r_idx, row in enumerate(self.grid):
            line = "".join(row)
            pos = line.find(text)
            if pos != -1:
                return (r_idx + 1, pos + 1)
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
            if row is not None and col is not None:
                val = self.get_string(row, col, len(text))
                if text in val:
                    return True
            else:
                if self.find_string(text) is not None:
                    return True
            time.sleep(0.01)
        return False

    def wait_for_ready(self, timeout: float = 15.0) -> None:
        # No simulador em memória, a transição é imediata
        pass

    # ================= TELAS MOCK 24x80 =================

    def _set_line(self, row: int, text: str, start_col: int = 1):
        r_idx = row - 1
        c_idx = start_col - 1
        for i, ch in enumerate(text):
            if c_idx + i < 80:
                self.grid[r_idx][c_idx + i] = ch

    def _render_login_screen(self):
        self.send_clear()
        self._set_line(3, "========================================", 21)
        self._set_line(4, "    SISTEMA INTEGRADO LEGADO (TN3270)   ", 21)
        self._set_line(5, "========================================", 21)
        self._set_line(8, "Matricula Operador : [        ]", 21)
        self._set_line(9, "Senha              : [        ]", 21)
        self._set_line(22, "Preencha suas credenciais e pressione ENTER", 19)

    def _render_menu_principal(self):
        self.send_clear()
        self._set_line(3, "--- MENU PRINCIPAL ---", 30)
        self._set_line(6, "1. Consultas Gerais       4. Parametros", 15)
        self._set_line(7, "2. Relatorios Diarios     5. Modulo de Solicitantes", 15)
        self._set_line(8, "3. Cadastro de Clientes   6. Finalizar Dia", 15)
        self._set_line(20, "Selecione uma opcao (1-6): [ ]", 15)
        self._set_line(22, "Pressione ENTER para confirmar ou PF3 para sair", 18)

    def _render_submenu(self):
        self.send_clear()
        self._set_line(3, "--- SUBMENU DE SOLICITANTES ---", 25)
        self._set_line(6, "08. Extrato Consolidado", 15)
        self._set_line(7, "09. Cancelamentos", 15)
        self._set_line(8, "10. Detalhamento Individual de Processos", 15)
        self._set_line(20, "Opcao desejada: [  ]", 15)
        self._set_line(22, "Pressione ENTER para confirmar ou PF3 para voltar", 18)

    def _render_solicitante_screen(self):
        self.send_clear()
        self._set_line(3, "--- CONSULTA DE REGISTROS DO SOLICITANTE ---", 18)
        self._set_line(8, "Matricula: [      ]        Digito: [ ]     Sequencia: [ ]", 12)
        self._set_line(22, "Preencha os dados e pressione ENTER", 23)

    def _render_lista_screen(self):
        self.send_clear()
        self._set_line(3, "--- REGISTROS ENCONTRADOS ---", 26)
        if not self.current_records:
            self._set_line(8, "Nenhum registro localizado para o solicitante informado.", 15)
            self._set_line(22, "Pressione PF3 para sair ou voltar", 20)
            return

        self._set_line(5, "Marque com [X] o(s) item(ns) desejado(s):", 15)
        for rec in self.current_records:
            line_str = f"[{rec['id'][-1]}] [ ] ID: {rec['id']} | Tipo: {rec['tipo']}"
            self._set_line(rec["row"], line_str, 5)
        self._set_line(22, "Marque com X e pressione ENTER para detalhar ou PF3 para sair", 10)

    def _render_detalhe_screen(self):
        self.send_clear()
        idx_marcado = self.marked_indices[self.detail_index]
        rec = self.current_records[idx_marcado - 1]
        total = len(self.marked_indices)
        current = self.detail_index + 1

        self._set_line(3, f"DETALHE DO REGISTRO ({current} de {total})", 26)
        self._set_line(4, "========================================", 20)
        self._set_line(6, f"ID REGISTRO : {rec['id']}", 15)
        self._set_line(7, f"TIPO        : {rec['tipo']}", 15)
        self._set_line(8, f"VALOR       : {rec['valor']}", 15)
        self._set_line(9, f"STATUS      : {rec['status']}", 15)
        self._set_line(10, f"DATA        : {rec['data']}", 15)
        self._set_line(11, "----------------------------------------", 20)
        if current < total:
            self._set_line(22, "Pressione ENTER para o proximo registro...", 20)
        else:
            self._set_line(22, "FIM DOS REGISTROS. Pressione ENTER para encerrar.", 16)

    def _render_fim_screen(self, msg: str):
        self.send_clear()
        self._set_line(12, f"Sessao finalizada com sucesso. ({msg})", 20)
