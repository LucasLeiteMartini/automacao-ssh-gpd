import { Component, input, output, signal } from '@angular/core';
import { RegistroDetalhe } from '../../core/models/solicitante.model';

@Component({
  selector: 'app-detalhe-registros',
  standalone: true,
  template: `
    <div class="fade-in">
      
      <!-- Cabeçalho de Sucesso -->
      <div class="custom-card p-3 p-md-4 mb-4 text-center text-sm-start">
        <div class="d-flex flex-column flex-sm-row justify-content-between align-items-center gap-3">
          <div class="d-flex align-items-center gap-3">
            <div class="d-flex align-items-center justify-content-center rounded-circle p-3"
                 style="background-color: var(--primary-accent-light); border: 1px solid var(--border-color-active);">
              <i class="bi bi-check2-circle text-warning fs-3"></i>
            </div>
            <div>
              <div class="d-flex align-items-center justify-content-center justify-content-sm-start gap-2 mb-1">
                <span class="badge rounded-pill bg-success">Fase 2 Concluída</span>
                <span class="badge rounded-pill" style="background-color: var(--badge-bg); color: var(--bs-body-color); border: 1px solid var(--border-color);">
                  {{ detalhes().length }} Registro(s) Extraído(s)
                </span>
              </div>
              <h2 class="h5 fw-bold mb-0">Detalhes dos Registros</h2>
              <small class="text-muted">Dados recuperados diretamente da sessão interativa do terminal legado.</small>
            </div>
          </div>

          <button 
            type="button" 
            class="btn btn-warning d-flex align-items-center gap-2 py-2 px-3 w-100 w-sm-auto justify-content-center"
            (click)="novaConsulta.emit()">
            <i class="bi bi-arrow-counterclockwise"></i>
            <span>Nova Consulta</span>
          </button>
        </div>
      </div>

      <!-- Grid de Detalhes (Cards Responsivos) -->
      <div class="row g-3 mb-4">
        @for (item of detalhes(); track item.id) {
          <div class="col-12 col-lg-6">
            <div class="custom-card p-3 p-md-4 h-100 position-relative">
              
              <!-- Topo do Card: ID e Status -->
              <div class="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom" 
                   style="border-color: var(--border-color) !important;">
                <span class="badge py-2 px-3 fs-6 fw-bold" 
                      style="background-color: var(--primary-accent-light); color: var(--primary-accent); border: 1px solid var(--border-color-active);">
                  {{ item.id || 'N/A' }}
                </span>

                <span 
                  class="badge rounded-pill py-2 px-3 fw-semibold"
                  [class.bg-success]="item.status?.toLowerCase() === 'aprovado'"
                  [class.bg-warning]="item.status?.toLowerCase() === 'pendente'"
                  [class.text-dark]="item.status?.toLowerCase() === 'pendente'"
                  [class.bg-info]="item.status?.toLowerCase() === 'em analise' || item.status?.toLowerCase() === 'em análise'">
                  {{ item.status || 'Status N/A' }}
                </span>
              </div>

              <!-- Lista de Campos Estruturados -->
              <div class="d-flex flex-column gap-2 mb-3">
                
                <!-- Tipo -->
                <div>
                  <small class="text-muted d-block" style="font-size: 0.75rem;">TIPO DE PROCESSO</small>
                  <div class="fw-semibold">{{ item.tipo || '—' }}</div>
                </div>

                <!-- Valor Destacado -->
                <div class="p-2 rounded mt-1 d-flex justify-content-between align-items-center"
                     style="background-color: var(--surface-card-hover); border: 1px solid var(--border-color);">
                  <div>
                    <small class="text-muted d-block" style="font-size: 0.72rem;">VALOR DECLARADO</small>
                    <span class="fs-5 fw-bold" style="color: var(--primary-accent);">
                      {{ item.valor || '—' }}
                    </span>
                  </div>
                  
                  @if (item.valor) {
                    <button 
                      type="button" 
                      class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1"
                      (click)="copiarTexto(item.valor, item.id!)"
                      [title]="copiadoId() === item.id ? 'Copiado!' : 'Copiar valor'">
                      @if (copiadoId() === item.id) {
                        <i class="bi bi-check text-success"></i>
                        <span class="small text-success">Copiado</span>
                      } @else {
                        <i class="bi bi-clipboard"></i>
                        <span class="small">Copiar</span>
                      }
                    </button>
                  }
                </div>

                <!-- Data -->
                <div class="mt-1">
                  <small class="text-muted d-block" style="font-size: 0.75rem;">DATA DO REGISTRO</small>
                  <div class="text-body-secondary small">
                    <i class="bi bi-calendar3 me-1"></i>
                    {{ item.data || '—' }}
                  </div>
                </div>

              </div>

            </div>
          </div>
        }
      </div>

      <!-- Rodapé com Ações de Saída -->
      <div class="d-flex justify-content-between align-items-center pt-3 border-top"
           style="border-color: var(--border-color) !important;">
        <button 
          type="button" 
          class="btn btn-outline-secondary d-flex align-items-center gap-1"
          (click)="voltarSelecao.emit()">
          <i class="bi bi-arrow-left"></i>
          <span>Voltar para Lista de Seleção</span>
        </button>

        <button 
          type="button" 
          class="btn btn-warning d-flex align-items-center gap-2"
          (click)="novaConsulta.emit()">
          <i class="bi bi-search"></i>
          <span>Consultar Outro Solicitante</span>
        </button>
      </div>

    </div>
  `,
})
export class DetalheRegistrosComponent {
  readonly detalhes = input.required<RegistroDetalhe[]>();
  readonly novaConsulta = output<void>();
  readonly voltarSelecao = output<void>();

  readonly copiadoId = signal<string | null>(null);

  copiarTexto(texto: string, id: string): void {
    navigator.clipboard.writeText(texto).then(() => {
      this.copiadoId.set(id);
      setTimeout(() => this.copiadoId.set(null), 2000);
    });
  }
}
