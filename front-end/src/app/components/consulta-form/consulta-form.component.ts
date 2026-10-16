import { Component, output, input } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ConsultaRegistrosRequest } from '../../core/models/solicitante.model';

@Component({
  selector: 'app-consulta-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="custom-card p-3 p-md-4 mb-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h2 class="h5 fw-bold mb-1 d-flex align-items-center gap-2">
            <i class="bi bi-search text-warning"></i>
            <span>Consultar Registros do Solicitante</span>
          </h2>
          <p class="text-muted small mb-0">Informe os dados cadastrais para consultar o terminal legado.</p>
        </div>
        <button 
          type="button" 
          class="btn btn-sm btn-outline-secondary d-none d-sm-inline-flex align-items-center gap-1"
          (click)="preencherExemplo()">
          <i class="bi bi-magic"></i>
          <span>Exemplo</span>
        </button>
      </div>

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <!-- Grid Responsivo: Empilhado no mobile, 3 colunas em telas médias+ -->
        <div class="row g-2 g-md-3">
          
          <!-- Matrícula: 6 dígitos numéricos -->
          <div class="col-12 col-md-5">
            <label class="form-label small fw-semibold text-muted mb-1" for="matricula">
              Matrícula do Solicitante (6 números)
            </label>
            <div class="input-group">
              <span class="input-group-text" style="background-color: var(--surface-card); border-color: var(--border-color);">
                <i class="bi bi-person-badge text-muted"></i>
              </span>
              <input
                id="matricula"
                type="text"
                maxlength="6"
                class="form-control"
                style="background-color: var(--surface-card); border-color: var(--border-color); color: var(--bs-body-color);"
                formControlName="matricula"
                placeholder="Ex: 123456"
                inputmode="numeric"
                autocomplete="off"
                [class.is-invalid]="form.get('matricula')?.invalid && form.get('matricula')?.touched"
              />
            </div>
            @if (form.get('matricula')?.invalid && form.get('matricula')?.touched) {
              <div class="text-danger small mt-1">A matrícula deve conter exatamente 6 números.</div>
            }
          </div>

          <!-- Dígito: 1 número -->
          <div class="col-6 col-md-3">
            <label class="form-label small fw-semibold text-muted mb-1" for="digito">
              Dígito (1 número)
            </label>
            <input
              id="digito"
              type="text"
              maxlength="1"
              class="form-control text-center fw-bold"
              style="background-color: var(--surface-card); border-color: var(--border-color); color: var(--bs-body-color);"
              formControlName="digito"
              placeholder="Ex: 0"
              inputmode="numeric"
              autocomplete="off"
              [class.is-invalid]="form.get('digito')?.invalid && form.get('digito')?.touched"
            />
            @if (form.get('digito')?.invalid && form.get('digito')?.touched) {
              <div class="text-danger small mt-1">Dígito de 1 número.</div>
            }
          </div>

          <!-- Sequência: 1 caracter alfanumérico -->
          <div class="col-6 col-md-4">
            <label class="form-label small fw-semibold text-muted mb-1" for="sequencia">
              Sequência (1 alfanumérico)
            </label>
            <input
              id="sequencia"
              type="text"
              maxlength="1"
              class="form-control text-center fw-bold"
              style="background-color: var(--surface-card); border-color: var(--border-color); color: var(--bs-body-color);"
              formControlName="sequencia"
              placeholder="Ex: 1 ou A"
              inputmode="text"
              autocomplete="off"
              [class.is-invalid]="form.get('sequencia')?.invalid && form.get('sequencia')?.touched"
            />
            @if (form.get('sequencia')?.invalid && form.get('sequencia')?.touched) {
              <div class="text-danger small mt-1">1 caractere (letra ou número).</div>
            }
          </div>

        </div>

        <!-- Botões de Ação -->
        <div class="d-flex flex-column flex-sm-row justify-content-between align-items-stretch align-items-sm-center gap-2 mt-3 pt-2 border-top" 
             style="border-color: var(--border-color) !important;">
          <button 
            type="button" 
            class="btn btn-sm btn-outline-secondary d-inline-flex d-sm-none justify-content-center align-items-center gap-1"
            (click)="preencherExemplo()">
            <i class="bi bi-magic"></i>
            <span>Preencher Dados de Teste</span>
          </button>

          <button
            type="submit"
            class="btn btn-warning w-100 w-sm-auto d-flex align-items-center justify-content-center gap-2 py-2 px-4 ms-auto"
            [disabled]="form.invalid || loading()">
            <i class="bi bi-arrow-right-circle-fill"></i>
            <span>Buscar Registros</span>
          </button>
        </div>
      </form>
    </div>
  `,
})
export class ConsultaFormComponent {
  readonly loading = input<boolean>(false);
  readonly buscar = output<ConsultaRegistrosRequest>();

  readonly form = new FormGroup({
    matricula: new FormControl('123456', [
      Validators.required,
      Validators.pattern(/^\d{6}$/),
    ]),
    digito: new FormControl('0', [
      Validators.required,
      Validators.pattern(/^\d{1}$/),
    ]),
    sequencia: new FormControl('1', [
      Validators.required,
      Validators.pattern(/^[a-zA-Z0-9]{1}$/),
    ]),
  });

  preencherExemplo(): void {
    this.form.patchValue({
      matricula: '123456',
      digito: '0',
      sequencia: '1',
    });
  }

  onSubmit(): void {
    if (this.form.valid) {
      const val = this.form.value;
      this.buscar.emit({
        matricula: val.matricula!.trim(),
        digito: val.digito!.trim(),
        sequencia: val.sequencia!.trim(),
      });
    } else {
      this.form.markAllAsTouched();
    }
  }
}
