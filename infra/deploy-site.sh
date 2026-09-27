#!/usr/bin/env bash
# Uploads site/ to the S3 bucket and clears the CloudFront cache.
#
#   infra/deploy-site.sh              # pages, styles, scripts, assets
#   infra/deploy-site.sh --seed-data  # also upload site/data (products.json + photos)
#
# site/data is owned by the Etsy sync Lambda once it's running, so it's only uploaded on request.
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

if [[ "${1:-}" == "--seed-data" ]]; then
  aws s3 sync "$SITE_DIR/data/images" "s3://$BUCKET/data/images" --only-show-errors \
    --cache-control "public, max-age=31536000, immutable"
  aws s3 cp "$SITE_DIR/data/products.json" "s3://$BUCKET/data/products.json" --only-show-errors \
    --cache-control "public, max-age=300" --content-type application/json
fi

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION" --paths "/*" \
  --query "Invalidation.Id" --output text >/dev/null

echo "Deployed to https://$(output DistributionDomain)"
