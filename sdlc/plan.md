# Plan

Stage 3: how we build it, in what order, and how we check each step. Status is updated as we go.

## Design decisions

| Decision | Why |
|---|---|
| Put the component in `mini_coding_agent.py` as `Skill`, `SkillRegistry`, `SkillLogger` | The project is one file on purpose, so the new component sits next to the other six and is numbered 7 the same way. |
| Word count cosine plus exact name match, not embeddings | No dependencies, runs instantly, and the scores are easy to explain in the log. Names count twice because they are short and specific. |
| Threshold 0.2 | Our skill prompts scored 0.34 to 1.0 and unrelated prompts scored under 0.08, so 0.2 sits in the gap. It can be changed with `--skill-threshold`. |
| Skill catalog in the prefix, skill body only when active | The prefix stays the same between steps (cache reuse, component 2) and the small model only sees the full steps it needs. |
| `use_skill` tool for mid-task loading | Lets the model fix a missed match. It goes through the same validation as the other tools (component 3). |
| Reuse the existing tools to execute the steps | Skills get the same approval rules as everything else, so a skill cannot run a shell command the user did not allow. |
| JSONL plus a text log | JSONL is easy to test and parse, the text log is easy to show in the video. |
| Read Claude Code's `SKILL.md` format and `.claude/skills/` | Our Lab 5 skills load with no format changes. |

## Tasks

| # | Task | Check | Status |
|---|---|---|---|
| 1 | Read the agent and map the six components | notes in this file | done |
| 2 | `parse_frontmatter`, `Skill`, `SkillRegistry.discover` | `test_parse_frontmatter...`, `test_discover...` | done |
| 3 | `score`, `rank`, `select` with threshold | `test_similarity...`, `test_manual_only...` | done |
| 4 | `SkillLogger` (jsonl + text) | `test_prompt_triggers_skill...` checks both files | done |
| 5 | Hook into `ask()`: log prompt, run check, activate | `test_prompt_triggers...`, `test_unrelated_prompt...` | done |
| 6 | `use_skill` tool, validation, example | `test_model_can_load_skill_mid_execution`, `test_use_skill_rejects...` | done |
| 7 | Explicit `/skill NAME`, `/skills` in the REPL, CLI flags, welcome banner | `test_explicit_slash...`, `test_cli_flags_parse` | done |
| 8 | No skills = old behavior | `test_no_skills_means_no_tool_no_log` and the original 19 tests | done |
| 9 | Example skill `skills/pr-review` | prompt "review my changes before I merge the PR" scores 0.69 | done |
| 10 | Lab 4 demo workspace from our Lab 4 and Lab 5 repos | `demo/setup_lab4_demo.py`, Lab 5 tests pass inside it | done |
| 11 | Offline replay of the demo | `demo/replay_demo.py` writes all four event types | done |
| 12 | Real run with Ollama on our laptops, save logs to `demo/logs/` | log files committed | PLACEHOLDER |
| 13 | README, video | | PLACEHOLDER |

## Verification

```
python -m pytest -q        # 48 passed, 1 skipped
python -m ruff check .
python demo/replay_demo.py --cwd tmp/lab4-demo
```

## Risks

- A 4B model may ignore the skill steps or stop early. In our first real run with qwen3.5:4b the
  model called `use_skill` again for the skill that was already active and ran out of the 12
  steps. We now log that as `skill_already_active` and tell the model to continue. In the second
  run it did all four sweeps and picked good values, but it tried to retype all four tables into
  its answer and ran out of output tokens before writing the file. So the demo setup gives
  `sweep.py` an `--out` flag that saves each table itself, and the model only writes a short
  `results/hyperparams-choice.md`. We also raised the demo limits to `--max-steps 20` and
  `--max-new-tokens 2048`.
- The sweep script can take longer than the `run_shell` 120 second cap on a slow laptop. Each
  sweep takes about 3 seconds on our machine, so this is unlikely.
- Bag of words matching misses synonyms ("make it learn faster" scores 0 for `tune`). The
  `use_skill` tool covers this, and the log shows the miss.
