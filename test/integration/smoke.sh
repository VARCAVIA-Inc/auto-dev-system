#!/usr/bin/env bash
set -euo pipefail

echo "-> Waiting state_aggregator to boot..."
sleep 5

grpcurl -plaintext localhost:50051 list | grep -q "StateAggregatorService"

grpcurl -plaintext \
  -d '{"state":{"taskId":"ci","status":"IN_PROGRESS","workerId":"ci"}}' \
  localhost:50051 \
  varcavia.state_aggregator.v1.StateAggregatorService/SetTaskState

echo "Smoke test OK"
