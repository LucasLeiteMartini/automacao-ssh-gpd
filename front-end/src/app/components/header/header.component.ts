import { Component, inject, input } from '@angular/core';
import { ThemeService } from '../../core/services/theme.service';
import { HealthStatus } from '../../core/models/solicitante.model';

@Component({
  selector: 'app-header',
  standalone: true,
  template: `
    <header class="navbar navbar-expand border-bottom py-2 px-3 mb-4" style="background-color: var(--navbar-bg);">
      <div class="container-fluid d-flex justify-content-between align-items-center">
        
        <!-- Slot para Logotipo / Identificação Institucional -->
        <div class="d-flex align-items-center gap-2">
          <div class="logo-slot d-flex align-items-center justify-content-center rounded p-1" 
               style="background: var(--primary-accent-light); width: 42px; height: 42px; border: 1px solid var(--border-color-active);">
            <!-- Placeholder para Logo (substituível por <img> posteriormente) -->
            <i class="bi bi-terminal-fill fs-4" style="color: var(--primary-accent);"></i>
          </div>
          <div>
            <h1 class="h6 mb-0 fw-bold d-flex align-items-center gap-2">
              <span>Terminal Legado</span>
              <span class="badge rounded-pill d-none d-sm-inline-block text-uppercase" 
                    style="background-color: var(--badge-bg); color: var(--primary-accent); border: 1px solid var(--border-color); font-size: 0.65rem;">
                Automação SSH
              </span>
            </h1>
            <small class="text-muted d-block" style="font-size: 0.72rem;">Sessão Segura Monousuário</small>
          </div>
        </div>

        <!-- Ações do Cabeçalho: Brasão, Status e Alternador de Tema -->
        <div class="d-flex align-items-center gap-2">
          
          <!-- Indicador de Status do Operador -->
          @if (health()) {
            <div class="d-none d-md-flex align-items-center gap-1 px-2 py-1 rounded" 
                 style="background-color: var(--surface-card); border: 1px solid var(--border-color); font-size: 0.78rem;">
              @if (health()!.operador_ocupado) {
                <span class="spinner-grow spinner-grow-sm text-warning" role="status"></span>
                <span class="text-warning fw-semibold">Operador Ocupado</span>
              } @else {
                <span class="badge bg-success rounded-circle p-1" style="width: 8px; height: 8px;"></span>
                <span class="text-success fw-semibold">Operador Livre</span>
              }
            </div>
          }

          <!-- Slot para Brasão Institucional (Placeholder) -->
          <div class="brasao-slot d-none d-sm-flex align-items-center justify-content-center rounded" 
               title="Espaço para Brasão Institucional"
               style="width: 38px; height: 38px; border: 1px dashed var(--border-color); color: var(--text-muted);">
            <i class="bi bi-shield-shaded fs-5"></i>
          </div>

          <!-- Botão Alternador de Tema Claro / Escuro -->
          <button 
            type="button" 
            class="btn btn-sm btn-outline-secondary d-flex align-items-center justify-content-center"
            style="width: 38px; height: 38px; border-radius: 0.5rem;"
            (click)="themeService.toggleTheme()"
            [title]="themeService.isDark() ? 'Mudar para Tema Claro' : 'Mudar para Tema Escuro'">
            @if (themeService.isDark()) {
              <i class="bi bi-sun-fill text-warning fs-5"></i>
            } @else {
              <i class="bi bi-moon-stars-fill text-dark fs-5"></i>
            }
          </button>

        </div>
      </div>
    </header>
  `,
})
export class HeaderComponent {
  readonly themeService = inject(ThemeService);
  readonly health = input<HealthStatus | null>(null);
}
