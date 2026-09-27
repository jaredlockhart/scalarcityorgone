#!/usr/bin/env bash
# Uploads site/ to the S3 bucket and clears the CloudFront cache.
#
#   infra/deploy-site.sh
#
# Uploads pages, styles, scripts and assets. site/data (products.json + photos) belongs to the Etsy sync
# Lambda, which writes it straight to the bucket, so it's never uploaded or deleted from here.
set -euo pipefail

STACK=scalarorgone-site
SITE_DIR="$(cd "$(dirname "$0")/../site" && pwd)"

output() {
  aws cloudformation describe-stacks --stack-name "$STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

BUCKET=$(output BucketName)
DISTRIBUTION=$(output DistributionId)

aws s3 sync "$SITE_DIR" "s3://$BUCKET" --only-show-errors --delete --exclude "data/*" --exclude ".*" \
  --cache-control "public, max-age=300"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION" --paths "/*" \
  --query "Invalidation.Id" --output text >/dev/null

echo "Deployed to https://$(output DistributionDomain)"
