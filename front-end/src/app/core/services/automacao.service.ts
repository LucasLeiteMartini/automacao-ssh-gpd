import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, of, tap, throwError } from 'rxjs';
import {
  ConsultaRegistrosRequest,
  ConsultaRegistrosResponse,
  DetalhesRequest,
  DetalhesResponse,
  HealthStatus,
} from '../models/solicitante.model';

interface EntradaCacheNavegador {
  expiraEm: number;
  dados: ConsultaRegistrosResponse;
}

@Injectable({
  providedIn: 'root',
})
export class AutomacaoService {
  private readonly http = inject(HttpClient);
  private readonly apiBase = '/api/solicitante';
  private readonly cachePrefix = 'sppc_cache_v1:';
  private readonly cacheTtlMs = 10 * 60 * 1000; // 10 minutos

  getHealth(): Observable<HealthStatus> {
    return this.http.get<HealthStatus>('/health').pipe(
      catchError(this.handleError)
    );
  }

  buscarRegistros(
    payload: ConsultaRegistrosRequest,
    forcarAtualizacao = false
  ): Observable<ConsultaRegistrosResponse> {
    const ignorarCache = forcarAtualizacao || !!payload.forcar_atualizacao;
    const chave = this.gerarChaveCache(payload);

    if (!ignorarCache) {
      const emCache = this.lerCacheNavegador(chave);
      if (emCache) {
        return of(emCache);
      }
    }

    return this.http
      .post<ConsultaRegistrosResponse>(`${this.apiBase}/registros`, {
        ...payload,
        forcar_atualizacao: ignorarCache,
      })
      .pipe(
        tap((resposta) => this.salvarCacheNavegador(chave, resposta)),
        catchError(this.handleError)
      );
  }

  extrairDetalhes(payload: DetalhesRequest): Observable<DetalhesResponse> {
    return this.http
      .post<DetalhesResponse>(`${this.apiBase}/detalhes`, payload)
      .pipe(catchError(this.handleError));
  }

  limparCacheNavegador(): void {
    try {
      const chavesParaRemover: string[] = [];
      for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i);
        if (k?.startsWith(this.cachePrefix)) {
          chavesParaRemover.push(k);
        }
      }
      chavesParaRemover.forEach((k) => sessionStorage.removeItem(k));
    } catch {
      // Ignora caso sessionStorage esteja indisponível
    }
  }

  private gerarChaveCache(payload: ConsultaRegistrosRequest): string {
    const mat = payload.matricula.trim();
    const dig = payload.digito.trim();
    const seq = payload.sequencia.trim().toUpperCase();
    const opc = payload.opcao_consulta.trim();
    return `${this.cachePrefix}${mat}-${dig}-${seq}-${opc}`;
  }

  private lerCacheNavegador(chave: string): ConsultaRegistrosResponse | null {
    try {
      const bruto = sessionStorage.getItem(chave);
      if (!bruto) return null;
      const entrada = JSON.parse(bruto) as EntradaCacheNavegador;
      if (Date.now() > entrada.expiraEm) {
        sessionStorage.removeItem(chave);
        return null;
      }
      return entrada.dados;
    } catch {
      return null;
    }
  }

  private salvarCacheNavegador(
    chave: string,
    dados: ConsultaRegistrosResponse
  ): void {
    try {
      const entrada: EntradaCacheNavegador = {
        expiraEm: Date.now() + this.cacheTtlMs,
        dados,
      };
      sessionStorage.setItem(chave, JSON.stringify(entrada));
    } catch {
      // Ignora se exceder cota de armazenamento da sessão
    }
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    let mensagemAmigavel = 'Ocorreu um erro inesperado ao se comunicar com o sistema.';

    if (error.status === 423) {
      mensagemAmigavel =
        error.error?.detail ||
        'O operador legado está ocupado processando outra requisição. Aguarde alguns instantes e tente novamente.';
    } else if (error.status === 504) {
      mensagemAmigavel =
        'O terminal legado demorou para responder (tempo limite esgotado). Tente novamente.';
    } else if (error.status === 0) {
      mensagemAmigavel =
        'Não foi possível conectar ao servidor backend. Verifique se a API está online.';
    } else if (error.error?.detail) {
      mensagemAmigavel = error.error.detail;
    }

    return throwError(() => new Error(mensagemAmigavel));
  }
}
