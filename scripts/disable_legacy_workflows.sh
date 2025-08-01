#!/usr/bin/env bash
# Disattiva i workflow GitHub Actions legacy rinominandoli
set -euo pipefail

for wf in build-test-push build-and-test security-scan; do
  FILE=".github/workflows/${wf}.yml"
  if [ -f "$FILE" ]; then
    git mv "$FILE" "${FILE}.disabled"
    echo "→ disabilitato $FILE"
  fi
done
