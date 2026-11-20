# Logs from our real Ollama run

Copied unchanged from `tmp/lab4-demo/` after the real run on 2026-11-18 with qwen3.5:4b
(`--approval auto --max-steps 20 --max-new-tokens 2048`), using the five prompts in
`evals/lab4-demo.json`.

| File | From | What it shows |
|---|---|---|
| `skills.log` | `.mini-coding-agent/logs/skills.log` | one readable line per event: PROMPT, SIMILARITY (every skill's score), EXECUTED, FINISHED |
| `skills.jsonl` | `.mini-coding-agent/logs/skills.jsonl` | the same events as JSON, with the full final answers |
| `hyperparams.md` | `results/hyperparams.md` | the four sweep tables written by the tune skill, plus the values its step 3 rule picked |

Grade them with `python evals/check_demo_log.py demo/logs --flat` (7 passed, 0 failed).
