#!/usr/bin/env bash
set -euo pipefail

echo "→ waiting for service start…"
sleep 10   # Redis + build + gRPC boot

# Reflection check
grpcurl -plaintext localhost:50051 list | grep -q StateAggregatorService

# Write call
grpcurl -plaintext \
  -d '{"state":{"taskId":"ci","status":"IN_PROGRESS","workerId":"ci"}}' \
  localhost:50051 \
  varcavia.state_aggregator.v1.StateAggregatorService/SetTaskState

echo "✔ smoke test OK"
