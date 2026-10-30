#!/usr/bin/env bash
# Deploy the Gradio demo to a Hugging Face Space.
# Needs: `hf auth login` (write token) once. Usage: scripts/deploy_space.sh <hf-username>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USER_NS="${1:?usage: deploy_space.sh <hf-username>}"
REPO="${USER_NS}/guardrailops"
STAGE="$(mktemp -d)"
cp -r "$ROOT/app.py" "$ROOT/src" "$ROOT/LICENSE" "$STAGE/"
printf 'gradio>=5.0\n' > "$STAGE/requirements.txt"
cp "$ROOT/deploy/hf-space/README.md" "$STAGE/README.md"
find "$STAGE" -name __pycache__ -prune -exec rm -rf {} +
hf repo create "$REPO" --repo-type space --space-sdk gradio --exist-ok
hf upload "$REPO" "$STAGE" . --repo-type space --commit-message "Deploy GuardrailOps demo"
if [ -n "${NEBIUS_API_KEY:-}" ]; then
  python3 - "$REPO" <<'PY'
import os, sys
from huggingface_hub import HfApi
HfApi().add_space_secret(sys.argv[1], "NEBIUS_API_KEY", os.environ["NEBIUS_API_KEY"])
print("NEBIUS_API_KEY secret set on the Space")
PY
fi
echo "Space: https://huggingface.co/spaces/${REPO}"
