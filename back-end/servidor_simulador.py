#!/usr/bin/env python3
"""
servidor_simulador.py
Simula a aplicação de terminal interativa com menus, autenticação,
busca horizontal e marcação de registros com 'X'.
"""

import socket
import time

HOST = "127.0.0.1"
PORT = 2222

DADOS_MOCK = [
    {
        "id": "REG-001",
        "tipo": "Solicitacao de Beneficio",
        "valor": "R$ 1.500,00",
        "status": "Aprovado",
        "data": "10/10/2026"
    },
    {
        "id": "REG-002",
        "tipo": "Reembolso Deslocamento",
        "valor": "R$ 340,50",
        "status": "Em Analise",
        "data": "12/10/2026"
    },
    {
        "id": "REG-003",
        "tipo": "Adiantamento Salarial",
        "valor": "R$ 800,00",
        "status": "Pendente",
        "data": "14/10/2026"
    }
]

def ler_linha(conn):
    buffer = ""
    while True:
        dado = conn.recv(1).decode("utf-8", errors="ignore")
        if not dado:
            return ""
        if dado in ("\r", "\n"):
            break
        buffer += dado
    return buffer.strip()

def rodar_servidor():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[*] Servidor simulador ouvindo em {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        print(f"[+] Conexao recebida de {addr}")

        try:
            # 1. Tela Inicial / Boas-vindas
            conn.sendall(b"\n========================================\n")
            conn.sendall(b"      SISTEMA INTEGRADO LEGADO          \n")
            conn.sendall(b"========================================\n")
            conn.sendall(b"[1] Autenticar no Sistema\n")
            conn.sendall(b"[0] Sair\n")
            conn.sendall(b"Escolha a opcao: ")
            
            opcao = ler_linha(conn)
            if opcao != "1":
                conn.sendall(b"Sessao encerrada.\n")
                conn.close()
                continue

            # 2. Login
            conn.sendall(b"\n--- AUTENTICACAO DE USUARIO ---\n")
            conn.sendall(b"Matricula Operador: ")
            mat_op = ler_linha(conn)
            conn.sendall(b"Senha: ")
            senha_op = ler_linha(conn)

            # 3. Menu Principal (Opcoes 1 a 6)
            conn.sendall(b"\n--- MENU PRINCIPAL ---\n")
            conn.sendall(b"1. Consultas Gerais       4. Parametros\n")
            conn.sendall(b"2. Relatorios Diarios     5. Modulo de Solicitantes\n")
            conn.sendall(b"3. Cadastro de Clientes   6. Finalizar Dia\n")
            conn.sendall(b"Selecione uma opcao (1-6): ")
            
            op_menu1 = ler_linha(conn)

            # 4. Menu Secundario (Opcoes subsequentes)
            conn.sendall(b"\n--- SUBMENU DE SOLICITANTES ---\n")
            conn.sendall(b"08. Extrato Consolidado\n")
            conn.sendall(b"09. Cancelamentos\n")
            conn.sendall(b"10. Detalhamento Individual de Processos\n")
            conn.sendall(b"Opcao desejada: ")
            
            op_menu2 = ler_linha(conn)

            # 5. Entrada Horizontal (Matricula, Digito, Sequencia)
            conn.sendall(b"\n--- CONSULTA DE REGISTROS DO SOLICITANTE ---\n")
            conn.sendall(b"Preencha os campos abaixo:\n")
            
            conn.sendall(b"Matricula: ")
            mat_sol = ler_linha(conn)
            
            conn.sendall(b"Digito: ")
            dig_sol = ler_linha(conn)
            
            conn.sendall(b"Sequencia: ")
            seq_sol = ler_linha(conn)

            # 6. Listagem de Registros para Marcacao com 'X'
            conn.sendall(b"\n--- REGISTROS ENCONTRADOS ---\n")
            conn.sendall(b"Marque com [X] o(s) item(ns) desejado(s):\n")
            
            selecionados = []
            for i, reg in enumerate(DADOS_MOCK, start=1):
                conn.sendall(f"[{i}] [ ] ID: {reg['id']} | Tipo: {reg['tipo']}\nMarcar [X/ENTER pula]: ".encode("utf-8"))
                marcado = ler_linha(conn)
                if marcado.upper() == "X":
                    selecionados.append(reg)

            # 7. Detalhes Sequenciais dos Itens Marcados
            if not selecionados:
                conn.sendall(b"\nNenhum registro selecionado. Pressione ENTER para sair.\n")
                ler_linha(conn)
            else:
                total = len(selecionados)
                for idx, reg in enumerate(selecionados, start=1):
                    conn.sendall(b"\n========================================\n")
                    conn.sendall(f"DETALHE DO REGISTRO ({idx} de {total})\n".encode("utf-8"))
                    conn.sendall(b"========================================\n")
                    conn.sendall(f"ID REGISTRO : {reg['id']}\n".encode("utf-8"))
                    conn.sendall(f"TIPO        : {reg['tipo']}\n".encode("utf-8"))
                    conn.sendall(f"VALOR       : {reg['valor']}\n".encode("utf-8"))
                    conn.sendall(f"STATUS      : {reg['status']}\n".encode("utf-8"))
                    conn.sendall(f"DATA        : {reg['data']}\n".encode("utf-8"))
                    conn.sendall(b"----------------------------------------\n")
                    
                    if idx < total:
                        conn.sendall(b"Pressione ENTER para o proximo registro...")
                        ler_linha(conn)
                    else:
                        conn.sendall(b"FIM DOS REGISTROS. Pressione ENTER para encerrar.")
                        ler_linha(conn)

            conn.sendall(b"\nSessao finalizada com sucesso.\n")
        except Exception as e:
            print(f"[-] Erro na sessao: {e}")
        finally:
            conn.close()
            print("[-] Conexao finalizada.")

if __name__ == "__main__":
    rodar_servidor()
