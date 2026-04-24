# Apply — Phase 5a Implementation Plan (Dashboard + Outcome Logging)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans.

**Goal:** Ship the user-facing dashboard surface that makes all previous phases *usable*: a real applications list page backed by the database, an outcome-marking UI that feeds `memory-mcp`, and an aggregate-stats dashboard (total applied, reply rate, cost-per-application, fit-score distribution). No new agent work — this phase takes the existing data and makes it visible.

**Architecture:** Three new REST endpoints (`GET /applications`, `GET /dashboard/stats`, `PATCH /applications/{id}/outcome`) backed by the existing Postgres tables + the `outcomes` table from Phase 3b. Frontend: `/applications/index` renders a real table; `/applications/$id` gains an outcome-marking form; new `/dashboard` route renders aggregated stats as cards + a simple bar chart.

**Tech Stack:** FastAPI + SQLAlchemy (existing). TanStack Start + React 19 (existing). No new deps.

**Scope limits:**
- **No chart library.** Stats use simple CSS bars and Tailwind. Adding recharts/chart.js is scope creep for a dashboard that shows <5 metrics.
- **Outcome marking is user-driven.** Auto-detection from inbox is Phase 5b / future work.
- **No auth.** Still a single-user local dev tool; adding auth is Phase 6+ when we hit multi-user.

**Spec reference:** `docs/superpowers/specs/2026-04-23-auto-apply-design.md` § 12 (build schedule, week 4)

---

## File map

**New (backend):**
- `backend/src/apply/api/routes_dashboard.py` — stats aggregation endpoint
- `backend/tests/test_api_dashboard.py`

**Modified (backend):**
- `backend/src/apply/api/routes_applications.py` — add `GET /applications` list endpoint
- `backend/src/apply/api/routes_applications.py` — add `PATCH /applications/{id}/outcome` endpoint
- `backend/src/apply/api/main.py` — mount dashboard router
- `backend/tests/test_api_applications.py` — append tests for new endpoints

**New (frontend):**
- `src/components/OutcomeMarker.tsx` — inline outcome dropdown + notes textarea
- `src/components/StatCard.tsx` — stat tile (value, label, trend)
- `src/routes/dashboard.tsx` — new dashboard page

**Modified (frontend):**
- `src/lib/types.ts` — add `ApplicationSummary`, `DashboardStats`, `OutcomeUpdate` types
- `src/lib/api.ts` — add `listApplications`, `getDashboardStats`, `updateOutcome` functions
- `src/routes/applications.index.tsx` — replace placeholder with real list fetched from API
- `src/routes/applications.$id.tsx` — add outcome-marking panel for COMPLETED applications
- `src/components/Header.tsx` — add `Dashboard` nav link

---

## Prerequisites

- Phase 4a merged to master (`git log master --oneline | head -1` shows `eb1cc05` or later)
- Postgres running
- Node + pnpm for frontend

---

## Task 1: API — `GET /applications` list

**Files:**
- Modify: `backend/src/apply/api/routes_applications.py`
- Modify: `backend/tests/test_api_applications.py`

- [ ] **Step 1: Write failing test**

Append to `backend/tests/test_api_applications.py`:

```python
@pytest.mark.asyncio
async def test_list_applications_empty(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/applications")

    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "total": 0}


@pytest.mark.asyncio
async def test_list_applications_returns_summaries(app, db_session):
    from apply.db.models import Application, User

    db_session.add(User(id="user-local", email="local@apply.dev", name="Local", profile_json={}))
    await db_session.flush()
    db_session.add(Application(
        id="app-1",
        user_id="user-local",
        status="SUBMITTED",
        job_listing_json={
            "id": "job-1",
            "company_name": "Acme AI",
            "role_title": "Founding Engineer",
            "url": "https://example.com/jobs/1",
        },
        fit_analysis_json={"overall_score": 78, "verdict": "MODERATE"},
        cost_breakdown_json={"per_agent_usd": {"intake": 0.001, "researcher": 0.05}},
    ))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/applications")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["id"] == "app-1"
    assert item["company_name"] == "Acme AI"
    assert item["role_title"] == "Founding Engineer"
    assert item["status"] == "SUBMITTED"
    assert item["fit_score"] == 78
    assert item["cost_usd"] == pytest.approx(0.051)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/test_api_applications.py -v -k list_applications
```

