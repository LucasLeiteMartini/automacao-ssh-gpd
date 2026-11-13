import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { App } from './app';
import { ConsultaRegistrosResponse } from './core/models/solicitante.model';

describe('App (Integração Front-End)', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    sessionStorage.clear();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    sessionStorage.clear();
    httpMock.verify();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    httpMock.expectOne('/health').flush({ status: 'online', operador_ocupado: false });
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should start on form step', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    httpMock.expectOne('/health').flush({ status: 'online', operador_ocupado: false });
    const app = fixture.componentInstance;
    expect(app.etapa()).toBe('form');
  });

  it('deve executar o fluxo integrado: submeter solicitante -> receber saldos consolidados -> confirmar operador livre no healthcheck', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    fixture.detectChanges();

    // Healthcheck inicial
    httpMock.expectOne('/health').flush({ status: 'online', operador_ocupado: false });

    // 1. Dispara busca a partir do formulário no Front-End
    app.onBuscar({
      matricula: '211598',
      digito: '0',
      sequencia: 'A',
      opcao_consulta: '10',
    });
    expect(app.etapa()).toBe('loading_busca');

    // 2. Intercepta POST /api/solicitante/registros e devolve o payload consolidado do back-end
    const reqRegistros = httpMock.expectOne('/api/solicitante/registros');
    expect(reqRegistros.request.method).toBe('POST');
    expect(reqRegistros.request.body).toEqual({
      matricula: '211598',
      digito: '0',
      sequencia: 'A',
      opcao_consulta: '10',
      forcar_atualizacao: false,
    });

    const respostaConsolidada: ConsultaRegistrosResponse = {
      solicitante: {
        matricula: '211598',
        digito: '0',
        sequencia: 'A',
        opcao_consulta: '10',
        nome: 'DOUGLAS ANDRE FONSECA BARBOSA',
        lotacao: '001 GPD 006 007 GERENCIA DE INFORMATICA',
      },
      registros: [
        {
          indice: 1,
          id: '01/01/13 a 01/01/14',
          descricao: 'Adq: 30d | Util: 12d | Saldo: 18d',
          aquisicao_inicio: '01/01/13',
          aquisicao_fim: '01/01/14',
          dias_adquiridos: 30,
          status: 'P',
          dias_utilizados: 12,
          dias_utilizados_periodo: 12,
          saldo_disponivel: 18,
        },
        {
          indice: 2,
          id: '01/01/16 a 01/01/17',
          descricao: 'Adq: 30d | Util: 0d | Saldo: 30d',
          aquisicao_inicio: '01/01/16',
          aquisicao_fim: '01/01/17',
          dias_adquiridos: 30,
          status: 'P',
          dias_utilizados: 0,
          dias_utilizados_periodo: 0,
          saldo_disponivel: 30,
        },
      ],
    };
    reqRegistros.flush(respostaConsolidada);

    // 3. Healthcheck pós-consulta confirma que a sessão 3270 desconectou e liberou o operador
    const reqHealthPos = httpMock.expectOne('/health');
    reqHealthPos.flush({ status: 'online', operador_ocupado: false });

    fixture.detectChanges();

    // 4. Verifica transição para a etapa 'lista' e renderização dos saldos consolidados
    expect(app.etapa()).toBe('lista');
    expect(app.health()?.operador_ocupado).toBe(false);

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('DOUGLAS ANDRE FONSECA BARBOSA');
    expect(compiled.textContent).toContain('01/01/13 a 01/01/14');
    expect(compiled.textContent).toContain('01/01/16 a 01/01/17');
    expect(compiled.textContent).toContain('Saldo Total Disponível: 48 dias');

    // 5. Seleciona o período #1 e dispara Fase 2 (extração de detalhes NC5F M13A)
    app.onConfirmarDetalhes([1]);
    expect(app.etapa()).toBe('loading_detalhes');

    const reqDetalhes = httpMock.expectOne('/api/solicitante/detalhes');
    expect(reqDetalhes.request.method).toBe('POST');
    expect(reqDetalhes.request.body).toEqual({
      matricula: '211598',
      digito: '0',
      sequencia: 'A',
      opcao_consulta: '10',
      indices_selecionados: [1],
    });

    reqDetalhes.flush({
      status: 'sucesso',
      dados: [
        {
          id: '01/01/2013 a 01/01/2014',
          aquisicao: '01/01/2013 a 01/01/2014',
          dias_adquiridos: 30,
          dias_utilizados: 2,
          dias_restantes: 28,
          situacao: 'Pendente',
          previsao: '01/04/2014 a 30/04/2014',
          utilizacao: '12/05/2022 a 13/05/2022',
          dias_gozados: 2,
          doc_tipo: 'MEM',
          doc_numero: '000035',
          doc_data: '09/05/2022',
          observacao: 'FERIAS CONCEDIDAS DPI/PC',
          tipo: 'MEM 000035',
          valor: 'Adquiridos: 30 | Utilizados: 02 | Restantes: 28',
          status: 'Pendente',
          data: '09/05/2022',
        },
      ],
    });

    const reqHealthPosDetalhes = httpMock.expectOne('/health');
    reqHealthPosDetalhes.flush({ status: 'online', operador_ocupado: false });
    fixture.detectChanges();

    expect(app.etapa()).toBe('detalhes');
    expect(compiled.textContent).toContain('NC5F M13A');
    expect(compiled.textContent).toContain('01/01/2013 a 01/01/2014');
    expect(compiled.textContent).toContain('01/04/2014 a 30/04/2014');
    expect(compiled.textContent).toContain('12/05/2022 a 13/05/2022');
    expect(compiled.textContent).toContain('MEM');
    expect(compiled.textContent).toContain('000035');
    expect(compiled.textContent).toContain('FERIAS CONCEDIDAS DPI/PC');
  });

  it('deve exibir detalhes instantaneamente do cache em conexão única e reutilizar sessionStorage até clicar em Atualizar', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    fixture.detectChanges();

    httpMock.expectOne('/health').flush({ status: 'online', operador_ocupado: false });

    const reqPayload = {
      matricula: '211598',
      digito: '0',
      sequencia: 'A',
      opcao_consulta: '10' as const,
    };

    // 1ª busca: vai ao back-end e já recebe os detalhes embutidos
    app.onBuscar(reqPayload);
    const req1 = httpMock.expectOne('/api/solicitante/registros');
    req1.flush({
      solicitante: {
        ...reqPayload,
        nome: 'DOUGLAS ANDRE FONSECA BARBOSA',
        lotacao: 'GERENCIA DE INFORMATICA',
      },
      registros: [
        {
          indice: 1,
          id: '01/01/16 a 01/01/17',
          descricao: 'Adq: 30d | Util: 0d | Saldo: 30d',
          dias_adquiridos: 30,
          status: 'P',
          dias_utilizados: 0,
          dias_utilizados_periodo: 0,
          saldo_disponivel: 30,
          detalhes: [
            {
              id: '01/01/2016 a 01/01/2017',
              aquisicao: '01/01/2016 a 01/01/2017',
              dias_adquiridos: 30,
              dias_utilizados: 0,
              dias_restantes: 30,
              situacao: 'Pendente.: 30',
              doc_tipo: 'MEM',
              doc_numero: '000094',
              doc_data: '24/03/2017',
              observacao: 'FERIAS PENDENTES',
              tipo: 'MEM 000094',
              valor: 'Adquiridos: 30 | Utilizados: 00 | Restantes: 30',
              status: 'Pendente.: 30',
              data: '24/03/2017',
            },
          ],
        },
      ],
    });
    httpMock.expectOne('/health').flush({ status: 'online', operador_ocupado: false });

    // Clicar em Detalhar abre a etapa 'detalhes' instantaneamente (0 chamadas para /api/solicitante/detalhes)
    app.onConfirmarDetalhes([1]);
    expect(app.etapa()).toBe('detalhes');
    expect(app.dadosDetalhes().length).toBe(1);
    expect(app.dadosDetalhes()[0].doc_numero).toBe('000094');

    // Nova busca para a mesma matrícula: lida 100% do sessionStorage (0 chamadas para /api/solicitante/registros)
    app.onBuscar(reqPayload);
    httpMock.expectNone('/api/solicitante/registros');
    httpMock.expectOne('/health').flush({ status: 'online', operador_ocupado: false });
    expect(app.etapa()).toBe('lista');

    // Clicar em Atualizar força releitura ignorando o cache (forcar_atualizacao: true)
    app.onAtualizarConsulta();
    const reqForcada = httpMock.expectOne('/api/solicitante/registros');
    expect(reqForcada.request.body.forcar_atualizacao).toBe(true);
    reqForcada.flush({
      solicitante: { ...reqPayload, nome: 'DOUGLAS ANDRE FONSECA BARBOSA' },
      registros: [],
    });
    httpMock.expectOne('/health').flush({ status: 'online', operador_ocupado: false });
  });
});
