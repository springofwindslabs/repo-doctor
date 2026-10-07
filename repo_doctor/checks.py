"""Core health checks. Each check returns a Finding list and a 0-100 sub-score."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".tox",
             ".mypy_cache", ".pytest_cache", "dist", "build", ".next", "target",
             ".idea", ".vscode", "vendor", "site-packages", ".ruff_cache"}
LARGE_FILE_MB = 5
MAX_SCAN_FILES = 4000
TEXT_EXT = {".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yml", ".yaml", ".toml",
            ".cfg", ".ini", ".sh", ".ps1", ".bat", ".env", ".txt", ".md", ".rb",
            ".go", ".rs", ".java", ".kt", ".c", ".cpp", ".h", ".cs", ".php", ".sql"}

# --- secret patterns: (rule_id, severity, regex, note) -----------------------
SECRET_RULES: list[tuple[str, str, str, str]] = [
    ("aws-access-key", "critical", r"\bAKIA[0-9A-Z]{16}\b", "AWS access key ID"),
    ("private-key-block", "critical", r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----", "Private key material"),
    ("github-token", "critical", r"\bgh[pousr]_[A-Za-z0-9]{30,}\b", "GitHub token"),
    ("slack-token", "critical", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "Slack token"),
    ("generic-assignment", "warning",
     r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
     "Hard-coded credential assignment"),
]
# Pro: extended ruleset is appended by repo_doctor.pro at import time if present.

ALLOWLIST_HINTS = ("example", "sample", "dummy", "placeholder", "changeme",
                   "your_", "xxxx", "<", "{{", "${", "test")


@dataclass
class Finding:
    check: str
    severity: str          # critical / warning / info / ok
    message: str
    path: str = ""
    fix: str = ""


@dataclass
class CheckResult:
    key: str
    label: str
    score: float           # 0-100
    weight: float
    findings: list[Finding] = field(default_factory=list)


@dataclass
class Diagnosis:
    root: str
    ts: str
    score: float
    grade: str
    results: list[CheckResult]

    @property
    def findings(self) -> list[Finding]:
        return [f for r in self.results for f in r.findings]


def _walk(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            out.append(Path(dirpath) / fn)
            if len(out) >= MAX_SCAN_FILES:
                return out
    return out


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _git(root: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), *args],
                           capture_output=True, text=True, timeout=20,
                           encoding="utf-8", errors="replace")
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


# --------------------------------------------------------------------------- #
def check_docs(root: Path, files: list[Path]) -> CheckResult:
    f: list[Finding] = []
    score = 100.0
    readmes = [p for p in files if p.parent == root and p.name.lower().startswith("readme")]
    if not readmes:
        score -= 45
        f.append(Finding("docs", "critical", "README not found",
                         fix="Add a README.md — it is the #1 signal of a maintained repo."))
    else:
        txt = _read(readmes[0])
        if len(txt) < 300:
            score -= 20
            f.append(Finding("docs", "warning", f"README is very short ({len(txt)} chars)",
                             str(readmes[0].name), "Describe what / why / install / usage."))
        low = txt.lower()
        missing = [s for s in ("install", "usage") if s not in low]
        if missing:
            score -= 10 * len(missing)
            f.append(Finding("docs", "warning",
                             "README lacks section(s): " + ", ".join(missing),
                             str(readmes[0].name), "Add Install and Usage sections."))
        else:
            f.append(Finding("docs", "ok", "README covers install & usage"))
    names = {p.name.lower() for p in files if p.parent == root}
    if not any(n.startswith("license") or n.startswith("copying") for n in names):
        score -= 25
        f.append(Finding("docs", "warning", "LICENSE file missing",
                         fix="No license = legally unusable by others. Add one (MIT/Apache-2.0...)."))
    for extra, pts in (("changelog", 5), ("contributing", 5), ("security", 5)):
        if not any(n.startswith(extra) for n in names):
            score -= pts
            f.append(Finding("docs", "info", f"{extra.upper()}.md not found",
                             fix=f"Optional but raises trust: add {extra.upper()}.md."))
    return CheckResult("docs", "Documentation", max(score, 0), 20, f)


def check_hygiene(root: Path, files: list[Path]) -> CheckResult:
    f: list[Finding] = []
    score = 100.0
    if not (root / ".gitignore").exists():
        score -= 25
        f.append(Finding("hygiene", "warning", ".gitignore missing",
                         fix="Generate one at gitignore.io for your stack."))
    junk_pat = re.compile(r"(^|[\\/])(__pycache__|node_modules|\.venv|venv|\.DS_Store|Thumbs\.db)([\\/]|$)|\.pyc$")
    junk = [p for p in files if junk_pat.search(str(p.relative_to(root)))]
    if junk:
        score -= min(30, 6 * len(junk))
        f.append(Finding("hygiene", "warning",
                         f"{len(junk)} junk/artifact file(s) inside the tree",
                         str(junk[0].relative_to(root)),
                         "Remove build artifacts & caches; add them to .gitignore."))
    big = []
    for p in files:
        try:
            if p.stat().st_size > LARGE_FILE_MB * 1024 * 1024:
                big.append(p)
        except OSError:
            continue
    if big:
        score -= min(25, 8 * len(big))
        f.append(Finding("hygiene", "warning",
                         f"{len(big)} file(s) larger than {LARGE_FILE_MB}MB",
                         str(big[0].relative_to(root)),
                         "Large binaries bloat clones — use Git LFS or external storage."))
    if score == 100:
        f.append(Finding("hygiene", "ok", "Tree is clean (no junk, no oversized files)"))
    return CheckResult("hygiene", "Repo hygiene", max(score, 0), 15, f)


def check_secrets(root: Path, files: list[Path]) -> CheckResult:
    f: list[Finding] = []
    score = 100.0
    env_tracked = [p for p in files if p.name == ".env"]
    if env_tracked:
        score -= 30
        f.append(Finding("secrets", "critical", ".env file present in the tree",
                         str(env_tracked[0].relative_to(root)),
                         "Move secrets out, add .env to .gitignore, rotate exposed keys."))
    hits = 0
    for p in files:
        if p.suffix.lower() not in TEXT_EXT and p.name != ".env":
            continue
        txt = _read(p)
        if not txt:
            continue
        for rule_id, sev, pat, note in SECRET_RULES:
            for m in re.finditer(pat, txt):
                frag = m.group(0).lower()
                if any(h in frag for h in ALLOWLIST_HINTS):
                    continue
                hits += 1
                if hits <= 10:
                    line = txt.count("\n", 0, m.start()) + 1
                    f.append(Finding("secrets", sev,
                                     f"{note} [{rule_id}]",
                                     f"{p.relative_to(root)}:{line}",
                                     "Remove from history (git filter-repo) and ROTATE the credential."))
    if hits:
        score -= min(80, 20 * hits)
    if score == 100:
        f.append(Finding("secrets", "ok", "No credential patterns detected"))
    return CheckResult("secrets", "Secrets exposure", max(score, 0), 25, f)


def check_testing_ci(root: Path, files: list[Path]) -> CheckResult:
    f: list[Finding] = []
    score = 100.0
    tests = [p for p in files
             if re.search(r"(^|[\\/])(tests?|spec)([\\/])", str(p.relative_to(root)))
             or re.match(r"test_.*\.py$|.*_test\.(py|go)$|.*\.(test|spec)\.(js|ts|jsx|tsx)$", p.name)]
    if not tests:
        score -= 50
        f.append(Finding("testing", "warning", "No test files detected",
                         fix="Even a smoke test prevents silent breakage."))
    else:
        f.append(Finding("testing", "ok", f"{len(tests)} test file(s) found"))
    ci = [p for p in files if ".github" in p.parts and "workflows" in p.parts] \
        or [p for p in files if p.name in (".gitlab-ci.yml", "azure-pipelines.yml", ".travis.yml", "Jenkinsfile")]
    if not ci:
        score -= 35
        f.append(Finding("testing", "warning", "No CI configuration found",
                         fix="Add a GitHub Actions workflow that runs the tests on push."))
    else:
        f.append(Finding("testing", "ok", "CI configuration present"))
    return CheckResult("testing", "Tests & CI", max(score, 0), 20, f)


def check_deps(root: Path, files: list[Path]) -> CheckResult:
    f: list[Finding] = []
    score = 100.0
    top = {p.name for p in files if p.parent == root}
    seen = False
    if "requirements.txt" in top:
        seen = True
        lines = [ln.strip() for ln in _read(root / "requirements.txt").splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]
        if lines:
            pinned = sum(1 for ln in lines if re.search(r"==|~=|>=.*<", ln))
            ratio = pinned / len(lines)
            if ratio < 0.5:
                score -= 30
                f.append(Finding("deps", "warning",
                                 f"Only {pinned}/{len(lines)} requirements are version-pinned",
                                 "requirements.txt",
                                 "Pin versions (pkg==x.y.z) for reproducible installs."))
            else:
                f.append(Finding("deps", "ok", f"{pinned}/{len(lines)} requirements pinned"))
    if "package.json" in top:
        seen = True
        if not ({"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"} & top):
            score -= 30
            f.append(Finding("deps", "warning", "package.json without a lockfile",
                             "package.json", "Commit the lockfile for reproducible builds."))
        else:
            f.append(Finding("deps", "ok", "JS lockfile present"))
    if {"pyproject.toml", "go.mod", "Cargo.toml", "Gemfile"} & top:
        seen = True
        f.append(Finding("deps", "ok", "Structured dependency manifest present"))
    if not seen:
        f.append(Finding("deps", "info", "No dependency manifest detected",
                         fix="If the project has dependencies, declare them explicitly."))
        score -= 10
    return CheckResult("deps", "Dependencies", max(score, 0), 10, f)


def check_git(root: Path, files: list[Path]) -> CheckResult:
    f: list[Finding] = []
    score = 100.0
    if not (root / ".git").exists():
        f.append(Finding("git", "info", "Not a git repository — history checks skipped"))
        return CheckResult("git", "Git history", 70, 10, f)
    cnt = _git(root, "rev-list", "--count", "HEAD")
    if cnt:
        n = int(cnt)
        if n < 5:
            score -= 15
            f.append(Finding("git", "info", f"Only {n} commit(s)",
                             fix="Small, frequent commits make history auditable."))
        else:
            f.append(Finding("git", "ok", f"{n} commits in history"))
    last = _git(root, "log", "-1", "--format=%cI")
    if last:
        try:
            dt = datetime.fromisoformat(last)
            age = (datetime.now(timezone.utc) - dt).days
            if age > 180:
                score -= 25
                f.append(Finding("git", "warning", f"Last commit was {age} days ago",
                                 fix="Stale repos lose users — commit or archive explicitly."))
            else:
                f.append(Finding("git", "ok", f"Last commit {age} day(s) ago"))
        except ValueError:
            pass
    dirty = _git(root, "status", "--porcelain")
    if dirty:
        n = len(dirty.splitlines())
        score -= min(15, n)
        f.append(Finding("git", "info", f"{n} uncommitted change(s) in working tree"))
    return CheckResult("git", "Git history", max(score, 0), 10, f)


CHECKS = [check_docs, check_hygiene, check_secrets, check_testing_ci,
          check_deps, check_git]


def grade_of(score: float) -> str:
    return ("A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60
            else "D" if score >= 40 else "F")


def diagnose(path: str | Path) -> Diagnosis:
    root = Path(path).resolve()
    if not root.is_dir():
        raise SystemExit(f"repo-doctor: not a directory: {root}")
    files = _walk(root)
    results = [c(root, files) for c in CHECKS]
    total_w = sum(r.weight for r in results)
    score = round(sum(r.score * r.weight for r in results) / total_w, 1)
    return Diagnosis(root=str(root),
                     ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     score=score, grade=grade_of(score), results=results)
