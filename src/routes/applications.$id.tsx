import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { HitlContentApproval } from "#/components/HitlContentApproval";
import { HitlFitGate } from "#/components/HitlFitGate";
import { HitlSubmissionGate } from "#/components/HitlSubmissionGate";
import { OutcomeMarker } from "#/components/OutcomeMarker";
import { PipelineTimeline } from "#/components/PipelineTimeline";
import { approveRun, getRun } from "#/lib/api";
import { useRunEvents } from "#/lib/sse";
import type { RunResponse } from "#/lib/types";

export const Route = createFileRoute("/applications/$id")({
  component: RunDetailPage,
});

function RunDetailPage() {
  const { id } = Route.useParams();
  const [run, setRun] = useState<RunResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const events = useRunEvents(id);

  async function refresh() {
    try {
      const r = await getRun(id);
      setRun(r);
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 1000);
    return () => clearInterval(interval);
  }, [id]);

  useEffect(() => {
    // Events can carry new state info; refresh eagerly on each
    if (events.length > 0) refresh();
  }, [events.length]);

  async function approve(checkpoint: "FIT" | "CONTENT" | "SUBMIT") {
    setSubmitting(true);
    try {
      await approveRun(id, { checkpoint, decision: "APPROVE" });
      await refresh();
    } finally {
      setSubmitting(false);
    }
  }

  if (!run) return <div className="p-8">Loading…</div>;

  const artifacts = run.artifacts as Record<string, any>;

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-4">
      <h1 className="text-2xl font-semibold">Application run</h1>
      <p className="text-xs text-gray-500">
        Run {run.run_id} • App {run.application_id} • Cost ${run.cost_accumulated_usd.toFixed(3)}
      </p>

      <PipelineTimeline currentState={run.state} events={events} />

      {run.state === "AWAITING_FIT_APPROVAL" && artifacts.fit_analysis && (
        <HitlFitGate
          fitAnalysis={artifacts.fit_analysis}
          companyResearch={artifacts.company_research}
          onApprove={() => approve("FIT")}
          onSkip={() => {/* SKIP flow in phase 2+ */}}
          submitting={submitting}
        />
      )}

      {run.state === "AWAITING_CONTENT_APPROVAL" && artifacts.cover_letter && (
        <HitlContentApproval
          coverLetter={artifacts.cover_letter}
          onApprove={() => approve("CONTENT")}
          onSkip={() => {/* SKIP flow in phase 2+ */}}
          submitting={submitting}
        />
      )}

      {run.state === "AWAITING_SUBMIT_APPROVAL" && artifacts.form_fill_result && (
        <HitlSubmissionGate
          formFillResult={artifacts.form_fill_result}
          onSubmit={() => approve("SUBMIT")}
          onCancel={() => {/* CANCEL flow in phase 2+ */}}
          submitting={submitting}
        />
      )}

      {run.state === "COMPLETED" && (
        <div className="border rounded-lg p-6 bg-green-50">
          <h2 className="text-xl font-semibold">Application submitted ✓</h2>
          <p className="text-sm mt-2">
            Confirmation: {(artifacts.submission_confirmation as any)?.url ?? "—"}
          </p>
          <OutcomeMarker
            applicationId={run.application_id}
            currentStatus={run.state}
            onUpdated={() => refresh()}
          />
        </div>
      )}
    </div>
  );
}
