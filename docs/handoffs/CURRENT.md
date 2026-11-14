---
status: complete
updated: 2026-11-15T00:00:00Z
---

# Current handoff

## Objective

v1.2.0: make the Engineering OS the technical partner for a non-technical product owner, with system-design depth, scale decisions at project start, owner-readable reviews, account ownership, operations, success measures, and compliance awareness.

## Completed

- `system-design` skill (complexity, capacity, scalability, reliability, trade-offs, project foundation); project initialization asks plain-language questions and records a scale profile before choosing a stack.
- `operations` skill (incidents, launch readiness, health checks) and `templates/runbook.md`.
- `AGENTS.md`: owner partnership rules (size and recurring cost up front, owner-owned accounts, glossary) and a two-layer review: owner summary first, technical diff second.
- `templates/services.md` is created by `eos.py init`; `templates/glossary.md` added; ADR template has "What this means for the owner"; requirement template has "Success measure".
- `engineering-review/references/compliance.md`, routed from features, release, and project foundation; release review now opens with a plain owner summary.
- Work roles (planner / implementer / independent reviewer) in `AGENTS.md`, model-neutral; Claude Code `implementer` (Sonnet) and `reviewer` (Opus, read-only) subagents in `runtimes/claude/agents/`, linked to `.claude/agents` by `eos.py adapters` (skipped, not overwritten, if a project already has `.claude/agents`). Runtime mapping in `docs/os/PORTABILITY.md`.
- Review-fix loop in `AGENTS.md`: reviewer verdict, implementer fixes in-scope findings without waiting for the owner, fresh re-review, max three rounds, explicit stop conditions; owner sees only passed work or a specific decision.
- "Lean, proportional changes" in `AGENTS.md` (no needless new files, rewrites, speculative or bloated code); reviewer treats violations as Medium fix-required findings.
- Security baseline (`engineering-review/references/security-baseline.md`) applied during build, foundation, review, and release; `eos.py check` also detects Stripe live keys, Google API keys, Slack tokens, and database URLs with passwords.
- Project foundation now covers product type (`system-design/references/product-types.md`), delivery pipeline (CI, preview deployments, approved deploys), data traps (time zones, money, locale), and usage conditions. All OS wording is domain-neutral.
- Git initialized on `main` with pre-commit hook; baseline commit `5055db9`. Not pushed to any remote.
- Eval cases added: `design-for-scale`, `new-project-foundation`, `health-check`, `review-fix-loop`, `small-fix-stays-small`, `security-baseline-in-build` (14 total). Strict check, 19 tests, and reference evals pass; `dist/engineering-os-v1.zip` rebuilt.

## In progress

- None.

## Blockers and decisions needed

- Live Codex/Claude acceptance runs are unrun: they need owner authorization, and neither CLI was found on this machine. See "Owner quick run" in `docs/os/ACCEPTANCE.md`.

## Important decisions and risks

- Owner decision: no mandatory performance check on every feature; scale work is front-loaded at initialization.
- Agents assume a non-technical owner unless `PROJECT.md` says otherwise.
- All guidance is unproven against a live agent until acceptance runs happen.

## Relevant files

- `AGENTS.md`
- `skills/system-design/`
- `skills/operations/`
- `skills/engineering-review/references/compliance.md`
- `templates/services.md`, `templates/runbook.md`, `templates/glossary.md`
- `evals/cases.json`

## Exact next step

Owner reviews v1.2.0, then, when ready, runs the owner quick run in `docs/os/ACCEPTANCE.md` on a disposable project.
