#!/usr/bin/env bash
# Imposta la branch protection sul ramo main
# Uso: GITHUB_TOKEN=... ./scripts/branch_protection.sh VARCAVIA-Inc/auto-dev-system

set -euo pipefail

REPO="${1:?Occorre specificare owner/repo}"
BRANCH="main"

gh api --method PUT "repos/${REPO}/branches/${BRANCH}/protection" \
  --field required_status_checks.strict=true \
  --field required_status_checks.contexts[]="ci-lint-and-test" \
  --field required_status_checks.contexts[]="ci-security-scan" \
  --field required_status_checks.contexts[]="dna-validation" \
  --field enforce_admins=true > /dev/null

gh api --method PATCH "repos/${REPO}/branches/${BRANCH}/protection/required_pull_request_reviews" \
  --field required_approving_review_count=2 \
  --field dismiss_stale_reviews=true \
  --field require_code_owner_reviews=false > /dev/null

echo "Branch protection configurata su ${REPO}:${BRANCH}"
