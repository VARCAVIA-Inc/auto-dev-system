#!/bin/bash

# Script per verificare la salute della configurazione di Vertex AI per VARCAVIA Office

echo "=== Vertex AI Project Profile ==="
echo "Active gcloud account : $(gcloud config get-value account)"
echo "Active project        : $(gcloud config get-value project)"
echo "Impersonated SA       : $(gcloud config get-value auth/impersonate_service_account)"
echo ""

echo "=== Enabled APIs ==="
gcloud services list --enabled --filter="aiplatform.googleapis.com OR iam.googleapis.com OR iamcredentials.googleapis.com" --format="value(config.name)"
echo ""

echo "=== ADC Quota Project ==="
gcloud auth application-default print-access-token > /dev/null 2>&1
ADC_FILE=$(gcloud info --format="value(config.paths.application_default_credentials)")
if [ -f "$ADC_FILE" ]; then
    QUOTA_PROJECT=$(grep "quota_project_id" "$ADC_FILE" | sed 's/.*: "\(.*\)",/\1/')
    echo "ADC Quota Project     : $QUOTA_PROJECT"
else
    echo "ADC file not found."
fi
echo ""

echo "=== Available Gemini Models (Global) ==="
gcloud ai models list --region=global --filter="publisher:google" --format="value(name)" | grep 'gemini'
echo ""

echo "=== Live Haiku Test (Gemini 2.5 Flash) ==="
TEST_PROMPT="Scrivi un haiku sul vento e il mare."
PROJECT_ID=$(gcloud config get-value project)
ACCESS_TOKEN=$(gcloud auth print-access-token)

curl -s -X POST \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    "https://global-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/global/publishers/google/models/gemini-2.5-flash:streamGenerateContent" \
    -d @- <<EOF
{
  "contents": {
    "role": "user",
    "parts": { "text": "$TEST_PROMPT" }
  }
}
EOF
echo ""
echo "=== Done ==="