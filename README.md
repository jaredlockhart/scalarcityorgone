# scalarcityorgone
Tools for joyful living

The website for [ScalarOrgone](https://www.etsy.com/shop/ScalarOrgone): a static page that shows the Etsy
shop's products and links each one to its Etsy listing. Orders happen on Etsy. The site has two looks:

- `/` (`site/index.html`) is the default: a hand-built 90s GeoCities-style page, 17 product "heroes" built
  from found GIFs. It's static HTML generated once by `retro/build.py` (see `retro/README.md`), but stays
  current on its own: `site/retro/retro.js` fetches `data/products.json` on load and patches in prices, each listing's WHAT'S INSIDE ingredients,
  hides listings that are sold or deactivated, and adds a plain listing for anything new on Etsy.
- `/modern.html` is the clean, contemporary look (the site's original design). It fetches
  `data/products.json` directly with `app.js` and renders the whole collection from it, so it always shows
  every current product (no regeneration needed for it to stay current).

Both pages carry a small "LOOK: 90s | MODERN" toggle to switch between them. `/terms.html` (modern style)
is linked from both.

```
site/          the static site
  index.html   the 90s look (generated -- see retro/, do not hand-edit)
  modern.html  the modern look (hand-edited), styles.css, app.js
  terms.html   Terms & Privacy (modern style)
  assets/      logo.svg (lettering traced from the original banner; the star and rosette rebuilt as exact
               geometry) and star-mark.svg (just the star), used by both looks
  retro/       assets/ (the 90s page's GIFs) and products/ (its hero photos), plus retro.js, the only
               JavaScript on the 90s page
  data/        products.json + product photos, written by the sync (not in git). Both looks fetch
               data/products.json when they load.
retro/         generates site/index.html -- see retro/README.md
sync/          Lambda that refreshes site/data from the Etsy API every 6 hours
infra/         CloudFormation templates and deploy scripts
```

## Preview locally

```
cd sync && npm run sync:local && cd ..   # fetch the current products into site/data (needs .env, below)
python3 -m http.server -d site 8000      # then open http://localhost:8000 (the 90s look) or /modern.html
```

The 90s page (`site/index.html`) only needs rebuilding for a layout or copy change:

```
python3 retro/build.py      # writes site/index.html
python3 retro/verify.py     # checks it against the artist's hard numbers
```

## Deploy

The site is a private S3 bucket behind CloudFront (stack `scalarorgone-site`, us-east-1).

```
infra/deploy-site.sh   # upload pages/styles/scripts/assets and clear the CDN cache; site/data is left alone
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

The sync Lambda (stack `scalarorgone-sync`) writes it, and the photos, straight into the S3 bucket every 6
hours, as Etsy's API terms require:

- it reads the shop's active listings from the Etsy Open API v3 and copies each listing's main photo into
  `data/images/`
- `sync/overrides.json` gives listings a shorter display name and a category; listings not in it use their
  Etsy title and a category guessed from the title
- it deletes photos of listings that are no longer active (Etsy's terms only allow keeping content while needed)
- if Etsy returns no listings, it leaves the existing file alone

The Etsy key lives in `.env` at the root of the main checkout (worktrees use that same file), which git ignores:
copy `.env.example` to `.env` and fill in the keystring and shared secret from
https://www.etsy.com/developers/your-apps. Then deploy (the schedule stays off until a key is set):

```
infra/deploy-sync.sh                                           # package the code and push the key from .env
aws lambda invoke --function-name $(aws cloudformation describe-stacks --stack-name scalarorgone-sync \
  --query "Stacks[0].Outputs[0].OutputValue" --output text) /dev/stdout   # run it now
```

The key is stored as a Lambda environment variable. Logs are in CloudWatch under `/aws/lambda/scalarorgone-sync-*`
and kept for 30 days.

Tests:

```
cd sync && npm test
```
