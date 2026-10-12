# retro/ — the 90s page's generator

This folder is not served. It generates `site/index.html`, the 90s-styled look of the site (the
default at `/`); the modern look lives at `site/modern.html` and is a normal hand-edited page.

- `build.py` writes `site/index.html` from the data in this folder (`products.json`, plus the
  product facts/blurbs/materials and the per-product GIF/layout choices baked into the script
  itself) and the GIFs/photos under `site/retro/`. It's self-contained: it doesn't read anything
  outside this repo. Rebuild after changing a product's copy, materials, price or layout, or after
  adding/removing a GIF in `site/retro/assets/`:

  ```
  python3 retro/build.py
  ```

- `verify.py` checks the result against the artist's hard numbers (GIF variety, animation count,
  marquees, no frame under 80ms, every GIF from an approved topic, nothing unused, everything
  sourced). Run it after `build.py`:

  ```
  python3 retro/verify.py
  ```

- `make_gifs.py` draws the hand-made (non-found) GIFs — toruses, wireframe pyramids, dividers,
  bullets, the counter — straight into `site/retro/assets/` with Pillow. Only needed if you want to
  redraw one of those from scratch; the found GIFs (tesla-electric, pyramids-egypt,
  crystals-geometry, esoteric-homepages) aren't reproduced by it.

- `SOURCES.md`: one line per GIF in `site/retro/assets/` saying where it came from. Almost all are
  found GIFs from GifCities (the Internet Archive's index of GeoCities GIFs); the rest are drawn
  for this page (`make_gifs.py`) or are the site's own logo/star mark recoloured for the dark
  background. The artist reviewed and approved every topic used here — she later dropped the whole
  "dividers-badges" topic, so no GIF whose name starts with `dividers-badges--` may be added back.

- `products.json`: the 17 products' id, name, category, price, Etsy url and the photo path that
  was live on Etsy when the page was last built (recorded as `data-image` on each listing's photo,
  so `site/retro/retro.js` can tell later if the photo changed). Refresh it from
  `site/data/products.json` (or `sync/catalogue.mjs`'s output) before rebuilding if you want the
  static price shown to start closer to current.

The page doesn't need rebuilding to stay current between deploys: `site/retro/retro.js` fetches
`data/products.json` at load and patches prices and each WHAT'S INSIDE table (from the listing's Etsy
materials, which is why the product copy never lists ingredients itself), hides sold-out/deactivated listings, and adds
brand-new listings on top — see its own comments for how. `build.py` is only for changing the
page's structure, copy or decoration.

## Adding decoration for a new product

A new product normally arrives on the page two ways:

1. **You add it as a real hero** (recommended once there's time to lay it out properly): add it to
   `products.json`, give it an entry in `build.py`'s `FACTS` (materials) and `BLURBS` (its three
   lines of copy) dicts, and give it a `HERO_CFG` entry (which GIF pools to pull from and how many
   of each, any `explicit` one-off GIFs, an optional `signature` GIF, and the table's `layout`,
   `border`, `bgcolor` and `width`, picked to look different from its neighbours). Then
   `python3 retro/build.py && python3 retro/verify.py`.

2. **It shows up on its own, with no static listing yet** (a brand-new Etsy listing synced into
   `data/products.json`): `retro.js` builds a plain version of it automatically — see "new
   products" in its header comment. `NEW_PRODUCT_GIF_POOLS` near the bottom of `build.py` is the
   small per-category GIF pool (Pyramids / Cloudbusters / Accessories) it draws from; add a name
   there (any approved GIF already in `site/retro/assets/`, written as `theme--name.gif`) if you
   want more variety in that pool, then rebuild so the page's embedded copy of the pool updates.

Every GIF and the tiled background are found artwork, not original art — see `SOURCES.md` for
where each one came from.
