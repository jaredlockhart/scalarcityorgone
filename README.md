# scalarcityorgone
Tools for joyful living

The website for [ScalarOrgone](https://www.etsy.com/shop/ScalarOrgone): a single static page that shows the
Etsy shop's products and links each one to its Etsy listing. Orders happen on Etsy.

```
site/        the static site (index.html, styles.css, app.js, assets/)
  assets/    logo.svg (lettering traced from the original banner; the star and rosette rebuilt as exact
             geometry) and star-mark.svg (just the star)
  data/      products.json + product photos. The page fetches data/products.json when it loads.
sync/        daily Lambda that refreshes site/data from the Etsy API
infra/       CloudFormation templates and the deploy script
```

## Preview locally

```
python3 -m http.server -d site 8000   # then open http://localhost:8000
```

## Deploy

The site is a private S3 bucket behind CloudFront (stack `scalarorgone-site`, us-east-1).

```
infra/deploy-site.sh               # upload pages/styles/scripts/assets and clear the CDN cache
infra/deploy-site.sh --seed-data   # also upload site/data (only until the sync Lambda owns it)
```

Infrastructure changes:

```
aws cloudformation deploy --stack-name scalarorgone-site --template-file infra/site.yaml \
  --parameter-overrides DomainName=scalarorgone.com CertificateArn=<arn from scalarorgone-cert stack>
```

`infra/certificate.yaml` (stack `scalarorgone-cert`) holds the HTTPS certificate for scalarorgone.com and
www.scalarorgone.com. DNS is at name.com, so its validation CNAMEs were added there by hand.

## Product data

`site/data/products.json`:

```json
{
  "updated": "2026-09-27T00:00:00.000Z",
  "shop": { "url": "...", "rating": 5, "reviews": 69, "sales": 195, "years": 5 },
  "products": [
    { "id": "4558993952", "name": "...", "category": "Pyramids",
      "price": { "amount": 333.33, "currency": "CAD" },
      "url": "https://www.etsy.com/listing/4558993952", "image": "data/images/4558993952-8452886199.jpg" }
  ]
}
```

Products are grouped Pyramids → Cloudbusters → Accessories, and the filter buttons are built from the
categories present.

The current file is seed data taken from the shop on 2026-09-27. Once there's an Etsy API key, the sync
Lambda (stack `scalarorgone-sync`) refreshes it every 6 hours, as Etsy's API terms require:

- it reads the shop's active listings from the Etsy Open API v3 and copies each listing's main photo into
  `data/images/`
- `sync/overrides.json` gives listings a shorter display name and a category; listings not in it use their
  Etsy title and a category guessed from the title
- it deletes photos of listings that are no longer active (Etsy's terms only allow keeping content while needed)
- if Etsy returns no listings, it leaves the existing file alone

The Etsy key lives in `.env` at the root of the main checkout (worktrees use that same file), which git ignores:
copy `.env.example` to `.env` and fill in the
keystring and shared secret from https://www.etsy.com/developers/your-apps. Then deploy (the schedule stays off
until a key is set):

```
infra/deploy-sync.sh                                           # package the code and push the key from .env
aws lambda invoke --function-name $(aws cloudformation describe-stacks --stack-name scalarorgone-sync \
  --query "Stacks[0].Outputs[0].OutputValue" --output text) /dev/stdout   # run it now
```

The key is stored as a Lambda environment variable. Logs are in CloudWatch under `/aws/lambda/scalarorgone-sync-*`
and kept for 30 days.

Try it locally (writes into `site/data`):

```
cd sync && npm run sync:local
npm test
```
