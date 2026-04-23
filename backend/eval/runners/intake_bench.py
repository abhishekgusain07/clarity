"""Intake bench runner.

Scores a `JobListing` against the `expected_fields` block of a goldenset
entry. Fields containing the sentinel string "FILL_AT_RUN_TIME" are
skipped (neither counted as hit nor miss) — the live executor is
expected to replace those with real expected values when they substitute
a fresh URL.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from apply.schemas.job import JobListing

FILL_SENTINEL = "FILL_AT_RUN_TIME"


@dataclass
class IntakeBenchResult:
    jd_id: str
    passed: bool
    field_recall: float  # fraction of checked fields that matched
    field_hits: int
    field_checked: int
    failed_fields: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _check(name: str, expected: Any, actual: Any, result: IntakeBenchResult) -> None:
    if isinstance(expected, str) and expected == FILL_SENTINEL:
        return  # skip
    result.field_checked += 1
    if expected == actual:
        result.field_hits += 1
    else:
        result.failed_fields.append(name)


def score_intake_result(expected: dict[str, Any], listing: JobListing) -> IntakeBenchResult:
    result = IntakeBenchResult(jd_id="", passed=False, field_recall=0.0, field_hits=0, field_checked=0)

    _check("source", expected.get("source"), listing.source.value, result)
    _check("company_name", expected.get("company_name"), listing.company_name, result)
    _check("role_title", expected.get("role_title"), listing.role_title, result)
    _check("location", expected.get("location"), listing.location, result)
    _check("remote_type", expected.get("remote_type"), listing.remote_type.value, result)

    # Counts are minimum thresholds, not exact matches
    min_reqs = expected.get("min_requirements_count")
    if isinstance(min_reqs, int):
        result.field_checked += 1
        if len(listing.requirements) >= min_reqs:
            result.field_hits += 1
        else:
            result.failed_fields.append("requirements")

    min_nths = expected.get("min_nice_to_haves_count")
    if isinstance(min_nths, int):
        result.field_checked += 1
        if len(listing.nice_to_haves) >= min_nths:
            result.field_hits += 1
        else:
            result.failed_fields.append("nice_to_haves")

    if result.field_checked == 0:
        result.field_recall = 1.0  # nothing to check means vacuous pass
    else:
        result.field_recall = result.field_hits / result.field_checked

    result.passed = result.field_recall >= 0.95
    return result


async def run_intake_bench(
    goldenset_path: Path,
    intake_fn,
    jd_fetch_fn,
) -> list[IntakeBenchResult]:
    """Run the intake bench.

    intake_fn: async callable(url, jd_text, raw_html_path) -> JobListing
    jd_fetch_fn: async callable(url) -> str (returns JD markdown/text)
    """
    data = json.loads(goldenset_path.read_text())
    results: list[IntakeBenchResult] = []

    for item in data["items"]:
        jd_text = await jd_fetch_fn(item["url"])
        if not jd_text:
            r = IntakeBenchResult(
                jd_id=item["id"],
                passed=False,
                field_recall=0.0,
                field_hits=0,
                field_checked=0,
                notes=["jd_fetch returned empty"],
            )
            results.append(r)
            continue

        listing = await intake_fn(
            url=item["url"],
            jd_text=jd_text,
            raw_html_path=f"/tmp/apply/bench-{item['id']}.html",
        )
        r = score_intake_result(expected=item["expected_fields"], listing=listing)
        r.jd_id = item["id"]
        results.append(r)

    return results
