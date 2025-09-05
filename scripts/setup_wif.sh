#!/usr/bin/env bash
set -euo pipefail

# Create Workload Identity Federation pool+provider for GitHub Actions and
# grant impersonation on a service account.
#
# Usage:
#   scripts/setup_wif.sh <PROJECT_ID> <POOL_NAME> <PROVIDER_NAME> <GITHUB_OWNER> <GITHUB_REPO> <SERVICE_ACCOUNT_EMAIL>
# Example:
#   scripts/setup_wif.sh click-it-3d06c github-pool github-provider ssinha2103 leads_dashboard deployer@click-it-3d06c.iam.gserviceaccount.com

PROJECT_ID=${1:?PROJECT_ID required}
POOL=${2:?POOL_NAME required}
PROVIDER=${3:?PROVIDER_NAME required}
OWNER=${4:?GITHUB_OWNER required}
REPO=${5:?GITHUB_REPO required}
SA_EMAIL=${6:?SERVICE_ACCOUNT_EMAIL required}

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud not found. Install Google Cloud SDK." >&2
  exit 127
fi

echo "Fetching project number..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
if [[ -z "$PROJECT_NUMBER" ]]; then
  echo "Failed to get project number for $PROJECT_ID" >&2
  exit 2
fi

echo "Creating WIF pool if missing..."
if ! gcloud iam workload-identity-pools describe "$POOL" --location=global --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "$POOL" \
    --project "$PROJECT_ID" \
    --location global \
    --display-name "GitHub Actions"
fi

echo "Creating WIF provider if missing..."
if ! gcloud iam workload-identity-pools providers describe "$PROVIDER" --workload-identity-pool "$POOL" --location=global --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
    --project "$PROJECT_ID" \
    --location global \
    --workload-identity-pool "$POOL" \
    --display-name "GitHub OIDC" \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition "attribute.repository=='$OWNER/$REPO'"
fi

WIF_PROVIDER_RESOURCE="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"
echo "Granting impersonation on $SA_EMAIL to GitHub repo via WIF provider..."
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository/$OWNER/$REPO"

echo
echo "Success. Use these GitHub secrets in your repo settings:"
echo "  WORKLOAD_IDENTITY_PROVIDER: $WIF_PROVIDER_RESOURCE"
echo "  SERVICE_ACCOUNT_EMAIL: $SA_EMAIL"

