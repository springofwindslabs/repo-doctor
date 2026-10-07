"""Build free + PRO distribution zips.

free zip : everything except repo_doctor/pro.py and PRO_LICENSE.txt  (GitHub)
pro zip  : everything including pro.py + PRO_LICENSE.txt             (Gumroad)
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
INCLUDE = [
    "README.md", "LICENSE", "pyproject.toml", ".gitignore",
    "repo_doctor/__init__.py", "repo_doctor/__main__.py",
    "repo_doctor/cli.py", "repo_doctor/checks.py", "repo_doctor/report.py",
    "tests/test_repo_doctor.py",
]
PRO_ONLY = ["repo_doctor/pro.py", "PRO_LICENSE.txt"]


def build(name: str, extra: list[str]) -> Path:
    DIST.mkdir(exist_ok=True)
    out = DIST / name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in INCLUDE + extra:
            f = ROOT / rel
            z.writestr("repo-doctor/" + rel.replace("\\", "/"),
                       f.read_bytes())
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{out.name}  {out.stat().st_size:,} bytes  sha256={sha[:16]}…")
    (DIST / (name + ".sha256")).write_text(sha + "  " + name + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    build("repo-doctor-free-1.0.0.zip", [])
    build("repo-doctor-pro-1.0.0.zip", PRO_ONLY)
