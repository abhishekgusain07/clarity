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
