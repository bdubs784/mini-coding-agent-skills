import json

from mini_coding_agent import (
    FakeModelClient,
    MiniAgent,
    SessionStore,
    SkillRegistry,
    WorkspaceContext,
    build_arg_parser,
    build_welcome,
    parse_frontmatter,
)

PR_REVIEW = """---
name: pr-review
description: Review a pull request or a git diff for bugs, missing tests, and style problems.
---
# PR review
1. Run `git diff` and read every changed file.
2. List bugs first, then missing tests, then style.
"""

TUNE = """---
name: tune
description: Hyperparameter sweep for the vacuum Q-learner. Use when choosing gamma, alpha, or epsilon.
---
# Tune
Run `python {skill_dir}/sweep.py --param gamma --values 0.5 0.9`.
"""

SUBMIT = """---
name: submit-check
description: Check the submission deliverables before turning in.
disable-model-invocation: true
---
Run the checklist.
"""


def make_repo(tmp_path, skills_folder="skills"):
    (tmp_path / "README.md").write_text("demo\n", encoding="utf-8")
    for name, text in (("pr-review", PR_REVIEW), ("tune", TUNE), ("submit-check", SUBMIT)):
        folder = tmp_path / skills_folder / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(text, encoding="utf-8")
    return tmp_path


def make_agent(tmp_path, outputs, **kwargs):
    workspace = WorkspaceContext.build(tmp_path)
    store = SessionStore(tmp_path / ".mini-coding-agent" / "sessions")
    return MiniAgent(
        model_client=FakeModelClient(outputs),
        workspace=workspace,
        session_store=store,
        approval_policy="auto",
        **kwargs,
    )


def read_log(tmp_path):
    path = tmp_path / ".mini-coding-agent" / "logs" / "skills.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_parse_frontmatter_reads_name_and_body():
    meta, body = parse_frontmatter(PR_REVIEW)
    assert meta["name"] == "pr-review"
    assert meta["description"].startswith("Review a pull request")
    assert body.startswith("# PR review")


def test_discover_finds_skill_folders(tmp_path):
    make_repo(tmp_path)
    registry = SkillRegistry.discover([tmp_path])
    assert sorted(registry.skills) == ["pr-review", "submit-check", "tune"]
    assert registry.get("submit-check").model_invocable is False


def test_discover_also_scans_claude_skills_folder(tmp_path):
    make_repo(tmp_path, skills_folder=".claude/skills")
    assert "tune" in SkillRegistry.discover([tmp_path]).skills


def test_similarity_picks_matching_skill_and_skips_unrelated_prompt(tmp_path):
    registry = SkillRegistry.discover([make_repo(tmp_path)])
    skill, ranking = registry.select("Please review my pull request diff for bugs")
    assert skill.name == "pr-review"
    assert ranking[0]["score"] >= registry.threshold
    skill, ranking = registry.select("write a binary search function")
    assert skill is None
    assert all(item["score"] < registry.threshold for item in ranking)


def test_manual_only_skill_is_never_auto_selected(tmp_path):
    registry = SkillRegistry.discover([make_repo(tmp_path)])
    skill, ranking = registry.select("check the submission deliverables before turning in")
    assert skill is None or skill.name != "submit-check"
    assert "submit-check" not in [item["skill"] for item in ranking]


def test_prompt_triggers_skill_injects_instructions_and_logs(tmp_path):
    make_repo(tmp_path)
    agent = make_agent(tmp_path, ["<final>Reviewed.</final>"])

    answer = agent.ask("Review the pull request diff for bugs")

    assert answer == "Reviewed."
    prompt = agent.model_client.prompts[0]
    assert "Active skill: pr-review" in prompt
    assert "List bugs first" in prompt
    events = read_log(tmp_path)
    assert [e["event"] for e in events] == ["prompt", "similarity_check", "skill_executed", "skill_finished"]
    assert events[0]["prompt"] == "Review the pull request diff for bugs"
    assert events[1]["selected"] == "pr-review"
    assert events[2]["skill"] == "pr-review" and events[2]["source"] == "user prompt"
    text_log = (tmp_path / ".mini-coding-agent" / "logs" / "skills.log").read_text(encoding="utf-8")
    assert "PROMPT" in text_log and "SIMILARITY" in text_log and "EXECUTED skill=pr-review" in text_log


def test_unrelated_prompt_logs_check_but_runs_no_skill(tmp_path):
    make_repo(tmp_path)
    agent = make_agent(tmp_path, ["<final>Done.</final>"])
    agent.ask("write a binary search function")
    events = read_log(tmp_path)
    assert [e["event"] for e in events] == ["prompt", "similarity_check"]
    assert events[1]["selected"] is None
    assert "Active skill: " not in agent.model_client.prompts[0]


