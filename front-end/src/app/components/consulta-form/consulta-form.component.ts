import { Component, output, input } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  ConsultaRegistrosRequest,
  OpcaoConsultaCodigo,
} from '../../core/models/solicitante.model';

export interface OpcaoConsultaItem {
  codigo: OpcaoConsultaCodigo;
  label: string;
}

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
          <p class="text-muted small mb-0">Informe os dados cadastrais para consulta.</p>
        </div>
      </div>

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <!-- Grid Responsivo: Empilhado no mobile, colunas em telas médias+ -->
        <div class="row g-2 g-md-3">

          <!-- Tipo de Consulta (envia o código numérico oculto para o back-end) -->
          <div class="col-12">
            <label class="form-label small fw-semibold text-muted mb-1" for="opcao_consulta">
              Tipo de Consulta
            </label>
            <div class="input-group">
              <span class="input-group-text" style="background-color: var(--surface-card); border-color: var(--border-color);">
                <i class="bi bi-list-ul text-muted"></i>
              </span>
              <select
                id="opcao_consulta"
                class="form-select fw-semibold"
                style="background-color: var(--surface-card); border-color: var(--border-color); color: var(--bs-body-color);"
                formControlName="opcao_consulta">
                <option value="" disabled>Escolha uma opção para consultar</option>
                @for (op of opcoesConsulta; track op.codigo) {
                  <option [value]="op.codigo">{{ op.label }}</option>
                }
              </select>
            </div>
          </div>

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
              inputmode="numeric"
              autocomplete="off"
              [class.is-invalid]="form.get('digito')?.invalid && form.get('digito')?.touched"
            />
            @if (form.get('digito')?.invalid && form.get('digito')?.touched) {
              <div class="text-danger small mt-1">Dígito de 1 número.</div>
            }
          </div>

          <!-- Sequência: 1 letra -->
          <div class="col-6 col-md-4">
            <label class="form-label small fw-semibold text-muted mb-1" for="sequencia">
              Sequência (letras A-Z)
            </label>
            <input
              id="sequencia"
              type="text"
              maxlength="1"
              class="form-control text-center fw-bold"
              style="background-color: var(--surface-card); border-color: var(--border-color); color: var(--bs-body-color);"
              formControlName="sequencia"
              inputmode="text"
              autocomplete="off"
              [class.is-invalid]="form.get('sequencia')?.invalid && form.get('sequencia')?.touched"
            />
            @if (form.get('sequencia')?.invalid && form.get('sequencia')?.touched) {
              <div class="text-danger small mt-1">Informe 1 letra (A-Z).</div>
            }
          </div>

        </div>

        <!-- Botões de Ação -->
        <div class="d-flex flex-column flex-sm-row justify-content-end align-items-stretch align-items-sm-center gap-2 mt-3 pt-2 border-top"
             style="border-color: var(--border-color) !important;">
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

  readonly opcoesConsulta: readonly OpcaoConsultaItem[] = [
    { codigo: '4', label: 'Tempo de serviço' },
    { codigo: '9', label: 'Faltas Registradas' },
    { codigo: '10', label: 'Férias' },
    { codigo: '13', label: 'Licenças Retiradas' },
    { codigo: '16', label: 'Punições e elogios' },
  ];

  readonly form = new FormGroup({
    opcao_consulta: new FormControl<OpcaoConsultaCodigo | ''>('', [
      Validators.required,
      Validators.pattern(/^(4|9|10|13|16)$/),
    ]),
    matricula: new FormControl('', [
      Validators.required,
      Validators.pattern(/^\d{6}$/),
    ]),
    digito: new FormControl('', [
      Validators.required,
      Validators.pattern(/^\d{1}$/),
    ]),
    sequencia: new FormControl('', [
      Validators.required,
      Validators.pattern(/^[a-zA-Z]{1}$/),
    ]),
  });

  onSubmit(): void {
    if (this.form.valid) {
      const val = this.form.value;
      this.buscar.emit({
        matricula: val.matricula!.trim(),
        digito: val.digito!.trim(),
        sequencia: val.sequencia!.trim(),
        opcao_consulta: val.opcao_consulta as OpcaoConsultaCodigo,
      });
    } else {
      this.form.markAllAsTouched();
    }
  }
}
