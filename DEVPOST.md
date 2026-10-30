# GuardrailOps: Devpost submission copy (Nebius x NVIDIA Global AI Hackathon)

DRAFT ONLY. Sanju reviews and submits. Nothing here has been submitted.

Devpost: https://nebiusglobalaihackathon.devpost.com/
Deadline: Fri Oct 30, 2026, 10:00 AM PDT (12:00 PM CT)

## Required submission fields (from the Devpost page, checked Oct 30, 2026)

| Requirement | Status |
| --- | --- |
| Runs on Nebius Token Factory or Nebius AI Cloud, uses at least one NVIDIA open model | Live adapter implemented (Token Factory + Nemotron). NOT yet run against the live API: needs a NEBIUS_API_KEY and one real live run before submit |
| Track selection | Suggest: Best Apps and Agents Track (alt: Coding and Agentic Engineering) |
| Project description | Below |
| Working demo URL (hosted app, demo, or test build) | MISSING. Fallback: the public repo with `scripts/demo_run.sh` as a test build, if the form accepts it |
| Demo video: public YouTube, 3 minutes or shorter, showing Token Factory + NVIDIA model use | MISSING. Script in DEMO_SCRIPT.md |
| Public repo (GitHub/GitLab/Bitbucket) with open source license visible at the top | MIT LICENSE present locally. Repo not pushed yet |
| README with setup and run instructions, highlighting NVIDIA model + Token Factory use | Done (README.md) |
| Feedback on Token Factory / NVIDIA tools | Draft below |
| If the project existed before the submission period, explain what changed | Scaffold started Oct 27, 2026; live Nebius adapter added Oct 30, 2026 |
| IRL Builders and Brews city (optional) | Leave blank unless Sanju attended one |

## Project name
GuardrailOps

## Tagline
Safety checks as real pipeline steps: grounding, eval, human review and a kill switch around NVIDIA Nemotron on Nebius Token Factory.

## Inspiration
Most agent demos generate first and worry about safety later. In regulated production work, an answer that is not supported by the source material, or that nobody would sign off on, should never reach the user. I wanted a small, readable pipeline where every safety check is a named stage that can pass, fail, or hold for a human, and where the default on any failure is to block.

## What it does
GuardrailOps runs every request through explicit stages:
1. Kill switch: `KILL_SWITCH=true` blocks the request before any model call.
2. Retrieve: assembles the context the answer must be based on (a fixed demo policy document today).
3. Generate: calls an NVIDIA Nemotron open model on Nebius Token Factory, prompted to answer only from context.
4. Grounding gate: blocks answers whose content does not overlap the retrieved context.
5. Eval gate: blocks answers below a configurable quality threshold.
6. Human-in-the-loop: holds low-confidence answers with a `needs_human_review` status.
Every run prints a stage-by-stage audit trace with pass/fail, scores and reasons. A mock mode runs the same pipeline offline so anyone can reproduce it without a key.

## How we built it
- Python 3.11, standard library only at runtime (urllib for HTTP, dataclasses for the trace).
- Nebius Token Factory OpenAI-compatible `/v1/chat/completions` API.
- NVIDIA Nemotron 3 Nano 30B A3B (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`) as the default model, swappable through `MODEL_ID` (for example Nemotron 3 Super 120B).
- One shared stage contract for mock and live inference, so the safety gates are identical in both modes.
- Fail-closed error handling: a missing key or failed live call returns a blocked status, never an unchecked answer.
- Environment-driven thresholds (`EVAL_THRESHOLD`, `HITL_THRESHOLD`) and kill switch.
- pytest suite (6 tests): happy path, kill switch, ungrounded block, score range, live call without key fails closed, and live response parsing against the OpenAI response shape.
- `scripts/demo_run.sh` for an unattended trace of a pass and a blocked run.

## Challenges we ran into
- Keeping the mock and live paths honest: the live model sits behind the exact same stage contract so the demo is not a different program.
- Picking grounding and eval heuristics that are easy to explain in a short video, while being clear they are simple token-overlap checks and not a full guardrail framework.
- Handling reasoning-style model output (stripping `<think>` blocks) so the gates score only the final answer.

## Accomplishments that we're proud of
- Kill switch, grounding, eval and human review are real control-flow outcomes in code, not README promises.
- Every failure has a stage name, a score and a reason in the trace.
- Runs with zero third-party runtime dependencies, so judges can clone and run it in seconds.

## What we learned
- Treating safety checks as pipeline nodes makes debugging much faster, because every block points to one stage.
- An OpenAI-compatible endpoint made swapping between Nemotron model sizes a one-line config change.
- A mock mode matters for judging and for tests: the safety logic can be verified without spending tokens.

## What's next
- Real retrieval over user-supplied documents instead of a fixed policy text.
- Stronger grounding checks, such as an NVIDIA guardrails toolkit or a second Nemotron call as a judge.
- A small review UI for held answers, plus an exportable audit log.
- A red-team regression pack of common jailbreak prompts.
- Deployment on Nebius Serverless Endpoints for a hosted demo.

## Feedback on Nebius Token Factory and NVIDIA models (required field, edit after the live run)
- The OpenAI-compatible API meant no SDK was needed; plain HTTP worked.
- [Sanju to add one or two honest notes after the live run: latency, model choice, docs, credits.]

## Built with
python, nebius-token-factory, nvidia-nemotron, openai-compatible-api, pytest

## Links
- Repo: https://github.com/Sonteru4/guardrailops-nebius (to be created and pushed)
- Video: [YouTube URL after recording]
- Demo: [hosted URL or repo test build]
