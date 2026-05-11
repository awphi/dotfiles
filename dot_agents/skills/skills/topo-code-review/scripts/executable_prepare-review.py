#!/usr/bin/env python3
"""Prepare a Topo code review bundle from live PR criteria and a git diff."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_DOCS_REPO = "Arm-Debug/topo-team-docs"
DEFAULT_DOCS_REMOTE = "https://github.com/Arm-Debug/topo-team-docs.git"
DOC_FILES = ("CODING_STYLE.md", "PULL_REQUESTS.md")


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


class ReviewPrepError(RuntimeError):
    pass


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    text: bool = True,
) -> CommandResult:
    proc = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    result = CommandResult(proc.stdout, proc.stderr, proc.returncode)
    if check and proc.returncode != 0:
        rendered = " ".join(command)
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise ReviewPrepError(f"Command failed ({rendered}):\n{detail}")
    return result


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def git(repo: Path, args: Iterable[str], *, check: bool = True) -> CommandResult:
    return run(["git", "-C", str(repo), *args], check=check)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def git_toplevel(repo: Path) -> Path:
    result = git(repo, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def current_branch(repo: Path) -> str:
    result = git(repo, ["branch", "--show-current"], check=False)
    return result.stdout.strip() or "(detached HEAD)"


def resolve_target_default_branch(repo: Path, remote: str) -> str | None:
    result = git(repo, ["symbolic-ref", "--quiet", "--short", f"refs/remotes/{remote}/HEAD"], check=False)
    if result.returncode == 0 and result.stdout.strip().startswith(f"{remote}/"):
        return result.stdout.strip().split("/", 1)[1]
    result = git(repo, ["remote", "show", remote], check=False)
    if result.returncode == 0:
        match = re.search(r"HEAD branch: (.+)", result.stdout)
        if match:
            return match.group(1).strip()
    return None


def rev_parse(repo: Path, ref: str) -> str | None:
    result = git(repo, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def resolve_ref(repo: Path, ref: str, remote: str, *, fetch: bool, kind: str) -> tuple[str, str]:
    sha = rev_parse(repo, ref)
    if sha:
        return ref, sha

    if "/" not in ref:
        remote_ref = f"{remote}/{ref}"
        sha = rev_parse(repo, remote_ref)
        if sha:
            return remote_ref, sha

        if fetch:
            git(repo, ["fetch", "--quiet", remote, f"{ref}:refs/remotes/{remote}/{ref}"], check=False)
            sha = rev_parse(repo, remote_ref)
            if sha:
                return remote_ref, sha

    raise ReviewPrepError(
        f"Could not resolve {kind} ref '{ref}'. Fetch the target repo, pass --base/--head explicitly, "
        f"or check that remote '{remote}' has that branch."
    )


def docs_default_branch(docs_repo: str, docs_remote: str) -> tuple[str, str]:
    if command_exists("gh"):
        result = run(
            ["gh", "repo", "view", docs_repo, "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"],
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip(), "gh repo view"

    if command_exists("git"):
        result = run(["git", "ls-remote", "--symref", docs_remote, "HEAD"], check=False)
        if result.returncode == 0:
            match = re.search(r"ref: refs/heads/([^\t\n]+)\s+HEAD", result.stdout)
            if match:
                return match.group(1).strip(), "git ls-remote"

    return "main", "fallback default"


def fetch_doc_with_gh(docs_repo: str, docs_ref: str, doc_path: str) -> tuple[str, str] | None:
    if not command_exists("gh"):
        return None
    endpoint = f"/repos/{docs_repo}/contents/{doc_path}?ref={docs_ref}"
    result = run(
        ["gh", "api", "-H", "Accept: application/vnd.github.raw", endpoint],
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout, f"gh api {docs_repo}@{docs_ref}:{doc_path}"
    return None


def fetch_doc_with_raw_github(docs_repo: str, docs_ref: str, doc_path: str) -> tuple[str, str] | None:
    url = f"https://raw.githubusercontent.com/{docs_repo}/{docs_ref}/{doc_path}"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            body = response.read().decode("utf-8")
            if body.strip():
                return body, url
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError):
        return None
    return None


def ensure_docs_clone(cache_root: Path, docs_repo: str, docs_remote: str, docs_ref: str) -> Path | None:
    cache_root.mkdir(parents=True, exist_ok=True)
    clone_dir = cache_root / re.sub(r"[^A-Za-z0-9_.-]+", "-", docs_repo)

    if clone_dir.exists():
        if not (clone_dir / ".git").exists():
            return None
        fetch_result = git(clone_dir, ["fetch", "--quiet", "origin", docs_ref], check=False)
        if fetch_result.returncode != 0:
            return None
    else:
        if command_exists("gh"):
            result = run(["gh", "repo", "clone", docs_repo, str(clone_dir), "--", "--quiet"], check=False)
            if result.returncode != 0:
                result = run(["git", "clone", "--quiet", docs_remote, str(clone_dir)], check=False)
        else:
            result = run(["git", "clone", "--quiet", docs_remote, str(clone_dir)], check=False)
        if result.returncode != 0:
            return None
        fetch_result = git(clone_dir, ["fetch", "--quiet", "origin", docs_ref], check=False)
        if fetch_result.returncode != 0:
            return None

    return clone_dir


def fetch_doc_with_clone(
    cache_root: Path,
    docs_repo: str,
    docs_remote: str,
    docs_ref: str,
    doc_path: str,
) -> tuple[str, str] | None:
    clone_dir = ensure_docs_clone(cache_root, docs_repo, docs_remote, docs_ref)
    if not clone_dir:
        return None

    refs_to_try = [f"origin/{docs_ref}", docs_ref, "FETCH_HEAD"]
    for ref in refs_to_try:
        result = git(clone_dir, ["show", f"{ref}:{doc_path}"], check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout, f"updated git clone cache {clone_dir} {ref}:{doc_path}"
    return None


def fetch_docs(
    out_dir: Path,
    *,
    docs_repo: str,
    docs_remote: str,
    docs_ref: str | None,
    cache_root: Path,
) -> list[str]:
    if docs_ref is None:
        docs_ref, default_source = docs_default_branch(docs_repo, docs_remote)
    else:
        default_source = "explicit --docs-ref"

    sources: list[str] = [f"docs ref: {docs_ref} ({default_source})"]
    criteria_dir = out_dir / "criteria"
    criteria_dir.mkdir(parents=True, exist_ok=True)

    for doc_file in DOC_FILES:
        fetched = (
            fetch_doc_with_gh(docs_repo, docs_ref, doc_file)
            or fetch_doc_with_raw_github(docs_repo, docs_ref, doc_file)
            or fetch_doc_with_clone(cache_root, docs_repo, docs_remote, docs_ref, doc_file)
        )
        if not fetched:
            raise ReviewPrepError(
                f"Could not fetch {doc_file} from {docs_repo}@{docs_ref}. Install/authenticate gh CLI "
                "or ensure network access to GitHub. Refusing to use a potentially stale local copy."
            )
        content, source = fetched
        write_text(criteria_dir / doc_file, content)
        sources.append(f"{doc_file}: {source}")

    return sources


def safe_patch_name(path: str) -> str:
    safe = path.replace("/", "__")
    safe = re.sub(r"[^A-Za-z0-9_.@+=,-]+", "_", safe)
    return safe[:180] or "root"


def parse_numstat(numstat: str) -> tuple[int, int, int, int]:
    added = deleted = text_files = binary_files = 0
    for line in numstat.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        if parts[0] == "-" or parts[1] == "-":
            binary_files += 1
            continue
        added += int(parts[0])
        deleted += int(parts[1])
        text_files += 1
    return added, deleted, text_files, binary_files


def resolve_base(
    repo: Path,
    base: str,
    remote: str,
    *,
    fetch: bool,
) -> tuple[str, str, str]:
    try:
        base_ref, base_sha = resolve_ref(repo, base, remote, fetch=fetch, kind="base")
        return base_ref, base_sha, ""
    except ReviewPrepError:
        default_branch = resolve_target_default_branch(repo, remote) if base == "main" else None
        if not default_branch or default_branch == base:
            raise

    base_ref, base_sha = resolve_ref(repo, default_branch, remote, fetch=fetch, kind="base")
    note = (
        f"Base input `{base}` was not found; used target repo default branch "
        f"`{default_branch}` instead. Pass --base to override."
    )
    return base_ref, base_sha, note


def capture_git_outputs(
    repo: Path,
    git_dir: Path,
    range_two_dot: str,
    range_three_dot: str,
) -> tuple[dict[str, str], CommandResult, list[str]]:
    commands = {
        "status.txt": ["status", "--short", "--branch"],
        "current-branch.txt": ["branch", "--show-current"],
        "commits.txt": ["log", "--oneline", "--decorate", range_two_dot],
        "diffstat.txt": ["diff", "--stat", range_three_dot],
        "numstat.txt": ["diff", "--numstat", range_three_dot],
        "changed-files.txt": ["diff", "--name-only", range_three_dot],
        "diff.patch": ["diff", "--find-renames", range_three_dot],
    }

    command_lines: list[str] = []
    command_outputs: dict[str, str] = {}
    for filename, args in commands.items():
        result = git(repo, args, check=False)
        command_outputs[filename] = result.stdout
        write_text(git_dir / filename, result.stdout + (result.stderr if result.stderr else ""))
        command_lines.append(f"git -C {repo} {' '.join(args)}")

    diff_check = git(repo, ["diff", "--check", range_three_dot], check=False)
    write_text(git_dir / "diff-check.txt", diff_check.stdout + diff_check.stderr)
    command_lines.append(f"git -C {repo} diff --check {range_three_dot}")
    return command_outputs, diff_check, command_lines


def write_per_file_patches(repo: Path, out_dir: Path, range_three_dot: str, changed_files: list[str]) -> None:
    patch_dir = out_dir / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch_index_lines = []
    for changed_file in changed_files:
        patch = git(repo, ["diff", "--find-renames", range_three_dot, "--", changed_file], check=False)
        patch_name = safe_patch_name(changed_file) + ".patch"
        write_text(patch_dir / patch_name, patch.stdout + (patch.stderr if patch.stderr else ""))
        patch_index_lines.append(f"{changed_file}\tpatches/{patch_name}")
    write_text(out_dir / "patch-index.tsv", "\n".join(patch_index_lines) + ("\n" if patch_index_lines else ""))


def prepare_git_context(
    out_dir: Path,
    *,
    repo: Path,
    base: str,
    head: str,
    remote: str,
    fetch: bool,
) -> dict[str, str | int]:
    toplevel = git_toplevel(repo)
    if fetch:
        git(toplevel, ["fetch", "--quiet", "--prune", remote], check=False)

    base_ref, base_sha, base_resolution_note = resolve_base(toplevel, base, remote, fetch=fetch)
    head_ref, head_sha = resolve_ref(toplevel, head, remote, fetch=fetch, kind="head")
    merge_base = git(toplevel, ["merge-base", base_ref, head_ref]).stdout.strip()
    range_two_dot = f"{base_ref}..{head_ref}"
    range_three_dot = f"{base_ref}...{head_ref}"

    git_dir = out_dir / "git"
    git_dir.mkdir(parents=True, exist_ok=True)
    command_outputs, diff_check, command_lines = capture_git_outputs(
        toplevel, git_dir, range_two_dot, range_three_dot
    )
    changed_files = [line for line in command_outputs["changed-files.txt"].splitlines() if line.strip()]
    write_per_file_patches(toplevel, out_dir, range_three_dot, changed_files)
    added, deleted, text_files, binary_files = parse_numstat(command_outputs["numstat.txt"])

    return {
        "repo": str(toplevel),
        "current_branch": current_branch(toplevel),
        "base_input": base,
        "base_ref": base_ref,
        "base_sha": base_sha,
        "base_resolution_note": base_resolution_note,
        "head_input": head,
        "head_ref": head_ref,
        "head_sha": head_sha,
        "merge_base": merge_base,
        "remote": remote,
        "fetch": "yes" if fetch else "no",
        "range_two_dot": range_two_dot,
        "range_three_dot": range_three_dot,
        "changed_files": len(changed_files),
        "added_lines": added,
        "deleted_lines": deleted,
        "text_files": text_files,
        "binary_files": binary_files,
        "diff_check_exit": diff_check.returncode,
        "command_lines": "\n".join(f"- `{line}`" for line in command_lines),
    }


def create_metadata(out_dir: Path, docs_sources: list[str], git_info: dict[str, str | int]) -> None:
    status_note = ""
    status_file = out_dir / "git" / "status.txt"
    if status_file.exists():
        status = status_file.read_text(encoding="utf-8")
        dirty_lines = [line for line in status.splitlines() if line and not line.startswith("##")]
        if dirty_lines:
            status_note = (
                "\n> Warning: the target repo has uncommitted changes. The branch diff bundle compares commits only; "
                "inspect the worktree separately if the user expects those changes to be reviewed.\n"
            )

    metadata = f"""