Expected: FAIL — endpoint doesn't exist yet (404).

- [ ] **Step 3: Implement endpoint**

Modify `backend/src/apply/api/routes_applications.py`. Add imports if missing:

```python
from sqlalchemy import desc, select

from apply.db.models import Application as ApplicationRow
```

Add response models at the top (after the existing request/response models):

```python
class ApplicationSummary(BaseModel):
    id: str
    company_name: str
    role_title: str
    status: str
    fit_score: int | None
    cost_usd: float
    created_at: str
    url: str | None


class ListApplicationsResponse(BaseModel):
    items: list[ApplicationSummary]
    total: int
```

Add the endpoint function:

```python
@router.get("", response_model=ListApplicationsResponse)
async def list_applications(
    session: AsyncSession = Depends(get_session),
) -> ListApplicationsResponse:
    stmt = select(ApplicationRow).order_by(desc(ApplicationRow.created_at))
    result = await session.execute(stmt)
    rows = result.scalars().all()

    items: list[ApplicationSummary] = []
    for row in rows:
        jd = row.job_listing_json or {}
        fit = row.fit_analysis_json or {}
        cost = (row.cost_breakdown_json or {}).get("per_agent_usd", {})
        items.append(
            ApplicationSummary(
                id=row.id,
                company_name=jd.get("company_name", ""),
                role_title=jd.get("role_title", ""),
                status=str(row.status),
                fit_score=fit.get("overall_score"),
                cost_usd=float(sum(cost.values())) if cost else 0.0,
                created_at=row.created_at.isoformat() if row.created_at else "",
                url=jd.get("url"),
            )
        )

    return ListApplicationsResponse(items=items, total=len(items))
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/test_api_applications.py -v -k list_applications
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/api/routes_applications.py backend/tests/test_api_applications.py
git commit -m "feat(api): GET /applications list with summaries"
```

---

## Task 2: API — `PATCH /applications/{id}/outcome`

**Files:**
- Modify: `backend/src/apply/api/routes_applications.py`
- Modify: `backend/tests/test_api_applications.py`

- [ ] **Step 1: Append failing test**

Append to `backend/tests/test_api_applications.py`:

```python
@pytest.mark.asyncio
async def test_update_outcome_new(app, db_session):
    from apply.db.models import Application, User

    db_session.add(User(id="user-local", email="l@e.co", name="L", profile_json={}))
    await db_session.flush()
    db_session.add(Application(
        id="app-2", user_id="user-local", status="SUBMITTED",
        job_listing_json={"company_name": "Acme", "role_title": "E"},
    ))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/applications/app-2/outcome",
            json={"status": "REPLIED", "notes": "Recruiter reached out"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["application_id"] == "app-2"
    assert body["status"] == "REPLIED"
    assert body["notes"] == "Recruiter reached out"


@pytest.mark.asyncio
async def test_update_outcome_404_on_unknown_app(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/applications/nonexistent/outcome",
            json={"status": "REPLIED"},
        )
    assert response.status_code == 404
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/test_api_applications.py -v -k update_outcome
```

Expected: FAIL (404 or unknown route).

- [ ] **Step 3: Implement endpoint**

Append to `backend/src/apply/api/routes_applications.py`:

