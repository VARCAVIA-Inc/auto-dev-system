#!/usr/bin/env bash
# Crea/aggiorna la ConfigMap del DNA e installa Reloader

set -euo pipefail

NAMESPACE="varcavia-services"

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap varcavia-dna --from-file=./dna -n "$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

# Installa Stakater Reloader (ultima versione stabile)
kubectl apply -f https://raw.githubusercontent.com/stakater/Reloader/v1.0.28/deployments/kubernetes/reloader.yaml

echo "ConfigMap DNA e Reloader installati nel namespace ${NAMESPACE}"
