"""Build the Lab 4 demo workspace for the agent skills component.

Lab 4 left the vacuum Q-learning problem set up for a coding agent (context files, sub-agent
specs, an empty src/). Lab 5 solved it with Claude Code and added three skills: tune,
render-policy and submit-check. This script builds a workspace where mini-coding-agent can
finish Lab 4 using those Lab 5 skills:

    <out>/                    copy of the Lab 4 repo (README, CLAUDE.md, .claude/context, ...)
    <out>/src/                vacuum_env.py and q_agent.py (+ tests) from Lab 5
    <out>/skills/<name>/      the Lab 5 skills, moved from .claude/skills/ to skills/

Edits to the Lab 5 skills:
- path fixes: ".claude/skills/" becomes "skills/" in SKILL.md, and the scripts look for src/
  one folder higher (parents[3] -> parents[2]).
- tune, adapted for a 4B local model (see SMALL_MODEL_TUNE): sweep.py gets an --out flag that
  appends each table to a file, and a new sweep_all.py runs all four sweeps in one command.
  qwen3.5:4b ran out of output tokens retyping the tables, and in the next run it ran one sweep
  twice and skipped epsilon. Now the model runs one command, reads the tables, and only writes
  the short file with the chosen values. Pass --original-skills to skip this.

Usage:
    python demo/setup_lab4_demo.py --lab4 PATH_TO_LAB4_REPO --lab5 PATH_TO_LAB5_REPO --out tmp/lab4-demo
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SRC_FILES = ("vacuum_env.py", "q_agent.py", "test_vacuum_env.py", "test_q_agent.py")
SWEEP_OUT_ARG = """    parser.add_argument("--out", help="Also append the table to this markdown file.")
    args = parser.parse_args()
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_file = out_path.open("a", encoding="utf-8")
        screen = sys.stdout

        class Tee:
            def write(self, text):
                screen.write(text)
                out_file.write(text)

            def flush(self):
                screen.flush()
                out_file.flush()

        sys.stdout = Tee()
"""

SWEEP_ALL = r'''"""Run all four tune sweeps in one command (added for small local models).

Same commands as step 2 of SKILL.md. Starts results/hyperparams.md fresh, then sweep.py --out
appends each table, so a sweep can not be skipped or written twice.
"""
import subprocess
import sys
from pathlib import Path

SWEEPS = [
    ("living_cost", ["-2", "-0.4", "-0.04", "0", "1"]),
    ("gamma", ["0.5", "0.7", "0.9", "0.99"]),
    ("alpha", ["0.05", "0.1", "0.3", "0.5", "0.9"]),
    ("epsilon", ["0.05", "0.2", "0.5", "0.8", "1.0"]),
]

out = Path("results/hyperparams.md")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("# Hyperparameter sweeps\n\n", encoding="utf-8")
sweep = Path(__file__).with_name("sweep.py")
for param, values in SWEEPS:
    subprocess.run([sys.executable, str(sweep), "--param", param, "--values", *values, "--out", str(out)], check=True)
    with out.open("a", encoding="utf-8") as handle:
        handle.write("\n")
print(f"saved all four tables to {out}")
'''

SMALL_MODEL_TUNE = {
    "2. Sweep one parameter at a time; everything else stays at the baseline":
        "2. Run ALL FOUR sweeps with this ONE command (it saves every table to `results/hyperparams.md`):\n"
        "   ```\n   python skills/tune/sweep_all.py\n   ```\n"
        "   For reference only, do not run these yourself. It runs, one parameter at a time, everything else at the baseline",
    "4. Write `results/hyperparams.md`: the four tables, the chosen values, and one sentence per":
        "4. The four tables are already saved in `results/hyperparams.md` by `--out`, do not copy them.\n"
        "   Use write_file to create `results/hyperparams-choice.md` with only the chosen values and one sentence per",
}

SKIP = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".mini-coding-agent", "class_context")


def adapt_tune(folder):
    sweep, skill = folder / "sweep.py", folder / "SKILL.md"
    if not sweep.is_file() or not skill.is_file():
        return
    code = sweep.read_text(encoding="utf-8")
    if "args = parser.parse_args()\n" in code and "--out" not in code:
        code = code.replace("    args = parser.parse_args()\n", SWEEP_OUT_ARG, 1)
        for name in ("sys", "from pathlib import Path"):
            line = name if name.startswith("from") else f"import {name}"
            if line not in code:
                code = line + "\n" + code
        sweep.write_text(code, encoding="utf-8")
    (folder / "sweep_all.py").write_text(SWEEP_ALL, encoding="utf-8")
    text = skill.read_text(encoding="utf-8")
    missing = [old for old in SMALL_MODEL_TUNE if old not in text]
    for old, new in SMALL_MODEL_TUNE.items():
        text = text.replace(old, new)
    text = text.replace("5. Report the chosen values in at most 5 lines.",
                        "5. Answer with <final> and the chosen values in at most 5 lines.")
    skill.write_text(text, encoding="utf-8")
    if missing:
        print("warning: tune SKILL.md did not match the expected text, check it by hand:", missing)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lab4", required=True, help="Path to the Lab 4 repo (vacuum-rl-context-engineering).")
    parser.add_argument("--lab5", required=True, help="Path to the Lab 5 repo (vacuum-rl-context-engineering-lab5).")
    parser.add_argument("--out", default="tmp/lab4-demo", help="Where to build the demo workspace.")
    parser.add_argument("--force", action="store_true", help="Delete --out first if it exists.")
    parser.add_argument("--original-skills", action="store_true", help="Copy the Lab 5 skills with path fixes only.")
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

    if not args.original_skills:
        adapt_tune(skills_out / "tune")

    # The Lab 4 skill drives Claude Code sub-agents, which mini-coding-agent does not have.
    shutil.rmtree(out / ".claude" / "skills", ignore_errors=True)
    (out / "results").mkdir(exist_ok=True)

    # The agent treats the git top level as the workspace root. Without its own repo, a
    # workspace inside this project would resolve to mini-coding-agent itself.
    if not (out / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=out, check=True)
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=out, capture_output=True, text=True)
    if Path(top.stdout.strip()).resolve() != out:
        sys.exit(f"git init in {out} did not work, run `git init` there by hand")

    print(f"demo workspace ready: {out}")
    print("skills:", ", ".join(sorted(p.name for p in skills_out.iterdir() if p.is_dir())))
    print("next:")
    print(f"  python mini_coding_agent.py --cwd {out} --approval auto --max-steps 20 --max-new-tokens 2048")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
