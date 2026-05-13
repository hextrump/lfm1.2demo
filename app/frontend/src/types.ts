export interface SampleApplication {
  id: string;
  title: string;
  text: string;
}

export interface DeficiencyItem {
  field: string;
  issue: string;
  severity: string;
}

export interface RiskFactor {
  category: string;
  description: string;
  score: number;
}

export interface PipelineResult {
  id: string;
  extracted: Record<string, unknown>;
  deficiency: Record<string, unknown>;
  risk: Record<string, unknown>;
  decision: Record<string, unknown>;
  ledger: Record<string, unknown>;
  is_unclear: boolean;
  unclear_reason: string;
  unclear_suggestion: string;
}

export interface ApiResponse {
  result?: PipelineResult;
  samples?: SampleApplication[];
  llama_server_ready?: boolean;
  model?: string;
}

export interface ProcessResponse {
  id: string;
  extracted: Record<string, unknown>;
  deficiency: Record<string, unknown>;
  risk: Record<string, unknown>;
  decision: Record<string, unknown>;
  ledger: Record<string, unknown>;
  is_unclear: boolean;
  unclear_reason: string;
  unclear_suggestion: string;
}

export interface LedgerEntry {
  id: string;
  ledger_id: string;
  applicant_name: string;
  applicant_dept: string;
  application_type: string;
  application_date: string;
  application_summary: string;
  estimated_cost: string;
  priority_level: string;
  risk_level: string;
  decision: string;
  status: string;
  confidence_score: number;
  entry_date: string;
  is_unclear: boolean;
  unclear_reason: string;
}

export interface LedgerForm {
  applicant_name: string;
  applicant_dept: string;
  application_type: string;
  application_date: string;
  application_summary: string;
  estimated_cost: string;
  priority_level: string;
  risk_level: string;
  decision: string;
  status: string;
}