# Topo code review bundle

{status_note}
## Target

- Repo: `{git_info['repo']}`
- Current branch: `{git_info['current_branch']}`
- Base input: `{git_info['base_input']}`
- Base resolved: `{git_info['base_ref']}` (`{git_info['base_sha']}`)
- Base resolution note: {git_info['base_resolution_note'] or 'n/a'}
- Head input: `{git_info['head_input']}`
- Head resolved: `{git_info['head_ref']}` (`{git_info['head_sha']}`)
- Merge base: `{git_info['merge_base']}`
- Diff range: `{git_info['range_three_dot']}`
- Commit range: `{git_info['range_two_dot']}`
- Fetched target remote `{git_info['remote']}` before diff: {git_info['fetch']}

## Size summary

- Changed files: {git_info['changed_files']}
- Added lines: {git_info['added_lines']}
- Deleted lines: {git_info['deleted_lines']}
- Text files in numstat: {git_info['text_files']}
- Binary files in numstat: {git_info['binary_files']}
- `git diff --check` exit code: {git_info['diff_check_exit']}

Compare size against the PR guideline in `criteria/PULL_REQUESTS.md` (~250 LoC target; split anything over ~500).

## Live criteria sources

{chr(10).join(f'- {source}' for source in docs_sources)}

## Files to read

