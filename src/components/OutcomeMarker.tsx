import { useState } from "react";
import { updateOutcome } from "#/lib/api";
import type { OutcomeStatus } from "#/lib/types";

type Props = {
  applicationId: string;
  currentStatus: string;
  onUpdated: (newStatus: string) => void;
};

const OPTIONS: { value: OutcomeStatus; label: string }[] = [
  { value: "SUBMITTED", label: "Submitted" },
  { value: "REPLIED", label: "Got a reply" },
  { value: "INTERVIEWED", label: "Interviewed" },
  { value: "OFFERED", label: "Got an offer" },
  { value: "REJECTED", label: "Rejected" },
  { value: "GHOSTED", label: "Ghosted" },
];

export function OutcomeMarker({ applicationId, currentStatus, onUpdated }: Props) {
  const [status, setStatus] = useState<OutcomeStatus>(
    (["SUBMITTED", "REPLIED", "INTERVIEWED", "OFFERED", "REJECTED", "GHOSTED"] as const).includes(
      currentStatus as OutcomeStatus,
    )
      ? (currentStatus as OutcomeStatus)
      : "SUBMITTED",
  );
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const res = await updateOutcome(applicationId, {
        status,
        notes: notes || undefined,
      });
      onUpdated(res.status);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="border rounded-lg p-4 bg-gray-50 mt-4">
      <h3 className="text-sm font-semibold mb-2">Mark outcome</h3>
      <div className="flex items-start gap-2 mb-2">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as OutcomeStatus)}
          disabled={saving}
          className="px-2 py-1 border rounded text-sm"
        >
          {OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notes (optional)"
          disabled={saving}
          className="flex-1 px-2 py-1 border rounded text-sm"
        />
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-3 py-1 bg-black text-white rounded text-sm disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save"}
        </button>
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {saved && <p className="text-xs text-green-700">Outcome recorded.</p>}
    </div>
  );
}
