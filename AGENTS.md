# AGENTS.md — instructions for AI coding agents

## What this is
`repo-doctor` — zero-dependency Python CLI that scores a repository's
**AI readiness** and health across 7 axes. Free edition (MIT) + PRO edition
(commercial, `repo_doctor/pro.py`, sold separately on Gumroad).

## Structure
- `repo_doctor/checks.py` — all 7 checks + `diagnose()`. Each check returns a `CheckResult` (0-100 sub-score + weighted).
- `repo_doctor/report.py` — console / JSON / Markdown rendering (free).
- `repo_doctor/pro.py` — HTML dashboard, SVG badge, history, extra secret rules (PRO; **not in the public repo**).
- `repo_doctor/cli.py` — argparse entry point; PRO flags are rejected when pro.py is absent.
- `tests/test_repo_doctor.py` — stdlib unittest smoke tests.

## Build / test / lint
```bash
python -m unittest discover -s tests -v   # run tests (no deps needed)
python -m repo_doctor .                   # self-diagnosis
python scripts/build_dist.py              # build free+pro zips into dist/
```

## Constraints — do NOT
- Do not add third-party dependencies. Zero-dependency is a product promise.
- Do not commit or reference `repo_doctor/pro.py` / `PRO_LICENSE.txt` in the public repo (they are .gitignored and sold on Gumroad).
- Do not make network calls from checks — fully-offline is a product promise.
- Do not change the Gumroad permalink `repodoctor` referenced in cli.py/README.
- Keep Python 3.9 compatibility (no `match`, no `tomllib`).
