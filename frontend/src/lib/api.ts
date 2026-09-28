const BASE_URL = import.meta.env.VITE_API_URL || '/api';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, `API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export interface RunStats {
  transactions: number;
  network_obs: number;
  alerts: number;
  alert_evidence: number;
}

export interface RunResponse {
  run_id: string;
  status: string;
  current_stage?: string;
  failed_stage?: string;
  error_message?: string;
  start_timestamp?: string;
  end_timestamp?: string;
  geoip_status?: string;
}

export interface AlertSummary {
  alert_id: string;
  txid: string;
  anomaly_strength: number;
  evidential_strength_tier: string;
  operational_queue_rank?: number;
  model_version: string;
  dampeners_applied: string[];
}

export interface PaginatedResponse<T> {
  limit: number;
  offset: number;
  total: number;
  data: T[];
}

export interface AlertReasonResponse {
  reason_text: string;
  signal_type: string;
  feature_name: string;
  computation_value: number;
}

export interface AlertEvidenceResponse {
  evidence_id: string;
  evidence_category: string;
  provenance_type: string;
  source_file?: string;
  source_row?: number;
  model_version?: string;
  schema_version?: string;
  feature_name?: string;
  underlying_evidence_references: string[];
  original_value?: string;
  derived_value?: string;
  uncertainty_semantics?: string;
}

export interface KeyDriverResponse {
  feature: string;
  value?: number;
  shap_value: number;
  direction: string;
  meaning: string;
}

export interface AlertDetail extends AlertSummary {
  reasons: AlertReasonResponse[];
  evidence: AlertEvidenceResponse[];
  summary?: string;
  key_drivers?: KeyDriverResponse[];
  investigation_caveats?: string[];
  provenance?: string[];
  human_readable_lead?: string;
}

export interface TransactionIO {
  address: string;
  amount: number;
}

export interface ObservedPeer {
  ip_address: string;
  port: number;
  geo_country?: string;
  asn?: string;
}

export interface ExplanationResponse {
  summary: string;
  key_drivers: KeyDriverResponse[];
  investigation_caveats: string[];
  provenance: string[];
  human_readable_lead: string;
}

export interface TransactionInvestigationResponse {
  txid: string;
  run_id: string;
  source_file: string;
  source_row: number;
  fee?: number;
  script_type?: string;
  inputs: TransactionIO[];
  outputs: TransactionIO[];
  first_observed_network_timestamp?: string;
  last_observed_network_timestamp?: string;
  observed_peers: ObservedPeer[];
  entity_clusters: number[];
  alerts: AlertSummary[];
  explanation?: ExplanationResponse;
}

export interface GraphNodeResponse {
  id: string;
  node_type: string;
  run_id: string;
  metadata?: Record<string, string | number | boolean>;
}

export interface GraphEdgeResponse {
  source: string;
  target: string;
  edge_type: string;
  network_role: string;
  provenance?: string;
  amount?: number;
  timestamp?: string;
}

export interface GraphResponse {
  nodes: GraphNodeResponse[];
  edges: GraphEdgeResponse[];
  run_id: string;
  depth: number;
}

export const apiClient = {
  health: () => fetchApi<{ status: string; version: string }>('/health'),
  getRuns: (limit = 50, offset = 0) => fetchApi<PaginatedResponse<RunResponse>>(`/runs?limit=${limit}&offset=${offset}`),
  getRun: (runId: string) => fetchApi<RunResponse>(`/runs/${runId}`),
  getRunStats: (runId: string) => fetchApi<RunStats>(`/runs/${runId}/stats`),
  getAlerts: (runId: string, limit = 50, offset = 0) => fetchApi<PaginatedResponse<AlertSummary>>(`/runs/${runId}/alerts?limit=${limit}&offset=${offset}`),
  getAlert: (runId: string, alertId: string) => fetchApi<AlertDetail>(`/runs/${runId}/alerts/${alertId}`),
  getTransaction: (runId: string, txid: string) => fetchApi<TransactionInvestigationResponse>(`/runs/${runId}/transactions/${txid}`),
  getGraphNeighbors: (runId: string, txid: string, depth = 1) => fetchApi<GraphResponse>(`/runs/${runId}/transactions/${txid}/neighbors?depth=${depth}`),
  search: (query: string, category: string, limit = 50, runId?: string) => {
    let url = `/search?q=${encodeURIComponent(query)}&category=${encodeURIComponent(category)}&limit=${limit}`;
    if (runId) url += `&run_id=${encodeURIComponent(runId)}`;
    return fetchApi<SearchResponse>(url);
  },
  createRun: (runId?: string) => fetchApi<RunResponse>(`/runs`, {
    method: 'POST',
    body: runId ? JSON.stringify({ run_id: runId }) : undefined
  }),
  uploadDataset: async (runId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/runs/${runId}/ingest`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new ApiError(response.status, `Upload Failed: ${response.statusText}`);
    return response.json();
  },
  executeRun: (runId: string) => fetchApi<{status: string}>(`/runs/${runId}/execute`, {
    method: 'POST'
  }),
};


export interface SearchResult {
  record_type: string;
  primary_identifier: string;
  display_name: string;
  run_id?: string;
  txid?: string;
  alert_id?: string;
  metadata?: Record<string, string>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  limit: number;
}
