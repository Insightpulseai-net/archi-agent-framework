# Fine-Tuning Dataset Generator

Generate training datasets for fine-tuning LLMs on InsightPulseAI specialized agent skills.

## Overview

This tool generates structured training examples for LoRA fine-tuning, following the [HuggingFace Smol Training Playbook](https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook).

## Agents Supported

| Agent | Domain | Examples |
|-------|--------|----------|
| documentation-parser | Documentation extraction | Odoo, Supabase, BIR docs |
| compliance-validator | Philippine tax compliance | SSS, PhilHealth, PAGIBIG, BIR |
| code-generator | Code generation | Odoo, FastAPI, React, SQL |
| sql-agent | Database transformations | Bronze/Silver/Gold, RLS |
| validation-agent | Testing and SLAs | pytest, coverage, latency |

## Usage

### Generate All Datasets

```bash
python generate_datasets.py --all --output ./datasets/
```

### Generate Specific Agent Dataset

```bash
python generate_datasets.py --agent compliance-validator --output ./datasets/
```

## Output Structure

```
datasets/
├── documentation-parser/
│   ├── train.jsonl    # 70% of examples
│   ├── val.jsonl      # 15% of examples
│   └── test.jsonl     # 15% of examples
├── compliance-validator/
│   ├── train.jsonl
│   ├── val.jsonl
│   └── test.jsonl
└── ...
```

## JSONL Format

Each line is a JSON object with:

```json
{
  "input": "The input text or structured data",
  "output": "The expected output (JSON or text)"
}
```

## Fine-Tuning Workflow

1. **Generate datasets**:
   ```bash
   python generate_datasets.py --all
   ```

2. **Load with HuggingFace datasets**:
   ```python
   from datasets import load_dataset

   dataset = load_dataset("json", data_files={
       "train": "datasets/compliance-validator/train.jsonl",
       "validation": "datasets/compliance-validator/val.jsonl"
   })
   ```

3. **Fine-tune with LoRA**:
   ```python
   from peft import LoraConfig, get_peft_model

   lora_config = LoraConfig(
       r=16,
       lora_alpha=32,
       target_modules=["q_proj", "v_proj"],
       lora_dropout=0.05,
       task_type="CAUSAL_LM"
   )

   model = get_peft_model(base_model, lora_config)
   trainer.train()
   ```

## Extending Datasets

To add more examples:

1. Edit `generate_datasets.py`
2. Add examples to the appropriate `generate_*_examples()` method
3. Regenerate datasets

## References

- [HuggingFace Smol Training Playbook](https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook)
- [Anthropic Agent Skills Specification](https://agentskills.io/specification)
- [PEFT (Parameter-Efficient Fine-Tuning)](https://github.com/huggingface/peft)
