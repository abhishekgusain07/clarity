type Props = {
  formFillResult: {
    fields_filled: { name: string; value: string; field_type: string }[];
    unknown_fields: { name: string; best_guess: string | null; reason_flagged: string }[];
    screenshot_path: string;
  };
  onSubmit: () => void;
  onCancel: () => void;
  submitting?: boolean;
};

export function HitlSubmissionGate({ formFillResult, onSubmit, onCancel, submitting }: Props) {
  return (
    <div className="border rounded-lg p-6 bg-white">
      <h2 className="text-xl font-semibold mb-2">Submission review</h2>
      <p className="text-sm text-gray-600 mb-4">
        Agent screenshot: <code>{formFillResult.screenshot_path}</code>
      </p>

      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-1">Fields filled:</h3>
        <ul className="text-xs space-y-1">
          {formFillResult.fields_filled.map((f) => (
            <li key={f.name}>
              <span className="font-mono">✓ {f.name}</span>
              <span className="text-gray-500">
                {" "}
                ({f.field_type}): {f.value.slice(0, 60)}
                {f.value.length > 60 ? "…" : ""}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {formFillResult.unknown_fields.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 rounded">
          <h3 className="text-sm font-semibold mb-1">⚠ Unknown fields (confirm before submitting):</h3>
          <ul className="text-xs space-y-1">
            {formFillResult.unknown_fields.map((f) => (
              <li key={f.name}>
                <span className="font-mono">{f.name}</span>: guess{" "}
                <span className="italic">"{f.best_guess}"</span> — {f.reason_flagged}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={onSubmit}
          disabled={submitting}
          className="px-4 py-2 bg-black text-white rounded-md disabled:opacity-50"
        >
          Submit application
        </button>
        <button
          onClick={onCancel}
          disabled={submitting}
          className="px-4 py-2 border rounded-md disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
