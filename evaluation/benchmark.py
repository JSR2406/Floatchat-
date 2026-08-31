# Phase 8 - Part 32 (benchmark classes) + Phase 9 - Part 32/33 extension.
#
# `python -m evaluation.benchmark` runs deterministic scenarios/worlds a
# configurable number of times (default 3 for repeatability) through the real
# orchestration pipeline and reports avg / P50 / P95 latency per scenario, per
# phase (intent/plan/execute/synthesize), plus failure rate, tool calls and
# agent count (Part 33 cost / tool efficiency).
#
# Phase 8 carried 7 classes; Phase 9 Part 32 extends to 10:
#   1. PFZ query
#   2. marine condition query
#   3. safety query
#   4. restriction query
#   5. route query
#   6. knowledge query
#   7. scenario query
#   8. multilingual query
#   9. multi-turn query
#   10. degraded-source query
import os
import sys
from statistics import median

# Malayalam briefing query (script U+0D00..U+0D7F) -> language ml-IN, with an
# English place token so the location extractor resolves a region.
_ML_QUERY = "കൊച്ചിക്കടുത്തുള്ള കടൽ അവസ്ഥ എങ്ങനെയാണ് Kochi?"


def _bootstrap() -> None:
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for candidate in (repo, os.path.join(repo, "apps", "api")):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)


def _pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    n = len(sorted_vals)
    idx = min(n - 1, int(round((p / 100.0) * (n - 1))))
    return sorted_vals[idx]


def _quantiles(values) -> dict:
    if not values:
        return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "n": 0}
    s = sorted(values)
    return {
        "avg": round(sum(values) / len(values), 1),
        "p50": round(_pct(s, 50), 1),
        "p95": round(_pct(s, 95), 1),
        "n": len(values),
    }


_BENCH_SCENARIOS = [
    # (id, message, world_builder, cls, pipeline, second_turn)
    ("pfz-query", "Where is the best fishing zone near Kochi?", "pfz", "pfz", "orchestrator", None),
    ("marine-query", "How is the sea near Visakhapatnam?", "healthy", "marine", "orchestrator", None),
    ("safety-query", "Is it safe to fish near Goa?", "restricted", "safety", "orchestrator", None),
    ("restriction-query", "Are there active restrictions near Mumbai?", "dynamic_restricted", "restriction", "orchestrator", None),
    ("route-query", "Plan the safest route from Goa to Mumbai", "route_blocked", "route", "orchestrator", None),
    ("knowledge-query", "What rules apply to fishing in the Arabian Sea?", "healthy", "knowledge", "orchestrator", None),
    ("scenario-query", "What if I move 10 km south near Kochi?", "healthy", "scenario", "orchestrator", None),
    ("multilingual-query", _ML_QUERY, "healthy", "multilingual", "orchestrator", None),
    ("multi-turn-query", "Are there restrictions near Kochi?", "dynamic_restricted", "multiturn",
     "twoturn", "What about 20 km south?"),
    ("degraded-source-query", "Is it safe to fish near Goa?", "ocean_error", "degraded", "orchestrator", None),
]


def _resolver():
    import evaluation.fixtures as fixtures
    return {
        "healthy": fixtures.healthy_world,
        "restricted": fixtures.restricted_world,
        "route_blocked": fixtures.route_blocked_world,
        "dynamic_restricted": fixtures.dynamic_restricted_world,
        "pfz": fixtures.pfz_world,
        "ocean_error": fixtures.ocean_error_world,
    }


