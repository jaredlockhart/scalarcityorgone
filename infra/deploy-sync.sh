#!/usr/bin/env bash
# Packages sync/ and deploys the Etsy sync Lambda (stack scalarorgone-sync).
#
#   infra/deploy-sync.sh
#
# The Etsy key is read from .env in the main checkout's root, shared by any worktrees (git ignores it; see
# .env.example), or from the environment. Without either, the key already stored in the Lambda is kept.
#
# The 6-hourly schedule is only enabled once a key is set.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$(dirname "$(git -C "$REPO" rev-parse --path-format=absolute --git-common-dir)")/.env"
if [[ -f "$ENV_FILE" ]]; then set -a; source "$ENV_FILE"; set +a; fi
FILES=(index.mjs sync.mjs catalogue.mjs overrides.json)

site_output() {
  aws cloudformation describe-stacks --stack-name scalarorgone-site \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

SITE_BUCKET=$(site_output BucketName)
CODE_BUCKET=$(site_output ArtifactsBucketName)

cd "$REPO/sync"
HASH=$(cat "${FILES[@]}" | shasum -a 256 | cut -c1-16)
CODE_KEY="sync/$HASH.zip"
ZIP=$(mktemp -d)/sync.zip
zip -q "$ZIP" "${FILES[@]}"
aws s3 cp "$ZIP" "s3://$CODE_BUCKET/$CODE_KEY" --only-show-errors

PARAMS=(SiteBucket="$SITE_BUCKET" CodeBucket="$CODE_BUCKET" CodeKey="$CODE_KEY")
if [[ -n "${ETSY_API_KEY:-}" ]]; then
  PARAMS+=(EtsyApiKey="$ETSY_API_KEY" EtsySharedSecret="${ETSY_SHARED_SECRET:?set ETSY_SHARED_SECRET too}")
fi

aws cloudformation deploy --stack-name scalarorgone-sync --template-file "$REPO/infra/sync.yaml" \
  --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset --parameter-overrides "${PARAMS[@]}"
