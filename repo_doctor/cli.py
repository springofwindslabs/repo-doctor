"""repo-doctor CLI entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from repo_doctor import __version__
from repo_doctor.checks import diagnose
from repo_doctor.report import render_console, render_json, render_markdown

try:
    from repo_doctor import pro  # noqa: F401  (paid distribution only)
    HAS_PRO = True
except ImportError:
    HAS_PRO = False

PRO_URL = "https://springofwindslabs.gumroad.com/l/repodoctor"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="repo-doctor",
        description="One-command repository health diagnosis (docs / hygiene / "
                    "secrets / tests / deps / git). Zero dependencies.")
    p.add_argument("path", nargs="?", default=".", help="repository path (default: .)")
    p.add_argument("--json", action="store_true", help="output JSON")
    p.add_argument("--md", metavar="FILE", help="write a Markdown report")
    p.add_argument("--version", action="version", version=f"repo-doctor {__version__}"
                                                          + (" PRO" if HAS_PRO else " (free)"))
    g = p.add_argument_group("PRO features" + ("" if HAS_PRO else f"  [get PRO → {PRO_URL}]"))
    g.add_argument("--html", metavar="FILE", help="write a self-contained HTML dashboard")
    g.add_argument("--badge", metavar="FILE", help="write an SVG health badge")
    g.add_argument("--fail-under", type=float, metavar="N",
                   help="exit 1 if score < N (CI quality gate)")
    g.add_argument("--history", action="store_true",
                   help="append score to .repo_doctor_history.json (trend in HTML report)")
    a = p.parse_args(argv)

    if not HAS_PRO and (a.html or a.badge or a.fail_under is not None or a.history):
        print(f"repo-doctor: --html / --badge / --fail-under / --history are PRO "
              f"features.\nGet the PRO edition (one-time purchase): {PRO_URL}",
              file=sys.stderr)
        return 2

    d = diagnose(a.path)

    hist = None
    if HAS_PRO and a.history:
        hist = pro.append_history(d, Path(d.root))
    if a.md:
        Path(a.md).write_text(render_markdown(d), encoding="utf-8")
        print(f"markdown report → {a.md}", file=sys.stderr)
    if HAS_PRO and a.html:
        Path(a.html).write_text(pro.render_html(d, hist), encoding="utf-8")
        print(f"HTML dashboard → {a.html}", file=sys.stderr)
    if HAS_PRO and a.badge:
        Path(a.badge).write_text(pro.render_badge(d), encoding="utf-8")
        print(f"SVG badge → {a.badge}", file=sys.stderr)

    if a.json:
        print(render_json(d))
    else:
        print(render_console(d))
        if not HAS_PRO:
            print(f"  ── free edition ── PRO adds: HTML dashboard / SVG badge / "
                  f"CI gate / 10+ extra secret rules / score history\n"
                  f"  → {PRO_URL}\n")

    if HAS_PRO and a.fail_under is not None and d.score < a.fail_under:
        print(f"repo-doctor: FAIL — score {d.score} < gate {a.fail_under}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
