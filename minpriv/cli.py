from __future__ import annotations

import json
import logging
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.logging import RichHandler

from minpriv.runner import AgentRunner
from minpriv.scoring import aggregate_scores, load_trace, score_run
from minpriv.task_loader import load_task
from minpriv.workspace import Workspace

app = typer.Typer()
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger("minpriv")


def run_single(task, model, prompt_mode, max_steps, out_dir):
    out_path = Path(out_dir)
    scores_dir = out_path / "scores"
    
    scores_dir.mkdir(parents=True, exist_ok=True)
    
    workspace = Workspace.from_spec(task.workspace)
    runner = AgentRunner(
        model_name=model,
        prompt_mode=prompt_mode,
        workspace=workspace,
        max_steps=max_steps,
        out_dir=out_path,
    )
    
    logger.info(f"Running task {task.task_id} with model={model}, prompt_mode={prompt_mode}")
    trace_logger = runner.execute(task)
    run_id = trace_logger.run_id
    
    events = load_trace(str(trace_logger._path()))
    score_result = score_run(events, task, model=model, prompt_mode=prompt_mode)
    
    score_path = scores_dir / f"{run_id}.json"
    score_path.write_text(score_result.model_dump_json(), encoding="utf-8")
    logger.info(f"Score written to {score_path}")
    
    console.print(f"[green]Success[/green]: task_id={score_result.task_id}, success={score_result.success}, orr={score_result.orr}, eac={score_result.eac}, pfa={score_result.pfa}")
    
    return score_result


@app.command()
def run(
    task: Annotated[str, typer.Option("--task", "-t", help="Path to task JSON file")] = ...,
    model: Annotated[str, typer.Option("--model", "-m", help="Model name (e.g. openai/gpt-4o)")] = ...,
    prompt_mode: Annotated[str, typer.Option("--prompt-mode", "-p", help="Prompt mode: none or explicit_least_privilege")] = "none",
    max_steps: Annotated[int, typer.Option("--max-steps", "-s", help="Maximum execution steps")] = 12,
    out_dir: Annotated[str, typer.Option("--out-dir", "-o", help="Output directory for traces and scores")] = "outputs",
):
    """Execute a single benchmark task."""
    if prompt_mode not in ("none", "explicit_least_privilege"):
        logger.error(f"Invalid prompt_mode: {prompt_mode}. Must be none or explicit_least_privilege")
        raise typer.Exit(code=1)

    task_path = Path(task)
    if not task_path.exists():
        logger.error(f"Task file not found: {task}")
        raise typer.Exit(code=1)

    try:
        loaded_task = load_task(str(task_path))
    except Exception as e:
        logger.error(f"Failed to load task: {e}")
        raise typer.Exit(code=1)

    try:
        run_single(loaded_task, model, prompt_mode, max_steps, out_dir)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    config: Annotated[str, typer.Argument(help="Path to YAML experiment config file")] = ...,
):
    """Execute a batch of benchmark tasks from a YAML config file."""
    config_file = Path(config)
    if not config_file.exists():
        logger.error(f"Config file not found: {config}")
        raise typer.Exit(code=1)

    try:
        config_data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise typer.Exit(code=1)

    models = config_data.get("models", [])
    prompt_modes = config_data.get("prompt_modes", ["none"])
    task_files = config_data.get("tasks", [])
    repeats = config_data.get("repeats", 1)
    max_steps = config_data.get("max_steps", 12)
    out_dir = config_data.get("out_dir", "outputs")

    if not models or not task_files:
        logger.error("Config must specify models and tasks")
        raise typer.Exit(code=1)

    out_path = Path(out_dir)
    scores_dir = out_path / "scores"
    traces_dir = out_path / "traces"
    aggregates_dir = out_path / "aggregates"

    scores_dir.mkdir(parents=True, exist_ok=True)
    traces_dir.mkdir(parents=True, exist_ok=True)
    aggregates_dir.mkdir(parents=True, exist_ok=True)

    total_runs = len(models) * len(prompt_modes) * len(task_files) * repeats
    run_count = 0

    logger.info(f"Starting batch execution: {total_runs} runs")

    for task_file in task_files:
        task_path = Path(task_file)
        if not task_path.exists():
            logger.warning(f"Task file not found: {task_file}, skipping")
            continue

        try:
            base_task = load_task(str(task_path))
        except Exception as e:
            logger.error(f"Failed to load task {task_file}: {e}")
            continue

        for model, prompt_mode, repeat in product(models, prompt_modes, range(1, repeats + 1)):
            run_count += 1
            logger.info(f"Running task={task_file}, model={model}, prompt_mode={prompt_mode}, repeat={repeat}")

            run_id = f"{base_task.task_id}_{model.replace('/', '_')}_{prompt_mode}_rep{repeat}"
            run_id = run_id.replace("__", "_")

            try:
                run_single(base_task, model, prompt_mode, max_steps, out_dir)
            except Exception as e:
                logger.error(f"Run failed for {run_id}: {e}")
                continue

    logger.info(f"Batch execution complete: {run_count} runs")

    score_files = list(scores_dir.glob("*.json"))
    if score_files:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = aggregates_dir / f"{timestamp}_results.csv"
        try:
            aggregate_scores([str(p) for p in score_files], str(csv_path))
            logger.info(f"Aggregate CSV written to {csv_path}")
        except Exception as e:
            logger.error(f"Failed to aggregate scores: {e}")
    else:
        logger.warning("No score files found to aggregate")


if __name__ == "__main__":
    app()
