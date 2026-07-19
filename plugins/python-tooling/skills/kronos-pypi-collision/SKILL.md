---
name: kronos-pypi-collision
description: |
  Fix for `pip install kronos` returning the wrong package when trying to use
  the financial K-line foundation model. Use when: (1) you intend to use the
  Kronos OHLCV/K-line transformer from arXiv 2508.02739 (Shi et al., AAAI 2026),
  (2) `pip install kronos` succeeds but `import kronos` fails with
  `ModuleNotFoundError: No module named 'django'` (the unrelated PyPI package
  is a Django-based scheduler), (3) you can't find a `kronos` pip package that
  exposes `Kronos`/`KronosTokenizer`/`KronosPredictor`. The financial Kronos
  model has no published pip package under that name; install from the GitHub
  repo (`shiyu-coder/Kronos`) instead. Also covers Mac (Apple Silicon) usage:
  device must be `"cpu"` or `"mps"`, never `"cuda:0"`.
author: Claude Code
version: 1.0.0
date: 2026-05-07
---

# Kronos PyPI Namespace Collision

## Problem

The financial **Kronos** foundation model — a decoder-only transformer pretrained on 12B K-line records from 45 exchanges, specifically tokenized for OHLCV (Shi et al., AAAI 2026, arXiv 2508.02739) — does NOT have a published pip package under the name `kronos`. Running `pip install kronos` succeeds but installs a completely unrelated Django-based scheduler, which fails on import with `ModuleNotFoundError: No module named 'django'` if Django isn't already installed (and even if it were, you'd be importing the wrong code).

The actual Kronos model code lives only on GitHub at `shiyu-coder/Kronos`. HuggingFace checkpoints are under the `NeoQuasar/` org. The importable package name is `model`, NOT `kronos`.

## Context / Trigger Conditions

- You're integrating Kronos for crypto / financial K-line forecasting.
- `pip install kronos` succeeds but `import kronos` doesn't expose `Kronos` / `KronosTokenizer` / `KronosPredictor`.
- You see `ModuleNotFoundError: No module named 'django'` after `import kronos`.
- A demo or paper references `from model import Kronos, KronosTokenizer, KronosPredictor` and you can't make `from kronos import ...` work.
- You're configuring a team in a multi-agent crypto-trading system that wants Kronos as a forecaster.

## Solution

Install from source:

```bash
git clone https://github.com/shiyu-coder/Kronos.git ~/.local/kronos
cd ~/.local/kronos
pip install -r requirements.txt
export PYTHONPATH=~/.local/kronos:$PYTHONPATH
```

Make the `PYTHONPATH` export persistent in shell rc (`.zshrc` / `.bashrc`) if Kronos is used regularly.

`requirements.txt` declares (as of 2026-05): `numpy`, `pandas==2.2.2`, `torch>=2.0.0`, `einops==0.8.1`, `huggingface_hub==0.33.1`, `matplotlib==3.9.3`, `tqdm==4.67.1`, `safetensors==0.6.2`. Python 3.10+.

Then in Python:

```python
from model import Kronos, KronosTokenizer, KronosPredictor
import os

# Optional: share HF cache across multiple teams/projects
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/hf"))

# Load tokenizer + model from HuggingFace (NeoQuasar org).
# Tokenizer pairings are paired per-model-size — use the right one:
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-base")

# Build predictor. Device on Mac is "cpu" or "mps" — NEVER "cuda:0".
predictor = KronosPredictor(model, tokenizer, device="cpu", max_context=512)
```

## Tokenizer ↔ Model Pairings

| Model checkpoint                     | Tokenizer                            | Max context |
|---|---|---|
| `NeoQuasar/Kronos-mini` (4M params)  | `NeoQuasar/Kronos-Tokenizer-2k`      | 2048        |
| `NeoQuasar/Kronos-small`             | `NeoQuasar/Kronos-Tokenizer-base`    | 512         |
| `NeoQuasar/Kronos-base`              | `NeoQuasar/Kronos-Tokenizer-base`    | 512         |
| `NeoQuasar/Kronos-large`             | `NeoQuasar/Kronos-Tokenizer-base`    | 512         |

Pairing the wrong tokenizer with a model produces incorrect tokenizations silently — no exception, just bad forecasts. Verify before trusting outputs.

## Verification

Quick smoke test (verified on macOS Darwin 25.x with Python 3.11):

```bash
git clone --depth 1 https://github.com/shiyu-coder/Kronos.git /tmp/kronos_smoke
uv run --python 3.11 \
  --with torch>=2.0.0 --with numpy --with pandas==2.2.2 \
  --with einops==0.8.1 --with huggingface_hub==0.33.1 \
  --with tqdm==4.67.1 --with safetensors==0.6.2 \
  python -c "
import sys; sys.path.insert(0, '/tmp/kronos_smoke')
from model import Kronos, KronosTokenizer, KronosPredictor
import torch
print(f'IMPORT_OK | torch={torch.__version__} | mps={torch.backends.mps.is_available()}')
"
```

Expected: `IMPORT_OK | torch=2.11.0 | mps=True`. The smoke test confirms imports only — it does NOT download checkpoints. For a full check, follow with a tiny `Kronos.from_pretrained("NeoQuasar/Kronos-mini")` (downloads ~16MB).

## Notes

- The repository's importable package is named `model` (with files `model/__init__.py`, `model/kronos.py`, `model/module.py`). DO NOT try `from kronos import Kronos` — that's the wrong name.
- The project's "Live Demo" page (<https://shiyu-coder.github.io/Kronos-demo/>) is a hosted prediction site, NOT a Python loader reference. Pin loader patterns from the HuggingFace model-card README + the GitHub repo's getting-started section. Don't fall back to the demo URL for code shape.
- Mac (Apple Silicon): both `device="cpu"` and `device="mps"` work. NEVER pass `device="cuda:0"` on Mac — silent fall-through can leave you on CPU without you realizing.
- Kronos uses its own `Kronos.from_pretrained` and `KronosTokenizer.from_pretrained` semantics — it is NOT a HuggingFace `transformers.AutoModel`. Don't try `AutoModel.from_pretrained("NeoQuasar/Kronos-base")`.
- This namespace collision may be resolved if shiyu-coder publishes a proper PyPI package later. Re-check before assuming this skill still applies past 2027.
- If running inside an environment where you can't set `PYTHONPATH` (e.g., some sandboxes), `pip install -e ~/.local/kronos` may work as an alternative, depending on the repo's `setup.py` shape.

## References

- Paper: Shi et al., "Kronos: A Foundation Model for K-Line Forecasting", AAAI 2026 — <https://arxiv.org/abs/2508.02739>
- Code: <https://github.com/shiyu-coder/Kronos>
- HuggingFace org: <https://huggingface.co/NeoQuasar>
- Verified install + smoke test: 2026-05-07 on macOS Darwin 25.x, Python 3.11, PyTorch 2.11.0, MPS backend available.
