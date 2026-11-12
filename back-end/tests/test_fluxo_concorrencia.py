"""
Testes automatizados da API de automação TN3270 (PRODAM / SPPC - CONFER) e controle de concorrência.
Valida navegação nas 5 telas reais, cálculo de saldo agrupado por Período de Aquisição e Lock.
"""

import asyncio
from httpx import ASGITransport, AsyncClient
import pytest

from automacao.core.config import settings
from automacao.driver.mock_3270 import Mock3270Driver
from automacao.driver.parsers import (
    parse_cabecalho_solicitante_3270,
    parse_detalhe_registro_3270,
    parse_lista_registros_3270,
)
from automacao.main import app


@pytest.fixture(autouse=True)
def _forcar_modo_mock_nos_testes():
    """Garante que a suíte de testes unitários use o Mock3270Driver mesmo com MODO_TESTE_LOCAL=false no .env."""
    valor_original = settings.MODO_TESTE_LOCAL
    object.__setattr__(settings, "MODO_TESTE_LOCAL", True)
    yield
    object.__setattr__(settings, "MODO_TESTE_LOCAL", valor_original)


def test_mock_3270_driver_fluxo_prodam_sppc():
    """Valida a navegação pelas 5 telas PRODAM/SPPC e logoff com duplo PF3 na matriz 24x80."""
    driver = Mock3270Driver()
    driver.connect("127.0.0.1", 23)

    assert driver.is_connected()
    # 1ª Tela: PRODAM
    assert driver.find_string("ENTRE COM A APLICACAO") is not None
    driver.send_string("A", row=23, col=7)
    driver.send_enter()

    # 2ª Tela: CICSCNTR
    assert driver.find_string("CICSCNTR") is not None
    driver.send_string("OPERADOR", row=20, col=14)
    driver.send_string("SENHA123", row=21, col=14)
    driver.send_enter()

    # 3ª Tela: CEUSPL02
    assert driver.find_string("CEUSPL02") is not None
    driver.send_string("5", row=23, col=23)
    driver.send_enter()

    # 4ª Tela: SPPC/CONSULTA
    assert driver.find_string("SPPC/CONSULTA") is not None
    driver.send_string("10", row=22, col=14)
    driver.send_enter()

    # 5ª Tela: SPPC/CONFER (auto-skip com 8 caracteres no cursor inicial)
    assert driver.find_string("SPPC/CONFER") is not None
    driver.send_string("2115980A")
    driver.send_enter()

    # Valida retorno do cabeçalho e registros
    cabecalho = parse_cabecalho_solicitante_3270(driver)
    assert cabecalho["nome"] == "DOUGLAS ANDRE FONSECA BARBOSA"
    assert cabecalho["lotacao"] == "001 GPD 006 007 GERENCIA DE INFORMATICA"

    # Logoff: 1º PF3 volta para CEUSPL02, 2º PF3 volta ao início/encerra
    driver.send_pf(3)
    assert driver.find_string("CEUSPL02") is not None
    driver.send_pf(3)
    assert driver.find_string("ENTRE COM A APLICACAO") is not None

    driver.disconnect()
    assert not driver.is_connected()


