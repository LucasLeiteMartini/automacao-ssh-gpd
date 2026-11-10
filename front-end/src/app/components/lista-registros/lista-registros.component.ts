import { Component, computed, input, linkedSignal, output, signal } from '@angular/core';
import {
  ConsultaRegistrosResponse,
  RegistroItem,
} from '../../core/models/solicitante.model';

export type FiltroFerias = 'pendentes' | 'todos';

@Component({
  selector: 'app-lista-registros',
  standalone: true,
  template: `
    <div class="fade-in">

      <!-- Cabeçalho do Servidor e Saldo Total Disponível -->
      <div class="custom-card p-3 p-md-4 mb-3" style="border-left: 4px solid var(--primary-accent);">
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-3">
          <div>
            <div class="d-flex align-items-center gap-2 mb-1">
              <span class="badge rounded-pill bg-warning text-dark fw-bold">SPPC / CONFER</span>
              <h2 class="h5 fw-bold mb-0">
                {{ dados().solicitante.nome || 'Consulta de Férias do Servidor' }}
              </h2>
            </div>
            <div class="d-flex flex-wrap align-items-center gap-2 text-muted small mt-1">
              <span>
                Matrícula:
                <strong class="text-body">
                  {{ dados().solicitante.matricula }}-{{ dados().solicitante.digito }}
                </strong>
                (Seq: <strong class="text-body">{{ dados().solicitante.sequencia }}</strong>)
              </span>
              @if (dados().solicitante.lotacao) {
                <span class="d-none d-sm-inline">•</span>
                <span>
                  Lotação: <strong class="text-body">{{ dados().solicitante.lotacao }}</strong>
                </span>
              }
            </div>
          </div>

          <!-- Resumo de Saldo Total e Controles -->
          <div class="d-flex flex-wrap align-items-center gap-2 w-100 w-md-auto justify-content-between justify-content-md-end">
            <span class="badge bg-warning text-dark fs-6 fw-bold px-3 py-2">
              Saldo Total Disponível: {{ saldoTotalDisponivel() }} dias
            </span>
            <div class="d-flex align-items-center gap-2">
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary"
                (click)="alternarTodos()">
                {{ todosSelecionados() ? 'Desmarcar Todos' : 'Marcar Todos' }}
              </button>
              @if (totalSelecionados() > 0) {
                <button
                  type="button"
                  class="btn btn-sm btn-warning d-inline-flex align-items-center gap-1"
                  [disabled]="loading()"
                  (click)="onConfirmar()">
                  <i class="bi bi-file-earmark-check-fill"></i>
                  <span>Detalhar ({{ totalSelecionados() }})</span>
                </button>
              }
            </div>
          </div>
        </div>

        <!-- Seletor de Visualização da Tela de Férias: Somente Pendentes vs Todos os Registros Disponíveis -->
        <div class="d-flex flex-column flex-sm-row align-items-stretch align-items-sm-center justify-content-between gap-2 mt-3 pt-3 border-top"
             style="border-color: var(--border-color) !important;">
          <span class="text-muted small fw-semibold">
            <i class="bi bi-funnel me-1 text-warning"></i>
            Exibição de Registros:
          </span>
          <div class="btn-group btn-group-sm" role="group" aria-label="Filtro de registros de férias">
            <button
              type="button"
              class="btn"
              [class.btn-warning]="filtro() === 'pendentes'"
              [class.btn-outline-secondary]="filtro() !== 'pendentes'"
              (click)="setFiltro('pendentes')">
              Somente pendentes
            </button>
            <button
              type="button"
              class="btn"
              [class.btn-warning]="filtro() === 'todos'"
              [class.btn-outline-secondary]="filtro() !== 'todos'"
              (click)="setFiltro('todos')">
              Todos os registros disponíveis
            </button>
          </div>
        </div>
      </div>

      <!-- VISUALIZAÇÃO MOBILE (Cards Consolidados por Período Aquisitivo) -->
      <div class="d-md-none mb-4">
        <div class="d-flex flex-column gap-2">
          @for (item of itensVisiveis(); track item.indice) {
            <div
              class="custom-card card-interactive p-3"
              [class.selected]="item.selecionado"
              [style.border-left]="item.status === 'P' ? '4px solid var(--primary-accent)' : ''"
              (click)="toggleItem(item)">

              <div class="d-flex align-items-center justify-content-between gap-2 mb-2">
                <div class="d-flex align-items-center gap-2">
                  <span class="badge rounded-pill fw-bold"
                        style="background-color: var(--badge-bg); color: var(--text-muted); border: 1px solid var(--border-color);">
                    #{{ item.indice }}
                  </span>
                  <span class="fw-bold" style="color: var(--primary-accent);">
                    {{ item.id }}
                  </span>
                  @if (item.status === 'P') {
                    <span class="badge bg-warning text-dark fw-bold">St: P</span>
                  } @else if (item.status) {
                    <span class="badge bg-secondary">St: {{ item.status }}</span>
                  }
                </div>

                <!-- Checkbox Touch-Friendly (Stand-by Fase 2) -->
                <div class="form-check form-switch m-0">
                  <input
                    type="checkbox"
                    class="form-check-input"
                    style="width: 2rem; height: 1.15rem; cursor: pointer;"
                    [checked]="item.selecionado"
                    (click)="$event.stopPropagation(); toggleItem(item)"
                  />
                </div>
              </div>

              <div class="row g-2 small mt-1 pt-2 border-top text-center" style="border-color: var(--border-color) !important;">
                <div class="col-4 text-start">
                  <span class="text-muted d-block">Adquiridos</span>
                  <strong>{{ item.dias_adquiridos ?? 0 }}d</strong>
                </div>
                <div class="col-4">
                  <span class="text-muted d-block">Utilizados</span>
                  <strong>{{ item.dias_utilizados ?? 0 }}d</strong>
                </div>
                <div class="col-4 text-end">
                  <span class="text-muted d-block">Saldo Disponível</span>
                  <strong class="text-warning fs-6">{{ item.saldo_disponivel ?? 0 }}d</strong>
                </div>
              </div>
            </div>
          } @empty {
            <div class="custom-card p-4 text-center text-muted">
              <i class="bi bi-inbox fs-2 d-block mb-2 text-warning"></i>
              <span>Nenhum período pendente encontrado para este solicitante.</span>
            </div>
          }
        </div>
      </div>

      <!-- VISUALIZAÇÃO DESKTOP (Tabela Consolidada: 1 Linha por Período Aquisitivo) -->
      <div class="custom-card d-none d-md-block overflow-hidden mb-4">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0" style="background-color: var(--surface-card);">
            <thead>
              <tr class="border-bottom" style="border-color: var(--border-color); background-color: var(--surface-card-hover);">
                <th style="width: 45px;" class="text-center">
                  <input
                    type="checkbox"
                    class="form-check-input"
                    [checked]="todosSelecionados()"
                    (change)="alternarTodos()"
                  />
                </th>
                <th style="width: 60px;">#</th>
                <th>Período Aquisitivo</th>
                <th class="text-center">Status</th>
                <th class="text-center">Dias Adquiridos</th>
                <th class="text-center">Dias Utilizados</th>
                <th class="text-center">Saldo Disponível</th>
              </tr>
            </thead>
            <tbody>
              @for (item of itensVisiveis(); track item.indice) {
                <tr
                  style="cursor: pointer;"
                  [class.table-active]="item.selecionado"
                  [style.border-left]="item.status === 'P' ? '4px solid var(--primary-accent)' : ''"
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
                    <span class="fw-bold" [style.color]="item.status === 'P' ? 'var(--primary-accent)' : 'var(--bs-body-color)'">
                      {{ item.id }}
                    </span>
                  </td>
                  <td class="text-center">
                    @if (item.status === 'P') {
                      <span class="badge bg-warning text-dark fw-bold px-2 py-1">P (Pendente)</span>
                    } @else if (item.status) {
                      <span class="badge bg-secondary px-2 py-1">{{ item.status }}</span>
                    } @else {
                      <span class="text-muted small">—</span>
                    }
                  </td>
                  <td class="text-center fw-semibold">
                    {{ item.dias_adquiridos ?? 0 }}d
                  </td>
                  <td class="text-center fw-semibold">
                    {{ item.dias_utilizados ?? 0 }}d
                  </td>
                  <td class="text-center">
                    <span class="badge bg-warning text-dark fw-bold fs-6 px-3 py-1">
                      {{ item.saldo_disponivel ?? 0 }}d
                    </span>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="7" class="text-center py-4 text-muted">
                    <i class="bi bi-inbox fs-3 d-block mb-1 text-warning"></i>
                    <span>Nenhum período pendente encontrado para este solicitante.</span>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- BARRA DE AÇÃO NO FLUXO DA PÁGINA (Nova Consulta + Fase 2) -->
      <div class="sticky-bottom-action-bar">
        <div class="d-flex flex-column flex-sm-row justify-content-between align-items-stretch align-items-sm-center gap-2">

          <button
            type="button"
            class="btn btn-outline-secondary d-flex align-items-center justify-content-center gap-1 py-2 px-3"
            (click)="voltar.emit()">
            <i class="bi bi-arrow-left"></i>
            <span>Nova Consulta</span>
          </button>

          <button
            type="button"
            class="btn btn-warning d-flex align-items-center justify-content-center gap-2 py-2 px-4 shadow-sm"
            [disabled]="totalSelecionados() === 0 || loading()"
            title="Fase 2: marca os itens selecionados com 'X' no terminal e abre a tela de detalhe NC5F"
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

  readonly filtro = signal<FiltroFerias>('todos');

  // Armazena a lista consolidada (1 linha por período aquisitivo) sincronizada via linkedSignal
  readonly itens = linkedSignal<RegistroItem[]>(() =>
    (this.dados().registros ?? []).map((r) => ({
      ...r,
      selecionado: false,
    }))
  );

  readonly itensVisiveis = computed<RegistroItem[]>(() => {
    const todos = this.itens();
    if (this.filtro() === 'pendentes') {
      return todos.filter((i) => i.status === 'P');
    }
    return todos;
  });

  readonly saldoTotalDisponivel = computed<number>(() =>
    this.itensVisiveis().reduce((acc, item) => acc + (item.saldo_disponivel ?? 0), 0)
  );

  readonly totalSelecionados = computed(
    () => this.itens().filter((i) => i.selecionado).length
  );

  readonly todosSelecionados = computed(() => {
    const visiveis = this.itensVisiveis();
    return visiveis.length > 0 && visiveis.every((i) => i.selecionado);
  });

  setFiltro(novoFiltro: FiltroFerias): void {
    this.filtro.set(novoFiltro);
  }

  toggleItem(item: RegistroItem): void {
    this.itens.update((current) =>
      current.map((i) =>
        i.indice === item.indice ? { ...i, selecionado: !i.selecionado } : i
      )
    );
  }

  alternarTodos(): void {
    const marcar = !this.todosSelecionados();
    const indicesVisiveis = new Set(this.itensVisiveis().map((v) => v.indice));
    this.itens.update((current) =>
      current.map((i) =>
        indicesVisiveis.has(i.indice) ? { ...i, selecionado: marcar } : i
      )
    );
  }

  onConfirmar(): void {
    const selecionados = this.itens()
      .filter((i) => i.selecionado)
      .map((i) => i.indice);
    this.confirmar.emit(selecionados);
  }
}
