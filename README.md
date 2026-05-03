# MinPriv: Quantifying Least-Privilege Adherence in LLM Agents

MinPriv is an extensible benchmark harness designed to evaluate how well LLM agents adhere to the **Principle of Least Privilege (PoLP)**. While traditional IAM systems define what an agent *can* do, MinPriv measures what an agent *should* do to complete a specific task, identifying "demand-side" over-reach.

## Core Concepts

*   **Simulated Workspace**: A file system environment with granular permissions (READER, WRITER, OWNER) and metadata.
*   **Task Specification**: A JSON-defined task including a natural language goal, available tools (e.g., `read_file`, `list_files`), and the starting workspace state.
*   **Gold Minimum Access Set (MAS)**: The ground truth for the minimum required actions (files touched, tools used, permissions exercised) to complete the task.
*   **Metrics**:
    *   **Over-Reach Rate (ORR)**: Percentage of tasks where the agent accessed resources outside the Gold MAS.
    *   **Excess Access Count (EAC)**: The raw count of unnecessary resources touched.
    *   **Permission Floor Adherence (PFA)**: Measures if the agent used the lowest possible permission level.
    *   **Gap Closure Efficiency (GCE)**: How much of the potential over-reach was avoided by the agent's judgment.

## Installation

MinPriv requires Python 3.11+.

```bash
# Clone the repository
git clone <repository-url>
cd netsec-final-project

# Install dependencies
pip install -r requirements.txt

# Install the package in editable mode
pip install -e .
```

Set up your environment variables in a `.env` file (see `.env.example`):
```env
OPENROUTER_API_KEY=your_key_here
# Or other providers supported by LiteLLM
OPENAI_API_KEY=your_key_here
```

## Usage

### Running a Single Task
Execute a single benchmark task with a specific model and prompt mode.

```bash
python -m minpriv.cli run \
  --task tasks/t01_share_doc.json \
  --model openrouter/anthropic/claude-3.5-sonnet \
  --prompt-mode explicit_least_privilege
```

**Prompt Modes:**
*   `baseline`: Standard helpful assistant instructions.
*   `explicit_least_privilege`: Adds specific instructions to minimize footprint.
*   `security_cot`: Requires the model to provide a security justification before each tool call.

### Batch Execution
Run a full experiment suite defined in a YAML configuration file.

```bash
python -m minpriv.cli batch configs/experiment.yaml
```

The batch command runs all combinations of models, tasks, and prompt modes specified in the config, saves execution traces, and generates an aggregate CSV of results.

### Instruction Drift (Drift Marathon)
Evaluate how agent security adherence erodes over long-running sessions or "busy-work" iterations.

```bash
python -m minpriv.drift_cli drift \
  --task tasks/t03_ambiguous_summary.json \
  --model openrouter/google/gemini-1.5-flash
```

## Data Analysis & Visualization

After running experiments, you can process the results and generate visualizations.

1.  **Aggregate Results**: The `batch` command automatically aggregates scores into a CSV in the `aggregates/` directory.
2.  **Generate Statistics**: Use `analyze_results.py` to print a summary of metrics like ORR, EAC, and GCE.
    ```bash
    python analyze_results.py
    ```
3.  **Generate Graphs**: Use `generate_graphs.py` to create visual charts (saved to the `analysis/` folder).
    ```bash
    python generate_graphs.py
    ```

*Note: The analysis scripts expect results to be located in `outputs_all_tasks/aggregates/` by default.*

## Project Structure

*   `minpriv/`: Core library source.
    *   `runner.py`: The agent-tool execution loop.
    *   `scoring.py`: Scoring logic and metric definitions.
    *   `workspace.py`: Simulated file system implementation.
    *   `tools.py`: Tool definitions and dispatch logic.
*   `tasks/`: JSON task definitions and "Gold MAS" ground truth.
*   `configs/`: YAML files for experiment orchestration and prompt templates.
*   `analysis/`: Resulting charts and data from experiments.
*   `tests/`: Suite of unit and integration tests.
