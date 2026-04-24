import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { StatCard } from "#/components/StatCard";
import { getDashboardStats } from "#/lib/api";
import type { DashboardStats } from "#/lib/types";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
});


function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  if (error) {
    return (
      <div className="max-w-5xl mx-auto p-8">
        <p className="text-sm text-red-600">Error: {error}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="max-w-5xl mx-auto p-8">
        <p className="text-sm text-gray-500">Loading…</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Applications"
          value={stats.total_applications.toString()}
        />
        <StatCard
          label="Total cost"
          value={`$${stats.total_cost_usd.toFixed(2)}`}
          sub={
            stats.total_applications > 0
              ? `$${(stats.total_cost_usd / stats.total_applications).toFixed(3)} / app`
              : undefined
          }
        />
        <StatCard
          label="Reply rate"
          value={`${(stats.reply_rate * 100).toFixed(0)}%`}
          sub={`Interview: ${(stats.interview_rate * 100).toFixed(0)}%`}
        />
        <StatCard
          label="Mean fit score"
          value={
            stats.mean_fit_score !== null
              ? stats.mean_fit_score.toFixed(1)
              : "—"
          }
        />
      </div>

      <h2 className="text-lg font-semibold mb-3">Status breakdown</h2>
      {Object.keys(stats.status_counts).length === 0 ? (
        <p className="text-sm text-gray-500">No applications yet.</p>
      ) : (
        <div className="space-y-2">
          {Object.entries(stats.status_counts)
            .sort((a, b) => b[1] - a[1])
            .map(([status, count]) => {
              const pct = stats.total_applications > 0
                ? (count / stats.total_applications) * 100
                : 0;
              return (
                <div key={status} className="flex items-center gap-3 text-sm">
                  <div className="w-40">{status}</div>
                  <div className="flex-1 h-4 bg-gray-100 rounded relative overflow-hidden">
                    <div
                      className="h-full bg-blue-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="w-12 text-right">{count}</div>
                </div>
              );
            })}
        </div>
      )}
    </div>
  );
}
