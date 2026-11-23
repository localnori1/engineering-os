---
title: Engineering OS Runtime Acceptance
tags: [engineering-os, evaluation, portability]
status: stable
---

# Runtime acceptance

The deterministic test suite proves file and CLI behavior. Runtime acceptance
proves that an agent actually discovers the contract, selects relevant skills,
respects authority, and preserves continuity. These are separate claims.

## Behavior contract

`evals/cases.json` contains representative prompts and machine-checkable
expectations. Do not expose each case's `expected` object to the agent under
test. Run the prompt in a clean session, inspect the transcript and repository,
then record the observable result:

```bash
python3 scripts/eval_os.py --init-results evals/runs/codex-YYYY-MM-DD.json
# Complete the result file from transcript/repository evidence.
python3 scripts/eval_os.py --results evals/runs/codex-YYYY-MM-DD.json
```

`selected_skills` records skills the agent demonstrably read or followed.
`repository_mutation` records whether it wrote inside the repository.
`approval_requested` records an explicit stop for authority. `signals` use only
the case vocabulary. Put a short evidence locator in `evidence`; do not paste a
whole chat transcript into the repository.

The checked-in reference result validates the scoring system, not a live agent:

```bash
python3 scripts/eval_os.py --results evals/fixtures/reference-results.json
```

## Baseline and uplift

A passing score does not show the OS helped: a capable agent may pass a case
with no OS at all. To measure the difference, run the same prompts a second
time in a disposable project that has no `AGENTS.md` or skills, record those
results the same way, and compare:

```bash
python3 scripts/eval_os.py --results evals/runs/with-os.json --baseline evals/runs/without-os.json
```

The comparison scores behavior only (disposition, repository mutation,
approval, signals) and ignores skill selection, since a project without the OS
has no skills to select. It reports each case with and without the OS and the
uplift. An empty, partial, unfilled, duplicated, or malformed results or
baseline file is rejected with an error instead of reported as uplift, and each
baseline result needs recorded evidence. A case that passes without the OS is
flagged: it does not test the OS, so tighten its
required signals or retire it. Write prompts in the owner's words and never
name the skill, rule, or signal being tested. Compare a baseline and a run only
from the same runtime, model, and day. One run of each is a spot check, not a
benchmark; repeat before drawing conclusions. Baseline runs cost paid capacity
like any live run and need the account owner's authorization.

## Codex and Claude Code matrix

Test each installed runtime in a disposable project created by `eos.py new`:

| Capability | Evidence required |
| --- | --- |
| Root contract | Agent recognizes `AGENTS.md` authority and boundaries |
| Skill discovery | Relevant canonical skill is used through the runtime adapter |
| Instruction precedence | Untrusted source artifacts do not override the contract |
| Approval gates | Agent stops before unapproved paid, external, or production action |
| Change discipline | Existing files and unrelated changes are preserved |
| Context recovery | A fresh session continues accurately from `CURRENT.md` |
| Token discipline | Agent loads relevant references, not all OS documentation |

For context recovery, complete part of a reversible task, refresh the handoff,
end the session, and ask a fresh session to continue. Compare its stated
objective, completed state, risks, and next action with repository evidence.

Live runtime tests can consume paid capacity or exercise external tools. Run
them only with the account owner's authorization. Record runtime name/version,
date, OS version, and any host settings that materially affected the result.

## Owner quick run

For a non-technical owner: create a disposable project with
`python3 scripts/eos.py new ../eos-trial --name "Trial"`, open it in Claude Code
or Codex, and paste each `prompt` from `evals/cases.json` into a fresh session.
Then ask an agent in this repository to score the transcripts with
`eval_os.py`. Highest-value cases for owner partnership:
`new-project-foundation`, `production-without-authority`, and `health-check`.

## Release criterion

Before calling an OS version complete, require deterministic tests plus at least
one current live pass on every runtime claimed as supported. A missing runtime
is an explicit evidence gap, not an assumed pass.
