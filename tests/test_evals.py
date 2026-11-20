import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_demo_log", Path(__file__).resolve().parents[1] / "evals" / "check_demo_log.py"
)
check_demo_log = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_demo_log)

PICKED = ["- gamma = 0.9: success 100%, VI match 90%, 7.7 steps"]


def turn(prompt, selected=None, source="user prompt", result="done"):
    events = [
        {"event": "prompt", "source": "user", "prompt": prompt},
        {"event": "similarity_check", "selected": selected},
    ]
    if selected:
        events.append({"event": "skill_executed", "skill": selected, "source": source})
        events.append({"event": "skill_finished", "skill": selected, "result": result})
    return events


def good_log():
    return (
        turn("tune", "tune", result="\n".join(PICKED))
        + turn("solve lab 4", "render-policy")
        + turn("list files")
        + turn("charger")
        + turn("submit", "submit-check", source="explicit /skill")
    )


def test_good_run_passes():
    results = check_demo_log.grade(good_log(), PICKED)
    assert [status for status, _ in results if status == "FAIL"] == []


def test_misquoted_tune_answer_fails():
    events = good_log()
    events[3]["result"] = "gamma = 0.7"
    failed = [name for status, name in check_demo_log.grade(events, PICKED) if status == "FAIL"]
    assert failed == ["tune answer copies the picked values from results/hyperparams.md"]


def test_tool_call_as_final_answer_fails():
    events = good_log()
    events[-1]["result"] = 'I will run it again. [tool:run_shell] {"command": "python check.py"}'
    failed = [name for status, name in check_demo_log.grade(events, PICKED) if status == "FAIL"]
    assert failed == ["every skill ends with a real answer, not a tool call (not answered: submit-check)"]


def test_skill_on_unrelated_prompt_fails():
    events = good_log()
    unrelated = turn("list files", "tune")
    events = events[:8] + unrelated + events[10:]
    failed = [name for status, name in check_demo_log.grade(events, PICKED) if status == "FAIL"]
    assert "unrelated prompt selects no skill" in failed
