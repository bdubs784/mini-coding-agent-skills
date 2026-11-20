# Evals (stage 4, Test)

One eval = one real task plus checks. `lab4-demo.json` is ours: five prompts that solve Lab 4 with
the Lab 5 skills, and checks that cite the requirements in [../sdlc/spec.md](../sdlc/spec.md).
`check_demo_log.py` grades a run from its `skills.jsonl` with plain code (no model), and
`tests/test_evals.py` tests the grader.

```
python evals/check_demo_log.py tmp/lab4-demo           # a fresh run
python evals/check_demo_log.py demo/logs --flat        # the saved run: 7 passed, 0 failed
```

The use_skill check is INFO, not PASS/FAIL: whether a 4B model notices it needs a skill varies
from run to run, and the log records what it did either way.

## Run history

Every run used qwen3.5:4b through Ollama on our laptops. Each row is what went wrong and what we
changed before the next run. Runs 1 to 5 were graded by reading the logs; runs 6 to 12 by the grader.

| Run | What happened | What we changed |
|---|---|---|
| 1 | The model called `use_skill` again for `tune`, which was already active, and ran out of its 12 steps. | Log it as `skill_already_active` and tell the model to continue. |
| 2 | All four sweeps ran, but the model tried to retype the four tables and ran out of output tokens before writing the file. | `sweep.py --out` saves each table itself; limits raised to `--max-steps 20 --max-new-tokens 2048`. |
| 3 | The model ran the living_cost sweep twice, skipped epsilon, and still reported an epsilon value. | `sweep_all.py` runs all four sweeps in one command. |
| 4 | `sweep_all.py` took longer than the 20 second `run_shell` timeout; the model kept adding `--timeout 120` to the command instead of the tool argument. | Skill `timeout:` frontmatter (tune uses 300), the exact tool call in the skill, and a timeout hint instead of a bare error. |
| 5 | Both skills ran, but the model broke step 3's selection rule for all four parameters (chose living_cost -0.4, gamma 0.7, alpha 0.3, epsilon 0.2 although other values had a higher success %), quoted numbers not in the tables (epsilon 0.2 "matches VI at 95%", the table says 72%), and skipped step 4's `write_file`. Only two prompts were run. | `sweep_all.py` applies the step 3 rule itself and prints "Values picked by the step 3 rule"; step 3 and step 5 tell the model to copy those lines. Added this eval with five prompts. |
| 6 | Right values, but the return and VI numbers were still invented: `sweep_all.py` printed all four tables first, and the agent clips tool output at 4000 characters, so the picked values at the end were cut off. A byte order mark from the piped input was in the first logged prompt, and "±" came through garbled. submit-check said it had "already been executed". | `sweep_all.py` prints only a short summary and the picked values. `run_shell` decodes UTF-8. The active-skill text no longer says "already loaded". |
| 7 | tune exact. submit-check answered "I cannot directly execute external skills" and used no tools. The BOM was still in the first prompt. | The `/skill NAME` default task says to do the skill's steps. The REPL strips the BOM from input. |
| 8 | render-policy named cells that do not differ. submit-check re-ran `check.py` in a loop and started "fixing" the workspace. | `render.py` prints "Cells where learned and value iteration differ"; submit-check's steps say run `check.py` once and answer. |
| 9 | All required checks passed, but in four runs the charger prompt (scores 0.0 for every skill) never led to `use_skill`. | When no skill is selected, the prompt lists the skills once more and reminds the model it can call `use_skill`. |
| 10 | First `use_skill` load: the charger prompt loaded `tune`. But submit-check re-ran `check.py` and ended with a tool call instead of an answer; the grader still passed it. | The `/skill` default task no longer says "using your tools". The grader fails a skill whose final answer is a tool call. |
| 11 | 7 passed, 0 failed. The charger prompt did not call `use_skill` this time. | Nothing; reran to see whether `use_skill` would repeat. |
| 12 | 7 passed, 0 failed, and the charger prompt loaded `tune` with `use_skill`. | This is the run saved in `demo/logs/`. |

Known gaps in run 12 that the grader does not check:

- Neither tune run wrote `results/hyperparams-choice.md` (step 4). No real run has done this
  step; the values and reasons are in the final answers instead.
- Two answers end mid-sentence (the second tune answer and submit-check). The model stopped on
  its own: `think` is off, there is no stop sequence, and the answers are far under 2048 tokens.
- The use_skill tune answer calls living_cost a penalty "for staying at the current cell"; it is
  a per-step cost.
- render-policy's cell and Q-value claims come from `render.py` output, which the skills log
  does not store (the session file in `tmp/lab4-demo/.mini-coding-agent/sessions/` does).

What the history shows: a skill is advisory. Each time the model got a step wrong, the fix that
held was to move that step into the skill's script (so the model copies a fact instead of
computing it) or into the agent's code, and to check it here.
