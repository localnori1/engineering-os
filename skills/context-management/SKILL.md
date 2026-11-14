---
name: context-management
description: Create or refresh a concise project handoff and maintain durable Markdown knowledge without context bloat. Use when work pauses, a session/agent/context boundary approaches, the user asks to remember or hand off, or project knowledge needs hygiene review.
---

# Context Management

Make continuation cheap and accurate. Do not dump conversation history.

## Handoff

1. Inspect the current objective, actual changed files/state, verification
   evidence, relevant requirements/decisions, and current handoff.
2. Update `docs/handoffs/CURRENT.md` with objective, completed work, in-progress
   work, blockers/decisions, important risks, relevant files, and one exact next
   step.
3. Prefer observable facts and commands over narrative. Mark unverified claims.
4. Remove superseded detail. Keep the file below the validator's size budget
   unless complexity clearly requires more.
5. When the objective is complete, mark it complete and leave only stable final
   evidence or reset for the next objective.
6. Run `python3 scripts/eos.py check` after editing the handoff or durable
   records; resolve structural failures and assess freshness/index warnings.

## Durable knowledge

Promote information from a handoff only when it changes future decisions:

- confirmed product intent/current technical map -> `PROJECT.md`
- traceable behavior -> requirement record
- consequential choice -> decision record
- material compromise -> debt record
- non-obvious reusable failure insight -> lesson record

Use templates as starting shapes, not mandatory artifacts. Consolidate duplicate
facts and delete stale low-value prose. Git history provides audit history; live
documents should optimize for current truth.

## Retrieval note

Ensure `PROJECT.md` points to a new record if future agents need to discover it.
Do not build large indexes that repeat titles and summaries already searchable by
filename or text.
