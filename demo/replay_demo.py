"""Offline check of the Lab 4 demo without Ollama.

Runs the real MiniAgent (real tools, real skills, real log files) in the demo workspace,
but the model's replies come from a fixed script (FakeModelClient). Use it to check the
setup and the log format before the real run, or when Ollama is not available. The video
should show the real run with Ollama; this is only a fallback and a smoke test.

Usage:
    python demo/replay_demo.py --cwd tmp/lab4-demo
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mini_coding_agent import FakeModelClient, MiniAgent, SessionStore, WorkspaceContext  # noqa: E402

PROMPT_1 = "Tune the hyperparameters for the vacuum Q-learner: choose gamma, alpha, epsilon and the living reward."
SCRIPT_1 = [
    '<tool>{"name":"list_files","args":{"path":"src"}}</tool>',
    '<tool>{"name":"run_shell","args":{"command":"python skills/tune/sweep.py --param gamma --values 0.5 0.7 0.9 0.99","timeout":120}}</tool>',
    "<final>Ran the gamma sweep from the tune skill. See the table above for success %, steps and VI match.</final>",
]

PROMPT_2 = "Solve Lab 4: train the vacuum Q-learning agent and show the learned policy and how it compares to value iteration."
SCRIPT_2 = [
    '<tool>{"name":"run_shell","args":{"command":"python skills/render-policy/render.py --living-cost -0.04 --episodes 2000 --seed 0","timeout":120}}</tool>',
    "<final>Trained for 2000 episodes and printed the learned policy next to the value-iteration policy.</final>",
]

PROMPT_3 = "The robot should get to the charger more reliably, figure out what to change."
SCRIPT_3 = [
    '<tool>{"name":"use_skill","args":{"name":"tune","reason":"choosing epsilon and alpha for the Q-learner"}}</tool>',
    '<tool>{"name":"run_shell","args":{"command":"python skills/tune/sweep.py --param epsilon --values 0.2 0.5 0.8","timeout":120}}</tool>',
    "<final>Loaded the tune skill mid-task and swept epsilon.</final>",
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cwd", default="tmp/lab4-demo")
    args = parser.parse_args(argv)
    workspace = WorkspaceContext.build(args.cwd)
    store = SessionStore(Path(workspace.repo_root) / ".mini-coding-agent" / "sessions")
    agent = MiniAgent(
        model_client=FakeModelClient(SCRIPT_1 + SCRIPT_2 + SCRIPT_3),
        workspace=workspace,
        session_store=store,
        approval_policy="auto",
        max_steps=8,
    )
    for prompt in (PROMPT_1, PROMPT_2, PROMPT_3):
        print(f"\n>>> {prompt}")
        print(agent.ask(prompt))
        last_tool = [item for item in agent.session["history"] if item["role"] == "tool"][-1]
        print(last_tool["content"][:1200])
    print(f"\nskill log: {agent.skill_logger.text_path}")
    print(agent.skill_logger.text_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
