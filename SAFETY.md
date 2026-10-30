# SAFETY.md - GuardrailOps

## Enforced in code (this scaffold)

1. **Mock-safe default.** `MOCK_MODE=true` unless explicitly disabled. No network calls in mock mode.
2. **Kill switch.** If `KILL_SWITCH=true`, the runner returns a fixed refusal and skips model/generation steps.
3. **Grounding gate.** Claims must be supported by retrieved context tokens (simple overlap heuristic in stub). Failure -> block.
4. **Eval gate.** Composite score must meet `EVAL_THRESHOLD`. Failure -> block.
5. **HITL hold.** If confidence < `HITL_THRESHOLD`, status is `needs_human_review` and auto-send is disabled.
6. **Structured audit log.** Every run emits a line-per-stage trace (stage, pass/fail, score, reason).
7. **Fail closed in live mode.** A missing NEBIUS_API_KEY or failed Token Factory call returns a blocked status, never an unchecked answer.

## Aspirational (hackathon stretch / post-demo)

- Full RAG retrieval against a real corpus on Nebius storage
- NVIDIA NeMo Guardrails or equivalent policy packs
- Signed audit export and red-team regression suite
- Multi-model judge ensemble for eval
- Production SSO-backed HITL console

## Threat notes for reviewers

This is a demo scaffold. Do not deploy to production without replacing heuristics with production guardrail services, rate limits, authn/z, and data retention controls.
