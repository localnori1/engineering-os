---
title: Engineering OS Maintenance
tags: [engineering-os, upgrades, safety]
status: stable
---

# Maintenance and upgrades

Every copy carries `ENGINEERING_OS_VERSION`. The version describes the OS
contract and supporting infrastructure, not the application release.

Use semantic versioning:

- patch: compatible clarification, validation fix, or template correction
- minor: backward-compatible capability or workflow addition
- major: authority, layout, command, or knowledge-model incompatibility

## Compare an update safely

Obtain and unpack the candidate OS separately, then run from the project copy:

```bash
python3 scripts/eos.py version
python3 scripts/eos.py update-check /path/to/candidate-engineering-os
```

The command hashes only OS-owned files. It excludes application code, project
knowledge, handoffs, source artifacts, Git state, runtime adapters, and build
output. It reports `ADD`, `REMOVE`, and `CHANGE` and never writes files.

Review each reported difference against local customizations. Apply accepted
changes through the normal engineering change loop, run strict validation,
tests, and runtime acceptance as appropriate, then update the version marker.
There is intentionally no auto-update or blind overwrite path: copied OS
instances may contain project-specific policy, and a three-way merge without a
trusted baseline would create false safety.

Keep project application dependencies independent from the OS; its CLI and
evaluator remain Python-standard-library tools to minimize upgrade friction.
