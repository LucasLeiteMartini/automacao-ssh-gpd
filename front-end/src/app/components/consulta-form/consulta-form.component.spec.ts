import { TestBed } from '@angular/core/testing';
import { ConsultaFormComponent } from './consulta-form.component';

describe('ConsultaFormComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConsultaFormComponent],
    }).compileComponents();
  });

  it('deve inicializar com valores válidos de exemplo (6 dígitos, 1 número, 1 alfanumérico)', () => {
    const fixture = TestBed.createComponent(ConsultaFormComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.form.valid).toBe(true);
    expect(component.form.get('matricula')?.value).toBe('123456');
    expect(component.form.get('digito')?.value).toBe('0');
    expect(component.form.get('sequencia')?.value).toBe('1');
  });

  it('deve invalidar o formulário quando a matrícula não tiver exatamente 6 números', () => {
    const fixture = TestBed.createComponent(ConsultaFormComponent);
    const component = fixture.componentInstance;

    // Menos de 6 dígitos
    component.form.patchValue({ matricula: '12345' });
    expect(component.form.get('matricula')?.invalid).toBe(true);

    // Letras na matrícula
    component.form.patchValue({ matricula: '12345A' });
    expect(component.form.get('matricula')?.invalid).toBe(true);

    // 6 dígitos corretos
    component.form.patchValue({ matricula: '654321' });
    expect(component.form.get('matricula')?.valid).toBe(true);
  });

  it('deve invalidar quando o dígito não for exatamente 1 número', () => {
    const fixture = TestBed.createComponent(ConsultaFormComponent);
    const component = fixture.componentInstance;

    component.form.patchValue({ digito: '12' });
    expect(component.form.get('digito')?.invalid).toBe(true);

    component.form.patchValue({ digito: 'X' });
    expect(component.form.get('digito')?.invalid).toBe(true);

    component.form.patchValue({ digito: '9' });
    expect(component.form.get('digito')?.valid).toBe(true);
  });

  it('deve aceitar sequência de 1 caractere alfanumérico (número ou letra)', () => {
    const fixture = TestBed.createComponent(ConsultaFormComponent);
    const component = fixture.componentInstance;

    // Número válido
    component.form.patchValue({ sequencia: '3' });
    expect(component.form.get('sequencia')?.valid).toBe(true);

    // Letra maiúscula válida
    component.form.patchValue({ sequencia: 'A' });
    expect(component.form.get('sequencia')?.valid).toBe(true);

    // Letra minúscula válida
    component.form.patchValue({ sequencia: 'z' });
    expect(component.form.get('sequencia')?.valid).toBe(true);

    // Inválido se tiver 2 caracteres
    component.form.patchValue({ sequencia: '01' });
    expect(component.form.get('sequencia')?.invalid).toBe(true);

    // Inválido se tiver caracteres especiais
    component.form.patchValue({ sequencia: '@' });
    expect(component.form.get('sequencia')?.invalid).toBe(true);
  });

  it('deve emitir o evento buscar ao submeter formulário válido', () => {
    const fixture = TestBed.createComponent(ConsultaFormComponent);
    const component = fixture.componentInstance;

    let payloadRecebido: any = null;
    component.buscar.subscribe((payload) => {
      payloadRecebido = payload;
    });

    component.form.patchValue({
      matricula: '654321',
      digito: '9',
      sequencia: 'A',
    });

    component.onSubmit();
    expect(payloadRecebido).toEqual({
      matricula: '654321',
      digito: '9',
      sequencia: 'A',
    });
  });
});
