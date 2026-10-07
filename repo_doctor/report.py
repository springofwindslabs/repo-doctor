"""Console / JSON / Markdown report rendering (free edition)."""
from __future__ import annotations

import json
import sys

from repo_doctor.checks import Diagnosis

SEV_ICON = {"critical": "🟥", "warning": "🟧", "info": "🟦", "ok": "✅"}
SEV_ORDER = {"critical": 0, "warning": 1, "info": 2, "ok": 3}


def _c(code: str, s: str) -> str:
    if not sys.stdout.isatty():
        return s
    return f"\033[{code}m{s}\033[0m"


def render_console(d: Diagnosis) -> str:
    bar = "█" * int(d.score / 5) + "░" * (20 - int(d.score / 5))
    col = "32" if d.score >= 75 else "33" if d.score >= 50 else "31"
    out = [
        "",
        _c("1", f"  repo-doctor — diagnosis of {d.root}"),
        f"  {d.ts}",
        "",
        _c(col, f"  HEALTH  {bar}  {d.score}/100   GRADE {d.grade}"),
        "",
    ]
    for r in d.results:
        out.append(_c("1", f"  [{r.label}]  {r.score:.0f}/100"))
        for f in sorted(r.findings, key=lambda x: SEV_ORDER.get(x.severity, 9)):
            loc = f"  ({f.path})" if f.path else ""
            out.append(f"    {SEV_ICON.get(f.severity, '•')} {f.message}{loc}")
            if f.fix:
                out.append(_c("90", f"       ↳ fix: {f.fix}"))
        out.append("")
    crit = sum(1 for f in d.findings if f.severity == "critical")
    warn = sum(1 for f in d.findings if f.severity == "warning")
    out.append(f"  {crit} critical / {warn} warning issue(s).")
    out.append("")
    return "\n".join(out)


def to_dict(d: Diagnosis) -> dict:
    return {
        "tool": "repo-doctor", "root": d.root, "ts": d.ts,
        "score": d.score, "grade": d.grade,
        "checks": [
            {"key": r.key, "label": r.label, "score": r.score, "weight": r.weight,
             "findings": [{"severity": f.severity, "message": f.message,
                           "path": f.path, "fix": f.fix} for f in r.findings]}
            for r in d.results],
    }


def render_json(d: Diagnosis) -> str:
    return json.dumps(to_dict(d), ensure_ascii=False, indent=2)


def render_markdown(d: Diagnosis) -> str:
    out = [f"# repo-doctor report — `{d.root}`", "",
           f"**Score: {d.score}/100 — Grade {d.grade}**  ({d.ts})", "",
           "| Check | Score | Findings |", "|---|---|---|"]
    for r in d.results:
        n = sum(1 for f in r.findings if f.severity in ("critical", "warning"))
        out.append(f"| {r.label} | {r.score:.0f}/100 | {n} issue(s) |")
    out.append("")
    for r in d.results:
        out.append(f"## {r.label} — {r.score:.0f}/100")
        for f in sorted(r.findings, key=lambda x: SEV_ORDER.get(x.severity, 9)):
            loc = f" (`{f.path}`)" if f.path else ""
            out.append(f"- {SEV_ICON.get(f.severity, '-')} **{f.severity}** — {f.message}{loc}")
            if f.fix:
                out.append(f"  - fix: {f.fix}")
        out.append("")
    return "\n".join(out)
