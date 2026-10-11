# Changelog

## 1.1.1 — 2026-10-11
- **Free-edition CLI tail notice redesigned** (single-variable experiment, Phase A —
  README untouched). The two-line footer is now a short boxed section that lists
  the actual PRO features with their flags, states the one-time price, and ends
  with "The free edition remains fully usable." No fabricated warnings, no fake
  previews — facts only.
- CLI-origin Gumroad links now carry `utm_source=cli` (`utm_medium=tail` for the
  post-diagnosis notice, `utm_medium=flag_gate` for the PRO-flag error) so CLI
  traffic is measurable separately from README links (`utm_medium=readme`).
- No functional changes to diagnosis, scoring, or outputs.

## 1.1.0 — 2026-10-08
- **New axis: 🤖 AI readiness (weight 20)** — the product's core differentiator.
  Checks: agent instruction files (AGENTS.md / CLAUDE.md / GEMINI.md /
  .cursorrules / .clinerules / .windsurfrules / copilot-instructions.md /
  .cursor/rules / .claude), discoverable build・test・lint commands (Makefile /
  package.json scripts / pyproject / README code blocks / agent instructions),
  entry-point discoverability, architecture description, explicit agent constraints.
- Rebalanced weights: ai 20 / docs 15 / hygiene 10 / secrets 25 / tests&CI 15 / deps 10 / git 5.
- repo-doctor now ships its own AGENTS.md (dogfooding).

## 1.0.0 — 2026-10-07
- First release. MISSION RAINMAKER product #001.
- 6-axis diagnosis: documentation / hygiene / secrets / tests & CI / dependencies / git history.
- Console, `--json`, `--md` outputs (free).
- PRO: `--html` dashboard, `--badge` SVG, `--fail-under` CI gate, `--history` trend, 15+ secret rules.
