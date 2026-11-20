# Intent: mini-coding-agent can use agent skills

Author: Group 23 (Andrew Barnett, Blaine Watkins). Status: accepted.

Stage 1 (Plan) of our AI-native SDLC: the problem in our own words, before any design.
Next stages: [spec.md](spec.md) (Design), [plan.md](plan.md) (Build), [../evals/](../evals/) (Test).

## Problem <!-- what can't be done today -->

mini-coding-agent has six components (repo context, prompt shape, tools, context reduction,
session memory, delegation) but no way to reuse a procedure. Every time we want it to do
something with fixed steps, like sweeping hyperparameters, we have to type the whole procedure
into the prompt. Claude Code solves this with agent skills: a folder with a `SKILL.md` file that
loads only when the task needs it. In Lab 5 we wrote three skills for Claude Code (`tune`,
`render-policy`, `submit-check`), and mini-coding-agent cannot use any of them.

## Proposed outcome <!-- what better looks like -->

A seventh component, Agent Skills, so the agent can:

1. Find skill folders in the workspace, for example `skills/pr-review/SKILL.md` or `skill/pr-review/skill.md`.
2. Decide on its own when a user prompt needs a skill, with a similarity check.
3. Load a skill in the middle of a task when it realizes it needs one.
4. Carry out (execute) the steps in the `SKILL.md` with its normal tools.
5. Log the prompt, the similarity check, and the executed skill to files we can show.

Then use our Lab 5 skills to finish Lab 4 (the vacuum Q-learning problem) with mini-coding-agent.

Success looks like: "tune the hyperparameters for the vacuum Q-learner" triggers `tune`, the agent
runs the sweep, and the log shows the prompt, every skill's score, and which skill ran; an
unrelated prompt runs no skill and the log shows why.

## Affected users and systems

- Us, running the agent on our laptops with Ollama and a small local model.
- The instructors, reading the logs and the code.
- `mini_coding_agent.py` (prompt building, tools, the REPL) and our Lab 4 and Lab 5 repos.

## Constraints <!-- non-negotiables -->

- Standard library only, like the rest of the project.
- With no skill folders the agent behaves exactly as before.
- A 4B local model (qwen3.5:4b) has to be able to use it: short skill text, simple tool calls.
- Read the same `SKILL.md` format Claude Code uses, so the Lab 5 skills work with only path fixes.
- Out of scope: embedding models or a vector database, installing skills from the internet,
  sub-agents inside a skill (our Lab 4 `implement-qlearning` skill needs Claude Code sub-agents,
  so the demo uses the Lab 5 skills).

## Open questions <!-- carried into spec.md -->

1. How should a prompt be matched to a skill without an embedding model? (Answered in spec R2.)
2. What happens when the words do not match but the task still needs a skill, e.g. "make it
   learn faster"? (Answered in spec R3: `use_skill` plus a no-match hint.)
3. Should a skill be allowed to change how tools behave, e.g. a longer shell timeout? (Spec R1.)
4. Can a 4B model follow a multi-step skill reliably? (Spec concern 1, tested in evals/.)
