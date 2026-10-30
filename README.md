# GuardrailOps

Production-grade safety checks as first-class steps in an agentic workflow on Nebius Token Factory with an NVIDIA open model.

**Author:** Sanjana Onteru · [sanjanaonteru.com](https://sanjanaonteru.com) · [github.com/Sonteru4](https://github.com/Sonteru4)
**Hackathon:** [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/)
**Deadline:** Fri Oct 30, 2026 ≈ 12:00 PM America/Chicago
**License:** MIT

## Problem

Most agent demos bolt safety on after generation. In regulated production GenAI, grounding, evaluation, and human-in-the-loop must be pipeline steps with kill switches, not aspirational checklists. GuardrailOps treats those checks as first-class nodes so an unsafe or ungrounded answer never reaches the user by default.

## Architecture

```
User query
    -> Planner (NVIDIA open model via Nebius Token Factory, or mock)
    -> Grounding check (claim vs retrieved context)
    -> Eval gate (policy + quality scores)
    -> Human-in-the-loop hold (optional on low confidence)
    -> Response or blocked with reason
```

Stack targets:
- Nebius Token Factory for model hosting / inference
- NVIDIA open model (swap via `MODEL_ID`)
- Python 3.11+ workflow runner with explicit safety stages

## How to run (mock mode, no paid keys)

```bash
cd guardrailops-nebius
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# MOCK_MODE=true is the default; no API keys required
./scripts/demo_run.sh
# or:
python -m guardrailops.main --query "Summarize the refund policy for digital goods."
```

Run tests:

```bash
pytest -q
```

## Live mode (Nebius Token Factory + NVIDIA Nemotron)

```bash
# in .env
MOCK_MODE=false
NEBIUS_API_KEY=your_key_from_tokenfactory.nebius.com
NEBIUS_API_BASE=https://api.tokenfactory.nebius.com/v1
MODEL_ID=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
python -m guardrailops.main --query "Summarize the refund policy for digital goods."
```

The `generate` stage calls the OpenAI-compatible `/chat/completions` endpoint on Nebius Token Factory with an NVIDIA Nemotron open model (standard library only, no SDK). Every later stage (grounding, eval, HITL) is identical in mock and live mode. If the live call fails or no key is set, the pipeline fails closed and returns a blocked status instead of an answer. Retrieval is still a fixed demo policy document in both modes.

## How NVIDIA and Nebius are used

- Model: NVIDIA Nemotron 3 Nano 30B A3B (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`), swappable via `MODEL_ID` (for example `nvidia/nemotron-3-super-120b-a12b`).
- Inference: Nebius Token Factory OpenAI-compatible API.
- Code: `nebius_generate()` in `src/guardrailops/pipeline.py`.

## Demo video notes

Record a 2 to 3 minute walkthrough:
1. Show mock unattended run with grounding pass and eval pass.
2. Show a blocked run (ungrounded claim) and the kill-switch message.
3. Briefly open `SAFETY.md` and the pipeline diagram.
4. Optional: flip to live Nebius Token Factory if keys are available.

Save as `demo.mp4` or upload to YouTube/Loom and paste the URL into Devpost.

## Safety and kill switch

- Grounding failure or eval score below threshold blocks the response.
- `KILL_SWITCH=true` short-circuits the pipeline and returns a safe refusal.
- HITL hold fires when confidence is below `HITL_THRESHOLD`.
- See `SAFETY.md` for what is enforced in code vs aspirational.

## Repo

Intended public repo (after GitHub connect): `https://github.com/Sonteru4/guardrailops-nebius`
