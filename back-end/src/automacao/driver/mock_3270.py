"""
Simulador em memória da matriz 24x80 do terminal IBM TN3270 (Mock3270Driver).
Reproduz fielmente as 6 telas do mainframe PRODAM / SPPC (CONFER) para testes automatizados.
"""
# pylint: disable=line-too-long

import time
from typing import Any, Dict, List, Optional, Tuple

from automacao.driver.driver_3270_interface import Base3270Driver


# Registros reais extraídos do 5º print (SPPC/CONFER) para validação do parser e cálculo de saldo
REGISTROS_PRINT_SPPC = [
    {
        "linha_texto": "_ 01/01/11 01/01/12 01/04/12  N  N   30  NP 04/06/12 30  MEM 001510 01/06/12",
        "aquisicao_4dig": "01/01/2011 a 01/01/2012",
        "adq": "30",
        "util": "30",
        "rest": "00",
        "status_extenso": "Nao Pendentes",
        "util_data_4dig": "04/06/2012",
        "doc_tp": "MEM",
        "doc_num": "001510",
        "doc_data_4dig": "01/06/2012",
    },
    {
        "linha_texto": "_ 01/01/12 01/01/13 01/04/13  N  N   30  NP 01/12/13 15  MEM 000605 28/11/13",
        "aquisicao_4dig": "01/01/2012 a 01/01/2013",
        "adq": "30",
        "util": "15",
        "rest": "00",
        "status_extenso": "Nao Pendentes",
        "util_data_4dig": "01/12/2013",
        "doc_tp": "MEM",
        "doc_num": "000605",
        "doc_data_4dig": "28/11/2013",
    },
    {
        "linha_texto": "_ 01/01/12 01/01/13 01/04/13  N  N   30  NP 01/12/14 15  MEM 000328 02/10/14",
        "aquisicao_4dig": "01/01/2012 a 01/01/2013",
        "adq": "30",
        "util": "15",
        "rest": "00",
        "status_extenso": "Nao Pendentes",
        "util_data_4dig": "01/12/2014",
        "doc_tp": "MEM",
        "doc_num": "000328",
        "doc_data_4dig": "02/10/2014",
    },
    {
        "linha_texto": "_ 01/01/13 01/01/14 01/04/14  N  N   30  P  12/05/22 02  MEM 000035 09/05/22",
        "aquisicao_4dig": "01/01/2013 a 01/01/2014",
        "adq": "30",
        "util": "02",
        "rest": "18",
        "status_extenso": "Pendentes",
        "util_data_4dig": "12/05/2022",
        "doc_tp": "MEM",
        "doc_num": "000035",
        "doc_data_4dig": "09/05/2022",
    },
    {
        "linha_texto": "_ 01/01/13 01/01/14 01/04/14  N  N   30  P  27/11/19 10  MEM 000555 13/11/19",
        "aquisicao_4dig": "01/01/2013 a 01/01/2014",
        "adq": "30",
        "util": "10",
        "rest": "18",
        "status_extenso": "Pendentes",
        "util_data_4dig": "27/11/2019",
        "doc_tp": "MEM",
        "doc_num": "000555",
        "doc_data_4dig": "13/11/2019",
    },
    {
        "linha_texto": "_ 01/01/14 01/01/15 01/04/15  N  N   30  NP 07/01/16 30  MEM 000239 09/11/15",
        "aquisicao_4dig": "01/01/2014 a 01/01/2015",
        "adq": "30",
        "util": "30",
        "rest": "00",
        "status_extenso": "Nao Pendentes",
        "util_data_4dig": "07/01/2016",
        "doc_tp": "MEM",
        "doc_num": "000239",
        "doc_data_4dig": "09/11/2015",
    },
    {
        "linha_texto": "_ 01/01/15 01/01/16 01/04/16  N  N   30  NP 19/12/16 15  MEM 000240 16/11/16",
        "aquisicao_4dig": "01/01/2015 a 01/01/2016",
        "adq": "30",
        "util": "15",
        "rest": "00",
        "status_extenso": "Nao Pendentes",
        "util_data_4dig": "19/12/2016",
        "doc_tp": "MEM",
        "doc_num": "000240",
        "doc_data_4dig": "16/11/2016",
    },
    {
        "linha_texto": "_ 01/01/15 01/01/16 01/04/16  N  N   30  NP 17/07/17 15  MEM 000229 29/06/17",
        "aquisicao_4dig": "01/01/2015 a 01/01/2016",
        "adq": "30",
        "util": "15",
        "rest": "00",
        "status_extenso": "Nao Pendentes",
        "util_data_4dig": "17/07/2017",
        "doc_tp": "MEM",
        "doc_num": "000229",
        "doc_data_4dig": "29/06/2017",
    },
    {
        "linha_texto": "_ 01/01/16 01/01/17 01/04/17  N  N   30  P               MEM 000094 24/03/17",
        "aquisicao_4dig": "01/01/2016 a 01/01/2017",
        "adq": "30",
        "util": "00",
        "rest": "30",
        "status_extenso": "Pendentes",
        "util_data_4dig": "24/03/2017",
        "doc_tp": "MEM",
        "doc_num": "000094",
        "doc_data_4dig": "24/03/2017",
    },
    {
        "linha_texto": "_ 01/01/17 01/01/18 01/04/18  N  N   30  NP 07/01/19 26  MEM 000093 23/04/18",
        "aquisicao_4dig": "01/01/2017 a 01/01/2018",
        "adq": "30",
        "util": "26",
        "rest": "04",
        "status_extenso": "Nao Pendentes",
        "util_data_4dig": "07/01/2019",
        "doc_tp": "MEM",
        "doc_num": "000093",
        "doc_data_4dig": "23/04/2018",
    },
]


