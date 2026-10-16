import { Component, input } from '@angular/core';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  template: `
    <div class="custom-card p-4 text-center my-4 fade-in">
      <div class="d-inline-flex align-items-center justify-content-center p-3 rounded-circle mb-3"
           style="background-color: var(--primary-accent-light); border: 1px solid var(--border-color-active);">
        <div class="spinner-border text-warning" style="width: 2.5rem; height: 2.5rem;" role="status">
          <span class="visually-hidden">Carregando...</span>
        </div>
      </div>
      <h3 class="h5 fw-bold mb-1">{{ titulo() }}</h3>
      <p class="text-muted small mb-0">{{ descricao() }}</p>
    </div>
  `,
})
export class LoadingSpinnerComponent {
  readonly titulo = input<string>('Processando...');
  readonly descricao = input<string>('Aguarde a resposta do terminal legado...');
}
