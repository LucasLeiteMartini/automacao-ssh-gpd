import { TestBed } from '@angular/core/testing';
import { Component, signal } from '@angular/core';
import { ListaRegistrosComponent } from './lista-registros.component';
import { ConsultaRegistrosResponse } from '../../core/models/solicitante.model';

@Component({
  standalone: true,
  imports: [ListaRegistrosComponent],
  template: `
    <app-lista-registros
      [dados]="dados()"
      (confirmar)="onConfirmar($event)">
    </app-lista-registros>
  `,
})
class TestHostComponent {
  readonly dados = signal<ConsultaRegistrosResponse>({
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
      {
        indice: 3,
        id: '01/01/21 a 01/01/22',
        descricao: 'Adq: 30d | Util: 20d | Saldo: 10d',
        aquisicao_inicio: '01/01/21',
        aquisicao_fim: '01/01/22',
        dias_adquiridos: 30,
        status: 'P',
        dias_utilizados: 20,
        dias_utilizados_periodo: 20,
        saldo_disponivel: 10,
      },
      {
        indice: 4,
        id: '01/01/11 a 01/01/12',
        descricao: 'Adq: 30d | Util: 30d | Saldo: 0d',
        aquisicao_inicio: '01/01/11',
        aquisicao_fim: '01/01/12',
        dias_adquiridos: 30,
        status: 'NP',
        dias_utilizados: 30,
        dias_utilizados_periodo: 30,
        saldo_disponivel: 0,
      },
    ],
  });
  selecionados: number[] = [];

  onConfirmar(indices: number[]): void {
    this.selecionados = indices;
  }
}

describe('ListaRegistrosComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHostComponent],
    }).compileComponents();
  });

  it('deve renderizar os períodos consolidados (1 linha por período) e o saldo total disponível', () => {
    const fixture = TestBed.createComponent(TestHostComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const listaComponent = fixture.debugElement.children[0].componentInstance as ListaRegistrosComponent;

    expect(compiled.textContent).toContain('DOUGLAS ANDRE FONSECA BARBOSA');
    expect(compiled.textContent).toContain('01/01/13 a 01/01/14');
    expect(compiled.textContent).toContain('01/01/16 a 01/01/17');
    expect(compiled.textContent).toContain('01/01/21 a 01/01/22');
    expect(listaComponent.itens().length).toBe(4);
    expect(listaComponent.itensVisiveis().length).toBe(4);
    expect(listaComponent.saldoTotalDisponivel()).toBe(58);
    expect(compiled.textContent).toContain('Saldo Total Disponível: 58 dias');

    // Filtra somente pendentes (St = P)
    listaComponent.setFiltro('pendentes');
    fixture.detectChanges();
    expect(listaComponent.itensVisiveis().length).toBe(3);
  });

  it('deve alternar a seleção de registros e calcular total (Fase 2 em stand-by)', () => {
    const fixture = TestBed.createComponent(TestHostComponent);
    fixture.detectChanges();

    const listaComponent = fixture.debugElement.children[0].componentInstance as ListaRegistrosComponent;

    expect(listaComponent.itens().length).toBe(4);
    expect(listaComponent.totalSelecionados()).toBe(0);

    listaComponent.toggleItem(listaComponent.itens()[0]);
    expect(listaComponent.totalSelecionados()).toBe(1);

    listaComponent.alternarTodos();
    expect(listaComponent.totalSelecionados()).toBe(4);
    expect(listaComponent.todosSelecionados()).toBe(true);
  });
});