```python
from typing import Literal


class OutcomeUpdateRequest(BaseModel):
    status: Literal["SUBMITTED", "REPLIED", "INTERVIEWED", "REJECTED", "GHOSTED", "OFFERED"]
    notes: str | None = None
    next_step: str | None = None


class OutcomeUpdateResponse(BaseModel):
    application_id: str
    outcome_id: str
    status: str
    notes: str | None
    next_step: str | None


@router.patch("/{application_id}/outcome", response_model=OutcomeUpdateResponse)
async def update_outcome(
    application_id: str,
    req: OutcomeUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> OutcomeUpdateResponse:
    from sqlalchemy import select
    from fastapi import HTTPException
    import uuid

    from apply.db.models import Application as ApplicationRow
    from apply.db.models import Outcome as OutcomeRow

    result = await session.execute(
        select(ApplicationRow).where(ApplicationRow.id == application_id)
    )
    app_row = result.scalar_one_or_none()
    if app_row is None:
        raise HTTPException(status_code=404, detail=f"application {application_id} not found")

    # Pull company + url from the stored JSON listing for denormalization
    listing = app_row.job_listing_json or {}

    outcome_id = f"out-{uuid.uuid4().hex[:8]}"
    outcome_row = OutcomeRow(
        id=outcome_id,
        application_id=application_id,
        status=req.status,
        notes=req.notes,
        next_step=req.next_step,
        company_name=listing.get("company_name"),
        jd_url=listing.get("url"),
        cover_letter_text=(app_row.cover_letter_json or {}).get("body_markdown"),
    )
    session.add(outcome_row)

    # Also update the application's top-level status for display consistency
    app_row.status = req.status
    await session.commit()

    return OutcomeUpdateResponse(
        application_id=application_id,
        outcome_id=outcome_id,
        status=req.status,
        notes=req.notes,
        next_step=req.next_step,
    )
```

- [ ] **Step 4: Run test to verify pass**

```bash
cd backend && uv run pytest tests/test_api_applications.py -v -k update_outcome
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/apply/api/routes_applications.py backend/tests/test_api_applications.py
git commit -m "feat(api): PATCH /applications/{id}/outcome with Outcome row creation"
```

---

## Task 3: API — `GET /dashboard/stats`

**Files:**
- Create: `backend/src/apply/api/routes_dashboard.py`
- Modify: `backend/src/apply/api/main.py`
- Create: `backend/tests/test_api_dashboard.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_api_dashboard.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from apply.api.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_dashboard_stats_empty(app, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/dashboard/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_applications"] == 0
    assert body["total_cost_usd"] == 0.0
    assert body["reply_rate"] == 0.0
    assert body["interview_rate"] == 0.0
    assert body["status_counts"] == {}


@pytest.mark.asyncio
async def test_dashboard_stats_with_applications(app, db_session):
    from apply.db.models import Application, User

    db_session.add(User(id="user-local", email="l@e.co", name="L", profile_json={}))
    await db_session.flush()

    # 3 apps: 1 SUBMITTED, 1 REPLIED, 1 INTERVIEWED
    db_session.add_all([
        Application(
            id="app-1", user_id="user-local", status="SUBMITTED",
            job_listing_json={"company_name": "A"},
            cost_breakdown_json={"per_agent_usd": {"a": 0.10}},
            fit_analysis_json={"overall_score": 70},
        ),
        Application(
            id="app-2", user_id="user-local", status="REPLIED",
            job_listing_json={"company_name": "B"},
            cost_breakdown_json={"per_agent_usd": {"a": 0.20}},
            fit_analysis_json={"overall_score": 85},
        ),
        Application(
            id="app-3", user_id="user-local", status="INTERVIEWED",
            job_listing_json={"company_name": "C"},
            cost_breakdown_json={"per_agent_usd": {"a": 0.30}},
            fit_analysis_json={"overall_score": 82},
        ),
    ])
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/dashboard/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_applications"] == 3
    assert body["total_cost_usd"] == pytest.approx(0.60)
    # reply_rate = replied-or-better / total = 2/3
    assert body["reply_rate"] == pytest.approx(2 / 3)
    assert body["interview_rate"] == pytest.approx(1 / 3)
    assert body["status_counts"]["SUBMITTED"] == 1
    assert body["status_counts"]["REPLIED"] == 1
    assert body["status_counts"]["INTERVIEWED"] == 1
    assert body["mean_fit_score"] == pytest.approx((70 + 85 + 82) / 3)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && uv run pytest tests/test_api_dashboard.py -v
```

Expected: FAIL (404).

- [ ] **Step 3: Implement endpoint**

