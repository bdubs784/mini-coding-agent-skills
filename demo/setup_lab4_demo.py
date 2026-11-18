"""Build the Lab 4 demo workspace for the agent skills component.

Lab 4 left the vacuum Q-learning problem set up for a coding agent (context files, sub-agent
specs, an empty src/). Lab 5 solved it with Claude Code and added three skills: tune,
render-policy and submit-check. This script builds a workspace where mini-coding-agent can
finish Lab 4 using those Lab 5 skills:

    <out>/                    copy of the Lab 4 repo (README, CLAUDE.md, .claude/context, ...)
    <out>/src/                vacuum_env.py and q_agent.py (+ tests) from Lab 5
    <out>/skills/<name>/      the Lab 5 skills, moved from .claude/skills/ to skills/

The only edits to the Lab 5 skills are path fixes: ".claude/skills/" becomes "skills/" in
SKILL.md, and the scripts look for src/ one folder higher (parents[3] -> parents[2]).

Usage:
    python demo/setup_lab4_demo.py --lab4 PATH_TO_LAB4_REPO --lab5 PATH_TO_LAB5_REPO --out tmp/lab4-demo
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SRC_FILES = ("vacuum_env.py", "q_agent.py", "test_vacuum_env.py", "test_q_agent.py")
SKIP = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".mini-coding-agent", "class_context")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lab4", required=True, help="Path to the Lab 4 repo (vacuum-rl-context-engineering).")
    parser.add_argument("--lab5", required=True, help="Path to the Lab 5 repo (vacuum-rl-context-engineering-lab5).")
    parser.add_argument("--out", default="tmp/lab4-demo", help="Where to build the demo workspace.")
    parser.add_argument("--force", action="store_true", help="Delete --out first if it exists.")
    args = parser.parse_args(argv)

    lab4, lab5, out = Path(args.lab4).resolve(), Path(args.lab5).resolve(), Path(args.out).resolve()
    for label, path, marker in (("lab4", lab4, "CLAUDE.md"), ("lab5", lab5, "src/q_agent.py")):
        if not (path / marker).exists():
            sys.exit(f"--{label} {path} does not look right: {marker} is missing")
    if out.exists():
        if not args.force:
            sys.exit(f"{out} already exists, pass --force to rebuild it")
        shutil.rmtree(out)

    shutil.copytree(lab4, out, ignore=SKIP)
    (out / "src").mkdir(exist_ok=True)
    for name in SRC_FILES:
        shutil.copy2(lab5 / "src" / name, out / "src" / name)

    skills_out = out / "skills"
    for skill_dir in sorted((lab5 / ".claude" / "skills").iterdir()):
        if not (skill_dir / "SKILL.md").is_file():
            continue
        target = skills_out / skill_dir.name
        shutil.copytree(skill_dir, target, ignore=SKIP)
        for path in target.iterdir():
            if path.suffix == ".md":
                path.write_text(path.read_text(encoding="utf-8").replace(".claude/skills/", "skills/"), encoding="utf-8")
            elif path.suffix == ".py":
                text = path.read_text(encoding="utf-8").replace(".claude/skills/", "skills/")
                path.write_text(text.replace(".parents[3]", ".parents[2]"), encoding="utf-8")

    # The Lab 4 skill drives Claude Code sub-agents, which mini-coding-agent does not have.
    shutil.rmtree(out / ".claude" / "skills", ignore_errors=True)
    (out / "results").mkdir(exist_ok=True)

    if not (out / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=out, check=False)

    print(f"demo workspace ready: {out}")
    print("skills:", ", ".join(sorted(p.name for p in skills_out.iterdir() if p.is_dir())))
    print("next:")
    print(f"  python mini_coding_agent.py --cwd {out} --approval auto --max-steps 12 --max-new-tokens 1024")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
