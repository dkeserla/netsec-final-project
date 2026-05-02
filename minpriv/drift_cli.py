"""CLI for running Instruction Drift experiments."""

from pathlib import Path

import typer
from dotenv import load_dotenv

from minpriv.drift_runner import DriftRunner
from minpriv.scoring import aggregate_scores, score_run
from minpriv.task_loader import load_task
from minpriv.workspace import Workspace

load_dotenv()
app = typer.Typer()

@app.command()
def drift(
    task: str = "tasks/t03_ambiguous_summary.json",
    model: str = "openrouter/google/gemini-3-flash-preview",
    prompt_mode: str = "explicit_least_privilege",
    out_dir: str = "outputs_drift",
):
    """Run a task at multiple stuffing levels to measure instruction drift."""
    loaded_task = load_task(task)
    workspace = Workspace.from_spec(loaded_task.workspace)
    out_path = Path(out_dir)
    scores_dir = out_path / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)

    for level in [0, 1, 2]:
        print(f"Running drift test: model={model}, level={level}")
        runner = DriftRunner(
            model_name=model,
            prompt_mode=prompt_mode,
            workspace=workspace,
            stuffing_level=level,
            out_dir=out_path
        )
        trace_logger = runner.execute(loaded_task)
        events = trace_logger.read_events()
        
        score_result = score_run(events, loaded_task, model=model, prompt_mode=f"{prompt_mode}_s{level}")
        score_path = scores_dir / f"{trace_logger.run_id}.json"
        score_path.write_text(score_result.model_dump_json())
        
        print(f"  Level {level} complete. ORR: {score_result.refined_orr}, EAC: {score_result.refined_eac}")

    score_files = list(scores_dir.glob("*.json"))
    csv_path = out_path / "drift_results.csv"
    aggregate_scores([str(p) for p in score_files], str(csv_path))
    print(f"Aggregate results written to {csv_path}")

if __name__ == "__main__":
    app()
