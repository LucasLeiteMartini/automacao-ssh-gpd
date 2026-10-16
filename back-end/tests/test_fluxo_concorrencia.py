"""
Testes automatizados da API de automação TN3270 (pw3270) e controle de concorrência.
Valida operações em matriz 24x80, parsers 3270, execução em duas fases e proteção com Lock.
"""

import asyncio
from httpx import ASGITransport, AsyncClient

from automacao.driver.mock_3270 import Mock3270Driver
from automacao.driver.parsers import (
    parse_detalhe_registro_3270,
    parse_lista_registros_3270,
    POS_SOLICITANTE_MATRICULA,
    POS_SOLICITANTE_DIGITO,
    POS_SOLICITANTE_SEQUENCIA,
)
from automacao.main import app


def test_mock_3270_driver_operacoes_matriz():
    """Valida as operações de posicionamento, leitura e submissão na matriz 24x80."""
    driver = Mock3270Driver()
    driver.connect("127.0.0.1", 23)

    assert driver.is_connected()
    # Verifica banner da tela de login
    assert "SISTEMA INTEGRADO LEGADO" in driver.get_string(4, 21, 40)

    # Preenche credenciais em coordenadas específicas
    driver.send_string("OP-9876", row=8, col=36)
    driver.send_string("SenhaForte@2026", row=9, col=36)
    assert driver.get_string(8, 36, 7) == "OP-9876"

    # Envia AID Enter para avançar para o menu
    driver.send_enter()
    assert "MENU PRINCIPAL" in driver.get_string(3, 30, 25)

    driver.disconnect()
    assert not driver.is_connected()


def test_parsers_3270_lista_e_detalhes():
    """Valida a extração de registros a partir da matriz de tela 24x80 com dados dinâmicos."""
    driver = Mock3270Driver()
    driver.connect("127.0.0.1", 23)

    # Navega até a tela de solicitante
    driver.send_enter()  # Menu Principal
    driver.send_enter()  # Submenu
    driver.send_enter()  # Solicitante

    # Preenche dados do solicitante 123456-0 / seq 1
    driver.send_string("123456", row=POS_SOLICITANTE_MATRICULA[0], col=POS_SOLICITANTE_MATRICULA[1])
    driver.send_string("0", row=POS_SOLICITANTE_DIGITO[0], col=POS_SOLICITANTE_DIGITO[1])
    driver.send_string("1", row=POS_SOLICITANTE_SEQUENCIA[0], col=POS_SOLICITANTE_SEQUENCIA[1])
    driver.send_enter()  # Lista de Registros

    # Extrai lista
    registros = parse_lista_registros_3270(driver)
    assert len(registros) == 3
    assert registros[0]["id"] == "REG-001"
    assert registros[0]["descricao"] == "Solicitacao de Beneficio"
    assert registros[0]["row"] == 8
    assert registros[0]["check_col"] == 9
    assert registros[1]["id"] == "REG-002"
    assert registros[2]["id"] == "REG-003"

    # Marca registro 1 com 'X' e envia Enter
    driver.send_string("X", row=registros[0]["row"], col=registros[0]["check_col"])
    driver.send_enter()

    # Valida tela de detalhe
    detalhes = parse_detalhe_registro_3270(driver)
    assert detalhes["id"] == "REG-001"
    assert detalhes["tipo"] == "Solicitacao de Beneficio"
    assert detalhes["valor"] == "R$ 1.500,00"
    assert detalhes["status"] == "Aprovado"
    assert detalhes["data"] == "10/10/2026"

    driver.disconnect()


def test_fase1_consulta_registros():
    """Valida a rota HTTP POST /api/solicitante/registros contra o driver TN3270."""
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "123456", "digito": "0", "sequencia": "1"},
            )
            assert response.status_code == 200
            dados = response.json()
            assert dados["solicitante"]["matricula"] == "123456"
            assert len(dados["registros"]) == 3
            assert dados["registros"][0]["id"] == "REG-001"
            assert dados["registros"][1]["id"] == "REG-002"
            assert dados["registros"][2]["id"] == "REG-003"

    asyncio.run(_run())


def test_fase2_extrair_detalhes():
    """Valida a rota HTTP POST /api/solicitante/detalhes com marcação dos itens [1, 3]."""
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/solicitante/detalhes",
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "1",
                    "indices_selecionados": [1, 3],
                },
            )
            assert response.status_code == 200
            corpo = response.json()
            assert corpo["status"] == "sucesso"
            assert len(corpo["dados"]) == 2
            assert corpo["dados"][0]["id"] == "REG-001"
            assert corpo["dados"][0]["valor"] == "R$ 1.500,00"
            assert corpo["dados"][1]["id"] == "REG-003"
            assert corpo["dados"][1]["valor"] == "R$ 800,00"

    asyncio.run(_run())


def test_concorrencia_e_serializacao_com_lock():
    """
    Dispara duas requisições simultâneas contra o backend 3270.
    O operator_lock garante que os acessos à credencial do mainframe ocorram de forma serializada.
    """
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            req1 = client.post(
                "/api/solicitante/registros",
                json={"matricula": "123456", "digito": "0", "sequencia": "1"},
            )
            req2 = client.post(
                "/api/solicitante/detalhes",
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "1",
                    "indices_selecionados": [2],
                },
            )

            resp1, resp2 = await asyncio.gather(req1, req2)
            assert resp1.status_code == 200
            assert resp2.status_code == 200
            assert len(resp1.json()["registros"]) == 3
            assert len(resp2.json()["dados"]) == 1
            assert resp2.json()["dados"][0]["id"] == "REG-002"

    asyncio.run(_run())


def test_validacao_campos_solicitante_invalido():
    """Valida que entradas fora da especificação (6 números, 1 dígito, 1 alfanumérico) retornam 422."""
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Matrícula com 5 dígitos (deve ter 6)
            resp_mat = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "12345", "digito": "0", "sequencia": "1"},
            )
            assert resp_mat.status_code == 422

            # Dígito com 2 números (deve ter 1)
            resp_dig = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "123456", "digito": "00", "sequencia": "1"},
            )
            assert resp_dig.status_code == 422

            # Sequência com 2 caracteres (deve ter 1 alfanumérico)
            resp_seq = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "123456", "digito": "0", "sequencia": "01"},
            )
            assert resp_seq.status_code == 422

    asyncio.run(_run())


def test_solicitante_dinamico_sem_registros_e_outro_cadastrado():
    """Valida o mock dinâmico retornando lista vazia e solicitante alternativo."""
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Solicitante inexistente / sem registros
            resp_vazio = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "999999", "digito": "9", "sequencia": "Z"},
            )
            assert resp_vazio.status_code == 200
            assert resp_vazio.json()["registros"] == []

            # 2. Solicitante B cadastrado (654321-9 / A)
            resp_b = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "654321", "digito": "9", "sequencia": "A"},
            )
            assert resp_b.status_code == 200
            registros_b = resp_b.json()["registros"]
            assert len(registros_b) == 2
            assert registros_b[0]["id"] == "REG-101"
            assert registros_b[1]["id"] == "REG-102"

    asyncio.run(_run())
