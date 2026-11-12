export type OpcaoConsultaCodigo = '4' | '9' | '10' | '13' | '16';

export interface SolicitanteIdentificacao {
  matricula: string;
  digito: string;
  sequencia: string;
  opcao_consulta: OpcaoConsultaCodigo;
  nome?: string | null;
  lotacao?: string | null;
}

export interface RegistroItem {
  indice: number;
  id: string;
  descricao: string;
  aquisicao_inicio?: string | null;
  aquisicao_fim?: string | null;
  dias_adquiridos?: number;
  status?: string | null;
  utilizacao_inicio?: string | null;
  dias_utilizados?: number;
  dias_utilizados_periodo?: number;
  saldo_disponivel?: number;
  doc_tipo?: string | null;
  doc_numero?: string | null;
  doc_data?: string | null;
  selecionado?: boolean; // Controle local da interface (Fase 2 em stand-by)
}

export interface PeriodoPendenteResumo {
  periodo: string;
  dias_adquiridos: number;
  dias_utilizados_periodo: number;
  saldo_disponivel: number;
}

export interface ConsultaRegistrosRequest {
  matricula: string;
  digito: string;
  sequencia: string;
  opcao_consulta: OpcaoConsultaCodigo;
}

export interface ConsultaRegistrosResponse {
  solicitante: SolicitanteIdentificacao;
  registros: RegistroItem[];
}

export interface DetalhesRequest {
  matricula: string;
  digito: string;
  sequencia: string;
  opcao_consulta: OpcaoConsultaCodigo;
  indices_selecionados: number[];
}

export interface RegistroDetalhe {
  id: string | null;
  aquisicao?: string | null;
  dias_adquiridos?: number;
  dias_utilizados?: number;
  dias_restantes?: number;
  situacao?: string | null;
  previsao?: string | null;
  utilizacao?: string | null;
  dias_gozados?: number;
  doc_tipo?: string | null;
  doc_numero?: string | null;
  doc_data?: string | null;
  observacao?: string | null;
  tipo: string | null;
  valor: string | null;
  status: string | null;
  data: string | null;
}

export interface DetalhesResponse {
  status: string;
  dados: RegistroDetalhe[];
}

export interface HealthStatus {
  status: string;
  operador_ocupado: boolean;
}
