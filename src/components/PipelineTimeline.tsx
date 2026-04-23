import type { PipelineEvent } from "#/lib/types";

const STATE_LABELS: Record<string, string> = {
  INTAKE_RUNNING: "Parsing JD",
  RESEARCHING: "Researching company + fit",
  AWAITING_FIT_APPROVAL: "⏸ Awaiting your fit approval",
  DRAFTING: "Drafting cover letter",
  AWAITING_CONTENT_APPROVAL: "⏸ Awaiting your content approval",
  FILLING_FORM: "Filling application form",
  AWAITING_SUBMIT_APPROVAL: "⏸ Awaiting your submit approval",
  SUBMITTING: "Submitting application",
  COMPLETED: "✓ Completed",
  ABANDONED: "Abandoned",
  ERRORED: "⚠ Errored",
};

type Props = {
  currentState: string | null;
  events: PipelineEvent[];
};

export function PipelineTimeline({ currentState, events }: Props) {
  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <h2 className="text-sm font-semibold mb-2 text-gray-700">Pipeline timeline</h2>
      <div className="text-sm mb-3">
        Current state:{" "}
        <span className="font-mono">
          {currentState ? STATE_LABELS[currentState] ?? currentState : "—"}
        </span>
      </div>
      <details>
        <summary className="text-xs text-gray-600 cursor-pointer">Events ({events.length})</summary>
        <ul className="text-xs mt-2 space-y-1 font-mono max-h-40 overflow-auto">
          {events.map((ev, i) => (
            <li key={i} className="text-gray-700">
              {ev.type}
              {ev.state ? ` → ${ev.state}` : ""}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
