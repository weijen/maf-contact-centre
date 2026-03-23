---
name: eval-review-run
description: "Run the maf-contact-centre evaluation review workflow end to end: execute scripts/run_eval.py, save the result as data/eval_results_v1_DD-MM-YYYY_testN.json, classify failures with the failure-taxonomy-classifier skill, and write or update the dated report at data/notes/failure-taxonomy-report-DD-MM-YY.md. Use when the user asks to run eval, review failures, or produce the failure taxonomy report in one pass."
argument-hint: "Optional dataset path or run notes"
user-invocable: true
---

# Eval Review Run

Use this skill for the full post-evaluation workflow in this repository.

This is a task-specific workflow skill, not a coding-standard instruction. It should be used when the user wants one pass that covers:

- running the eval dataset
- classifying failures with the approved taxonomy
- saving a dated eval artifact
- writing the dated failure taxonomy report

## Required companion skills

- Load [../failure-taxonomy-classifier/SKILL.md](../failure-taxonomy-classifier/SKILL.md) before classifying any rows.
- Load [../microsoft-agent-framework/SKILL.md](../microsoft-agent-framework/SKILL.md) if the task also requires prompt, agent, or workflow changes after the review.

## Output conventions

Use these paths unless the user explicitly asks for different ones:

- Eval artifact: `data/eval_results_v1_DD-MM-YYYY_testN.json`
- Daily report: `data/notes/failure-taxonomy-report-DD-MM-YY.md`

Rules:

- Always preserve the raw runner output in `data/eval_results_v1.json` unless the user explicitly asks to overwrite it.
- Copy the fresh eval output into the dated artifact before writing taxonomy fields.
- Never overwrite an existing `testN` artifact. Discover the next available `N` for the current date.
- If the daily report already exists, append a new section for the current test run instead of replacing earlier sections.

## Workflow

1. Run the eval.

- Default command: `uv run python scripts/run_eval.py`
- If the user supplied a dataset path, pass it with `--dataset`.
- Confirm that the command completed and that `data/eval_results_v1.json` was refreshed.

2. Create the dated artifact path.

- Use today's date in `DD-MM-YYYY` format for the eval artifact.
- Inspect existing files in `data/` matching `eval_results_v1_<date>_test*.json`.
- Choose the next unused integer for `testN`.
- Copy `data/eval_results_v1.json` to the dated file before editing taxonomy fields.

3. Classify failures.

- Read the dated eval artifact row by row.
- Apply the failure taxonomy to every row, using the approved schema and enums only.
- Write these fields back into the dated artifact for every row:
  - `outputs.failure_taxonomy.primary_failure`
  - `outputs.failure_taxonomy.secondary_failures`
  - `outputs.failure_taxonomy.failure_notes`
- Default passing rows to `no_failure`, empty secondary failures, and a brief note.
- Be careful not to copy stale classifications from older dated files without checking the current row evidence.

4. Write the daily report.

- Create `data/notes/` if it does not exist.
- Use the template in [./report-template.md](./report-template.md).
- Name the report file with today's date in `DD-MM-YY` format.
- Add one section per run with the heading `# Eval on DD/MM/YYYY - test N`.
- Include only rows whose primary failure is not `no_failure` in the detailed case table.
- Build the primary-failure count table from the dated artifact, not from memory.
- Keep the `Priority` section short and action-oriented. Focus on root-cause fixes, not score-chasing.

5. Validate the output.

- Confirm the dated eval artifact exists and is valid JSON.
- Confirm the report file exists and contains the new run section.
- Summarize the produced paths and the main failure counts back to the user.

## Report guidance

Follow these rules when writing priorities:

- Prioritize root causes over symptoms.
- Group repeated issues under one action item.
- Call out evaluator or gold-label problems separately from agent defects.
- If the most important issue is a prompt problem, name the affected agent and scenario directly.
- If there are no meaningful failures, say so explicitly instead of inventing action items.

## Example invocation

- `/eval-review-run`
- `/eval-review-run data/eval_dataset_v1.jsonl`
- `/eval-review-run rerun after support prompt update`

## Completion criteria

- The eval was run successfully.
- A new dated eval artifact was created without overwriting prior tests.
- Taxonomy fields were written into that dated artifact.
- The failure taxonomy report was created or updated in `data/notes/`.
- The user received the artifact paths plus a concise summary of the findings.