def test_model_can_load_skill_mid_execution(tmp_path):
    make_repo(tmp_path)
    agent = make_agent(
        tmp_path,
        [
            '<tool>{"name":"use_skill","args":{"name":"tune","reason":"need to choose gamma"}}</tool>',
            "<final>Tuned.</final>",
        ],
    )

    answer = agent.ask("make the robot learn faster")

    assert answer == "Tuned."
    tool_item = next(item for item in agent.session["history"] if item["role"] == "tool")
    assert tool_item["name"] == "use_skill"
    assert "Active skill: tune" in tool_item["content"]
    assert (tmp_path / "skills" / "tune").as_posix() in tool_item["content"]  # {skill_dir} filled in
    assert "Active skill: tune" in agent.model_client.prompts[1]
    executed = [e for e in read_log(tmp_path) if e["event"] == "skill_executed"]
    assert executed[0]["skill"] == "tune" and executed[0]["source"] == "use_skill tool"


def test_use_skill_rejects_unknown_and_manual_only(tmp_path):
    make_repo(tmp_path)
    agent = make_agent(tmp_path, [])
    assert agent.run_tool("use_skill", {"name": "nope"}).startswith("error: unknown skill")
    assert "only be started by the user" in agent.run_tool("use_skill", {"name": "submit-check"})
    assert agent.run_tool("use_skill", {}).startswith("error: invalid arguments")


def test_explicit_slash_skill_runs_manual_only_skill(tmp_path):
    make_repo(tmp_path)
    agent = make_agent(tmp_path, ["<final>Checked.</final>"])
    agent.ask("/submit-check")
    assert "Active skill: submit-check" in agent.model_client.prompts[0]
    executed = [e for e in read_log(tmp_path) if e["event"] == "skill_executed"]
    assert executed[0]["source"] == "explicit /skill"


def test_no_skills_means_no_tool_no_log(tmp_path):
    (tmp_path / "README.md").write_text("demo\n", encoding="utf-8")
    agent = make_agent(tmp_path, ["<final>ok</final>"])
    assert "use_skill" not in agent.tools
    agent.ask("review the pull request")
    assert not (tmp_path / ".mini-coding-agent" / "logs").exists()


def test_skill_catalog_and_tool_are_in_prompt_and_welcome(tmp_path):
    make_repo(tmp_path)
    agent = make_agent(tmp_path, [])
    assert "Available agent skills:" in agent.prefix
    assert "- tune: Hyperparameter sweep" in agent.prefix
    assert "use_skill(" in agent.prefix
    assert "pr-review" in build_welcome(agent, model="m", host="h")


def test_cli_flags_parse():
    args = build_arg_parser().parse_args(["--skills-dir", "x", "--skill-threshold", "0.3", "--no-skills"])
    assert args.skills_dir == ["x"] and args.skill_threshold == 0.3 and args.no_skills


def test_use_skill_on_active_skill_is_logged_and_redirected(tmp_path):
    make_repo(tmp_path)
    agent = make_agent(
        tmp_path,
        [
            '<tool>{"name":"use_skill","args":{"name":"tune","reason":"tune it"}}</tool>',
            "<final>ok</final>",
        ],
    )
    agent.ask("tune the gamma value")
    tool_item = next(item for item in agent.session["history"] if item["role"] == "tool")
    assert "Do not call use_skill again" in tool_item["content"]
    events = [e["event"] for e in read_log(tmp_path)]
    assert events.count("skill_executed") == 1
    assert "skill_already_active" in events


def test_skill_timeout_sets_default_shell_timeout(tmp_path):
    make_repo(tmp_path)
    skill_md = tmp_path / "skills" / "tune" / "SKILL.md"
    skill_md.write_text(TUNE.replace("name: tune", "name: tune\ntimeout: 300"), encoding="utf-8")
    agent = make_agent(tmp_path, [])
    assert agent.shell_timeout() == 20
    agent.active_skills = ["tune"]
    assert agent.shell_timeout() == 300
    agent.validate_tool("run_shell", {"command": "echo hi", "timeout": 250})


def test_shell_timeout_returns_hint_instead_of_crashing(tmp_path):
    make_repo(tmp_path)
    agent = make_agent(tmp_path, [])
    result = agent.run_tool("run_shell", {"command": "python -c \"import time; time.sleep(3)\"", "timeout": 1})
    assert "timed out after 1 seconds" in result
    assert '"timeout":120' in result
