# Spec: mini-coding-agent can use agent skills

Stage 2 (Design): turns [intent.md](intent.md) into numbered, testable requirements.
Requirements are numbered so [plan.md](plan.md), the tests, and [../evals/](../evals/) can cite them.

Constraints carried in: standard library only; no behavior change without skill folders; usable
by qwen3.5:4b; Claude Code's `SKILL.md` format.

## Requirements <!-- numbered, so tests can cite them -->

- **R1. Skill format and discovery.** A skill is a folder with `SKILL.md` or `skill.md`. The agent
  loads every such folder under `skills/`, `skill/`, `.agents/skills/`, `.claude/skills/` in the
  repo root (plus `--skills-dir PATH`). If two skills share a name, the first one wins.
- **R2. Similarity check.** For every user prompt the agent scores every model-invocable skill and
  selects the best one if its score is at least the threshold (default 0.2, `--skill-threshold`).
- **R3. Triggers.** A skill runs from a matching user prompt, from the model calling
  `use_skill(name, reason)` mid-task, or from the user typing `/skill NAME`, `/NAME`, or `$NAME`.
  Skills with `disable-model-invocation: true` only run through the explicit trigger.
- **R4. Execution.** An active skill's instructions are in front of the model on every step of
  that request, and the model carries them out with the normal tools and approval rules.
- **R5. Logging.** The prompt, the similarity check (all scores, threshold, selection), the
  executed skill, and its end are logged to `.mini-coding-agent/logs/skills.jsonl` and `skills.log`.
- **R6. Off switch.** With no skill folders, or with `--no-skills`, there is no `use_skill` tool,
  no skill text in the prompt, and no log files: the agent behaves like the original.

## Design

**Skill file (R1).**

```
skills/pr-review/SKILL.md
---
name: pr-review
description: Review a pull request ... Use when asked to review code changes or a PR.
disable-model-invocation: false      # optional, true = only the user can start it
timeout: 300                         # optional, run_shell default timeout while active (max 600)
---
# Steps in markdown ...
```

`name` defaults to the folder name and `description` to the first body line. `{skill_dir}` in the
body becomes the skill folder path. Bodies over 6000 characters are clipped.

**Score (R2).** 1.0 if the skill name appears in the prompt as whole words. Otherwise cosine
similarity between word counts of the prompt and of the skill's name (counted twice) plus its
description. Words are lowercased, stop words removed, and `ing`/`ed`/`es`/`s` stripped.

**Triggers (R3).**

| Trigger | When | Logged `source` |
|---|---|---|
| user prompt | best score >= threshold at the start of `ask()` | `user prompt` |
| `use_skill` tool | the model calls `use_skill(name, reason)` mid-task | `use_skill tool` |
| explicit | `/skill NAME`, `/NAME`, or `$NAME` | `explicit /skill` |

When no skill is selected, the request's prompt gets a short "Skill check" section listing the
model-invocable skills and telling the model to call `use_skill` if one fits (answers intent
question 2). It disappears once a skill is active. A `use_skill` call logs its own `prompt`
(the reason) and `similarity_check`, then loads the named skill. That check scores the name plus
the reason, so the named skill always scores 1.0: the model's explicit choice wins, and the
check records the reason and how the other skills compare. For `/skill NAME` with no task text,
the logged prompt is the default task the model receives ("Follow the steps of the active
skill NAME, then answer."), and the check lists only that skill at 1.0.

**Execution (R4).** The cached prompt prefix lists every skill's name and description, the
`use_skill` tool, and the rules for following an active skill. The active skill's full text goes
in an `Active skill: NAME` section after memory and before the transcript. A `skill` entry is added
to the session history. Active skills reset at each new request. Child agents from `delegate`
share the registry and logger but skip the prompt match.

**Log events (R5).**

| event | fields |
|---|---|
| `prompt` | time, session, source, prompt |
| `similarity_check` | time, session, source, method, threshold, scores (every skill), selected |
| `skill_executed` | time, session, skill, source, score, path |
| `skill_finished` | time, session, skill, tools used during the request, final answer |
| `skill_already_active` | time, session, skill, source (the model called `use_skill` for an active skill; it is told to continue) |

## Areas of concern <!-- each one has an owner -->

1. **A 4B model may not follow a skill's steps** (skip steps, pick other values, misquote
   numbers). A skill is advisory. Mitigation: where a step must hold, move it into the skill's
   script (deterministic) and check the result in `evals/`. Still open: in every real run the
   model skipped tune's step 4 (write `results/hyperparams-choice.md`), and some answers stop
   mid-sentence. Owner: Blaine.
2. **Bag-of-words matching misses synonyms** ("make it learn faster" scores 0 for `tune`).
   Mitigation: `use_skill` and the no-match hint; the log shows every miss. Owner: Andrew.
3. **Skills run shell commands.** They go through the same approval gate as every other tool;
   the demo uses `--approval auto` only on our own workspace. Owner: Andrew.

## Acceptance

Every requirement has tests in `tests/test_skills.py` (mapped in plan.md, Proof). All tests in
`tests/` pass, and the Lab 4 eval in `evals/` passes on a real Ollama run.
