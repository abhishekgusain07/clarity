import { useState } from "react";

type Props = {
  coverLetter: {
    body_markdown: string;
    word_count: number;
    voice_similarity_score: number;
    references_company_specifics: string[];
  };
  onApprove: () => void;
  onSkip: () => void;
  submitting?: boolean;
};

export function HitlContentApproval({ coverLetter, onApprove, onSkip, submitting }: Props) {
  const [body, setBody] = useState(coverLetter.body_markdown);
  const voicePct = (coverLetter.voice_similarity_score * 100).toFixed(0);
  const voiceWarning = coverLetter.voice_similarity_score < 0.6;

  return (
    <div className="border rounded-lg p-6 bg-white">
      <h2 className="text-xl font-semibold mb-2">Cover letter review</h2>
      <div className="flex gap-4 text-xs text-gray-600 mb-3">
        <span>{coverLetter.word_count} words</span>
        <span className={voiceWarning ? "text-amber-700 font-medium" : ""}>
          Voice match: {voicePct}%{voiceWarning ? " ⚠" : ""}
        </span>
      </div>

      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        className="w-full min-h-[300px] border rounded-md p-3 font-mono text-sm"
      />

      <div className="mt-4">
        <h3 className="text-sm font-semibold mb-1">Company specifics cited:</h3>
        <ul className="text-xs text-gray-600 list-disc ml-5">
          {coverLetter.references_company_specifics.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          onClick={onApprove}
          disabled={submitting}
          className="px-4 py-2 bg-green-600 text-white rounded-md disabled:opacity-50"
        >
          Approve — fill the form
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
