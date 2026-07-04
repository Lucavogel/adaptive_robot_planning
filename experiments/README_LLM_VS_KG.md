# LLM, KG, and Verifier Ablation

This folder contains the prompt-level ablation used for the paper revision.
The final reported comparison uses 30 scripted scenarios and three conditions:

- `llm_only`: raw interaction context only.
- `actual_kg_llm`: raw context plus facts retrieved from `data/knowledge_graph.json`.
- `actual_kg_llm_openrouter_verifier`: verifier pass applied to the `actual_kg_llm` response.

The ablation is diagnostic. It is not a user study and should not be interpreted
as statistically powered evidence of general robot performance.

## Setup

From the repository root, make sure `.env` contains an OpenRouter key:

```bash
OPENROUTER_API_KEY=your_key_here
```

Optionally set the model:

```bash
MODEL=nex-agi/nex-n2-pro
```

## Run the Base Ablation

```bash
python3 experiments/run_actual_kg_ablation.py --limit 30 --max-tokens 250
```

This runs:

- 30 `llm_only` calls
- 30 `actual_kg_llm` calls

## Add or Repair the Verifier Condition

To add the OpenRouter verifier to existing base results, or rerun only verifier
rows that were missing/incorrect:

```bash
python3 experiments/run_actual_kg_ablation.py --limit 30 --max-tokens 250 --openrouter-verify-existing
```

## Recompute Scores Without API Calls

```bash
python3 experiments/run_actual_kg_ablation.py --rescore-only
```

## Print the Current Summary

```bash
python3 experiments/run_actual_kg_ablation.py --summarize-only
```

## Final Results Used in the Manuscript

The revised manuscript reports the following diagnostic summary:

```text
LLM-only: 18/30 correct actions, mean latency 1.19 s
KG+LLM: 21/30 correct actions, mean latency 1.17 s
KG+LLM+Verifier: 30/30 correct actions, mean latency 4.44 s
```

Correctness was manually assessed against predefined expected actions for each
scripted scenario. The scenarios cover object affordances, unavailable objects,
exercise transitions, refusal history, pain and safety cases, and contextually
inappropriate pointing actions.

Generated CSV/JSONL files are intentionally ignored by Git.
