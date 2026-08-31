# Execution Benchmark (Phase 8)

generated: `2026-08-31T17:35:01.267972`  repeats per scenario: `3`  bench classes: `7`

latency in milliseconds (lower is better).

| # | bench | rate-limit class | status | avg | P50 | P95 | n |
|---|---|---|---|---|---|---|---|
| 1 | intent-routing | intent | success | 67.7 | 16.0 | 187.0 | 3 |
| 2 | planner | planner | success | 0.0 | 0.0 | 0.0 | 3 |
| 3 | verifier | verifier | success | 5.0 | 0.0 | 15.0 | 3 |
| 4 | constraint-eval | constraint | success | 0.0 | 0.0 | 0.0 | 3 |
| 5 | terminal-orchestration | terminal | success | 0.0 | 0.0 | 0.0 | 3 |
| 6 | map-payload | map builder | success | 0.0 | 0.0 | 0.0 | 3 |
| 7 | chart-payload | chart builder | success | 0.0 | 0.0 | 0.0 | 3 |

Phase breakdown (avg / P50 / P95):

| bench | intent | plan | execute | synthesize |
|---|---|---|---|---|
| intent-routing | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 67.7/16.0/187.0 | 5.3/0.0/16.0 |
| planner | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 5.0/0.0/15.0 |
| verifier | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 5.0/0.0/15.0 | 0.0/0.0/0.0 |
| constraint-eval | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 0.0/0.0/0.0 |
| terminal-orchestration | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 0.0/0.0/0.0 |
| map-payload | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 0.0/0.0/0.0 |
| chart-payload | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 0.0/0.0/0.0 | 5.3/0.0/16.0 |