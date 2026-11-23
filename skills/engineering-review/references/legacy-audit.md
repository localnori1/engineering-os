# Legacy-pattern audit

Use when adopting or inheriting a codebase, or when asked what is outdated:
deprecated or unmaintained dependencies, deprecated APIs, hand-built versions of
things the platform or framework now provides, and old workarounds. This is
read-only; finding something never authorizes fixing it.

## Method

1. **Fix the yardstick.** State what "outdated" means here: the project's
   support target and stack versions from `PROJECT.md`, and the current
   documentation for each. If no target exists, say so and use the widely
   supported baseline. Check current references, not memory.
2. **Scan.** Prefer deterministic searches (dependency manifests and audit
   tools, deprecation warnings from the build, targeted pattern searches) over
   reading everything. Record each candidate with its location. Note what the
   scan cannot see.
3. **Verify each candidate in context.** Read the surrounding code. Drop it if the
   old pattern is still needed (a supported older environment, a documented
   workaround for a real bug, a replacement that behaves differently). Keep a
   short list of what was dropped and why, so the same candidate is not
   re-raised.
4. **Report.** For each confirmed finding: location, what is outdated, the
   modern replacement, evidence, effort (small, medium, large), and risk of
   changing it. Rank by consequence (security, breakage, maintenance cost), not
   age. Flag features newer than the support target or only partly supported.
5. **Stop for direction.** The owner chooses what to fix. Findings that are real
   but not worth fixing now become debt records (`templates/debt.md`) with a
   revisit trigger. Do not fix, upgrade, or refactor during the audit.

## When fixes are authorized

Work one finding at a time, smallest change first. After each, re-run the same
scan on the changed files and the project's tests, and confirm behavior is
unchanged. Do not batch unrelated modernizations into one change.

## Calibration

A confirmed finding must be mostly right: if a pattern is often legitimate,
report it as "check" with the condition, not as a defect. Do not report
cosmetic age ("old syntax") with no consequence.
