"""Grade a Lab 4 demo run from its skills log (the checks in evals/lab4-demo.json).

Deterministic, no model: reads <workspace>/.mini-coding-agent/logs/skills.jsonl and
<workspace>/results/hyperparams.md, prints PASS/FAIL/INFO per check, exits 1 if any check fails.

Usage:
    python evals/check_demo_log.py tmp/lab4-demo
    python evals/check_demo_log.py demo/logs --flat     # saved logs: skills.jsonl and hyperparams.md side by side
"""
import json
import sys
from pathlib import Path

PICKED_HEADER = "## Values picked by the step 3 rule"


def load(folder, flat):
    folder = Path(folder)
    log = folder / "skills.jsonl" if flat else folder / ".mini-coding-agent" / "logs" / "skills.jsonl"
    table = folder / "hyperparams.md" if flat else folder / "results" / "hyperparams.md"
    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    picked = []
    if table.is_file():
        text = table.read_text(encoding="utf-8")
        if PICKED_HEADER in text:
            picked = [line.strip() for line in text.split(PICKED_HEADER, 1)[1].splitlines() if line.startswith("- ")]
    return events, picked


def turns(events):
    """Split the log into one list of events per user prompt."""
    groups = []
    for event in events:
        if event["event"] == "prompt" and event.get("source") == "user":
            groups.append([])
        if groups:
            groups[-1].append(event)
    return groups


def executed(turn, skill, source=None):
    return any(e["event"] == "skill_executed" and e["skill"] == skill and (source is None or e["source"] == source)
               for e in turn)


def finished(turn, skill):
    return next((e for e in turn if e["event"] == "skill_finished" and e["skill"] == skill), None)


def grade(events, picked):
    results = []
    groups = turns(events)
    if len(groups) < 5:
        return [("FAIL", f"expected 5 user prompts in the log, found {len(groups)}")]
    tune, render, unrelated, charger, submit = groups[:5]

    results.append(("PASS" if executed(tune, "tune", "user prompt") else "FAIL", "tune triggered by the prompt"))
    done = finished(tune, "tune")
    copied = bool(picked) and done is not None and all(line in done["result"] for line in picked)
    results.append(("PASS" if copied else "FAIL",
                    "tune answer copies the picked values from results/hyperparams.md"
                    + ("" if picked else " (no picked values found)")))
    ok = executed(render, "render-policy", "user prompt") and finished(render, "render-policy")
    results.append(("PASS" if ok else "FAIL", "render-policy triggered by the prompt and finished"))
    check = next((e for e in unrelated if e["event"] == "similarity_check"), None)
    ok = check is not None and check["selected"] is None and not any(e["event"] == "skill_executed" for e in unrelated)
    results.append(("PASS" if ok else "FAIL", "unrelated prompt selects no skill"))
    loaded = [e["skill"] for e in charger if e["event"] == "skill_executed" and e["source"] == "use_skill tool"]
    results.append(("INFO", "charger prompt loaded " + (", ".join(loaded) + " with use_skill" if loaded
                                                         else "no skill (use_skill not called)")))
    ok = executed(submit, "submit-check", "explicit /skill") and finished(submit, "submit-check")
    results.append(("PASS" if ok else "FAIL", "submit-check runs through explicit /skill"))
    started = [(i, e["skill"]) for i, turn in enumerate(groups) for e in turn if e["event"] == "skill_executed"]
    missing = [skill for i, skill in started if not finished(groups[i], skill)]
    results.append(("PASS" if not missing else "FAIL",
                    "every executed skill has a FINISHED event" + (f" (missing: {', '.join(missing)})" if missing else "")))
    unanswered = [skill for i, skill in started if (done := finished(groups[i], skill)) and is_tool_call(done["result"])]
    results.append(("PASS" if not unanswered else "FAIL",
                    "every skill ends with a real answer, not a tool call"
                    + (f" (not answered: {', '.join(unanswered)})" if unanswered else "")))
    return results


def is_tool_call(text):
    """The model ran out of steps or wrote a tool call as its final answer."""
    return "[tool:" in text or "<tool>" in text or text.startswith("Stopped after")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    flat = "--flat" in args
    args = [arg for arg in args if arg != "--flat"]
    if len(args) != 1:
        print(__doc__)
        return 2
    results = grade(*load(args[0], flat))
    for status, name in results:
        print(f"{status:4}  {name}")
    failed = sum(status == "FAIL" for status, _ in results)
    print(f"\n{sum(status == 'PASS' for status, _ in results)} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
