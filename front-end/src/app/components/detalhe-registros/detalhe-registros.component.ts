import { Component, input, output, signal } from '@angular/core';
import {
  RegistroDetalhe,
  SolicitanteIdentificacao,
} from '../../core/models/solicitante.model';

@Component({
  selector: 'app-detalhe-registros',
  standalone: true,
  template: `
    <div class="fade-in">
      
      <!-- Cabeçalho Institucional (Espelhando o topo do NC5F M13A da PRODAM) -->
      <div class="custom-card p-3 p-md-4 mb-3" style="border-left: 4px solid var(--primary-accent);">
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-3">
          <div>
            <div class="d-flex flex-wrap align-items-center gap-2 mb-1">
              <span class="badge rounded-pill bg-warning text-dark fw-bold">SPPC / CONFER</span>
              <span class="badge rounded-pill" style="background-color: var(--badge-bg); color: var(--primary-accent); border: 1px solid var(--border-color-active);">
                NC5F M13A
              </span>
              <h2 class="h5 fw-bold mb-0">
                {{ solicitante()?.nome || 'Consulta Férias — Detalhamento' }}
              </h2>
            </div>

            @if (solicitante()) {
              <div class="d-flex flex-wrap align-items-center gap-2 text-muted small mt-1">
                <span>
                  Matric / D / Seq:
                  <strong class="text-body">
                    {{ solicitante()!.matricula }}-{{ solicitante()!.digito }} ({{ solicitante()!.sequencia }})
                  </strong>
                </span>
                @if (solicitante()!.lotacao) {
                  <span class="d-none d-sm-inline">•</span>
                  <span>
                    Lotação: <strong class="text-body">{{ solicitante()!.lotacao }}</strong>
                  </span>
                }
              </div>
            }
          </div>

          <div class="d-flex align-items-center gap-2 w-100 w-md-auto justify-content-between justify-content-md-end">
            <span class="badge rounded-pill py-2 px-3" style="background-color: var(--badge-bg); color: var(--bs-body-color); border: 1px solid var(--border-color);">
              {{ detalhes().length }} Registro(s) Detalhado(s)
            </span>
            <button 
              type="button" 
              class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1"
              (click)="voltarSelecao.emit()">
              <i class="bi bi-arrow-left"></i>
              <span>Voltar à Lista</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Lista de Telas NC5F M13A Extraídas -->
      <div class="d-flex flex-column gap-3 mb-4">
        @for (item of detalhes(); track $index) {
          <div class="custom-card p-3 p-md-4 position-relative"
               [style.border-left]="isPendente(item) ? '4px solid var(--primary-accent)' : '4px solid var(--border-color)'">
            
            <!-- Linha 1: Aquisição e Situação -->
            <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 pb-3 mb-3 border-bottom"
                 style="border-color: var(--border-color) !important;">
              <div>
                <small class="text-muted text-uppercase fw-semibold d-block" style="font-size: 0.72rem; letter-spacing: 0.04em;">
                  Período de Aquisição
                </small>
                <div class="fs-5 fw-bold" style="color: var(--primary-accent);">
                  {{ item.aquisicao || item.id || 'Não informado' }}
                </div>
              </div>

              <span 
                class="badge rounded-pill py-2 px-3 fw-bold"
                [class.bg-warning]="isPendente(item)"
                [class.text-dark]="isPendente(item)"
                [class.bg-secondary]="!isPendente(item)">
                {{ item.situacao || item.status || 'Situação N/A' }}
              </span>
            </div>

            <!-- Linha 2: Bloco Dias (Adquiridos / Utilizados) e Datas (Previsão / Utilização) -->
            <div class="row g-3 mb-3">
              
              <!-- Bloco Dias -->
              <div class="col-12 col-md-5">
                <div class="p-3 rounded h-100" style="background-color: var(--surface-card-hover); border: 1px solid var(--border-color);">
                  <small class="text-muted text-uppercase fw-semibold d-block mb-2" style="font-size: 0.72rem; letter-spacing: 0.04em;">
                    Dias no Registro
                  </small>
                  <div class="row text-center g-2">
                    <div class="col-4 border-end" style="border-color: var(--border-color) !important;">
                      <span class="text-muted small d-block">Adquiridos</span>
                      <strong class="fs-5">{{ item.dias_adquiridos ?? 0 }}</strong>
                    </div>
                    <div class="col-4 border-end" style="border-color: var(--border-color) !important;">
                      <span class="text-muted small d-block">Utilizados</span>
                      <strong class="fs-5" [style.color]="varColorUtilizados(item)">
                        {{ item.dias_utilizados ?? 0 }}
                      </strong>
                    </div>
                    <div class="col-4">
                      <span class="text-muted small d-block">Pendentes</span>
                      <strong class="fs-5" style="color: var(--primary-accent);">
                        {{ item.dias_restantes ?? 0 }}
                      </strong>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Bloco Previsão e Utilização -->
              <div class="col-12 col-md-7">
                <div class="p-3 rounded h-100 d-flex flex-column justify-content-center gap-2"
                     style="background-color: var(--surface-card-hover); border: 1px solid var(--border-color);">
                  <div class="d-flex flex-column flex-sm-row justify-content-between align-items-sm-center gap-1">
                    <span class="text-muted small fw-semibold">Previsão:</span>
                    <span class="fw-semibold">{{ item.previsao || '—' }}</span>
                  </div>
                  <div class="border-top pt-2 d-flex flex-column flex-sm-row justify-content-between align-items-sm-center gap-1"
                       style="border-color: var(--border-color) !important;">
                    <span class="text-muted small fw-semibold">Utilização:</span>
                    <span>
                      @if (item.utilizacao) {
                        <strong style="color: var(--primary-accent);">{{ item.utilizacao }}</strong>
                        @if (item.dias_gozados) {
                          <span class="badge bg-warning text-dark ms-2">{{ item.dias_gozados }} Dias</span>
                        }
                      } @else {
                        <span class="text-muted fst-italic">Sem utilização lançada</span>
                      }
                    </span>
                  </div>
                </div>
              </div>

            </div>

            <!-- Linha 3: Quadro Documento (+--- Documento ---+) igual ao sistema da PRODAM -->
            <div class="rounded p-3" style="background-color: var(--surface-card-hover); border: 1px solid var(--border-color);">
              <div class="d-flex justify-content-between align-items-center mb-2 pb-1 border-bottom"
                   style="border-color: var(--border-color) !important;">
                <small class="text-uppercase fw-bold" style="color: var(--primary-accent); font-size: 0.75rem; letter-spacing: 0.05em;">
                  <i class="bi bi-file-earmark-text me-1"></i>
                  Documento
                </small>

                @if (item.doc_numero || item.observacao) {
                  <button 
                    type="button" 
                    class="btn btn-sm btn-outline-secondary py-0 px-2 d-flex align-items-center gap-1"
                    (click)="copiarResumoDocumento(item, $index)">
                    @if (copiadoIdx() === $index) {
                      <i class="bi bi-check text-success"></i>
                      <span class="small text-success">Copiado</span>
                    } @else {
                      <i class="bi bi-clipboard"></i>
                      <span class="small">Copiar</span>
                    }
                  </button>
                }
              </div>

              <div class="row g-2 small">
                <div class="col-4 col-sm-2">
                  <span class="text-muted d-block" style="font-size: 0.72rem;">TP</span>
                  <strong>{{ item.doc_tipo || '—' }}</strong>
                </div>
                <div class="col-4 col-sm-3">
                  <span class="text-muted d-block" style="font-size: 0.72rem;">NÚMERO</span>
                  <strong>{{ item.doc_numero || '—' }}</strong>
                </div>
                <div class="col-4 col-sm-3">
                  <span class="text-muted d-block" style="font-size: 0.72rem;">DATA</span>
                  <strong>{{ item.doc_data || item.data || '—' }}</strong>
                </div>
                <div class="col-12 col-sm-4">
                  <span class="text-muted d-block" style="font-size: 0.72rem;">OBSERVAÇÃO</span>
                  <strong class="text-break">{{ item.observacao || '—' }}</strong>
                </div>
              </div>
            </div>

          </div>
        } @empty {
          <div class="custom-card p-4 text-center text-muted">
            <i class="bi bi-inbox fs-2 d-block mb-2 text-warning"></i>
            <span>Nenhum detalhe retornado para a seleção.</span>
          </div>
        }
      </div>

      <!-- Barra de Ação no Fluxo da Página / Rodapé -->
      <div class="sticky-bottom-action-bar">
        <div class="d-flex flex-column flex-sm-row justify-content-between align-items-stretch align-items-sm-center gap-2">
          <button 
            type="button" 
            class="btn btn-outline-secondary d-flex align-items-center justify-content-center gap-1 py-2 px-3"
            (click)="voltarSelecao.emit()">
            <i class="bi bi-arrow-left"></i>
            <span>Voltar para Lista</span>
          </button>

          <button 
            type="button" 
            class="btn btn-warning d-flex align-items-center justify-content-center gap-2 py-2 px-4"
            (click)="novaConsulta.emit()">
            <i class="bi bi-search"></i>
            <span>Nova Consulta</span>
          </button>
        </div>
      </div>

    </div>
  `,
})
export class DetalheRegistrosComponent {
  readonly solicitante = input<SolicitanteIdentificacao | null>(null);
  readonly detalhes = input.required<RegistroDetalhe[]>();
  readonly novaConsulta = output<void>();
  readonly voltarSelecao = output<void>();

  readonly copiadoIdx = signal<number | null>(null);

  isPendente(item: RegistroDetalhe): boolean {
    const sit = (item.situacao || item.status || '').toLowerCase();
    return sit.includes('pendente') && !sit.includes('nao') && !sit.includes('não');
  }

  varColorUtilizados(item: RegistroDetalhe): string {
    return (item.dias_utilizados ?? 0) > 0 ? 'var(--primary-accent)' : 'var(--bs-body-color)';
  }

  copiarResumoDocumento(item: RegistroDetalhe, idx: number): void {
    const partes = [
      `Período: ${item.aquisicao || item.id || '-'}`,
      `Doc: ${item.doc_tipo || ''} ${item.doc_numero || ''} (${item.doc_data || '-'})`.trim(),
      item.observacao ? `Obs: ${item.observacao}` : '',
    ].filter(Boolean);
    navigator.clipboard.writeText(partes.join(' | ')).then(() => {
      this.copiadoIdx.set(idx);
      setTimeout(() => this.copiadoIdx.set(null), 2000);
    });
  }
}
