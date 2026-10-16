import { Component, computed, input, linkedSignal, output } from '@angular/core';
import {
  ConsultaRegistrosResponse,
  RegistroItem,
} from '../../core/models/solicitante.model';

@Component({
  selector: 'app-lista-registros',
  standalone: true,
  template: `
    <div class="fade-in">
      
      <!-- Cabeçalho com Identificação do Solicitante e Controles -->
      <div class="custom-card p-3 p-md-4 mb-3">
        <div class="d-flex flex-column flex-sm-row justify-content-between align-items-start align-items-sm-center gap-2 mb-3">
          <div>
            <div class="d-flex align-items-center gap-2 mb-1">
              <span class="badge rounded-pill bg-warning text-dark fw-bold">Fase 1 Concluída</span>
              <h2 class="h5 fw-bold mb-0">Registros Encontrados</h2>
            </div>
            <p class="text-muted small mb-0">
              Solicitante: 
              <strong class="text-body">{{ dados().solicitante.matricula }}-{{ dados().solicitante.digito }}</strong>
              (Sequência: {{ dados().solicitante.sequencia }})
            </p>
          </div>

          <!-- Contador e Botão Selecionar Todos -->
          <div class="d-flex align-items-center gap-2 w-100 w-sm-auto justify-content-between justify-content-sm-end">
            <span class="badge" style="background-color: var(--badge-bg); color: var(--bs-body-color); border: 1px solid var(--border-color);">
              {{ totalSelecionados() }} de {{ itens().length }} marcados
            </span>
            <button 
              type="button" 
              class="btn btn-sm btn-outline-secondary"
              (click)="alternarTodos()">
              {{ todosSelecionados() ? 'Desmarcar Todos' : 'Marcar Todos' }}
            </button>
          </div>
        </div>

        <!-- Instrução Clara para o Operador -->
        <div class="alert alert-info py-2 px-3 small d-flex align-items-center gap-2 mb-0" 
             style="background-color: var(--primary-accent-light); border-color: var(--border-color-active); color: var(--bs-body-color);">
          <i class="bi bi-info-circle-fill text-warning fs-5"></i>
          <span>Selecione abaixo os registros que deseja marcar com <strong>'X'</strong> para extrair os detalhes.</span>
        </div>
      </div>

      <!-- VISUALIZAÇÃO MOBILE (Cards de Toque Amplo) -->
      <div class="d-md-none mb-4">
        <div class="d-flex flex-column gap-2">
          @for (item of itens(); track item.indice) {
            <div 
              class="custom-card card-interactive p-3 d-flex align-items-center justify-content-between"
              [class.selected]="item.selecionado"
              (click)="toggleItem(item)">
              
              <div class="d-flex align-items-center gap-3">
                <!-- Badge com o Índice do Terminal -->
                <span 
                  class="badge rounded-pill d-flex align-items-center justify-content-center fw-bold"
                  [style.background-color]="item.selecionado ? 'var(--primary-accent)' : 'var(--badge-bg)'"
                  [style.color]="item.selecionado ? '#000000' : 'var(--text-muted)'"
                  style="width: 32px; height: 32px; font-size: 0.85rem; border: 1px solid var(--border-color);">
                  #{{ item.indice }}
                </span>

                <!-- Identificador e Descrição -->
                <div>
                  <div class="fw-bold mb-1 d-flex align-items-center gap-2">
                    <span style="color: var(--primary-accent);">{{ item.id }}</span>
                  </div>
                  <div class="text-body-secondary small text-truncate" style="max-width: 210px;">
                    {{ item.descricao }}
                  </div>
                </div>
              </div>

              <!-- Checkbox Touch-Friendly -->
              <div class="form-check form-switch m-0">
                <input 
                  type="checkbox" 
                  class="form-check-input" 
                  style="width: 2.2rem; height: 1.25rem; cursor: pointer;"
                  [checked]="item.selecionado"
                  (click)="$event.stopPropagation(); toggleItem(item)"
                />
              </div>

            </div>
          } @empty {
            <div class="custom-card p-4 text-center text-muted">
              <i class="bi bi-inbox fs-2 d-block mb-2 text-warning"></i>
              <span>Nenhum registro encontrado para este solicitante.</span>
            </div>
          }
        </div>
      </div>

      <!-- VISUALIZAÇÃO DESKTOP (Tabela Completa) -->
      <div class="custom-card d-none d-md-block overflow-hidden mb-4">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0" style="background-color: var(--surface-card);">
            <thead>
              <tr class="border-bottom" style="border-color: var(--border-color); background-color: var(--surface-card-hover);">
                <th style="width: 50px;" class="text-center">
                  <input 
                    type="checkbox" 
                    class="form-check-input"
                    [checked]="todosSelecionados()"
                    (change)="alternarTodos()"
                  />
                </th>
                <th style="width: 70px;">Índice</th>
                <th style="width: 140px;">Identificador</th>
                <th>Descrição / Tipo de Solicitação</th>
                <th style="width: 120px;" class="text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              @for (item of itens(); track item.indice) {
                <tr 
                  style="cursor: pointer;"
                  [class.table-active]="item.selecionado"
                  (click)="toggleItem(item)">
                  <td class="text-center" (click)="$event.stopPropagation()">
                    <input 
                      type="checkbox" 
                      class="form-check-input"
                      [checked]="item.selecionado"
                      (change)="toggleItem(item)"
                    />
                  </td>
                  <td class="fw-bold text-muted">#{{ item.indice }}</td>
                  <td>
                    <span class="badge" style="background-color: var(--badge-bg); color: var(--primary-accent); border: 1px solid var(--border-color);">
                      {{ item.id }}
                    </span>
                  </td>
                  <td class="fw-semibold">{{ item.descricao }}</td>
                  <td class="text-center">
                    @if (item.selecionado) {
                      <span class="badge bg-warning text-dark"><i class="bi bi-check-lg"></i> Marcado [X]</span>
                    } @else {
                      <span class="text-muted small">Não marcado</span>
                    }
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="5" class="text-center py-4 text-muted">
                    <i class="bi bi-inbox fs-3 d-block mb-1 text-warning"></i>
                    <span>Nenhum registro encontrado para este solicitante.</span>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- BARRA DE AÇÃO FLUTUANTE (Sticky Bottom no Mobile / Inline no Desktop) -->
      <div class="sticky-bottom-action-bar">
        <div class="d-flex flex-row justify-content-between align-items-center gap-2">
          
          <button 
            type="button" 
            class="btn btn-outline-secondary d-flex align-items-center gap-1 py-2 px-3"
            (click)="voltar.emit()">
            <i class="bi bi-arrow-left"></i>
            <span class="d-none d-sm-inline">Nova Consulta</span>
          </button>

          <button 
            type="button" 
            class="btn btn-warning d-flex align-items-center justify-content-center gap-2 py-2 px-4 shadow-sm"
            [disabled]="totalSelecionados() === 0 || loading()"
            (click)="onConfirmar()">
            <i class="bi bi-file-earmark-check-fill"></i>
            <span>
              Extrair Detalhes
              @if (totalSelecionados() > 0) {
                <span class="badge bg-dark text-warning ms-1">{{ totalSelecionados() }}</span>
              }
            </span>
          </button>

        </div>
      </div>

    </div>
  `,
})
export class ListaRegistrosComponent {
  readonly dados = input.required<ConsultaRegistrosResponse>();
  readonly loading = input<boolean>(false);

  readonly confirmar = output<number[]>();
  readonly voltar = output<void>();

  // Armazena a lista com o estado da seleção (sincronizada via linkedSignal)
  readonly itens = linkedSignal<RegistroItem[]>(() =>
    (this.dados().registros ?? []).map((r) => ({
      ...r,
      selecionado: false,
    }))
  );

  readonly totalSelecionados = computed(
    () => this.itens().filter((i) => i.selecionado).length
  );

  readonly todosSelecionados = computed(
    () =>
      this.itens().length > 0 &&
      this.itens().every((i) => i.selecionado)
  );

  toggleItem(item: RegistroItem): void {
    this.itens.update((current) =>
      current.map((i) =>
        i.indice === item.indice ? { ...i, selecionado: !i.selecionado } : i
      )
    );
  }

  alternarTodos(): void {
    const marcar = !this.todosSelecionados();
    this.itens.update((current) =>
      current.map((i) => ({ ...i, selecionado: marcar }))
    );
  }

  onConfirmar(): void {
    const selecionados = this.itens()
      .filter((i) => i.selecionado)
      .map((i) => i.indice);
    this.confirmar.emit(selecionados);
  }
}