def test_parsers_3270_calculo_saldo_ferias_sppc():
    """
    Valida a extração das 10 linhas do 5º print (SPPC/CONFER) e o cálculo do saldo disponível
    agrupado por Período de Aquisição (incluindo linhas parceladas e linhas com utilização em branco).
    """
    driver = Mock3270Driver()
    driver.connect("127.0.0.1", 23)

    # Avança pelas 5 telas até a listagem de 211598-0 / A
    driver.send_enter()  # -> CICSCNTR
    driver.send_enter()  # -> CEUSPL02
    driver.send_enter()  # -> SPPC/CONSULTA
    driver.send_enter()  # -> SPPC/CONFER
    driver.send_string("2115980A")
    driver.send_enter()  # -> Lista carregada

    registros = parse_lista_registros_3270(driver, opcao_consulta="10")
    # 10 linhas brutas consolidam em 7 períodos aquisitivos únicos (11/12, 12/13, 13/14, 14/15, 15/16, 16/17, 17/18)
    assert len(registros) == 7

    # Período 1 (01/01/11 a 01/01/12): Adq=30, St=NP, Util=30 -> Saldo=0
    assert registros[0]["aquisicao_inicio"] == "01/01/11"
    assert registros[0]["aquisicao_fim"] == "01/01/12"
    assert registros[0]["status"] == "NP"
    assert registros[0]["dias_adquiridos"] == 30
    assert registros[0]["dias_utilizados"] == 30
    assert registros[0]["saldo_disponivel"] == 0
    assert registros[0]["row"] == 11
    assert registros[0]["check_col"] == 3

    # Período 3 (01/01/13 a 01/01/14): Adq=30, St=P, duas parcelas (02 + 10 = 12) -> Saldo=18
    assert registros[2]["aquisicao_inicio"] == "01/01/13"
    assert registros[2]["status"] == "P"
    assert registros[2]["dias_utilizados"] == 12
    assert registros[2]["dias_utilizados_periodo"] == 12
    assert registros[2]["saldo_disponivel"] == 18

    # Período 6 (01/01/16 a 01/01/17): Adq=30, St=P, utilização em branco (0) -> Saldo=30
    assert registros[5]["aquisicao_inicio"] == "01/01/16"
    assert registros[5]["aquisicao_fim"] == "01/01/17"
    assert registros[5]["status"] == "P"
    assert registros[5]["utilizacao_inicio"] is None
    assert registros[5]["dias_utilizados"] == 0
    assert registros[5]["dias_utilizados_periodo"] == 0
    assert registros[5]["saldo_disponivel"] == 30
    assert registros[5]["doc_tipo"] == "MEM"
    assert registros[5]["doc_numero"] == "000094"

    # Testa Fase 2 em stand-by (marca linha 1 com 'X' na coluna 3 e abre tela NC5F M13A)
    driver.send_string("X", row=registros[0]["row"], col=registros[0]["check_col"])
    driver.send_enter()

    detalhes = parse_detalhe_registro_3270(driver)
    assert detalhes["id"] == "01/01/2011 a 01/01/2012"
    assert detalhes["aquisicao"] == "01/01/2011 a 01/01/2012"
    assert detalhes["dias_adquiridos"] == 30
    assert detalhes["dias_utilizados"] == 30
    assert detalhes["dias_restantes"] == 0
    assert detalhes["situacao"] == "Nao Pendentes"
    assert detalhes["previsao"] == "01/04/2012 a 30/04/2012"
    assert detalhes["utilizacao"] == "04/06/2012 a 04/06/2012"
    assert detalhes["doc_tipo"] == "MEM"
    assert detalhes["doc_numero"] == "001510"
    assert detalhes["doc_data"] == "01/06/2012"
    assert detalhes["observacao"] == "FERIAS CONCEDIDAS DPI/PC"
    assert detalhes["tipo"] == "MEM 001510"
    assert detalhes["status"] == "Nao Pendentes"
    assert detalhes["data"] == "01/06/2012"

    driver.disconnect()


def test_fase1_consulta_registros():
    """Valida a rota HTTP POST /api/solicitante/registros retornando cabeçalho e saldo de férias."""
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "211598",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                },
            )
            assert response.status_code == 200
            dados = response.json()
            assert dados["solicitante"]["matricula"] == "211598"
            assert dados["solicitante"]["nome"] == "DOUGLAS ANDRE FONSECA BARBOSA"
            assert "GERENCIA DE INFORMATICA" in dados["solicitante"]["lotacao"]
            assert len(dados["registros"]) == 7
            assert dados["registros"][2]["saldo_disponivel"] == 18
            assert dados["registros"][5]["saldo_disponivel"] == 30

    asyncio.run(_run())


def test_fase2_extrair_detalhes():
    """Valida a rota HTTP POST /api/solicitante/detalhes (em stand-by) com marcação dos itens [1, 4]."""
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Índice 1 (11/12), Índice 3 (13/14: 2 parcelas) e Índice 6 (16/17: Utilizados em branco)
            response = await client.post(
                "/api/solicitante/detalhes",
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                    "indices_selecionados": [1, 3, 6],
                },
            )
            assert response.status_code == 200
            corpo = response.json()
            assert corpo["status"] == "sucesso"
            assert len(corpo["dados"]) == 4
            assert corpo["dados"][0]["id"] == "01/01/2011 a 01/01/2012"
            assert corpo["dados"][0]["doc_numero"] == "001510"
            assert corpo["dados"][1]["id"] == "01/01/2013 a 01/01/2014"
            assert corpo["dados"][1]["dias_utilizados"] == 2
            assert corpo["dados"][1]["doc_numero"] == "000035"
            assert corpo["dados"][2]["id"] == "01/01/2013 a 01/01/2014"
            assert corpo["dados"][2]["dias_utilizados"] == 10
            assert corpo["dados"][2]["doc_numero"] == "000555"
            # Período 16/17 (quando Utilizados não aparece na linha 13 da NC5F M13A)
            assert corpo["dados"][3]["id"] == "01/01/2016 a 01/01/2017"
            assert corpo["dados"][3]["dias_adquiridos"] == 30
            assert corpo["dados"][3]["dias_utilizados"] == 0
            assert corpo["dados"][3]["dias_restantes"] == 30
            assert corpo["dados"][3]["situacao"] == "Pendente.: 30"
            assert corpo["dados"][3]["doc_numero"] == "000094"

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
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                },
            )
            req2 = client.post(
                "/api/solicitante/detalhes",
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                    "indices_selecionados": [2],
                },
            )

            resp1, resp2 = await asyncio.gather(req1, req2)
            assert resp1.status_code == 200
            assert resp2.status_code == 200
            assert len(resp1.json()["registros"]) == 7
            # Índice 2 (01/01/12 a 01/01/13) possui 2 parcelas de 15 dias -> 2 detalhes
            assert len(resp2.json()["dados"]) == 2

    asyncio.run(_run())