1. `criteria/CODING_STYLE.md`
2. `criteria/PULL_REQUESTS.md`
3. `git/status.txt`
4. `git/commits.txt`
5. `git/diffstat.txt`
6. `git/diff-check.txt`
7. `git/diff.patch` or per-file patches listed in `patch-index.tsv`

## Commands captured

{git_info['command_lines']}
""".lstrip()
    write_text(out_dir / "metadata.md", metadata)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch live Topo review criteria and prepare git branch review context.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo", default=os.getcwd(), help="Target git repo to review")
    parser.add_argument("--base", default="main", help="Base branch/ref for review")
    parser.add_argument("--head", default="HEAD", help="Head branch/ref for review")
    parser.add_argument("--remote", default="origin", help="Target repo remote to fetch/resolve branches")
    parser.add_argument("--no-fetch", action="store_true", help="Do not fetch target repo remote before preparing diff")
    parser.add_argument("--docs-repo", default=DEFAULT_DOCS_REPO, help="GitHub owner/repo for live criteria docs")
    parser.add_argument("--docs-remote", default=DEFAULT_DOCS_REMOTE, help="Git remote URL used for criteria clone fallback")
    parser.add_argument("--docs-ref", default=None, help="Docs branch/ref; defaults to docs repo default branch via gh, else main")
    parser.add_argument(
        "--cache-root",
        default=str(Path.home() / ".cache" / "topo-code-review"),
        help="Cache directory for clone fallback only",
    )
    parser.add_argument("--out", default=None, help="Output directory; defaults to a new temp directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out).resolve() if args.out else Path(tempfile.mkdtemp(prefix="topo-code-review-"))
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        docs_sources = fetch_docs(
            out_dir,
            docs_repo=args.docs_repo,
            docs_remote=args.docs_remote,
            docs_ref=args.docs_ref,
            cache_root=Path(args.cache_root).expanduser().resolve(),
        )
        git_info = prepare_git_context(
            out_dir,
            repo=Path(args.repo).expanduser().resolve(),
            base=args.base,
            head=args.head,
            remote=args.remote,
            fetch=not args.no_fetch,
        )
        create_metadata(out_dir, docs_sources, git_info)
    except ReviewPrepError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(f"partial bundle, if any: {out_dir}", file=sys.stderr)
        return 1

    print(
        textwrap.dedent(
            f"""
            Prepared Topo review bundle: {out_dir}

            Read in this order:
              1. {out_dir / 'metadata.md'}
              2. {out_dir / 'criteria' / 'CODING_STYLE.md'}
              3. {out_dir / 'criteria' / 'PULL_REQUESTS.md'}
              4. {out_dir / 'git' / 'diffstat.txt'}
              5. {out_dir / 'git' / 'diff.patch'} (or per-file patches from {out_dir / 'patch-index.tsv'})

            The criteria files were fetched live from the docs repository for this run.
            """
        ).strip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
