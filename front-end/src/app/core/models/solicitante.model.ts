export interface SolicitanteIdentificacao {
  matricula: string;
  digito: string;
  sequencia: string;
}

export interface RegistroItem {
  indice: number;
  id: string;
  descricao: string;
  selecionado?: boolean; // Controle local da interface
}

export interface ConsultaRegistrosRequest {
  matricula: string;
  digito: string;
  sequencia: string;
}

export interface ConsultaRegistrosResponse {
  solicitante: SolicitanteIdentificacao;
  registros: RegistroItem[];
}

export interface DetalhesRequest {
  matricula: string;
  digito: string;
  sequencia: string;
  indices_selecionados: number[];
}

export interface RegistroDetalhe {
  id: string | null;
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