def test_validacao_campos_solicitante_invalido():
    """Valida que entradas fora da especificação (6 números, 1 dígito, 1 letra) retornam 422."""
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_mat = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "12345",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                },
            )
            assert resp_mat.status_code == 422

            resp_dig = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "123456",
                    "digito": "00",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                },
            )
            assert resp_dig.status_code == 422

            resp_seq = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "1",
                    "opcao_consulta": "10",
                },
            )
            assert resp_seq.status_code == 422

            resp_opcao = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "123456",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "99",
                },
            )
            assert resp_opcao.status_code == 422

            resp_sem_opcao = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "123456", "digito": "0", "sequencia": "A"},
            )
            assert resp_sem_opcao.status_code == 422

    asyncio.run(_run())


def test_paginacao_pf8_e_envio_opcao_consulta(monkeypatch):
    """
    Valida que o back-end envia a opcao_consulta selecionada na 4ª tela (SPPC/CONSULTA)
    e pagina automaticamente com PF8 na 6ª tela para trazer todos os registros disponíveis,
    inclusive permitindo detalhar registros da 2ª página na Fase 2.
    """
    drivers_criados = []

    def _factory_spy(config=None):
        drv = Mock3270Driver()
        drv.connect("127.0.0.1", 992, secure=True)
        drivers_criados.append(drv)
        return drv

    monkeypatch.setattr(
        "automacao.services.automacao_service.conectar_terminal_3270",
        _factory_spy,
    )

    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "777777",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                },
            )
            assert resp.status_code == 200
            corpo = resp.json()
            assert corpo["solicitante"]["opcao_consulta"] == "10"
            # 7 períodos da 1ª página + 2 períodos da 2ª página (19/20 e 20/21) = 9 períodos
            assert len(corpo["registros"]) == 9
            assert corpo["registros"][7]["id"] == "01/01/19 a 01/01/20"
            assert corpo["registros"][8]["id"] == "01/01/20 a 01/01/21"
            assert drivers_criados[0].last_submenu_option == "10"

            # Extrai detalhes do período #8 (que está na 2ª página do terminal)
            resp_det = await client.post(
                "/api/solicitante/detalhes",
                json={
                    "matricula": "777777",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                    "indices_selecionados": [8],
                },
            )
            assert resp_det.status_code == 200
            detalhes = resp_det.json()["dados"]
            assert len(detalhes) == 1
            assert detalhes[0]["id"] == "01/01/2019 a 01/01/2020"
            assert detalhes[0]["doc_numero"] == "000001"

    asyncio.run(_run())


def test_solicitante_inexistente_retorna_404_e_desconecta(monkeypatch):
    """
    Valida que quando a tela SPPC/CONFER retorna '>>> Matricula Inexiste no Cadastro' na linha 1,
    o backend interrompe imediatamente com HTTP 404 (CadastroInexistenteError) e executa
    duplo PF3 + disconnect no bloco finally.
    """
    drivers_criados = []

    def _factory_spy(config=None):
        drv = Mock3270Driver()
        drv.connect("127.0.0.1", 992, secure=True)
        drivers_criados.append(drv)
        return drv

    monkeypatch.setattr(
        "automacao.services.automacao_service.conectar_terminal_3270",
        _factory_spy,
    )

    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_inexistente = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "999999",
                    "digito": "9",
                    "sequencia": "Z",
                    "opcao_consulta": "10",
                },
            )
            assert resp_inexistente.status_code == 404
            assert "Matricula Inexiste no Cadastro" in resp_inexistente.json()["detail"]

            # Confirma que mesmo em caso de erro na 5ª tela, o duplo PF3 e disconnect rodaram
            assert len(drivers_criados) == 1
            assert drivers_criados[0].current_screen == "APLICACAO"
            assert not drivers_criados[0].is_connected()

            resp_b = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "654321",
                    "digito": "9",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                },
            )
            assert resp_b.status_code == 200
            registros_b = resp_b.json()["registros"]
            assert len(registros_b) == 2

    asyncio.run(_run())


