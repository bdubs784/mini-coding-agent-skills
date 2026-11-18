# Intent

Stage 1 of our SDLC for code agents: what we want and why, before any design.

**Group 23:** Andrew Barnett, Blaine Watkins

## Problem

mini-coding-agent has six components (repo context, prompt shape, tools, context reduction,
session memory, delegation) but no way to reuse a procedure. Every time we want it to do
something with fixed steps, like sweeping hyperparameters, we have to type the whole procedure
into the prompt. Claude Code solves this with agent skills: a folder with a `SKILL.md` file that
the agent loads only when it is needed. In Lab 5 we wrote three skills for Claude Code
(`tune`, `render-policy`, `submit-check`). We want mini-coding-agent to use the same kind of
skill.

## Goal

Add a seventh component, Agent Skills, so the agent can:

1. Find skill folders in the workspace, for example `skills/pr-review/SKILL.md`.
2. Decide on its own when a user prompt needs a skill, using a similarity check.
3. Load a skill in the middle of a task when it realizes it needs one.
4. Follow (execute) the steps in the `SKILL.md` with its normal tools.
5. Log the prompt, the similarity check, and the executed skill to files we can show.

Then use our Lab 5 skills to finish Lab 4 (the vacuum Q-learning problem) with mini-coding-agent.

## Users

- Us, running the agent on our laptops with Ollama.
- The instructors, reading the logs and the code.

## Success looks like

- A prompt like "tune the hyperparameters for the vacuum Q-learner" triggers `tune`, the agent
  runs the sweep script, and the log shows the prompt, every skill's score, and which skill ran.
- A prompt that has nothing to do with any skill runs no skill, and the log shows why (all
  scores under the threshold).
- The original agent behaves exactly the same when there are no skill folders.

## Constraints

- Keep the project's rule of no dependencies outside the Python standard library.
- Small local models (qwen3.5:4b) have to be able to use it, so the skill text has to be short
  and the tool call simple.
- Read the same `SKILL.md` format Claude Code uses, so our Lab 5 skills work with only path fixes.

## Out of scope

- Embedding models or a vector database for matching.
- Installing skills from the internet.
- Running sub-agents from inside a skill (our Lab 4 `implement-qlearning` skill needs Claude Code
  sub-agents, so the demo uses the Lab 5 skills instead).