# pylint: disable=too-many-instance-attributes,line-too-long
class Mock3270Driver(Base3270Driver):
    """Driver mock que simula a matriz 24x80 fiel às telas PRODAM / SPPC."""

    CATALOGO_SOLICITANTES: Dict[Tuple[str, str, str], Dict[str, Any]] = {
        ("211598", "0", "A"): {
            "nome": "DOUGLAS ANDRE FONSECA BARBOSA",
            "lotacao": "001 GPD            006 007         GERENCIA DE INFORMATICA",
            "registros": REGISTROS_PRINT_SPPC,
        },
        ("123456", "0", "1"): {
            "nome": "DOUGLAS ANDRE FONSECA BARBOSA",
            "lotacao": "001 GPD            006 007         GERENCIA DE INFORMATICA",
            "registros": REGISTROS_PRINT_SPPC,
        },
        ("654321", "9", "A"): {
            "nome": "SERVIDOR TESTE SECUNDARIO",
            "lotacao": "002 DELEGACIA GERAL               SETOR ADMINISTRATIVO",
            "registros": REGISTROS_PRINT_SPPC[:2],
        },
        ("777777", "0", "A"): {
            "nome": "SERVIDOR MULTIPLAS PAGINAS",
            "lotacao": "001 GPD            006 007         GERENCIA DE INFORMATICA",
            "registros": REGISTROS_PRINT_SPPC
            + [
                {
                    "linha_texto": "_ 01/01/19 01/01/20 01/04/20  N  N   30  P               MEM 000001 21/03/21",
                    "aquisicao_4dig": "01/01/2019 a 01/01/2020",
                    "adq": "30",
                    "util": "00",
                    "rest": "30",
                    "status_extenso": "Pendentes",
                    "util_data_4dig": "21/03/2021",
                    "doc_tp": "MEM",
                    "doc_num": "000001",
                    "doc_data_4dig": "21/03/2021",
                },
                {
                    "linha_texto": "_ 01/01/20 01/01/21 01/04/21  N  N   30  P               MEM 000002 21/03/21",
                    "aquisicao_4dig": "01/01/2020 a 01/01/2021",
                    "adq": "30",
                    "util": "00",
                    "rest": "30",
                    "status_extenso": "Pendentes",
                    "util_data_4dig": "21/03/2021",
                    "doc_tp": "MEM",
                    "doc_num": "000002",
                    "doc_data_4dig": "21/03/2021",
                },
            ],
        },
    }

    def __init__(self):
        self.connected = False
        self.cursor_row = 23
        self.cursor_col = 7
        self.current_screen = "APLICACAO"
        self.current_page = 1
        self.last_submenu_option = "10"
        self.marked_indices: List[int] = []
        self.detail_index = 0
        self.current_solicitante: Optional[Tuple[str, str, str]] = None
        self.current_records: List[Dict[str, Any]] = []
        self.grid: List[List[str]] = [[" " for _ in range(80)] for _ in range(24)]

    def connect(
        self,
        host: str,
        port: int = 23,
        timeout: float = 15.0,
        secure: bool = False,
    ) -> None:
        self.connected = True
        self._render_aplicacao_screen()

    def disconnect(self) -> None:
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def send_string(self, value: str, row: Optional[int] = None, col: Optional[int] = None) -> None:
        if not self.connected:
            raise ConnectionError("Terminal TN3270 não conectado.")

        r = row if row is not None else self.cursor_row
        c = col if col is not None else self.cursor_col

        # Se estiver na 5ª tela (SPPC/CONFER) e receber os 8 caracteres concatenados (auto-skip)
        if (
            self.current_screen == "SOLICITANTE"
            and row is None
            and col is None
            and len(value) == 8
        ):
            self._write_at(6, 3, value[:6])
            self._write_at(6, 10, value[6:7])
            self._write_at(6, 13, value[7:8])
            return

        self._write_at(r, c, value)
        self.cursor_row = r
        self.cursor_col = min(80, c + len(value))

    def _write_at(self, row: int, col: int, value: str) -> None:
        r_idx = row - 1
        c_idx = col - 1
        for i, ch in enumerate(value):
            if 0 <= r_idx < 24 and 0 <= c_idx + i < 80:
                self.grid[r_idx][c_idx + i] = ch

    def send_enter(self) -> None:  # pylint: disable=too-many-branches
        """Processa a transação correspondente à tela PRODAM/SPPC ativa."""
        if not self.connected:
            raise ConnectionError("Terminal TN3270 não conectado.")

        if self.current_screen == "APLICACAO":
            self.current_screen = "LOGIN"
            self._render_login_screen()

        elif self.current_screen == "LOGIN":
            self.current_screen = "MENU_PRINCIPAL"
            self._render_menu_principal()

        elif self.current_screen == "MENU_PRINCIPAL":
            self.current_screen = "SUBMENU"
            self._render_submenu()

        elif self.current_screen == "SUBMENU":
            self.last_submenu_option = self.get_string(22, 14, 4).strip() or "10"
            self.current_screen = "SOLICITANTE"
            self._render_solicitante_screen()

        elif self.current_screen == "SOLICITANTE":
            mat = self.get_string(6, 3, 6).strip()
            dig = self.get_string(6, 10, 1).strip()
            seq = self.get_string(6, 13, 1).strip().upper()

            chave = (mat, dig, seq)
            self.current_solicitante = chave
            dados_servidor = self.CATALOGO_SOLICITANTES.get(chave)
            if not dados_servidor:
                self._render_solicitante_screen()
                self._set_line(1, ">>> Matricula Inexiste no Cadastro", 2)
                return

            self.current_records = dados_servidor["registros"]
            self.current_page = 1
            self.current_screen = "LISTA"
            self._render_lista_screen(dados_servidor)

        elif self.current_screen == "LISTA":
            self.marked_indices = []
            offset = (self.current_page - 1) * 10
            fatia_pagina = self.current_records[offset : offset + 10]
            for idx in range(len(fatia_pagina)):
                r_pos = 11 + idx
                val = self.get_string(r_pos, 3, 1)
                if val.upper() == "X":
                    self.marked_indices.append(offset + idx + 1)

            if self.marked_indices:
                self.detail_index = 0
                self.current_screen = "DETALHES"
                self._render_detalhe_screen()

        elif self.current_screen == "DETALHES":
            self.detail_index += 1
            if self.detail_index < len(self.marked_indices):
                self._render_detalhe_screen()
            else:
                self.current_screen = "LISTA"
                if self.current_solicitante:
                    self._render_lista_screen(
                        self.CATALOGO_SOLICITANTES.get(self.current_solicitante)
                    )

    def send_pf(self, key_number: int) -> None:
        """
        Emula PF3, PF7 (-Pag) e PF8 (+Pag) fiéis ao mainframe real.
        """
        if key_number == 3:
            if self.current_screen in ("SUBMENU", "SOLICITANTE", "LISTA", "DETALHES"):
                self.current_screen = "MENU_PRINCIPAL"
                self._render_menu_principal()
            else:
                self.current_screen = "APLICACAO"
                self._render_aplicacao_screen()
        elif key_number == 8 and self.current_screen == "LISTA":
            if self.current_page * 10 < len(self.current_records):
                self.current_page += 1
                if self.current_solicitante:
                    self._render_lista_screen(
                        self.CATALOGO_SOLICITANTES.get(self.current_solicitante)
                    )
            else:
                self._set_line(1, ">>> Fim da Paginacao", 2)
        elif key_number == 7 and self.current_screen == "LISTA":
            if self.current_page > 1:
                self.current_page -= 1
                if self.current_solicitante:
                    self._render_lista_screen(
                        self.CATALOGO_SOLICITANTES.get(self.current_solicitante)
                    )

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
        pass

    # ================= TELAS PRODAM / SPPC (24x80) =================

    def _set_line(self, row: int, text: str, start_col: int = 1) -> None:
        self._write_at(row, start_col, text)

    def _render_aplicacao_screen(self) -> None:
        self.send_clear()
        self._set_line(4, "PRODAM - PROCESSAMENTO DE DADOS DO AMAZONAS", 18)
        self._set_line(14, "A ==> CICS DE APLICACOES PRODAM", 18)
        self._set_line(22, "ENTRE COM A APLICACAO", 2)
        self._set_line(23, "==>", 2)
        self.cursor_row, self.cursor_col = 23, 7

    def _render_login_screen(self) -> None:
        self.send_clear()
        self._set_line(1, "CICSCNTR", 2)
        self._set_line(18, "IDENTIFIQUE-SE POR FAVOR :", 30)
        self._set_line(20, "IDENT ==>", 4)
        self._set_line(21, "SENHA ==>", 4)
        self.cursor_row, self.cursor_col = 20, 14

    def _render_menu_principal(self) -> None:
        self.send_clear()
        self._set_line(2, "CEUSPL02", 3)
        self._set_line(3, "Controle de Entrada e Utilizacao de Sistemas", 20)
        self._set_line(10, "( 5 )  SPPC     - SISTEMA PESSOAL DA POLICIA CIVIL", 12)
        self._set_line(23, "=======>", 14)
        self.cursor_row, self.cursor_col = 23, 23

    def _render_submenu(self) -> None:
        self.send_clear()
        self._set_line(2, "SPPC/CONSULTA", 3)
        self._set_line(15, "10 CONFER    Ferias", 6)
        self._set_line(22, "Comando ==>", 2)
        self.cursor_row, self.cursor_col = 22, 14

    def _render_solicitante_screen(self) -> None:
        self.send_clear()
        self._set_line(2, "SPPC/CONFER           SISTEMA PESSOAL DA POLICIA CIVIL", 3)
        self._set_line(3, "Consulta Férias                    PC05  M05A", 36)
        self._set_line(5, "Matric D Seq   Nome", 3)
        self._set_line(7, "Lotacao:", 3)
        self._set_line(15, "Situação.: _   1 - Pendente", 13)
        self.cursor_row, self.cursor_col = 6, 4

    def _render_lista_screen(self, dados_servidor: Optional[Dict[str, Any]]) -> None:
        self.send_clear()
        if not dados_servidor or not self.current_solicitante:
            return

        mat, dig, seq = self.current_solicitante
        self._set_line(2, "SPPC/CONFER           SISTEMA PESSOAL DA POLICIA CIVIL", 3)
        self._set_line(3, "Consulta Férias                    MC5A  NC5A", 36)
        self._set_line(5, "Matric D Seq   Nome", 3)
        self._set_line(6, f"{mat} {dig}  {seq}    {dados_servidor['nome']}", 3)
        self._set_line(7, f"Lotacao: {dados_servidor['lotacao']}", 3)
        self._set_line(
            9,
            "+---Aquisicao---+ Previsao        Dias   Utilizacao  --- Documentos ----",
            5,
        )
        self._set_line(
            10,
            "Inicial     Final Inicial  Ab 13o Adq. St Inicial Dias Tp Numero     Data",
            5,
        )

        offset = (self.current_page - 1) * 10
        for idx, rec in enumerate(self.current_records[offset : offset + 10]):
            self._set_line(11 + idx, rec["linha_texto"], 3)

        self.cursor_row, self.cursor_col = 11, 3

    def _render_detalhe_screen(self) -> None:
        self.send_clear()
        idx_marcado = self.marked_indices[self.detail_index]
        rec = self.current_records[idx_marcado - 1]
        aq_espacos = rec["aquisicao_4dig"].replace("/", " ")
        util_espacos = rec["util_data_4dig"].replace("/", " ")
        doc_data_espacos = rec["doc_data_4dig"].replace("/", " ")

        self._set_line(2, "SPPC/CONFER              SISTEMA PESSOAL DA POLICIA CIVIL           21/10/2026", 3)
        self._set_line(3, "Consulta Férias                    NC5F  M13A", 36)
        self._set_line(8, f"Aquisicao....: {aq_espacos}", 8)
        self._set_line(10, "Dias", 8)
        if rec["util"] == "00":
            self._set_line(
                11,
                f"Adquiridos.: {rec['adq']}                        Pendente.: {rec['rest']}",
                11,
            )
        else:
            self._set_line(
                11,
                f"Adquiridos.: {rec['adq']}    Utilizados.: {rec['util']}   {rec['status_extenso']}",
                11,
            )
        self._set_line(13, "Previsão.....: 01 04 2012  a  30 04 2012", 8)
        self._set_line(
            14,
            f"Utilização...: {util_espacos}  a  {util_espacos}  {rec['util']} Dias",
            8,
        )
        self._set_line(
            16,
            "+-------------------------- Documento ----------------------------+",
            11,
        )
        self._set_line(17, "TP   Numero  Data        Observacao", 11)
        self._set_line(
            18,
            f"{rec['doc_tp']}  {rec['doc_num']}  {doc_data_espacos}  FERIAS CONCEDIDAS_DPI/PC_________________",
            11,
        )
