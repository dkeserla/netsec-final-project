# Issue: Build CLI with typer for single-task and batch execution

## Objective
Create `minpriv/cli.py` using `typer` to provide a command-line interface for running benchmark tasks.

## Requirements

1. **Single-task command `run`**
   - Arguments/Options:
     - `--task`: path to a task JSON file (required)
     - `--model`: model name string (required)
     - `--prompt-mode`: `none` or `explicit_least_privilege` (default: `none`)
     - `--max-steps`: int (default: 12)
     - `--out-dir`: path for traces and scores (default: `outputs/`)
   - Execution flow: load task → instantiate workspace → run `AgentRunner.execute(task)` → score with `score_run` → write score JSON to `outputs/scores/`

2. **Batch command `batch`**
   - Argument: path to a YAML experiment config file (e.g., `configs/experiment.yaml`)
   - Config fields: `models`, `prompt_modes`, `tasks`, `repeats`, `max_steps`
   - Iterate over the Cartesian product and run each combination
   - Write one score JSON per run
   - After all runs complete, call `aggregate_scores` to produce a CSV in `outputs/aggregates/`

3. **Output structure**
   - Traces: `{out_dir}/traces/{run_id}.jsonl`
   - Scores: `{out_dir}/scores/{run_id}.json`
   - Aggregate CSV: `{out_dir}/aggregates/{timestamp}_results.csv`

## Acceptance Criteria
- `python -m minpriv.cli run --task tasks/t01_share_doc.json --model openai/gpt-4o --prompt-mode none` executes successfully
- `python -m minpriv.cli batch configs/experiment.yaml` executes a full grid and emits CSV
- CLI handles adapter/import errors gracefully and logs them

## Dependencies
- `typer`
- `pyyaml`
- Existing modules: `task_loader`, `workspace`, `runner`, `scoring`, `traces`

## Files to Create
- `minpriv/cli.py`
- `configs/experiment.yaml` (example batch config)
