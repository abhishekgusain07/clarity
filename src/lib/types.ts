export type HealthResponse = {
  status: string;
  version: string;
};

export type CreateApplicationResponse = {
  run_id: string;
  application_id: string;
  state: string;
};

export type RunResponse = {
  run_id: string;
  application_id: string;
  state: string;
  cost_accumulated_usd: number;
  artifacts: Record<string, unknown>;
};

export type ApproveRequest = {
  checkpoint: "FIT" | "CONTENT" | "SUBMIT";
  decision: "APPROVE" | "EDIT" | "REGENERATE" | "SKIP" | "CANCEL";
  user_edits?: string;
  notes?: string;
};

export type PipelineEvent = {
  type: string;
  [key: string]: unknown;
};

export type ApplicationSummary = {
  id: string;
  company_name: string;
  role_title: string;
  status: string;
  fit_score: number | null;
  cost_usd: number;
  created_at: string;
  url: string | null;
};

export type ListApplicationsResponse = {
  items: ApplicationSummary[];
  total: number;
};

export type DashboardStats = {
  total_applications: number;
  total_cost_usd: number;
  reply_rate: number;
  interview_rate: number;
  status_counts: Record<string, number>;
  mean_fit_score: number | null;
};

export type OutcomeStatus =
  | "SUBMITTED" | "REPLIED" | "INTERVIEWED" | "REJECTED" | "GHOSTED" | "OFFERED";

export type OutcomeUpdate = {
  status: OutcomeStatus;
  notes?: string;
  next_step?: string;
};

export type OutcomeUpdateResponse = {
  application_id: string;
  outcome_id: string;
  status: string;
  notes: string | null;
  next_step: string | null;
};
