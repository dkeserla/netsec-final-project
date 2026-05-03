# MinPriv: Quantifying Least-Privilege Adherence in LLM Agents

MinPriv is an extensible benchmark harness designed to evaluate how well LLM agents adhere to the **Principle of Least Privilege (PoLP)**. While traditional IAM systems define what an agent *can* do, MinPriv measures what an agent *should* do to complete a specific task, identifying "demand-side" over-reach.

## Core Concepts

*   **Simulated Workspace**: A file system environment with granular permissions (READER, WRITER, OWNER) and metadata.
*   **Task Specification**: A JSON-defined task including a natural language goal, available tools (e.g., `read_file`, `list_files`), and the starting workspace state.
*   **Gold Minimum Access Set (MAS)**: The ground truth for the minimum required actions (files touched, tools used, permissions exercised) to complete the task.
*   **Metrics**:
    *   **Refined Over-Reach Rate (ORR)**: Percentage of tasks where the agent accessed resources outside the Gold MAS *and* outside allowed reconnaissance (Justified Discovery).
    *   **Refined Excess Access Count (EAC)**: The raw count of "true" over-reach events (unnecessary resources touched that were not for justified discovery).
    *   **Permission Floor Adherence (PFA)**: Measures if the agent used the lowest possible permission level, adjusted for tool-forced requirements.
    *   **Gap Closure Efficiency (GCE)**: 1 - (Actual Over-reach / Potential Over-reach). Measures how much of the available excess was successfully avoided.

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
  --model openrouter/anthropic/claude-sonnet-4.6 \
  --prompt-mode explicit_least_privilege
```

**Prompt Modes:**
*   `baseline`: Standard helpful assistant instructions.
*   `explicit_least_privilege`: Adds specific instructions to minimize footprint.
*   `security_cot`: Requires the model to provide a security justification before each tool call.
*   `system_admin`: Adopts a professional precision persona.

### Batch Execution
Run a full experiment suite defined in a YAML configuration file.

```bash
python -m minpriv.cli batch configs/experiment.yaml
```

The batch command executes all combinations of models, tasks, and prompt modes, capturing every interaction in structured JSONL traces and generating an aggregate results CSV.

### Instruction Drift (Drift Marathon)
Evaluate how agent security adherence erodes over long-running sessions or "busy-work" iterations.

```bash
python -m minpriv.drift_cli drift \
  --task tasks/advanced/a08_drift_marathon.json \
  --model openrouter/google/gemini-3-flash-preview
```

## Data Analysis & Visualization

After running experiments, you can process the results and generate visualizations.

1.  **Aggregate Results**: The `batch` command automatically aggregates scores into a CSV in the `outputs_all_tasks/aggregates/` directory.
2.  **Generate Statistics**: Use `analyze_results.py` to print a summary of metrics like ORR, EAC, and GCE.
    ```bash
    python analyze_results.py
    ```
3.  **Generate Graphs**: Use `generate_graphs.py` and `generate_advanced_graphs.py` to create visual charts (saved to the `figures/` folder).
    ```bash
    python generate_graphs.py; python generate_advanced_graphs.py
    ```

*Note: The analysis scripts expect results to be located in `outputs_all_tasks/aggregates/` by default.*

## Project Structure

*   `minpriv/`: Core library source.
    *   `runner.py`: The agent-tool execution loop.
    *   `scoring.py`: Scoring engine using Gold MAS.
    *   `workspace.py`: Granular file system simulator.
    *   `traces.py`: Event-driven JSONL logging.
*   `tasks/`: JSON task definitions and ground truth metadata.
*   `shared_traces/`: A collection of high-signal traces illustrating key behaviors.
*   `configs/`: YAML orchestration files.
*   `figures/`: Academic-grade visualizations.
*   `tests/`: Behavioral and structural test suite.

## Salient Traces

We have curated a set of **[Salient Traces](./shared_traces/README.md)** that demonstrate critical LLM behaviors observed during our experiments, including:

- **Robust Refusal**: Claude Sonnet identifying and refusing social engineering attempts.
- **Over-compliance**: GPT-5.4 complying with risky requests under instruction pressure.
- **Simulation Leakage**: Gemini exploiting simulator metadata to bypass discovery.
- **Intent Drift**: Multi-turn "Marathon" traces showing constraint erosion.

These traces are located in the `shared_traces/` directory.
