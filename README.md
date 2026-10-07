# 🩺 repo-doctor

**Is your repo ready for AI coding agents — and for humans? One command tells you.**
Zero dependencies. Python 3.9+. Fully offline.

```
  HEALTH  ████████████████░░░░  82.4/100   GRADE B

  [AI readiness]  60/100
    🟧 No agent instruction file (AGENTS.md / CLAUDE.md / .cursorrules ...)
       ↳ fix: Add AGENTS.md: 10 lines on what the project is, how to build/test,
         and what an agent must not touch. Biggest single lever for AI-assisted development.
  [Secrets exposure]  40/100
    🟥 AWS access key ID [aws-access-key]  (config/deploy.yml:12)
       ↳ fix: Remove from history (git filter-repo) and ROTATE the credential.
  ...
```

AI coding agents (Copilot, Claude, Cursor, Codex…) fail on repos they can't
understand. `repo-doctor` scores **seven axes** in seconds — the first one is
the one nobody else measures:

| Axis | What it catches |
|---|---|
| 🤖 **AI readiness** | no AGENTS.md / CLAUDE.md / .cursorrules, undiscoverable build/test commands, no entry point, no architecture notes, no explicit agent constraints |
| 📚 Documentation | missing/thin README, no LICENSE, no CHANGELOG / CONTRIBUTING / SECURITY |
| 🧹 Repo hygiene | committed `node_modules` / `__pycache__` / `.DS_Store`, files > 5 MB, missing `.gitignore` |
| 🔑 Secrets exposure | AWS keys, GitHub/Slack tokens, private-key blocks, hard-coded credentials, tracked `.env` |
| 🧪 Tests & CI | no test files, no CI workflow |
| 📦 Dependencies | unpinned requirements, missing lockfiles |
| 🕰 Git history | stale repos, tiny histories, dirty working tree |

Every finding ships with a **concrete fix**, not just a complaint.

## Install

```bash
pip install .            # from a clone
# or run without installing:
python -m repo_doctor /path/to/repo
```

## Usage

```bash
repo-doctor                 # diagnose the current directory
repo-doctor /path/to/repo   # diagnose any path
repo-doctor --json          # machine-readable output
repo-doctor --md report.md  # Markdown report
```

No network access. Nothing leaves your machine.

## 🚀 PRO edition

The free edition is fully functional for console / JSON / Markdown diagnosis.
**PRO** (one-time purchase, no subscription) adds the automation layer:

| | Free | PRO |
|---|---|---|
| 7-axis diagnosis incl. **AI readiness** + fixes | ✅ | ✅ |
| JSON / Markdown output | ✅ | ✅ |
| Secret rules | 5 core rules | **15+ rules** (Stripe, OpenAI, HF, Google, DB URLs, JWT…) |
| Self-contained **HTML dashboard** (`--html`) | — | ✅ gauge + per-axis cards |
| **SVG health badge** for your README (`--badge`) | — | ✅ |
| **CI quality gate** (`--fail-under 80` → exit 1) | — | ✅ |
| **Score history & trend chart** (`--history`) | — | ✅ |

**→ [Get repo-doctor PRO on Gumroad]( https://springofwindslabs.gumroad.com/l/repodoctor?utm_source=github&utm_medium=readme&utm_campaign=repo_doctor )**

```bash
# PRO in CI (GitHub Actions):
- run: repo-doctor --fail-under 75 --html health.html --badge health.svg --history
```

## Why trust this?

Built by [SpringOfWinds Labs](https://github.com/springofwindslabs) — we ship
[validated LLM training datasets](https://springofwindslabs.github.io/springofwinds-datasets/)
with published evidence (28,922 rows, 100% schema pass). Same discipline, applied to your repo.

## License

Free edition: MIT. PRO edition: commercial license (per-seat, included in the package).
