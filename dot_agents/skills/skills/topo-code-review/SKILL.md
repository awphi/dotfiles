---
name: topo-code-review
description: "Reviews a git branch or PR in any repo against the latest Topo team PR guidelines and coding standards fetched from Arm-Debug/topo-team-docs. Use when asked to review a branch, PR, merge request, or code changes against Topo standards."
compatibility: "Requires git and Python 3. gh CLI is recommended for private GitHub access."
---

# Topo Code Review

Review a branch or PR against the current `CODING_STYLE.md` and `PULL_REQUESTS.md` from `https://github.com/Arm-Debug/topo-team-docs`.

## Non-negotiable

Always fetch the criteria for the current run. Do **not** rely on criteria text embedded in this skill, model memory, or local checked-out copies of `topo-team-docs` unless the fetch script explicitly reports that it updated/read a clone cache. If live criteria cannot be fetched, stop and explain what authentication/network setup is missing.

## Inputs

Confirm or infer:
- target repo path (default: current working directory)
- base branch/ref (default: `main`; the helper falls back to the target repo default branch if `main` does not exist)
- head branch/ref (default: current `HEAD`)
- whether uncommitted worktree changes should be reviewed separately

## Prepare review bundle

From this skill directory, run:

```bash
./scripts/prepare-review.py --repo <target-repo> --base <base-ref> --head <head-ref>
```

Useful variants:

```bash
./scripts/prepare-review.py --repo .                         # current branch vs main
./scripts/prepare-review.py --repo . --base origin/main       # explicit base
./scripts/prepare-review.py --repo . --base main --head topic # named head
./scripts/prepare-review.py --repo . --docs-ref main          # pin docs ref if asked
```

The script:
- fetches `CODING_STYLE.md` and `PULL_REQUESTS.md` live from `Arm-Debug/topo-team-docs` using `gh`, raw GitHub, or an updated clone cache
- fetches the target repo remote unless `--no-fetch` is passed
- writes a temp bundle with metadata, criteria, commits, diff stats, changed files, full diff, and per-file patches

Read `metadata.md` first, then both criteria files fully, then inspect the diff files listed by the script.

## Review workflow

1. Summarise the current criteria as a short checklist for this review.
2. Inspect `git/status.txt`; if dirty, state whether uncommitted changes are included (they are not included in the branch diff bundle).
3. Inspect commits, diff stat, `diff-check.txt`, full/per-file patches, and changed files in the target repo as needed.
4. Check PR shape: atomicity, approximate LoC target, readiness, tests, and any process issues required by `PULL_REQUESTS.md`.
5. Check code quality: names, comments explaining why, pure-function opportunities, function length, error handling, fail-fast validation/assertions, YAGNI, tests, and focused tests per `CODING_STYLE.md`.
6. Tie every finding to a criterion. Avoid personal preference nits not supported by the criteria.
7. Use file paths and line references where possible. If line numbers are uncertain, cite the patch hunk/function and say so.

## Output format

```md
Summary: <1-3 sentences, including base/head reviewed and criteria source>

Criteria checklist:
- <short checklist extracted from live docs>

Blocking issues:
- <severity, file:line or hunk, criterion, rationale, actionable fix>

Non-blocking issues:
- <file:line or hunk, criterion, rationale, actionable fix>

Questions:
- <clarifications needed, if any>

Tests:
- <tests observed/run/not run and why>
```

If no issues are found in a section, write `None`.
