import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import {
  ConsultaRegistrosRequest,
  ConsultaRegistrosResponse,
  DetalhesRequest,
  DetalhesResponse,
  HealthStatus,
} from '../models/solicitante.model';

@Injectable({
  providedIn: 'root',
})
export class AutomacaoService {
  private readonly http = inject(HttpClient);
  private readonly apiBase = '/api/solicitante';

  getHealth(): Observable<HealthStatus> {
    return this.http.get<HealthStatus>('/health').pipe(
      catchError(this.handleError)
    );
  }

  buscarRegistros(
    payload: ConsultaRegistrosRequest
  ): Observable<ConsultaRegistrosResponse> {
    return this.http
      .post<ConsultaRegistrosResponse>(`${this.apiBase}/registros`, payload)
      .pipe(catchError(this.handleError));
  }

  extrairDetalhes(payload: DetalhesRequest): Observable<DetalhesResponse> {
    return this.http
      .post<DetalhesResponse>(`${this.apiBase}/detalhes`, payload)
      .pipe(catchError(this.handleError));
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
