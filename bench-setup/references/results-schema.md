# Run record schema (`results/runs.jsonl`)

One JSON object per line, UTF-8. The file is append-only.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `run_id` | string | yes | Unique, e.g. `<method>-<dataset>-s<seed>-<yyyymmddHHMMSS>` |
| `timestamp` | string | yes | ISO-8601 time the run finished |
| `role` | string | yes | `repro_baseline`, `baseline`, `extension`, `ablation`, `smoke` |
| `method` | string | yes | Stable method name; matches `reported_targets.json` for reproduction |
| `dataset` | string | yes | Dataset name including version |
| `split` | string | yes | `test`, `val`, or workload name |
| `seed` | integer | yes | Random seed or repetition index |
| `config_path` | string | yes | Path relative to the workspace |
| `config_hash` | string | yes | Hash of the resolved config without the seed |
| `git_commit` | string | yes | Harness commit |
| `git_dirty` | boolean | yes | Uncommitted changes present |
| `budget` | object | yes | e.g. `{"epochs": 100, "trials": 20, "gpu": "A100-80G", "threads": 16}` |
| `status` | string | yes | `ok` or `failed` |
| `metrics` | object | yes | `{metric_name: number}`; `{}` for failed runs |
| `env` | object | no | Python/compiler, key package versions, CUDA, OS, hostname |
| `wall_time_s` | number | no | Total run time |
| `error` | string | when failed | Short failure reason |
| `supersedes` | list[string] | no | Earlier `run_id`s this run invalidates (e.g. a bug fix) |
| `notes` | string | no | Free text |

Metric names are consistent across methods, e.g. `recall@10`, `latency_p99_ms`, `throughput_qps`. Put units in the name.

## Superseding

Never delete records. If runs were wrong (a bug, a wrong split), append corrected runs with `supersedes` listing the bad `run_id`s. Checkers and plotting ignore superseded runs.

## Example

```json
{"run_id": "hnsw-sift1m-s0-20260917101500", "timestamp": "2026-09-17T10:15:00Z", "role": "repro_baseline", "method": "hnsw", "dataset": "sift1m", "split": "test", "seed": 0, "config_path": "experiments/configs/repro/hnsw-sift1m.yaml", "config_hash": "3f9a1c", "git_commit": "a1b2c3d", "git_dirty": false, "budget": {"threads": 16, "cpu": "Xeon 8380"}, "status": "ok", "metrics": {"recall@10": 0.951, "throughput_qps": 12040}, "wall_time_s": 812.4}
```
