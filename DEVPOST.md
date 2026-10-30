# GuardrailOps: Devpost submission copy (Nebius x NVIDIA Global AI Hackathon)

DRAFT ONLY. Sanju reviews and submits. Nothing here has been submitted.

Devpost: https://nebiusglobalaihackathon.devpost.com/
Deadline: Fri Oct 30, 2026, 10:00 AM PDT (12:00 PM CT)

## Field values to paste

| Field | Value |
| --- | --- |
| Project name | GuardrailOps |
| Tagline (Elevator pitch) | Safety checks as real pipeline steps around NVIDIA Nemotron on Nebius Token Factory: kill switch, injection screen, grounding, eval and human review. |
| Track | Best Apps and Agents Track |
| Repo URL | https://github.com/Sonteru4/guardrailops-nebius |
| Demo URL | Hugging Face Space URL if deployed, otherwise https://github.com/Sonteru4/guardrailops-nebius#quick-start-hosted-style-demo-ui-gradio |
| Video URL | Public YouTube link to guardrailops-nebius-demo.mp4 (about 90 seconds) |
| Built with | python, gradio, nebius-token-factory, nvidia-nemotron, openai-compatible-api, playwright, pytest |
| IRL Builders and Brews city | Leave blank |

## Project description (About the project)

### Inspiration
Most agent demos generate first and worry about safety later. In regulated production work, an answer that is not supported by the source material, or that nobody would sign off on, should never reach the user. I wanted a small, readable pipeline where every safety check is a named stage that can pass, fail, or hold for a human, and where the default on any failure is to block.

### What it does
GuardrailOps runs every request through explicit stages:
1. Kill switch: blocks the request before any model call.
2. Input screen: blocks common prompt-injection phrasing before any model call.
3. Retrieve: the policy text the answer must be grounded in (editable in the UI).
4. Generate: NVIDIA Nemotron 3 Nano 30B A3B on Nebius Token Factory, prompted to answer only from the context or reply INSUFFICIENT_CONTEXT.
5. Grounding gate: blocks INSUFFICIENT_CONTEXT replies and answers whose content does not overlap the context.
6. Eval gate: blocks answers below a configurable quality threshold.
7. Human-in-the-loop: holds low-confidence answers with a needs_human_review status.

A Gradio app shows the question, the released answer or block reason, the verdict and a full audit trace (PASS or FAIL, score and reason per stage). The same pipeline runs from the CLI. A mock mode runs identical gates offline so anyone can reproduce it without a key.

### How we built it
- Python, standard library only for the pipeline (urllib for HTTP, dataclasses for the trace); Gradio for the demo UI.
- Nebius Token Factory OpenAI-compatible /v1/chat/completions API.
- NVIDIA Nemotron 3 Nano 30B A3B (nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B) by default, switchable in the UI to Nemotron 3 Super or Ultra.
- One stage contract for mock and live inference, so the safety gates are identical in both modes.
- Fail-closed error handling: a missing key or failed live call returns a blocked status, never an unchecked answer.
- Latency and token usage from each Token Factory call are recorded in the trace.
- 9 pytest tests, including the injection screen, INSUFFICIENT_CONTEXT handling and a mocked OpenAI-shape response.
- A headless video pipeline (Playwright plus ffmpeg) that records the app and renders the demo video.
- One-command Hugging Face Space deploy script that stores the key as a Space secret.

### Challenges we ran into
- Keeping the mock and live paths honest: the live model sits behind the exact same stage contract, so the demo is not a different program.
- Reasoning-style output: stripping think blocks and giving the model enough token budget so the gates score only the final answer.
- Picking grounding and eval checks that are easy to explain, while being clear they are simple token-overlap heuristics and not a full guardrail framework.

### Accomplishments that we're proud of
- Kill switch, injection screen, grounding, eval and human review are real control-flow outcomes in code, not README promises.
- Every block points to one stage with a score and a reason.
- The pipeline has zero third-party runtime dependencies, so judges can clone and run it in seconds.

### What we learned
- Treating safety checks as pipeline nodes makes debugging much faster.
- An OpenAI-compatible endpoint made swapping between Nemotron sizes a one-line change.
- Telling the model exactly how to refuse (INSUFFICIENT_CONTEXT) turns "I don't know" into a clean, testable block instead of a guess.

### What's next
- Real retrieval over user-supplied documents.
- A second Nemotron call as a judge, and NVIDIA NeMo Guardrails as an extra stage.
- A review queue for held answers and an exportable audit log.
- A red-team regression pack of jailbreak prompts.
- Deployment on Nebius Serverless Endpoints.

### Updated during the submission period
The scaffold (mock pipeline and tests) was started Oct 27, 2026. During the submission period I added the live Nebius Token Factory and Nemotron adapter, the input screen, INSUFFICIENT_CONTEXT handling, the Gradio app, the Space deploy script and the demo video pipeline.

## Feedback on Nebius Token Factory and NVIDIA tools

- The OpenAI-compatible API was the biggest win: plain HTTP from the Python standard library worked, with no SDK, and switching Nemotron sizes is a single model string.
- The model catalog is clear about model IDs and prices. One thing that tripped me up while reading it: models live in different regions with different base URLs (for example Nemotron 3 Nano in eu-north1 on the default endpoint, Nemotron 3 Super in us-central1). A region column next to the base URL in the quickstart, or a single global endpoint, would save a debugging round trip.
- Nemotron's reasoning-style output needs a larger max_tokens budget and some post-processing so only the final answer is scored. A documented, per-model switch for turning thinking on or off would make guardrail pipelines simpler.
- Requests for the hackathon: a free test key or credits visible right after signup, and a copy-paste curl in the console that already contains a Nemotron model ID.
- LIVE RUN NOTE: [fill after the live run: observed latency and token counts from the trace, and whether the pass and block cases behaved as expected]
