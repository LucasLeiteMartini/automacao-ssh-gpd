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
    solicitante: { matricula: '123456', digito: '0', sequencia: '01' },
    registros: [
      { indice: 1, id: 'REG-001', descricao: 'Beneficio 1' },
      { indice: 2, id: 'REG-002', descricao: 'Beneficio 2' },
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

  it('deve carregar e renderizar os registros recebidos via linkedSignal', () => {
    const fixture = TestBed.createComponent(TestHostComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    // Verifica se os identificadores dos registros aparecem no DOM
    expect(compiled.textContent).toContain('REG-001');
    expect(compiled.textContent).toContain('REG-002');
    expect(compiled.textContent).toContain('0 de 2 marcados');
  });

  it('deve alternar a seleção de registros e calcular total', () => {
    const fixture = TestBed.createComponent(TestHostComponent);
    fixture.detectChanges();

    const host = fixture.componentInstance;
    const listaComponent = fixture.debugElement.children[0].componentInstance as ListaRegistrosComponent;

    expect(listaComponent.itens().length).toBe(2);
    expect(listaComponent.totalSelecionados()).toBe(0);

    // Marca o primeiro item
    listaComponent.toggleItem(listaComponent.itens()[0]);
    expect(listaComponent.totalSelecionados()).toBe(1);

    // Marca todos
    listaComponent.alternarTodos();
    expect(listaComponent.totalSelecionados()).toBe(2);
    expect(listaComponent.todosSelecionados()).toBe(true);
  });
});
