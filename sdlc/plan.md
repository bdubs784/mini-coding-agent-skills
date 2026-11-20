# Plan: mini-coding-agent can use agent skills

Stage 3 (Build): how we implement [spec.md](spec.md), written before the code and updated in the
same commit whenever the build departs from it. Real-run results live in [../evals/](../evals/).

## Files that change

| File | Change |
|---|---|
| `mini_coding_agent.py` | Component 7: `parse_frontmatter`, `Skill`, `SkillRegistry`, `SkillLogger`; `MiniAgent` hooks in `ask()`, `prompt()`, `build_tools()` (`use_skill`), `run_shell` timeout; REPL `/skills`, `/skill`; CLI flags |
| `tests/test_skills.py` | new: one or more tests per requirement |
| `skills/pr-review/SKILL.md` | new: example skill |
| `demo/setup_lab4_demo.py`, `demo/replay_demo.py` | new: Lab 4 workspace with the Lab 5 skills, offline replay |
| `evals/` | new: the Lab 4 eval and its deterministic grader |

## Design decisions

| Decision | Why |
|---|---|
| Put the component in `mini_coding_agent.py` | The project is one file on purpose, so component 7 sits next to the other six. |
| Word-count cosine plus exact name match, not embeddings (R2) | No dependencies, instant, and the scores are easy to explain in the log. Names count twice because they are short and specific. |
| Threshold 0.2 (R2) | In our runs (`demo/logs/skills.log`) the skill that fit a prompt scored 0.51 or 1.0 and the pr-review example prompt scores 0.69; skills that did not fit scored at most 0.103. 0.2 sits in that gap. `--skill-threshold` changes it. |
| Skill catalog in the prefix, skill body only when active (R4) | The prefix stays the same between steps (cache reuse, component 2) and the small model only sees the steps it needs. |
| `use_skill` tool plus a no-match hint (R3) | Lets the model fix a missed word match. It goes through the same validation as the other tools (component 3). |
| Reuse the existing tools to execute steps (R4) | Skills get the same approval rules as everything else. |
| JSONL plus a text log (R5) | JSONL is easy to test and grade, the text log is easy to show in the video. |
| Skill `timeout:` frontmatter (R1) | The tune sweeps take about a minute, longer than the 20 second shell default. |
| Steps that must hold go in the skill's script (concern 1) | A skill is advisory. The demo setup makes `sweep_all.py` apply tune's step 3 rule and `render.py` list the differing cells, so the model copies facts instead of computing them. |

## Order of work

| # | Task | Requirements | Check | Status |
|---|---|---|---|---|
| 1 | Read the agent and map the six components | | notes in this file | done |
| 2 | `parse_frontmatter`, `Skill`, `SkillRegistry.discover` | R1 | discovery tests | done |
| 3 | `score`, `rank`, `select` with threshold | R2 | similarity tests | done |
| 4 | `SkillLogger` (jsonl + text) | R5 | log tests | done |
| 5 | Hook into `ask()`: log prompt, run check, activate | R2, R3, R5 | trigger tests | done |
| 6 | `use_skill` tool, validation, no-match hint | R3 | `use_skill` and hint tests | done |
| 7 | `/skill NAME`, `/skills`, CLI flags, welcome banner | R3, R6 | explicit and CLI tests | done |
| 8 | No skills = old behavior | R6 | off-switch test and the original tests | done |
| 9 | Example skill `skills/pr-review` | R1, R2 | "review my changes before I merge the PR" scores 0.69 | done |
| 10 | Lab 4 demo workspace from our Lab 4 and Lab 5 repos | R4 | Lab 5 tests pass inside it | done |
| 11 | Lab 4 eval and grader | R2-R5 | `tests/test_evals.py` | done |
| 12 | Real Ollama run graded by the eval, logs saved to `demo/logs/` | R2-R5 | `evals/check_demo_log.py` passes | done |
| 13 | README and video | | | README done, video pending |

## Risks

- A 4B model may skip steps, pick its own values, or misquote numbers (spec concern 1).
  Mitigation: facts the answer depends on are computed by scripts, and the eval checks the answer
  against them. The history of what went wrong per run is in `evals/README.md`.
- Bag-of-words matching misses synonyms (spec concern 2). Mitigation: `use_skill` and the
  no-match hint. The model may still not call it; the eval records this as INFO, not a failure.
- A skill script can run longer than its `timeout:`. All four sweeps take about a minute on our
  laptops against tune's 300 seconds.
- Windows: piped input can carry a BOM and child output may not be UTF-8. The REPL strips the BOM
  and `run_shell` decodes UTF-8.

## Proof <!-- the tests that prove it is done -->

| Requirement | Tests (`tests/test_skills.py` unless noted) |
|---|---|
| R1 | `test_parse_frontmatter_reads_name_and_body`, `test_discover_finds_skill_folders`, `test_discover_also_scans_claude_skills_folder`, `test_discover_scans_singular_skill_folder`, `test_discover_reads_lowercase_skill_md`, `test_skill_timeout_sets_default_shell_timeout` |
| R2 | `test_similarity_picks_matching_skill_and_skips_unrelated_prompt`, `test_manual_only_skill_is_never_auto_selected`, `test_unrelated_prompt_logs_check_but_runs_no_skill` |
| R3 | `test_model_can_load_skill_mid_execution`, `test_no_match_hint_lists_model_skills_until_one_is_loaded`, `test_matched_prompt_gets_no_hint`, `test_use_skill_rejects_unknown_and_manual_only`, `test_explicit_slash_skill_runs_manual_only_skill`, `test_use_skill_on_active_skill_is_logged_and_redirected` |
| R4 | `test_prompt_triggers_skill_injects_instructions_and_logs`, `test_skill_catalog_and_tool_are_in_prompt_and_welcome`, `test_shell_timeout_returns_hint_instead_of_crashing` |
| R5 | `test_prompt_triggers_skill_injects_instructions_and_logs` (both log files), `tests/test_evals.py` |
| R6 | `test_no_skills_means_no_tool_no_log`, `test_cli_flags_parse`, all of `tests/test_mini_coding_agent.py` |

```
python -m pytest -q                              # all tests pass
python -m ruff check .
python evals/check_demo_log.py tmp/lab4-demo     # after a real run: 0 failed
```
