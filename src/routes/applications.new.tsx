import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { createApplication } from "#/lib/api";

export const Route = createFileRoute("/applications/new")({
  component: NewApplicationPage,
});

function NewApplicationPage() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await createApplication(url);
      navigate({ to: "/applications/$id", params: { id: res.run_id } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "unknown error");
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-4">New application</h1>
      <p className="text-sm text-gray-600 mb-6">
        Paste a job posting URL. The agent team will research, draft, and prepare the application for your approval.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://workatastartup.com/jobs/123"
          className="w-full px-3 py-2 border rounded-md"
          disabled={submitting}
        />
        <button
          type="submit"
          disabled={submitting || !url}
          className="px-4 py-2 bg-black text-white rounded-md disabled:opacity-50"
        >
          {submitting ? "Starting..." : "Start application"}
        </button>
      </form>
      {error && <p className="mt-4 text-red-600 text-sm">{error}</p>}
    </div>
  );
}
