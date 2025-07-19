#!/usr/bin/env bash
set -euo pipefail

echo "=== Vertex AI Project Profile ==="
echo "Active gcloud account : $(gcloud config get-value account)"
echo "Active project        : $(gcloud config get-value project)"
echo "Impersonated SA       : $(gcloud config get-value auth/impersonate_service_account)"
echo ""

echo "=== Enabled APIs ==="
gcloud services list --enabled \
  --filter="aiplatform.googleapis.com OR iam.googleapis.com OR iamcredentials.googleapis.com" \
  --format="value(config.name)"
echo ""

echo "=== ADC Quota Project Check ==="
ADC_FILE=${GOOGLE_APPLICATION_CREDENTIALS:-$HOME/.config/gcloud/application_default_credentials.json}
if [[ -f "$ADC_FILE" ]]; then
  python3 - <<PY
import json, os
with open("$ADC_FILE") as f:
    d=json.load(f)
print("ADC quota_project_id :", d.get("quota_project_id", "not set"))
PY
else
  echo "ADC file not found"
fi
echo ""

echo "=== Available Gemini models (us-central1) ==="
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/$(gcloud config get-value project)/locations/us-central1/publishers/google/models" \
  | grep -E '"displayName":.*gemini' || true
echo ""

echo "=== Live Haiku Test (gemini‑2.5‑flash) ==="
curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/$(gcloud config get-value project)/locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Scrivi un haiku sul codice che finalmente funziona"}]}]}' \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['candidates'][0]['content']['parts'][0]['text'].strip())"
echo ""
echo "=== Done ==="
