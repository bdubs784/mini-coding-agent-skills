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
- tune gets `timeout: 300` in its frontmatter (the four sweeps take about a minute).
- tune, adapted for a 4B local model (see SMALL_MODEL_TUNE): sweep.py gets an --out flag that
  appends each table to a file, and a new sweep_all.py runs all four sweeps in one command.
  qwen3.5:4b ran out of output tokens retyping the tables, and in the next run it ran one sweep
  twice and skipped epsilon. Later it broke the step 3 selection rule and misquoted table numbers,
  so sweep_all.py also applies the step 3 rule and prints the picked values. Now the model runs one
  command and only writes the short file with those values.
- render-policy: render.py also prints the cells where the learned policy and value iteration
  differ (the model named the wrong cells when comparing the grids itself).
- submit-check: run check.py once and answer (the model re-ran it in a loop and began fixing).
Pass --original-skills to skip these adaptations.

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
appends each table, so a sweep can not be skipped or written twice. At the end it applies the
step 3 rule to the saved tables and appends and prints the picked values.
"""
import re
import subprocess
import sys
from pathlib import Path

BASELINE = {"living_cost": -0.04, "gamma": 0.9, "alpha": 0.5, "epsilon": 0.8}

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
    # The tables go to the file only; printing all four would push the picked values below
    # past the agent's tool output limit.
    subprocess.run([sys.executable, str(sweep), "--param", param, "--values", *values, "--out", str(out)],
                   check=True, stdout=subprocess.DEVNULL)
    with out.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    print(f"swept {param}: {' '.join(values)}")
print(f"saved all four tables to {out}")


def read_tables(text):
    """{param: [(value, success, vi_match, steps), ...]} from the saved markdown tables."""
    tables, param = {}, None
    for line in text.splitlines():
        header = re.match(r"Sweep: (\w+)", line)
        if header:
            param = header.group(1)
            tables[param] = []
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if param and len(cells) == 5 and re.match(r"-?[\d.]+$", cells[0]):
            success = float(cells[1].split()[0])
            tables[param].append((float(cells[0]), success, float(cells[4]), float(cells[2])))
    return tables


def pick(param, rows):
    """Step 3: highest success %, then highest VI match %, then fewest steps, then the baseline."""
    return max(rows, key=lambda row: (row[1], row[2], -row[3], row[0] == BASELINE[param]))


lines = ["## Values picked by the step 3 rule", ""]
for param, rows in read_tables(out.read_text(encoding="utf-8")).items():
    value, success, match, steps = pick(param, rows)
    lines.append(f"- {param} = {value:g}: success {success:g}%, VI match {match:g}%, {steps:g} steps")
section = "\n".join(lines) + "\n"
with out.open("a", encoding="utf-8") as handle:
    handle.write(section)
print()
print(section)
'''

SMALL_MODEL_TUNE = {
    "3. Choose each value by: highest success %, then highest match with value iteration, then fewest\n"
    "   steps. On a tie, prefer the more standard value.":
        "3. The rule is: highest success %, then highest match with value iteration, then fewest steps,\n"
        "   and on a tie the baseline value. sweep_all.py already applies this rule and prints the picked\n"
        "   values at the end under \"Values picked by the step 3 rule\". Use exactly those values and\n"
        "   numbers. Do not pick different ones.",
    "5. Report the chosen values in at most 5 lines.":
        "5. Answer with <final>: copy the four lines under \"Values picked by the step 3 rule\" exactly, then\n"
        "   one short sentence per parameter. Do not add numbers that are not in those four lines.",
    "2. Sweep one parameter at a time; everything else stays at the baseline":
        "2. Run ALL FOUR sweeps with this ONE tool call (it saves every table to `results/hyperparams.md`).\n"
        "   It takes about a minute, so keep the timeout argument and do not add flags to the command:\n"
        '   <tool>{"name":"run_shell","args":{"command":"python skills/tune/sweep_all.py","timeout":300}}</tool>\n'
        "   For reference only, do not run these yourself. It runs, one parameter at a time, everything else at the baseline",
    "4. Write `results/hyperparams.md`: the four tables, the chosen values, and one sentence per":
        "4. The four tables are already saved in `results/hyperparams.md` by `--out`, do not copy them.\n"
        "   Use write_file to create `results/hyperparams-choice.md` with only the chosen values and one sentence per",
}

RENDER_VI_LINE = '    print("\\nValue-iteration policy:\\n" + policy_grid(value_iteration(args.living_cost, args.gamma)))\n'
RENDER_VI_DIFF = '''    learned, vi = agent.greedy_policy(), value_iteration(args.living_cost, args.gamma)
    print("\\nValue-iteration policy:\\n" + policy_grid(vi))
    diff = [f"({x},{y}) learned {ARROWS.get(learned.get((x, y)), '.')} vs VI {ARROWS.get(action, '.')}"
            for (x, y), action in sorted(vi.items()) if learned.get((x, y)) != action]
    print("\\nCells where learned and value iteration differ: " + ("; ".join(diff) or "none"))
'''

SMALL_MODEL_SUBMIT = {
    "1. Run `python skills/submit-check/check.py` and show its output.":
        "1. Run `python skills/submit-check/check.py` ONCE and show its output. Do not run it again.",
    "2. For each FAIL, give a one-line fix. Do not fix anything unless asked.":
        "2. For each FAIL, give a one-line fix (each check name says what must be true; FAIL means it is\n"
        "   not true yet). Do not fix anything unless asked and do not call more tools, answer with <final>.",
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
    if "\ntimeout:" not in text.split("\n---", 1)[0]:
        text = text.replace("\nname: tune\n", "\nname: tune\ntimeout: 300\n", 1)
    skill.write_text(text, encoding="utf-8")
    if missing:
        print("warning: tune SKILL.md did not match the expected text, check it by hand:", missing)


def adapt_render(folder):
    """render.py also prints which cells differ, so the model does not have to compare grids."""
    script = folder / "render.py"
    if not script.is_file():
        return
    code = script.read_text(encoding="utf-8")
    if RENDER_VI_LINE not in code:
        print("warning: render.py did not match the expected text, check it by hand")
        return
    script.write_text(code.replace(RENDER_VI_LINE, RENDER_VI_DIFF), encoding="utf-8")


def adapt_submit(folder):
    """A 4B model looped on check.py and started fixing things, so the steps say run once and stop."""
    skill = folder / "SKILL.md"
    if not skill.is_file():
        return
    text = skill.read_text(encoding="utf-8")
    missing = [old for old in SMALL_MODEL_SUBMIT if old not in text]
    for old, new in SMALL_MODEL_SUBMIT.items():
        text = text.replace(old, new)
    skill.write_text(text, encoding="utf-8")
    if missing:
        print("warning: submit-check SKILL.md did not match the expected text, check it by hand:", missing)


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
                path.write_text(path.read_text(encoding="utf-8").replace(".claude/skills", "skills"), encoding="utf-8")
            elif path.suffix == ".py":
                text = path.read_text(encoding="utf-8").replace(".claude/skills", "skills")
                path.write_text(text.replace(".parents[3]", ".parents[2]"), encoding="utf-8")

    if not args.original_skills:
        adapt_tune(skills_out / "tune")
        adapt_render(skills_out / "render-policy")
        adapt_submit(skills_out / "submit-check")

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
