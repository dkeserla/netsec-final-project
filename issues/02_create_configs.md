# Issue: Create prompt configs, model configs, and experiment YAML files

## Objective
Populate the `configs/` directory with the YAML files needed to drive benchmark experiments.

## Requirements

1. **`configs/prompts.yaml`**
   - Define two prompt templates exactly matching the constants in `runner.py`:
     - `baseline`: standard tool-using agent instructions (`SYSTEM_BASE`)
     - `explicit_least_privilege`: baseline plus the least-privilege directive (`LP_ADDITION`)
   - Structure should allow the runner to optionally load prompts from file instead of hardcoded strings.

2. **`configs/models.yaml`**
   - List the three frontier models planned for the 60-run experiment:
     - `anthropic/claude-sonnet-4.6`
     - `google/gemini-3-flash-preview`
     - `openai/gpt-5.4`
   - Format: simple list or object with model nicknames → full LiteLLM strings.

3. **`configs/experiment.yaml`**
   - Full experiment configuration matching the design document's grid:
     ```yaml
     models:
       - anthropic/claude-sonnet-4.6
       - google/gemini-3-flash-preview
       - openai/gpt-5.4
     prompt_modes:
       - none
       - explicit_least_privilege
     tasks:
       - tasks/t01_share_doc.json
       - tasks/t02_update_report.json
       - tasks/t03_ambiguous_summary.json
       - tasks/t04_move_file.json
       - tasks/t05_create_folder_doc.json
       - tasks/t06_delete_old.json
     repeats: 1
     max_steps: 12
     ```

## Acceptance Criteria
- All three YAML files are valid and parseable
- `experiment.yaml` references the 6 task files that will exist in `tasks/`
- `prompts.yaml` mirrors the exact wording in `runner.py` so behavior is consistent

## Files to Create
- `configs/prompts.yaml`
- `configs/models.yaml`
- `configs/experiment.yaml`
