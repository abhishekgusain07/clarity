import { Link, createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { listApplications } from "#/lib/api";
import type { ApplicationSummary } from "#/lib/types";

export const Route = createFileRoute("/applications/")({
  component: ApplicationsIndexPage,
});


const STATUS_COLORS: Record<string, string> = {
  DRAFTING: "bg-gray-100 text-gray-700",
  AWAITING_APPROVAL: "bg-amber-100 text-amber-800",
  SUBMITTED: "bg-blue-100 text-blue-800",
  SUBMITTED_UNCONFIRMED: "bg-blue-50 text-blue-700",
  REPLIED: "bg-green-100 text-green-800",
  INTERVIEWED: "bg-emerald-100 text-emerald-900",
  OFFERED: "bg-purple-100 text-purple-900",
  REJECTED: "bg-red-100 text-red-800",
  GHOSTED: "bg-gray-200 text-gray-600",
  SKIPPED: "bg-gray-50 text-gray-500",
};


function ApplicationsIndexPage() {
  const [items, setItems] = useState<ApplicationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listApplications()
      .then((res) => {
        setItems(res.items);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Applications</h1>
        <Link
          to="/applications/new"
          className="px-4 py-2 bg-black text-white rounded-md text-sm"
        >
          New application
        </Link>
      </div>

      {loading && <p className="text-sm text-gray-500">Loading…</p>}
      {error && <p className="text-sm text-red-600">Error: {error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="text-sm text-gray-600">
          No applications yet. Start one above.
        </p>
      )}

      {items.length > 0 && (
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 pr-4">Company</th>
              <th className="py-2 pr-4">Role</th>
              <th className="py-2 pr-4">Fit</th>
              <th className="py-2 pr-4">Cost</th>
              <th className="py-2 pr-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((app) => (
              <tr key={app.id} className="border-b hover:bg-gray-50">
                <td className="py-2 pr-4 font-medium">{app.company_name || "—"}</td>
                <td className="py-2 pr-4">{app.role_title || "—"}</td>
                <td className="py-2 pr-4">
                  {app.fit_score !== null ? app.fit_score : "—"}
                </td>
                <td className="py-2 pr-4">${app.cost_usd.toFixed(3)}</td>
                <td className="py-2 pr-4">
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      STATUS_COLORS[app.status] ?? "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {app.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