def test_integracao_fluxo_completo_e_desconexao_segura(monkeypatch):
    """
    Teste de integração ponta a ponta:
    Simula o envio do payload do front-end para POST /api/solicitante/registros,
    valida a consolidação dos períodos repetidos (1 linha por período com Adq, Util, Saldo)
    e confirma que o driver TN3270 executou o duplo PF3, desconectou e liberou o operator_lock.
    """
    drivers_criados = []

    def _factory_spy(config=None):
        drv = Mock3270Driver()
        drv.connect("127.0.0.1", 992, secure=True)
        drivers_criados.append(drv)
        return drv

    monkeypatch.setattr(
        "automacao.services.automacao_service.conectar_terminal_3270",
        _factory_spy,
    )

    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/solicitante/registros",
                json={
                    "matricula": "211598",
                    "digito": "0",
                    "sequencia": "A",
                    "opcao_consulta": "10",
                },
            )
            assert resp.status_code == 200
            corpo = resp.json()
            assert corpo["solicitante"]["nome"] == "DOUGLAS ANDRE FONSECA BARBOSA"
            assert len(corpo["registros"]) == 7

            # Verifica que o período 01/01/13 a 01/01/14 (que tinha 2 parcelas: 2d e 10d)
            # foi consolidado em uma única linha com Adq=30, Util=12, Saldo=18
            periodo_13_14 = [
                r for r in corpo["registros"] if r["id"] == "01/01/13 a 01/01/14"
            ]
            assert len(periodo_13_14) == 1
            assert periodo_13_14[0]["dias_adquiridos"] == 30
            assert periodo_13_14[0]["dias_utilizados"] == 12
            assert periodo_13_14[0]["saldo_disponivel"] == 18

            # Confirma desconexão segura do driver TN3270 e liberação do lock no /health
            assert len(drivers_criados) == 1
            drv = drivers_criados[0]
            assert drv.current_screen == "APLICACAO"  # Duplo PF3 retornou ao início
            assert not drv.is_connected()             # disconnect() foi executado

            resp_health = await client.get("/health")
            assert resp_health.status_code == 200
            assert resp_health.json() == {"status": "online", "operador_ocupado": False}

    asyncio.run(_run())


def test_consultas_4_9_13_16_paginacao_pf8_e_leitura_buffer(monkeypatch):
    """
    Valida a leitura do buffer 24x80 e paginação via PF8 nas opções:
    - 4 (SPPC/CONATS - Tempo de Serviço, 2 páginas: 001/002 -> 002/002)
    - 9 (SPPC/CONFLT - Faltas, 'Não existem faltas cadastradas.' -> lista vazia)
    - 13 (SPPC/CONLCA - Licenças, 1 página: 001/001)
    - 16 (SPPC/CONPUE - Punições e Elogios, 2 páginas: 001/002 -> 002/002, iniciando na linha 10)
    """
    def _factory_spy(config=None):
        drv = Mock3270Driver()
        drv.connect("127.0.0.1", 992, secure=True)
        return drv

    monkeypatch.setattr(
        "automacao.services.automacao_service.conectar_terminal_3270",
        _factory_spy,
    )

    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Opção 4: Tempo de Serviço (2 páginas -> 3 registros)
            r4 = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "211598", "digito": "0", "sequencia": "A", "opcao_consulta": "4"},
            )
            assert r4.status_code == 200
            d4 = r4.json()
            assert d4["solicitante"]["nome"] == "DOUGLAS ANDRE FONSECA BARBOSA"
            assert len(d4["registros"]) == 3
            assert "SEC MUNICIPAL SAUDE" in d4["registros"][0]["id"]
            assert "PER. CONTR. CNIS 8" in d4["registros"][2]["id"]

            # Opção 9: Faltas ('Não existem faltas cadastradas.' -> 0 registros)
            r9 = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "211598", "digito": "0", "sequencia": "A", "opcao_consulta": "9"},
            )
            assert r9.status_code == 200
            d9 = r9.json()
            assert d9["solicitante"]["nome"] == "DOUGLAS ANDRE FONSECA BARBOSA"
            assert d9["registros"] == []

            # Opção 13: Licenças (1 página -> 2 registros)
            r13 = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "211598", "digito": "0", "sequencia": "A", "opcao_consulta": "13"},
            )
            assert r13.status_code == 200
            d13 = r13.json()
            assert len(d13["registros"]) == 2
            assert "Licenca Paternidade" in d13["registros"][0]["id"]

            # Opção 16: Punições e Elogios (2 páginas -> 3 registros, linha 10 inclusa)
            r16 = await client.post(
                "/api/solicitante/registros",
                json={"matricula": "211598", "digito": "0", "sequencia": "A", "opcao_consulta": "16"},
            )
            assert r16.status_code == 200
            d16 = r16.json()
            assert len(d16["registros"]) == 3
            assert "05/12/16" in d16["registros"][0]["id"]
            assert "07/08/19" in d16["registros"][2]["id"]

    asyncio.run(_run())