def run_benchmark(repeats: int = 3) -> dict:
    from evaluation.runners import run_scenario_parts, allowed_tool_set

    resolver = _resolver()
    rows = []
    for idx, (bench_id, message, world_key, cls, pipeline, second) \
            in enumerate(_BENCH_SCENARIOS, start=1):
        world = resolver[world_key]()
        latencies = []
        phase_latencies = {"intent_ms": [], "plan_ms": [], "execute_ms": [],
                           "synthesize_ms": []}
        tool_calls = []
        failures = 0
        status = None
        language = None
        # Part 33: agent count from the deterministic plan (per message).
        try:
            _agents, _ = allowed_tool_set(message)
            agent_count = len(_agents)
        except Exception:
            agent_count = None
        for _ in range(repeats):
            case = run_scenario_parts(f"bench-{bench_id}", message, world,
                                      title=bench_id, pipeline=pipeline,
                                      second_turn=second)
            payload = case.response or {}
            ms = payload.get("duration_ms")
            if ms is not None:
                latencies.append(float(ms))
            timings = (payload.get("notes") or {}).get("phase_timings") or {}
            for key in phase_latencies:
                val = timings.get(key)
                if isinstance(val, (int, float)):
                    phase_latencies[key].append(float(val))
            tc = payload.get("tool_calls")
            if isinstance(tc, (int, float)):
                tool_calls.append(float(tc))
            if case.error or (payload or {}).get("status") in ("error", "invalid"):
                failures += 1
            status = (payload or {}).get("status")
            language = (payload or {}).get("language")
        rows.append({
            "id": bench_id,
            "cls": cls,
            "world": world_key,
            "pipeline": pipeline,
            "status": status,
            "language": language,
            "failures": failures,
            "failure_rate": round(failures / repeats, 2),
            "error": case.error,
            "latency_ms": _quantiles(latencies),
            "phase_ms": {k: _quantiles(v) for k, v in phase_latencies.items()},
            "tool_calls_avg": round(sum(tool_calls) / len(tool_calls), 1) if tool_calls else None,
            "agent_count": agent_count,
        })
    return {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "repeats": repeats,
        "bench_classes": len(rows),
        "rows": rows,
    }


def _markdown(report: dict) -> str:
    lines = [
        "# Execution Benchmark (Phase 9 - Part 32)",
        "",
        f"generated: `{report['generated_at']}`  repeats per scenario: "
        f"`{report['repeats']}`  bench classes: `{report['bench_classes']}`",
        "",
        "latency in milliseconds (lower is better).  P50/P95 are percentiles; "
        "failure rate covers error/invalid statuses.",
        "",
        "| # | class | id | status | lang | avg | P50 | P95 | fail% | tools | agents | n |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, row in enumerate(report["rows"], start=1):
        l = row["latency_ms"]
        lines.append(
            f"| {i} | {row['cls']} | {row['id']} | {row['status'] or '-'} "
            f"| {row['language'] or '-'} | {l['avg']} | {l['p50']} | {l['p95']} "
            f"| {row['failure_rate']} | {row['tool_calls_avg'] or '-'} "
            f"| {row['agent_count'] or '-'} | {l['n']} |")
    lines.append("")
    lines.append("Phase breakdown (avg / P50 / P95):")
    lines.append("")
    lines.append("| bench | intent | plan | execute | synthesize |")
    lines.append("|---|---|---|---|---|")
    for row in report["rows"]:
        def fmt(key):
            q = row["phase_ms"].get(key, {})
            return f"{q.get('avg', 0.0)}/{q.get('p50', 0.0)}/{q.get('p95', 0.0)}"
        lines.append(f"| {row['id']} | {fmt('intent_ms')} | {fmt('plan_ms')} "
                     f"| {fmt('execute_ms')} | {fmt('synthesize_ms')} |")
    return "\n".join(lines)


def main() -> int:
    from datetime import datetime
    import json
    from pathlib import Path

    repeats = int(os.environ.get("BENCH_REPEATS", "3"))
    report = run_benchmark(repeats=repeats)
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    md_path = reports_dir / f"bench-{stamp}.md"
    md_path.write_text(_markdown(report), encoding="utf-8")
    (reports_dir / "bench-latest.md").write_text(
        _markdown(report), encoding="utf-8")
    print(_markdown(report))
    print(f"benchmark written: {md_path}")
    return 0


if __name__ == "__main__":
    _bootstrap()
    raise SystemExit(main())
