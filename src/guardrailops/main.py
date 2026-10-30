"""CLI entry for GuardrailOps."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(description="GuardrailOps demo runner")
    parser.add_argument(
        "--query",
        default="Summarize the refund policy for digital goods.",
        help="User query to run through the safety pipeline",
    )
    args = parser.parse_args(argv)

    # Ensure src layout works when run as python -m from project root.
    from guardrailops.pipeline import run_pipeline

    print("[guardrailops] starting pipeline")
    print(f"[guardrailops] MOCK_MODE={os.getenv('MOCK_MODE', 'true')}")
    print(f"[guardrailops] KILL_SWITCH={os.getenv('KILL_SWITCH', 'false')}")
    print(f"[guardrailops] query={args.query}")

    result = run_pipeline(args.query)
    for line in result.to_trace():
        print(line)
    print(f"[guardrailops] done status={result.status}")
    return 0 if result.status in {"ok", "needs_human_review", "blocked"} else 1


if __name__ == "__main__":
    sys.exit(main())