Create `backend/src/apply/api/routes_dashboard.py`:

```python
from collections import Counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apply.db.models import Application as ApplicationRow
from apply.db.session import get_session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStatsResponse(BaseModel):
    total_applications: int
    total_cost_usd: float
    reply_rate: float  # replied-or-better / total
    interview_rate: float  # interviewed-or-better / total
    status_counts: dict[str, int]
    mean_fit_score: float | None


REPLIED_OR_BETTER = {"REPLIED", "INTERVIEWED", "OFFERED"}
INTERVIEWED_OR_BETTER = {"INTERVIEWED", "OFFERED"}


@router.get("/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    session: AsyncSession = Depends(get_session),
) -> DashboardStatsResponse:
    result = await session.execute(select(ApplicationRow))
    rows = result.scalars().all()

    if not rows:
        return DashboardStatsResponse(
            total_applications=0,
            total_cost_usd=0.0,
            reply_rate=0.0,
            interview_rate=0.0,
            status_counts={},
            mean_fit_score=None,
        )

    total_cost = 0.0
    fit_scores: list[int] = []
    status_counter: Counter = Counter()
    for row in rows:
        cost = (row.cost_breakdown_json or {}).get("per_agent_usd", {})
        if cost:
            total_cost += float(sum(cost.values()))
        fit = (row.fit_analysis_json or {}).get("overall_score")
        if fit is not None:
            fit_scores.append(int(fit))
        status_counter[str(row.status)] += 1

    total = len(rows)
    replied = sum(status_counter[s] for s in REPLIED_OR_BETTER)
    interviewed = sum(status_counter[s] for s in INTERVIEWED_OR_BETTER)
    mean_fit = sum(fit_scores) / len(fit_scores) if fit_scores else None

    return DashboardStatsResponse(
        total_applications=total,
        total_cost_usd=total_cost,
        reply_rate=replied / total,
        interview_rate=interviewed / total,
        status_counts=dict(status_counter),
        mean_fit_score=mean_fit,
    )
```

- [ ] **Step 4: Mount the router**

Modify `backend/src/apply/api/main.py`. Add import:

```python
from apply.api.routes_dashboard import router as dashboard_router
```

Add after the existing `app.include_router(runs_router)` line:

```python
    app.include_router(dashboard_router)
```

- [ ] **Step 5: Run tests**

```bash
cd backend && uv run pytest tests/test_api_dashboard.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/src/apply/api/routes_dashboard.py backend/src/apply/api/main.py backend/tests/test_api_dashboard.py
git commit -m "feat(api): GET /dashboard/stats with aggregated metrics"
```

---

## Task 4: Frontend types + API client extensions

**Files:**
- Modify: `src/lib/types.ts`
- Modify: `src/lib/api.ts`

- [ ] **Step 1: Extend types**

Append to `src/lib/types.ts`:

```typescript
export type ApplicationSummary = {
  id: string;
  company_name: string;
  role_title: string;
  status: string;
  fit_score: number | null;
  cost_usd: number;
  created_at: string;
  url: string | null;
};

export type ListApplicationsResponse = {
  items: ApplicationSummary[];
  total: number;
};

export type DashboardStats = {
  total_applications: number;
  total_cost_usd: number;
  reply_rate: number;
  interview_rate: number;
  status_counts: Record<string, number>;
  mean_fit_score: number | null;
};

export type OutcomeStatus =
  | "SUBMITTED" | "REPLIED" | "INTERVIEWED" | "REJECTED" | "GHOSTED" | "OFFERED";

export type OutcomeUpdate = {
  status: OutcomeStatus;
  notes?: string;
  next_step?: string;
};

export type OutcomeUpdateResponse = {
  application_id: string;
  outcome_id: string;
  status: string;
  notes: string | null;
  next_step: string | null;
};
```

- [ ] **Step 2: Extend API client**

Append to `src/lib/api.ts`:

```typescript
import type {
  ApplicationSummary,
  DashboardStats,
  ListApplicationsResponse,
  OutcomeUpdate,
  OutcomeUpdateResponse,
} from "#/lib/types";

export async function listApplications(): Promise<ListApplicationsResponse> {
  return apiFetch("/applications");
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiFetch("/dashboard/stats");
}

export async function updateOutcome(
  applicationId: string,
  body: OutcomeUpdate,
): Promise<OutcomeUpdateResponse> {
  return apiFetch(`/applications/${applicationId}/outcome`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}
```

- [ ] **Step 3: Verify build**

```bash
cd /Users/sanyamupadhyay/Documents/gusain/clarity && pnpm build 2>&1 | tail -5
```

Expected: clean build.

- [ ] **Step 4: Commit**

```bash
git add src/lib/types.ts src/lib/api.ts
git commit -m "feat(frontend): types + API client for list/stats/outcome"
```

---

## Task 5: Applications list page with real data

**Files:**
- Modify: `src/routes/applications.index.tsx`

- [ ] **Step 1: Replace placeholder with real data-fetching page**

Replace `src/routes/applications.index.tsx`:

```tsx
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
              <th className="py-2"></th>
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
                <td className="py-2 text-right">
                  <Link
                    to="/applications/$id"
                    params={{ id: app.id }}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

Note: the `id` URL param for `/applications/$id` was previously the **run id** (from the POST response). We keep that routing — clicking View navigates to the application ID, which the detail page will accept as either.

Actually, looking at the existing route — it uses `run_id`. Let me keep that consistent: the Link above passes `app.id` which is the application ID, but the existing detail page (`applications.$id.tsx`) expects a **run_id**. Either:

Option A (safer): change the Link to navigate using a different URL or fetch the run for this app
Option B (simpler): add a helper endpoint to map application_id → latest run_id

For V1, implement Option B as a quick lookup in the detail page when the URL param looks like an application ID. OR simpler: just link to a new app-detail route.

**Pragmatic choice for this task:** drop the "View" link for now. The applications list shows data; clicking into an application to see the full brief is Phase 5a Task 6. For now just omit the "View" column.

Revised table: remove the last `<td>` and the `<th></th>`. Applications list is read-only for V1.

- [ ] **Step 2: Build + visual check**

```bash
pnpm build 2>&1 | tail -3
```

Expected: clean build.

- [ ] **Step 3: Commit**

```bash
git add src/routes/applications.index.tsx
git commit -m "feat(frontend): applications list page backed by real API"
```

---

## Task 6: Outcome-marking UI on application detail page

**Files:**
- Create: `src/components/OutcomeMarker.tsx`
- Modify: `src/routes/applications.$id.tsx`

- [ ] **Step 1: OutcomeMarker component**

Create `src/components/OutcomeMarker.tsx`:

```tsx
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
```

- [ ] **Step 2: Integrate into application detail page**

Modify `src/routes/applications.$id.tsx`. Add import:

```tsx
import { OutcomeMarker } from "#/components/OutcomeMarker";
```

In the `COMPLETED` state block, below the `submission_confirmation` display, add:

```tsx
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
```

(The `refresh()` call is already defined in the existing component.)

- [ ] **Step 3: Build**

```bash
pnpm build 2>&1 | tail -3
```

Expected: clean build.

- [ ] **Step 4: Commit**

```bash
git add src/components/OutcomeMarker.tsx src/routes/applications.$id.tsx
git commit -m "feat(frontend): outcome-marking UI on application detail page"
```

---

## Task 7: Dashboard page

**Files:**
- Create: `src/components/StatCard.tsx`
- Create: `src/routes/dashboard.tsx`
- Modify: `src/components/Header.tsx`

- [ ] **Step 1: StatCard component**

Create `src/components/StatCard.tsx`:

```tsx
type Props = {
  label: string;
  value: string;
  sub?: string;
};

export function StatCard({ label, value, sub }: Props) {
  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}
```

- [ ] **Step 2: Dashboard route**

Create `src/routes/dashboard.tsx`:

```tsx
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
```

- [ ] **Step 3: Add Dashboard nav link**

In `src/components/Header.tsx`, find the existing nav (which has the Applications link from Phase 1). Add a Dashboard link alongside it — read the file first, then add minimally.

Likely addition (preserving existing structure):

```tsx
<Link to="/dashboard" className="text-sm hover:underline">
  Dashboard
