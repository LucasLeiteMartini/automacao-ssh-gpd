import { Injectable, signal, effect } from '@angular/core';

export type AppTheme = 'dark' | 'light';

@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  private readonly THEME_KEY = 'automacao_theme';
  
  // Inicia com tema escuro (preto e amarelo) por padrão
  readonly currentTheme = signal<AppTheme>(
    (localStorage.getItem(this.THEME_KEY) as AppTheme) || 'dark'
  );

  constructor() {
    // Aplica o tema sempre que o signal for atualizado
    effect(() => {
      const theme = this.currentTheme();
      document.documentElement.setAttribute('data-bs-theme', theme);
      localStorage.setItem(this.THEME_KEY, theme);
    });
  }

  toggleTheme(): void {
    this.currentTheme.update((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }

  isDark(): boolean {
    return this.currentTheme() === 'dark';
  }
}
