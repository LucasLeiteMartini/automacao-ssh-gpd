#!/usr/bin/env python3
"""
cliente_automacao_ssh.py
Robô para automação de terminal interativo usando Paramiko (ou socket direto para testes).
"""

import os
import re
import socket
import time

import paramiko
from dotenv import load_dotenv

load_dotenv()

# ================= CONFIGURAÇÕES =================
MODO_TESTE_LOCAL = True  # Mude para False para rodar em SSH real

# Credenciais do Servidor / SSH
SSH_HOST = os.environ.get("SSH_HOST")
SSH_PORT = os.environ.get("SSH_HOST")
SSH_USER = os.environ.get("SSH_USER")
SSH_PASS = os.environ.get("SSH_PASS")

# Credenciais da Aplicação (Operador)
APP_MATRICULA = os.environ.get("APP_MATRICULA")
APP_SENHA = os.environ.get("APP_SENHA")

# Dados do Solicitante para Consulta
SOLICITANTE_MATRICULA = os.environ.get("SOLICITANTE_MATRICULA")
SOLICITANTE_DIGITO = os.environ.get("SOLICITANTE_DIGITO")
SOLICITANTE_SEQUENCIA = os.environ.get("SOLICITANTE_SEQUENCIA")

# Índices que queremos marcar com 'X' na lista (ex: primeiro e terceiro)
ITENS_PARA_MARCAR = [1, 3]
# =================================================


def limpar_ansi(texto: str) -> str:
    """Remove caracteres de controle ANSI e formatação de cursor/cores."""
    ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_regex.sub("", texto)


class TerminalDriver:
    """Wrapper para padronizar o envio e leitura via Paramiko Channel ou Raw Socket."""

    def __init__(self, stream):
        self.stream = stream

    def send(self, data: str):
        # Pequena pausa para garantir cadência aceita por terminais legados
        time.sleep(0.05)
        if hasattr(self.stream, "sendall"):
            self.stream.sendall(data.encode("utf-8"))
        else:
            self.stream.send(data.encode("utf-8"))

    def esperar(self, texto_gatilho: str, timeout: int = 15) -> str:
        """Lê o buffer até encontrar a âncora especificada."""
        inicio = time.time()
        buffer = ""

        while time.time() - inicio < timeout:
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
                if texto_gatilho in buffer_limpo:
                    return buffer_limpo
            time.sleep(0.1)

        raise TimeoutError(
            f"Timeout esperando por '{texto_gatilho}'. Buffer recebido até o momento:\n{buffer}"
        )


def executar_fluxo():
    print("[*] Iniciando conexao...")

    if MODO_TESTE_LOCAL:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SSH_HOST, SSH_PORT))
        term = TerminalDriver(sock)
        cliente_ssh = None
    else:
        cliente_ssh = paramiko.SSHClient()
        cliente_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cliente_ssh.connect(
            SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS
        )
        canal = cliente_ssh.invoke_shell(term="vt100", width=80, height=24)
        term = TerminalDriver(canal)

    try:
        # 1. Tela Inicial
        term.esperar("Escolha a opcao:")
        term.send("1\n")

        # 2. Autenticação na Aplicação
        term.esperar("Matricula Operador:")
        term.send(f"{APP_MATRICULA}\n")

        term.esperar("Senha:")
        term.send(f"{APP_SENHA}\n")

        # 3. Menu Principal (Opção 5)
        term.esperar("Selecione uma opcao (1-6):")
        term.send("5\n")

        # 4. Submenu (Opção 10)
        term.esperar("Opcao desejada:")
        term.send("10\n")

        # 5. Entrada Horizontal dos Dados do Solicitante
        term.esperar("Matricula:")
        term.send(f"{SOLICITANTE_MATRICULA}\n")

        term.esperar("Digito:")
        term.send(f"{SOLICITANTE_DIGITO}\n")

        term.esperar("Sequencia:")
        term.send(f"{SOLICITANTE_SEQUENCIA}\n")

        # 6. Marcação com 'X' na Lista de Registros
        print("[*] Percorrendo e marcando registros solicitados...")
        for i in range(1, 4):  # mock possui 3 itens
            term.esperar("Marcar [X/ENTER pula]:")
            if i in ITENS_PARA_MARCAR:
                term.send("X\n")
            else:
                term.send("\n")

        # 7. Recuperação e Extração dos Dados Detalhados
        registros_extraidos = []
        qtd_marcados = len(ITENS_PARA_MARCAR)

        for idx in range(1, qtd_marcados + 1):
            tela = term.esperar(f"DETALHE DO REGISTRO ({idx} de {qtd_marcados})")

            # Parser simples por Regex nos campos retornados
            id_reg = re.search(r"ID REGISTRO\s*:\s*(.+)", tela)
            tipo_reg = re.search(r"TIPO\s*:\s*(.+)", tela)
            valor_reg = re.search(r"VALOR\s*:\s*(.+)", tela)
            status_reg = re.search(r"STATUS\s*:\s*(.+)", tela)
            data_reg = re.search(r"DATA\s*:\s*(.+)", tela)

            dados = {
                "id": id_reg.group(1).strip() if id_reg else None,
                "tipo": tipo_reg.group(1).strip() if tipo_reg else None,
                "valor": valor_reg.group(1).strip() if valor_reg else None,
                "status": status_reg.group(1).strip() if status_reg else None,
                "data": data_reg.group(1).strip() if data_reg else None,
            }
            registros_extraidos.append(dados)

            # Avança para o próximo ou encerra
            term.send("\n")

        # Aguarda finalização da sessão
        term.esperar("Sessao finalizada com sucesso.")
        print("[+] Fluxo concluido com exito!")

        # 8. Exibição dos Dados Estruturados
        print("\n--- DADOS RECUPERADOS PELO SCRIPT ---")
        for reg in registros_extraidos:
            print(reg)

    finally:
        if MODO_TESTE_LOCAL:
            sock.close()
        else:
            canal.close()
            cliente_ssh.close()


if __name__ == "__main__":
    executar_fluxo()
