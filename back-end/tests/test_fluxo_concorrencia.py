"""
Testes automatizados da API de automação de terminal legado e controle de concorrência.
Valida ANSI cleaning, parsers isolados, execução em duas fases e proteção com Lock.
"""

import asyncio
import threading
import time
import pytest
from httpx import ASGITransport, AsyncClient

from automacao.driver.ansi import limpar_ansi
from automacao.driver.parsers import parse_detalhe_registro, parse_lista_registros
from automacao.main import app
from servidor_simulador import rodar_servidor


@pytest.fixture(scope="session", autouse=True)
def iniciar_simulador():
    """Inicia o servidor_simulador em uma thread daemon para os testes de integração."""
    thread = threading.Thread(target=rodar_servidor, daemon=True)
    thread.start()
    # Aguarda o socket subir
    time.sleep(0.3)
    yield


def test_limpar_ansi():
    texto_com_ansi = "\x1B[31mErro no sistema\x1B[0m\r\n\x1B[2JTela Limpa"
    resultado = limpar_ansi(texto_com_ansi)
    assert resultado == "Erro no sistema\r\nTela Limpa"


def test_parsers_lista_e_detalhes():
    buffer_mock_lista = (
        "[1] [ ] ID: REG-001 | Tipo: Solicitacao de Beneficio\n"
        "[2] [ ] ID: REG-002 | Tipo: Reembolso Deslocamento\n"
        "[3] [ ] ID: REG-003 | Tipo: Adiantamento Salarial\n"
    )
    itens = parse_lista_registros(buffer_mock_lista)
    assert len(itens) == 3
    assert itens[0] == {"indice": 1, "id": "REG-001", "descricao": "Solicitacao de Beneficio"}
    assert itens[1]["id"] == "REG-002"
    assert itens[2]["id"] == "REG-003"

    buffer_mock_detalhe = (
        "DETALHE DO REGISTRO (1 de 2)\n"
        "ID REGISTRO : REG-001\n"
        "TIPO        : Solicitacao de Beneficio\n"
        "VALOR       : R$ 1.500,00\n"
        "STATUS      : Aprovado\n"
        "DATA        : 10/10/2026\n"
    )
    detalhes = parse_detalhe_registro(buffer_mock_detalhe)
    assert detalhes["id"] == "REG-001"
    assert detalhes["tipo"] == "Solicitacao de Beneficio"
    assert detalhes["valor"] == "R$ 1.500,00"
    assert detalhes["status"] == "Aprovado"
    assert detalhes["data"] == "10/10/2026"


def test_fase1_consulta_registros():
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "123456", "digito": "0", "sequencia": "01"},
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
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/solicitante/detalhes",
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "01",
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
    Dispara duas requisições simultâneas. Como o simulador só atende uma conexão
    por vez e a sessão é monousuário, o operator_lock serializa os acessos sem colisões.
    """
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            req1 = client.post(
                "/api/solicitante/registros",
                json={"matricula": "123456", "digito": "0", "sequencia": "01"},
            )
            req2 = client.post(
                "/api/solicitante/detalhes",
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "01",
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
