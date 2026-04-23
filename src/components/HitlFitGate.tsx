type Props = {
  fitAnalysis: {
    overall_score: number;
    verdict: string;
    matches: { dimension: string; evidence_jd: string; evidence_resume: string | null }[];
    stretches: { dimension: string; evidence_jd: string; evidence_resume: string | null }[];
    gaps: { dimension: string; evidence_jd: string; evidence_resume: string | null }[];
    reasoning: string;
    recommended_action: string;
  };
  companyResearch?: { company_name: string; signal_score: number };
  onApprove: () => void;
  onSkip: () => void;
  submitting?: boolean;
};

export function HitlFitGate({ fitAnalysis, companyResearch, onApprove, onSkip, submitting }: Props) {
  return (
    <div className="border rounded-lg p-6 bg-white">
      <h2 className="text-xl font-semibold mb-2">Fit review</h2>
      {companyResearch && (
        <p className="text-sm text-gray-600 mb-4">
          {companyResearch.company_name} — research signal score: {(companyResearch.signal_score * 100).toFixed(0)}%
        </p>
      )}

      <div className="flex items-baseline gap-4 mb-4">
        <span className="text-4xl font-bold">{fitAnalysis.overall_score}</span>
        <span className="text-sm text-gray-500">/ 100 — {fitAnalysis.verdict}</span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <FitColumn title="Matches" items={fitAnalysis.matches} color="green" />
        <FitColumn title="Stretches" items={fitAnalysis.stretches} color="amber" />
        <FitColumn title="Gaps" items={fitAnalysis.gaps} color="red" />
      </div>

      <p className="text-sm text-gray-700 mb-4 italic">{fitAnalysis.reasoning}</p>

      <div className="flex gap-2">
        <button
          onClick={onApprove}
          disabled={submitting}
          className="px-4 py-2 bg-green-600 text-white rounded-md disabled:opacity-50"
        >
          Proceed — draft cover letter
        </button>
        <button
          onClick={onSkip}
          disabled={submitting}
          className="px-4 py-2 border rounded-md disabled:opacity-50"
        >
          Skip
        </button>
      </div>
    </div>
  );
}

function FitColumn({
  title,
  items,
  color,
}: {
  title: string;
  items: { dimension: string; evidence_jd: string; evidence_resume: string | null }[];
  color: "green" | "amber" | "red";
}) {
  const bg = { green: "bg-green-50", amber: "bg-amber-50", red: "bg-red-50" }[color];
  return (
    <div className={`${bg} p-3 rounded text-sm`}>
      <h3 className="font-semibold mb-2">{title}</h3>
      {items.length === 0 && <p className="text-xs text-gray-500">none</p>}
      <ul className="space-y-2">
        {items.map((p, i) => (
          <li key={i}>
            <div className="font-medium">{p.dimension}</div>
            <div className="text-xs text-gray-600">JD: "{p.evidence_jd}"</div>
            {p.evidence_resume && (
              <div className="text-xs text-gray-600">Resume: "{p.evidence_resume}"</div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
