"""Safety-first pipeline stages for GuardrailOps."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


@dataclass
class StageResult:
    name: str
    passed: bool
    detail: str
    score: float | None = None


@dataclass
class PipelineResult:
    status: str
    answer: str
    stages: list[StageResult] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_trace(self) -> list[str]:
        lines = [
            f"[trace] status={self.status}",
            f"[trace] answer={self.answer}",
        ]
        for s in self.stages:
            score = f" score={s.score:.2f}" if s.score is not None else ""
            flag = "PASS" if s.passed else "FAIL"
            lines.append(f"[trace] stage={s.name} {flag}{score} detail={s.detail}")
        for k, v in self.meta.items():
            lines.append(f"[trace] meta.{k}={v}")
        return lines


def tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


DEFAULT_CONTEXT = (
    "Digital goods refund policy: customers may request a refund within 14 days "
    "if the download was not completed. Partial downloads are reviewed case by case. "
    "Chargebacks without contacting support may suspend the account."
)


def mock_retrieve(query: str, context: str | None = None) -> str:
    """Return the policy context the answer must be grounded in.

    Callers (CLI, Gradio app) can pass their own policy text; otherwise a
    fixed demo policy is used.
    """
    return (context or "").strip() or DEFAULT_CONTEXT


INJECTION_PATTERNS = [
    r"ignore (all |the |any |previous |prior |your )*(instructions|policy|policies|rules|context)",
    r"disregard (the |all |your )*(instructions|policy|rules|context)",
    r"(reveal|print|show).{0,20}system prompt",
    r"\bjailbreak\b",
    r"developer mode",
    r"pretend (you are|to be) .{0,40}(no|without) (rules|restrictions)",
]


def screen_input(query: str) -> tuple[bool, str]:
    """Cheap pre-model input screen for common prompt-injection phrasing."""
    q = query.lower()
    for pat in INJECTION_PATTERNS:
        if re.search(pat, q):
            hit = re.search(pat, q).group(0)
            return False, f"prompt-injection phrase detected: '{hit}'"
    return True, "no injection pattern matched"


def mock_generate(query: str, context: str) -> tuple[str, float]:
    """Mock model answer grounded in context."""
    answer = (
        "Per the refund policy, you can request a refund within 14 days if the download "
        "was not completed. Partial downloads are reviewed case by case."
    )
    confidence = 0.82
    if "make up" in query.lower() or "hallucinate" in query.lower():
        # Deliberately ungrounded: no overlap with refund policy context.
        answer = "Purple comets grant unlimited store credit on Mars colonies every Tuesday."
        confidence = 0.4
    return answer, confidence


DEFAULT_API_BASE = "https://api.tokenfactory.nebius.com/v1"
DEFAULT_MODEL_ID = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

SYSTEM_PROMPT = (
    "You answer strictly from the provided context. If the context does not "
    "support an answer, reply exactly: INSUFFICIENT_CONTEXT. Keep answers under "
    "80 words."
)


LAST_CALL: dict[str, Any] = {}


def nebius_generate(query: str, context: str, model_id: str) -> tuple[str, float]:
    """Call an NVIDIA open model on Nebius Token Factory (OpenAI-compatible API).

    Uses only the standard library so judges need no extra installs.
    Confidence is a simple proxy: 0.3 when the model reports insufficient
    context, otherwise 0.8. Grounding and eval gates still run afterwards.
    """
    import json
    import urllib.request

    api_key = os.getenv("NEBIUS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("NEBIUS_API_KEY is not set")
    base = (os.getenv("NEBIUS_API_BASE") or DEFAULT_API_BASE).rstrip("/")
    body = {
        "model": model_id,
        "temperature": 0.2,
        "max_tokens": int(os.getenv("MAX_TOKENS", "1500")),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    import time

    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    LAST_CALL.clear()
    LAST_CALL["latency_s"] = round(time.time() - t0, 2)
    LAST_CALL["response_model"] = data.get("model", model_id)
    usage = data.get("usage") or {}
    LAST_CALL["prompt_tokens"] = usage.get("prompt_tokens")
    LAST_CALL["completion_tokens"] = usage.get("completion_tokens")
    msg = data["choices"][0]["message"]
    LAST_CALL["finish_reason"] = data["choices"][0].get("finish_reason")
    answer = (msg.get("content") or "").strip()
    # Some reasoning models wrap thinking in <think> tags; keep only the answer.
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.S).strip()
    confidence = 0.3 if "INSUFFICIENT_CONTEXT" in answer else 0.8
    return answer, confidence


def grounding_score(answer: str, context: str) -> float:
    a = tokenize(answer)
    c = tokenize(context)
    if not a:
        return 0.0
    overlap = len(a & c) / max(len(a), 1)
    return min(1.0, overlap * 1.5)


def eval_score(answer: str, query: str) -> float:
    """Simple quality proxy: length + query term overlap."""
    if not answer.strip():
        return 0.0
    q = tokenize(query)
    a = tokenize(answer)
    overlap = len(q & a) / max(len(q), 1)
    length_ok = 1.0 if 20 <= len(answer.split()) <= 120 else 0.5
    return max(0.0, min(1.0, 0.6 * overlap + 0.4 * length_ok))


def run_pipeline(query: str, context: str | None = None) -> PipelineResult:
    stages: list[StageResult] = []
    mock_mode = _env_bool("MOCK_MODE", True)
    kill = _env_bool("KILL_SWITCH", False)
    eval_threshold = _env_float("EVAL_THRESHOLD", 0.7)
    hitl_threshold = _env_float("HITL_THRESHOLD", 0.55)
    model_id = os.getenv("MODEL_ID") or DEFAULT_MODEL_ID

    meta = {
        "mock_mode": mock_mode,
        "model_id": model_id,
        "eval_threshold": eval_threshold,
        "hitl_threshold": hitl_threshold,
    }

    if kill:
        stages.append(
            StageResult("kill_switch", False, "KILL_SWITCH=true; pipeline short-circuited")
        )
        return PipelineResult(
            status="blocked",
            answer="Request blocked by kill switch. No model call was made.",
            stages=stages,
            meta=meta,
        )
    stages.append(StageResult("kill_switch", True, "inactive"))

    ok, why = screen_input(query)
    stages.append(StageResult("input_screen", ok, why))
    if not ok:
        return PipelineResult(
            status="blocked",
            answer="Blocked: input looks like a prompt-injection attempt. No model call was made.",
            stages=stages,
            meta=meta,
        )

    context = mock_retrieve(query, context)
    stages.append(StageResult("retrieve", True, f"context_chars={len(context)}"))

    if mock_mode:
        answer, confidence = mock_generate(query, context)
        stages.append(
            StageResult("generate", True, "mock NVIDIA/Nebius adapter", score=confidence)
        )
    else:
        try:
            answer, confidence = nebius_generate(query, context, model_id)
            for k, v in LAST_CALL.items():
                meta[f"nebius_{k}"] = v
            stages.append(
                StageResult(
                    "generate",
                    True,
                    f"live Nebius Token Factory model={model_id}",
                    score=confidence,
                )
            )
        except Exception as exc:  # fail closed: never answer without a model result
            stages.append(StageResult("generate", False, f"live call failed: {exc}"))
            return PipelineResult(
                status="blocked",
                answer="Blocked: live model call failed; failing closed.",
                stages=stages,
                meta=meta,
            )

    if not answer or "INSUFFICIENT_CONTEXT" in answer:
        stages.append(
            StageResult(
                "grounding",
                False,
                "model reported the context does not support an answer",
                score=0.0,
            )
        )
        return PipelineResult(
            status="blocked",
            answer="Blocked: the policy context does not support an answer (model replied INSUFFICIENT_CONTEXT).",
            stages=stages,
            meta=meta,
        )

    g = grounding_score(answer, context)
    g_pass = g >= 0.45
    stages.append(
        StageResult(
            "grounding",
            g_pass,
            "claim/context token overlap heuristic",
            score=g,
        )
    )
    if not g_pass:
        return PipelineResult(
            status="blocked",
            answer="Blocked: answer failed grounding check against retrieved context.",
            stages=stages,
            meta=meta,
        )

    e = eval_score(answer, query)
    e_pass = e >= eval_threshold
    stages.append(
        StageResult("eval", e_pass, f"threshold={eval_threshold}", score=e)
    )
    if not e_pass:
        return PipelineResult(
            status="blocked",
            answer="Blocked: answer failed eval gate.",
            stages=stages,
            meta=meta,
        )

    if confidence < hitl_threshold:
        stages.append(
            StageResult(
                "hitl",
                False,
                f"confidence {confidence:.2f} < {hitl_threshold}; hold for human",
                score=confidence,
            )
        )
        return PipelineResult(
            status="needs_human_review",
            answer=answer,
            stages=stages,
            meta=meta,
        )

    stages.append(
        StageResult("hitl", True, "auto-approve; confidence above threshold", score=confidence)
    )
    return PipelineResult(status="ok", answer=answer, stages=stages, meta=meta)
