import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AutomacaoService } from './core/services/automacao.service';
import {
  ConsultaRegistrosRequest,
  ConsultaRegistrosResponse,
  HealthStatus,
  RegistroDetalhe,
} from './core/models/solicitante.model';
import { HeaderComponent } from './components/header/header.component';
import { ConsultaFormComponent } from './components/consulta-form/consulta-form.component';
import { ListaRegistrosComponent } from './components/lista-registros/lista-registros.component';
import { DetalheRegistrosComponent } from './components/detalhe-registros/detalhe-registros.component';
import { LoadingSpinnerComponent } from './shared/loading-spinner/loading-spinner.component';

export type EtapaFluxo =
  | 'form'
  | 'loading_busca'
  | 'lista'
  | 'loading_detalhes'
  | 'detalhes';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    ConsultaFormComponent,
    ListaRegistrosComponent,
    DetalheRegistrosComponent,
    LoadingSpinnerComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  private readonly automacaoService = inject(AutomacaoService);

  readonly health = signal<HealthStatus | null>(null);
  readonly etapa = signal<EtapaFluxo>('form');
  readonly solicitanteAtivo = signal<ConsultaRegistrosRequest | null>(null);
  readonly dadosLista = signal<ConsultaRegistrosResponse | null>(null);
  readonly dadosDetalhes = signal<RegistroDetalhe[]>([]);
  readonly erroMensagem = signal<string | null>(null);

  ngOnInit(): void {
    this.carregarHealth();
  }

  carregarHealth(): void {
    this.automacaoService.getHealth().subscribe({
      next: (status) => this.health.set(status),
      error: () => this.health.set(null),
    });
  }

  onBuscar(req: ConsultaRegistrosRequest, forcarAtualizacao = false): void {
    this.erroMensagem.set(null);
    this.solicitanteAtivo.set(req);
    this.etapa.set('loading_busca');

    this.automacaoService.buscarRegistros(req, forcarAtualizacao).subscribe({
      next: (resp) => {
        this.dadosLista.set(resp);
        this.etapa.set('lista');
        this.carregarHealth();
      },
      error: (err: Error) => {
        this.erroMensagem.set(err.message);
        this.etapa.set('form');
        this.carregarHealth();
      },
    });
  }

  onAtualizarConsulta(): void {
    const sol = this.solicitanteAtivo();
    if (!sol) return;
    this.onBuscar(sol, true);
  }

  onConfirmarDetalhes(indices: number[]): void {
    const sol = this.solicitanteAtivo();
    if (!sol) return;

    this.erroMensagem.set(null);

    const registrosAtuais = this.dadosLista()?.registros ?? [];
    const conjuntoIndices = new Set(indices);
    const detalhesPreCarregados = registrosAtuais
      .filter((r) => conjuntoIndices.has(r.indice))
      .flatMap((r) => r.detalhes ?? []);

    if (detalhesPreCarregados.length > 0) {
      this.dadosDetalhes.set(detalhesPreCarregados);
      this.etapa.set('detalhes');
      return;
    }

    this.etapa.set('loading_detalhes');

    this.automacaoService
      .extrairDetalhes({
        matricula: sol.matricula,
        digito: sol.digito,
        sequencia: sol.sequencia,
        opcao_consulta: sol.opcao_consulta,
        indices_selecionados: indices,
      })
      .subscribe({
        next: (resp) => {
          this.dadosDetalhes.set(resp.dados);
          this.etapa.set('detalhes');
          this.carregarHealth();
        },
        error: (err: Error) => {
          this.erroMensagem.set(err.message);
          this.etapa.set('lista');
          this.carregarHealth();
        },
      });
  }

  onNovaConsulta(): void {
    this.erroMensagem.set(null);
    this.dadosLista.set(null);
    this.dadosDetalhes.set([]);
    this.etapa.set('form');
    this.carregarHealth();
  }

  onVoltarParaLista(): void {
    this.erroMensagem.set(null);
    this.etapa.set('lista');
  }
}
