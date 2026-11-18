# Spec

Stage 2: what the Agent Skills component does, precisely enough to test.

## Skill format

A skill is a folder with a `SKILL.md` (or `skill.md`) file:

```
skills/pr-review/SKILL.md
---
name: pr-review
description: Review a pull request ... Use when asked to review code changes or a PR.
disable-model-invocation: false      # optional, true = only the user can start it
---
# Steps in markdown ...
```

- `name` defaults to the folder name, `description` defaults to the first line of the body.
- `{skill_dir}` in the body is replaced with the skill folder path, so a skill can call its own
  bundled scripts.
- Bodies longer than 6000 characters are clipped.

## Discovery (FR1)

On start the agent scans these folders under the repo root, in order, and loads every
subfolder that has a `SKILL.md`: `skills/`, `skill/`, `.agents/skills/`, `.claude/skills/`.
`--skills-dir PATH` adds more folders. If two skills have the same name, the first one wins.

## Similarity check (FR2)

For every user prompt the agent scores every model-invocable skill:

- If the skill name appears in the prompt as whole words, the score is 1.0.
- Otherwise score = cosine similarity between word counts of the prompt and word counts of
  the skill's name (counted twice) plus its description. Words are lowercased, stop words are
  removed, and simple suffixes (`ing`, `ed`, `es`, `s`) are stripped.
- The best skill is selected if its score is at least the threshold (default 0.2,
  `--skill-threshold`). Otherwise no skill runs.

## Triggering (FR3)

Three ways a skill runs:

| Trigger | When | Logged `source` |
|---|---|---|
| user prompt | best score >= threshold at the start of `ask()` | `user prompt` |
| `use_skill` tool | the model calls `use_skill(name, reason)` mid-task | `use_skill tool` |
| explicit | the user types `/skill NAME` or `/NAME` | `explicit /skill` |

Skills with `disable-model-invocation: true` are left out of the similarity ranking and the
`use_skill` tool refuses them, so they only run through the explicit trigger.

## Executing a skill (FR4)

- The prefix (cached part of the prompt) lists every skill's name and description, a
  `use_skill` tool, and three rules telling the model to follow an active skill step by step.
- When a skill is active, its full instructions are added to the prompt in an
  `Active skill: NAME` section after memory and before the transcript, on every step of that
  request. The model carries out the steps with the normal tools (`run_shell`, `write_file`, ...),
  which keep their approval rules.
- A `skill` entry is added to the session history so the transcript shows the activation.
- Active skills reset at the start of each new request.

## Logging (FR5)

Every event goes to `<repo>/.mini-coding-agent/logs/skills.jsonl` (one JSON object per line) and
`skills.log` (one readable line per event):

| event | fields |
|---|---|
| `prompt` | time, session, source, prompt |
| `similarity_check` | time, session, source, method, threshold, scores (every skill), selected |
| `skill_executed` | time, session, skill, source, score, path |
| `skill_finished` | time, session, skill, tools used during the request, final answer |

## Non-functional

- Standard library only. No change to behavior when no skills are found (no `use_skill` tool,
  no log files).
- `--no-skills` turns the component off.
- Child agents from `delegate` share the registry and logger but do not re-run the prompt match.

## Acceptance tests

Each FR has at least one test in `tests/test_skills.py`. All tests in `tests/` must pass, and the
Lab 4 demo (`demo/`) must produce a log with all four event types.
