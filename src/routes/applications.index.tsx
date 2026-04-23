import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/applications/")({
  component: ApplicationsIndexPage,
});

function ApplicationsIndexPage() {
  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-4">Applications</h1>
      <p className="text-sm text-gray-600 mb-6">
        List view coming in Phase 5 — for now, start a new application.
      </p>
      <Link
        to="/applications/new"
        className="inline-block px-4 py-2 bg-black text-white rounded-md"
      >
        New application
      </Link>
    </div>
  );
}
