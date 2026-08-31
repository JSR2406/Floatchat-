# Phase 8 - Part 32 (benchmark class) + execution benchmarking.
#
# `python -m evaluation.benchmark` runs deterministic scenarios/worlds a
# configurable number of times (default 3 for repeatability) through the real
# orchestration pipeline and reports avg / P50 / P95 latency per scenario and
# per phase (intent/plan/execute/synthesize) when phase timings are available.
# 7 benchmark classes (Part 32 verification):
#   1. intent routing
#   2. planner
#   3. verifier
#   4. constraint evaluation
#   5. terminal step orchestration
#   6. map payload builder
#   7. chart payload builder
import os
import sys
from statistics import median


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
    # (id, message, world_builder, part)
    ("intent-routing", "Is it safe to fish near Kochi?", "healthy", "1"),
    ("planner", "Plan the safest route from Goa to Mumbai", "route_blocked", "2"),
    ("verifier", "Is it safe near Goa?", "conflict", "3"),
    ("constraint-eval", "Are there active restrictions near Mumbai?", "dynamic_restricted", "4"),
    ("terminal-orchestration", "Give me a marine briefing near Visakhapatnam", "healthy", "5"),
    ("map-payload", "Where is the best fishing zone near Kochi?", "pfz", "6"),
    ("chart-payload", "Show fishing productivity near Chennai", "productivity", "7"),
]


def _resolver():
    import evaluation.fixtures as fixtures
    return {
        "healthy": fixtures.healthy_world,
        "route_blocked": fixtures.route_blocked_world,
        "conflict": fixtures.conflict_world,
        "dynamic_restricted": fixtures.dynamic_restricted_world,
        "pfz": fixtures.pfz_world,
        "productivity": fixtures.productivity_world,
    }


def run_benchmark(repeats: int = 3) -> dict:
    from evaluation.runners import run_scenario_parts

    resolver = _resolver()
    rows = []
    for bench_id, message, world_key, part in _BENCH_SCENARIOS:
        world = resolver[world_key]()
        latencies = []
        phase_latencies = {"intent_ms": [], "plan_ms": [], "execute_ms": [],
                           "synthesize_ms": []}
        for _ in range(repeats):
            case = run_scenario_parts(f"bench-{bench_id}", message, world,
                                      title=bench_id)
            payload = case.response or {}
            ms = payload.get("duration_ms")
            if ms is not None:
                latencies.append(float(ms))
            timings = (payload.get("notes") or {}).get("phase_timings") or {}
            for key in phase_latencies:
                val = timings.get(key)
                if isinstance(val, (int, float)):
                    phase_latencies[key].append(float(val))
        rows.append({
            "id": bench_id,
            "part": part,
            "world": world_key,
            "status": (case.response or {}).get("status"),
            "error": case.error,
            "latency_ms": _quantiles(latencies),
            "phase_ms": {k: _quantiles(v) for k, v in phase_latencies.items()},
        })
    return {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "repeats": repeats,
        "bench_classes": len(rows),
        "rows": rows,
    }


def _markdown(report: dict) -> str:
    lines = [
        "# Execution Benchmark (Phase 8)",
        "",
        f"generated: `{report['generated_at']}`  repeats per scenario: "
        f"`{report['repeats']}`  bench classes: `{report['bench_classes']}`",
        "",
        "latency in milliseconds (lower is better).",
        "",
        "| # | bench | rate-limit class | status | avg | P50 | P95 | n |",
        "|---|---|---|---|---|---|---|---|",
    ]
    CLASS_LABEL = {"1": "intent", "2": "planner", "3": "verifier",
                   "4": "constraint", "5": "terminal", "6": "map builder",
                   "7": "chart builder"}
    for row in report["rows"]:
        l = row["latency_ms"]
        lines.append(
            f"| {row['part']} | {row['id']} | {CLASS_LABEL.get(row['part'], '?')} "
            f"| {row['status'] or '-'} | {l['avg']} | {l['p50']} | {l['p95']} "
            f"| {l['n']} |")
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