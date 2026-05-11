---
description: Think through a task and produce an implementation plan without editing files
argument-hint: "<rough task>"
---

Enter planning mode for this task:

$ARGUMENTS

Rules:
- Do not modify files.
- Inspect the codebase/docs as needed.
- Think deeply before answering.
- Ask me at most 3 clarifying questions, but only if the answers materially change the plan.
- If assumptions are reasonable, state them and continue instead of blocking.
- Prefer simple, incremental implementation.
- Identify risks, unknowns, and test strategy.

Produce a markdown plan with:

# Goal
# Current understanding
# Key findings
# Assumptions
# Proposed approach
# Implementation steps
# Tests / verification
# Risks / tradeoffs
# Questions, if any

End with: “Reply `go` to implement, or tell me what to change.”
