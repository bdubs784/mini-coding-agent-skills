---
name: pr-review
description: Review a pull request, branch, or git diff for bugs, missing tests, and risky changes before merging. Use when asked to review code changes or a PR.
---
# Review a pull request

1. Run `git status` and `git diff` (or `git diff main...HEAD` for a branch) to see what changed.
2. Read each changed file around the changed lines with `read_file`. Do not edit anything.
3. Run the tests if there is a test command in the README (for this repo: `python -m pytest -q`).
4. Report, in this order:
   - Bugs: wrong behavior, crashes, edge cases. Give the file and line.
   - Missing tests for new behavior.
   - Risky changes: deleted checks, new shell commands, secrets, large files.
   - Small style notes, at most three.
5. End with one line: `verdict: approve` or `verdict: request changes`.
