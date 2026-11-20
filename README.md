&nbsp;
# Mini-Coding-Agent + Agent Skills (CS440 Group 23)

**Group 23:** Andrew Barnett, Blaine Watkins

This is a copy of [rasbt/mini-coding-agent](https://github.com/rasbt/mini-coding-agent) with a
seventh component added: **Agent Skills**. The agent finds skill folders such as
`skills/pr-review/SKILL.md`, runs a similarity check between each prompt and every skill, and
executes the matching skill's instructions. It can also load a skill in the middle of a task
with a `use_skill` tool. Every prompt, similarity check, and executed skill is logged to
`.mini-coding-agent/logs/`. We used it with our Lab 5 skills to finish Lab 4.

Quick links: [What we added](#agent-skills-what-we-added) ·
[Run the Lab 4 demo](#run-the-lab-4-demo) · SDLC: [intent](sdlc/intent.md) ·
[spec](sdlc/spec.md) · [plan](sdlc/plan.md) · [evals](evals/README.md)

&nbsp;
## Agent Skills: what we added

### Project structure

```
mini-coding-agent/
├── mini_coding_agent.py      # the agent; component 7 = Skill, SkillRegistry, SkillLogger,
│                             #   MiniAgent.match_skills / activate_skill / tool_use_skill
├── skills/
│   └── pr-review/SKILL.md    # example skill (folder skill format)
├── sdlc/                     # AI-native SDLC stages, as in the lecture
│   ├── intent.md             #   1. Plan: problem, outcome, users, constraints, open questions
│   ├── spec.md               #   2. Design: numbered requirements R1-R6, design, concerns + owners
│   └── plan.md               #   3. Build: files, decisions, order of work, risks, proof (tests per R)
├── evals/                    #   4. Test: the Lab 4 eval, its grader, and the history of real runs
│   ├── lab4-demo.json        #      prompts + checks (cites R numbers)
│   ├── check_demo_log.py     #      deterministic grader for a run's skills.jsonl
│   └── README.md             #      what each real run got wrong and what we changed
├── demo/
│   ├── setup_lab4_demo.py    # builds the Lab 4 workspace with our Lab 5 skills in skills/
│   ├── replay_demo.py        # offline run of the demo with scripted model replies (no Ollama)
│   └── logs/                 # log files copied from our real Ollama run
├── tests/
│   ├── test_mini_coding_agent.py   # original tests (unchanged)
│   ├── test_skills.py              # tests for the skills component
│   └── test_evals.py               # tests for the eval grader
├── group_23.txt              # repository links for the submission
├── EXAMPLE.md                # original usage example
└── README.md
```

### How it works

1. **Discovery.** At start the agent loads every `<folder>/<skill>/SKILL.md` (or `skill.md`) under `skills/`,
   `skill/`, `.agents/skills/`, and `.claude/skills/` in the workspace (plus any `--skills-dir`).
   The frontmatter gives `name`, `description`, and optionally `disable-model-invocation: true`.
2. **Similarity check.** For each prompt, every skill gets a score: 1.0 if the skill name is in
   the prompt, otherwise cosine similarity of word counts between the prompt and the skill's
   name plus description. The best skill runs if it scores at least the threshold (0.2).
3. **Execution.** The active skill's steps are added to the prompt as an `Active skill` section,
   and the model carries them out with the normal tools (same approval rules).
4. **Mid-task.** The model can call `use_skill(name, reason)` when it realizes it needs a skill.
   When the word match picks nothing, the prompt lists the skills once more and reminds the model
   it can call `use_skill`. The user can force a skill with `/skill NAME` or `/NAME`.
5. **Logs.** `.mini-coding-agent/logs/skills.log` (readable) and `skills.jsonl` (one JSON per
   event): `prompt`, `similarity_check` (all scores, threshold, selected), `skill_executed`
   (skill, trigger, score, file), `skill_finished` (tools used, final answer).

Example `skills.log`, lines from our real Ollama run in [demo/logs/](demo/logs/) (paths shortened):

```
[2026-11-18 14:37:21] PROMPT (user): Tune the hyperparameters for the vacuum Q-learner and report the values you picked
[2026-11-18 14:37:21] SIMILARITY (user prompt) threshold=0.2 scores: tune=1.000, render-policy=0.103 -> selected: tune
[2026-11-18 14:37:21] EXECUTED skill=tune via=user prompt score=1.0 file=...\tmp\lab4-demo\skills\tune\SKILL.md
[2026-11-18 14:37:59] FINISHED skill=tune tools=[run_shell] result: - living_cost = -0.04: success 100%, VI match 90%, 7.7 steps - gamma...ite old estimates, and epsilon balances exploration and exploitation.
[2026-11-18 14:38:08] PROMPT (user): List the files in src
[2026-11-18 14:38:08] SIMILARITY (user prompt) threshold=0.2 scores: render-policy=0.000, tune=0.000 -> selected: none
[2026-11-18 14:38:14] PROMPT (user): The robot should get to the charger more reliably, figure out what to change
[2026-11-18 14:38:14] SIMILARITY (user prompt) threshold=0.2 scores: render-policy=0.000, tune=0.000 -> selected: none
[2026-11-18 14:38:17] PROMPT (use_skill tool): The user wants to improve reliability by tuning hyperparameters. The skill 'tune' handles hyperparameter sweeps for the vacuum Q-learner.
[2026-11-18 14:38:17] SIMILARITY (use_skill tool) threshold=0.2 scores: tune=1.000, render-policy=0.032 -> selected: tune
[2026-11-18 14:38:17] EXECUTED skill=tune via=use_skill tool score=1.0 file=...\tmp\lab4-demo\skills\tune\SKILL.md
```

New flags: `--skills-dir PATH` (repeatable), `--skill-threshold 0.2`, `--no-skills`.
New REPL commands: `/skills` (list skills and log path), `/skill NAME [task]`.

&nbsp;
## Run the Lab 4 demo

Lab 4 set up the vacuum Q-learning problem for a coding agent. Lab 5 solved it with Claude Code
and added the skills `tune`, `render-policy`, and `submit-check`. The demo workspace is our Lab 4
repo plus the Lab 5 `src/` code (our Q-learning solution, copied in, not rewritten by the agent)
and the Lab 5 skills moved to `skills/`. The setup fixes paths and adapts the skills for a 4B
model: `tune` gets one `sweep_all.py` command that runs all four sweeps, saves the tables, and
applies the skill's step 3 selection rule, plus `timeout: 300`; `render.py` also prints the cells
where the learned policy and value iteration differ; `submit-check` runs its script once and
answers. Each change fixed a failure in a real run (see `evals/README.md`). Pass
`--original-skills` to get the Lab 5 skills with path fixes only.

Needs Python 3.10+, numpy (`pip install numpy`), and Ollama with a model pulled (`ollama pull qwen3.5:4b`).

```bash
# 1. build the workspace (paths to your clones of our Lab 4 and Lab 5 repos)
python demo/setup_lab4_demo.py --lab4 ../vacuum-rl-context-engineering --lab5 ../vacuum-rl-context-engineering-lab5 --out tmp/lab4-demo

# 2. optional: offline check without Ollama
python demo/replay_demo.py --cwd tmp/lab4-demo

# 3. real run with Ollama
python mini_coding_agent.py --cwd tmp/lab4-demo --approval auto --max-steps 20 --max-new-tokens 2048

# 4. grade the run (stage 4, evals/): prints PASS/FAIL per check
python evals/check_demo_log.py tmp/lab4-demo
```

To feed the prompts below without typing them, put one per line in `prompts.txt` (ending with
`/exit`) and run `Get-Content prompts.txt | python mini_coding_agent.py --cwd tmp/lab4-demo ...`
in PowerShell.

Prompts we use in the REPL:

```
/skills
Tune the hyperparameters for the vacuum Q-learner and report the values you picked
Solve Lab 4: train the vacuum Q-learning agent and show the learned policy compared to value iteration
List the files in src
The robot should get to the charger more reliably, figure out what to change
/skill submit-check
```

`List the files in src` shows a similarity check with no skill selected. The charger prompt shares
few words with any skill, so the model may load `tune` itself with the `use_skill` tool.

Then open `tmp/lab4-demo/.mini-coding-agent/logs/skills.log`.

Tests: `python -m pytest -q`

The rest of this README is the original project's documentation.

&nbsp;
# Original README

## Mini-Coding-Agent

This folder contains a small standalone coding agent:

- code: `mini_coding_agent.py`
- CLI: `mini-coding-agent`

It is a minimal local agent loop with:

- workspace snapshot collection
- stable prompt plus turn state
- structured tools
- approval handling for risky tools
- transcript and memory persistence
- bounded delegation

The model backend is currently based on Ollama.

<a href="https://magazine.sebastianraschka.com/p/components-of-a-coding-agent">
  <img src="https://substack-post-media.s3.amazonaws.com/public/images/49b97718-57f4-4977-99c8-8ad5c4d32af3_1548x862.png" width="500px">
</a>

<br>

**[The detailed tutorial: Components of a Coding Agent](https://magazine.sebastianraschka.com/p/components-of-a-coding-agent)**


&nbsp;
## Six Core Components

<a href="https://magazine.sebastianraschka.com/p/components-of-a-coding-agent">
  <img alt="Six core components of a coding agent" src="https://sebastianraschka.com/images/github/mini-coding-agent/six-components.webp" width="500px">
</a>

This coding harness is organized around six practical building blocks:

1. **Live repo context**  
   The agent collects stable workspace facts upfront, such as repo layout, instructions, and git state.
2. **Prompt shape and cache reuse**  
   A stable prompt prefix, which is separate from the changing request, transcript, and memory so repeated model calls can reuse the static parts efficiently.
3. **Structured tools, validation, and permissions**  
   The model works through named tools with checked inputs, workspace path validation, and approval gates instead of free-form arbitrary actions.
4. **Context reduction and output management**  
   Long outputs are clipped, repeated reads are deduplicated, and older transcript entries are compressed to keep prompt size under control.
5. **Transcripts, memory, and resumption**  
   The runtime keeps both a full durable transcript and a smaller working memory so sessions can be resumed while preserving important state via working memory.
6. **Delegation and bounded subagents**  
   Scoped subtasks can be delegated to helper agents that inherit enough context to help (but operate within limits).

&nbsp;
## Requirements

You need:

- Python 3.10+
- Ollama installed
- an Ollama model pulled locally

Optional:

- `uv` for environment management and the `mini-coding-agent` CLI entry point

This project has no Python runtime dependency beyond the standard library, so you can run it directly with `python mini_coding_agent.py` if you do not want to use `uv`.

&nbsp;
## Install Ollama

Install Ollama on your machine so the `ollama` command is available in your shell.

Official installation link: [ollama.com/download](https://ollama.com/download)

Then verify:

```bash
ollama --help
```

Start the server:

```bash
ollama serve
```

In another terminal, pull a model. Example:

```bash
ollama pull qwen3.5:4b
```

Qwen 3.5 model library:

- [ollama.com/library/qwen3.5](https://ollama.com/library/qwen3.5)

The default in this project is `qwen3.5:4b`. If you have sufficient memory, it is worth trying a larger model such as `qwen3.5:9b` or another larger Qwen 3.5 variant. The agent just sends prompts to Ollama's `/api/generate` endpoint.

&nbsp;
## Project Setup

Clone the repo or your fork and change into it:

```bash
git clone https://github.com/rasbt/mini-coding-agent.git
cd mini-coding-agent
```

If you forked it first, use your fork URL instead:

```bash
git clone https://github.com/<your-github-user>/mini-coding-agent.git
cd mini-coding-agent
```



&nbsp;
## Basic Usage

Start the agent:

```bash
cd mini-coding-agent
uv run mini-coding-agent
```

Without `uv`, run the script directly:

```bash
cd mini-coding-agent
python mini_coding_agent.py
```

By default it uses:

- model: `qwen3.5:4b`
- approval: `ask`

For a concrete usage example, see [EXAMPLE.md](EXAMPLE.md).

&nbsp;
## Approval Modes

Risky tools such as shell commands and file writes are gated by approval.

- `--approval ask`
  prompts before risky actions (default and recommended)
- `--approval auto`
  allows risky actions automatically, including arbitrary command execution and file writes by the model; use only with trusted prompts and trusted repositories
- `--approval never`
  denies risky actions

Example:

```bash
uv run mini-coding-agent --approval auto
```



&nbsp;
## Resume Sessions

The agent saves sessions under the target workspace root in:

```text
.mini-coding-agent/sessions/
```

Resume the latest session:

```bash
uv run mini-coding-agent --resume latest
```


Resume a specific session:

```bash
uv run mini-coding-agent --resume 20260401-144025-2dd0aa
```


&nbsp;
## Interactive Commands

Inside the REPL, slash commands are handled directly by the agent instead of
being sent to the model as a normal task.

- `/help`
  shows the list of available interactive commands
- `/memory`
  prints the distilled session memory, including the current task, tracked files, and notes
- `/session`
  prints the path to the current saved session JSON file
- `/skills`
  lists the discovered agent skills, the similarity threshold, and the skill log path
- `/skill NAME [task]`
  runs a skill directly without the similarity check (also works for manual-only skills)
- `/reset`
  clears the current session history and distilled memory but keeps you in the REPL
- `/exit`
  exits the interactive session
- `/quit`
  exits the interactive session; alias for `/exit`

&nbsp;
## Main CLI Flags

```bash
uv run mini-coding-agent --help
```

Without `uv`:

```bash
python mini_coding_agent.py --help
```

CLI flags are passed before the agent starts. Use them to choose the workspace,
model connection, resume behavior, approval mode, and generation limits.

Important flags:

- `--cwd`
  sets the workspace directory the agent should inspect and modify; default: `.`
- `--model`
  selects the Ollama model name, such as `qwen3.5:4b`; default: `qwen3.5:4b`
- `--host`
  points the agent at the Ollama server URL (usually not needed); default: `http://127.0.0.1:11434`
- `--ollama-timeout`
  controls how long the client waits for an Ollama response (usually not needed); default: `300` seconds
- `--resume`
  resumes a saved session by id or uses `latest`; default: start a new session
- `--approval`
  controls how risky tools are handled: `ask`, `auto`, or `never`; default: `ask`
- `--max-steps`
  limits how many model and tool turns are allowed for one user request; default: `6`
- `--max-new-tokens`
  caps the model output length for each step; default: `512`
- `--temperature`
  controls sampling randomness; default: `0.2`
- `--top-p`
  controls nucleus sampling for generation; default: `0.9`
- `--skills-dir`
  adds a folder of skills to scan (repeatable); `skills/`, `skill/`, `.agents/skills/`, `.claude/skills/` are always scanned
- `--skill-threshold`
  minimum similarity score for a prompt to trigger a skill; default: `0.2`
- `--no-skills`
  turns the agent skills component off

&nbsp;
## Example

See [EXAMPLE.md](EXAMPLE.md)

&nbsp;
## Notes & Tips

- The agent expects the model to emit either `<tool>...</tool>` or `<final>...</final>`.
- Different Ollama models will follow those instructions with different reliability.
- If the model does not follow the format well, use a stronger instruction-following model.
- The agent is intentionally small and optimized for readability, not robustness.
