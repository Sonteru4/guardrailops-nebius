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
    -> Kill switch (KILL_SWITCH=true blocks before any model call)
    -> Input screen (blocks common prompt-injection phrasing before any model call)
    -> Retrieve (policy context the answer must be grounded in; editable in the UI)
    -> Generate: NVIDIA Nemotron via Nebius Token Factory (or mock mode)
    -> INSUFFICIENT_CONTEXT check + grounding gate (answer vs context)
    -> Eval gate (quality threshold)
    -> Human-in-the-loop hold (low confidence)
    -> Released answer, held for review, or blocked with a reason
```

Every run produces a stage-by-stage audit trace (PASS/FAIL, score, reason).

## Quick start: hosted-style demo UI (Gradio)

```bash
git clone https://github.com/Sonteru4/guardrailops-nebius
cd guardrailops-nebius
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export NEBIUS_API_KEY=your_key   # optional; without it the app runs in mock mode
python app.py                    # open http://127.0.0.1:7860
```

The UI shows the question, the Nemotron answer (or block reason), the verdict and the full audit trace. Built-in examples cover a pass, an unanswerable question, a prompt injection and the kill switch.

### Deploy as a Hugging Face Space

```bash
pip install huggingface_hub && hf auth login      # write token
NEBIUS_API_KEY=your_key ./scripts/deploy_space.sh <your-hf-username>
```

This uploads `app.py`, `src/` and a Space README (`deploy/hf-space/README.md`), and stores `NEBIUS_API_KEY` as a Space secret.

## CLI demo (no UI)

```bash
pip install -r requirements.txt
./scripts/demo_run.sh            # 4 scenarios: pass, unanswerable, injection, kill switch
python -m guardrailops.main --query "Summarize the refund policy for digital goods."
pytest -q                        # 9 tests
```

`scripts/demo_run.sh` uses live mode automatically when `NEBIUS_API_KEY` is set, and mock mode otherwise.

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

## Demo video

`scripts/make_video.py` renders the demo video headlessly: it drives the running Gradio app with Playwright, renders the CLI trace, and adds title cards and captions with ffmpeg.

## Demo video notes (manual recording)

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

https://github.com/Sonteru4/guardrailops-nebius (MIT)
