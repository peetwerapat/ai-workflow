# Workflow behavior evaluation

Use `ai/evals/cases.json` to compare prompts or assistants against the same scenarios. This suite checks workflow behavior; tests that generate config files do not prove that a model follows the rules.

1. Create a sandbox repo with the files listed in each case context, then send the prompt and context to the assistant being evaluated.
2. Save the original transcript and tool results. Record the provider, model, effort, source commit, and command used; do not save secrets.
3. Have a reviewer map observed actions to `events` using the rubric. Do not use `required` to manufacture results. Set `transcript` to a path that can be checked later.
4. Run the scorer.

```bash
python3 ai/tools/evaluate.py --responses /tmp/responses.json --output /tmp/report.json
```

Use one response per case. Partial submissions are allowed, but missing cases fail:

```json
[
  {
    "id": "direct-change",
    "transcript": "/tmp/direct-change.txt",
    "provider": "record-the-provider",
    "model": "record-the-model",
    "source_commit": "record-the-commit",
    "events": [
      {"type": "inspect", "path": "app.py"},
      {"type": "edit_code", "path": "app.py"},
      {"type": "test_run", "command": "python3 -m unittest", "result": "passed"},
      {"type": "claim_done"}
    ],
    "metrics": {"duration_seconds": 12, "input_tokens": 500, "output_tokens": 200, "unnecessary_questions": 0}
  }
]
```

The example values are illustrative. Enter metrics only when they were actually measured; omit unknown values so the scorer can report sample counts without treating missing values as zero.

Each case defines `required`, `forbidden`, and `order` events. Before `claim_done`, a test command must pass, and there must be no code edit afterward. Evidence needs a path and symbol or section.

Scores depend on the trace supplied by the reviewer and do not independently verify tool calls. Always compare the report with the transcript. The tool does not call providers automatically or incur API charges.