</Link>
```

- [ ] **Step 4: Build + verify routes register**

```bash
pnpm build 2>&1 | tail -5
```

Expected: clean build with new `/dashboard` route.

- [ ] **Step 5: Commit**

```bash
git add src/components/StatCard.tsx src/routes/dashboard.tsx src/components/Header.tsx src/routeTree.gen.ts
git commit -m "feat(frontend): dashboard page with aggregated stats + nav link"
```

---

## Task 8: Final verification + docs + tag

- [ ] **Step 1: Full suite + ruff**

```bash
cd backend && uv run pytest --tb=short
cd backend && uv run ruff check src/ tests/ eval/
```

Expected: all pass. Ruff clean (no per-file-ignore changes should be needed — the new code follows existing patterns).

- [ ] **Step 2: Walking skeleton still green**

```bash
cd backend && APPLY_USE_REAL_AGENTS=false uv run pytest tests/test_e2e_skeleton.py -v
```

Expected: 1 passed.

- [ ] **Step 3: Frontend build clean**

```bash
pnpm build 2>&1 | tail -3
```

Expected: clean build.

- [ ] **Step 4: LEARNINGS entry**

Append to `LEARNINGS.md`:

```markdown

## 2026-04-24 — Dashboard is where the agent work becomes visible
Tags: product-decisions, architecture

Phase 5a adds the three things that turn the agent stack into a usable
product: an applications list page, outcome marking (so memory-mcp gets
real data over time), and a dashboard showing reply rate / cost / fit
distribution. All backed by the existing Postgres + outcomes table from
Phase 3b.

No chart library added. A dashboard that shows <5 metrics doesn't need
recharts or chart.js — CSS bars + text are more than enough and keep
the frontend bundle tight.

Outcome marking is intentionally user-driven (dropdown + free-text
notes). Inbox auto-detection is tempting but requires OAuth + inbox
permissions, and it moves the app from "runs on your laptop with your
keys" to "needs a third-party auth flow" — too much scope for V1 and
slower to ship for the audience that will mostly just eyeball their
own applications.

**Takeaway:** dashboards compound. The first entry is worthless; the
100th is the money shot. Ship the write path cheaply and let the data
accumulate rather than over-engineering the read path before there's
anything to show.

---
```

- [ ] **Step 5: README update**

Replace the existing Status callout in `README.md`:

```markdown
> **Status:** V1 functionally complete. All 7 agents real, two custom
> FastMCP servers, eval harness with cross-model LLM-as-judge,
> dashboard + outcome marking. Ready for live use against YC WaaS.
> Optional: Phase 4b (Greenhouse/Lever ATS support), Phase 5b
> (deployment).
```

- [ ] **Step 6: Tag + commit docs**

```bash
git tag v0.5.0-dashboard
git add LEARNINGS.md README.md
git commit -m "docs: Phase 5a LEARNINGS entry + README V1-complete status"
```

---

## Self-review checklist

- [ ] All 3 new API endpoints have tests (list + outcome + dashboard stats)
- [ ] Walking skeleton E2E still passes with stubs
- [ ] No new backend dependencies
- [ ] No new frontend dependencies
- [ ] Outcome marker updates both the Application row (display status) AND creates an Outcome row (for memory-mcp)
- [ ] Dashboard returns sane defaults (0.0, empty dict) when no applications exist
- [ ] Frontend handles empty states (no apps, loading, error)
- [ ] No `Co-Authored-By:` trailer on any commit

---

## Out of scope (Phase 5b / future)

- Deployment (Dockerfile for backend, Fly.io/Railway setup, Vercel frontend) — Phase 5b
- Blog post + Loom demo — personal artifacts, not engineering
- Auth / multi-user support — Phase 6+
- Inbox auto-detection of outcomes — Phase 6+
- Chart library for time-series graphs (applications/week, cost trend)
- Per-application cost drill-down page
- Export to CSV / JSON
