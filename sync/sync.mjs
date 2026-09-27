// Fetches the shop's active listings from the Etsy Open API v3 and writes data/products.json plus
// product photos into a store (S3 in Lambda, a local directory from the CLI).

import { readFileSync } from 'node:fs';
import { buildCatalogue, IMAGE_PREFIX } from './catalogue.mjs';

const API = 'https://openapi.etsy.com/v3/application';
const PAGE_SIZE = 100;

const overrides = JSON.parse(readFileSync(new URL('./overrides.json', import.meta.url), 'utf8'));

function etsyClient({ apiKey, sharedSecret }) {
  return async function get(path, params = {}) {
    const url = new URL(API + path);
    for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
    const response = await fetch(url, { headers: { 'x-api-key': `${apiKey}:${sharedSecret}` } });
    if (!response.ok) throw new Error(`Etsy ${path} returned ${response.status}: ${await response.text()}`);
    return response.json();
  };
}

async function fetchShop(get, shopName) {
  const { results } = await get('/shops', { shop_name: shopName });
  const shop = results.find((s) => s.shop_name.toLowerCase() === shopName.toLowerCase());
  if (!shop) throw new Error(`Etsy shop ${shopName} not found`);
  return shop;
}

async function fetchActiveListings(get, shopId) {
  const listings = [];
  for (let offset = 0; ; offset += PAGE_SIZE) {
    const { results } = await get(`/shops/${shopId}/listings/active`, { limit: PAGE_SIZE, offset });
    listings.push(...results);
    if (results.length < PAGE_SIZE) break;
  }
  // The active-listings endpoint doesn't include photos; the batch endpoint does.
  const withImages = new Map();
  for (let i = 0; i < listings.length; i += PAGE_SIZE) {
    const ids = listings.slice(i, i + PAGE_SIZE).map((l) => l.listing_id);
    const { results } = await get('/listings/batch', { listing_ids: ids.join(','), includes: 'Images' });
    for (const listing of results) withImages.set(listing.listing_id, listing);
  }
  return listings.map((l) => withImages.get(l.listing_id) ?? l);
}

export async function sync({ store, apiKey, sharedSecret, shopName, now = new Date() }) {
  const get = etsyClient({ apiKey, sharedSecret });
  const shop = await fetchShop(get, shopName);
  const listings = await fetchActiveListings(get, shop.shop_id);

  // An empty shop is far more likely to be an API hiccup than a real state, so keep the last good file.
  if (listings.length === 0) throw new Error('Etsy returned no active listings; leaving products.json unchanged');

  const { catalogue, images } = buildCatalogue({ shop, listings, overrides, now });

  // Image keys include Etsy's image id, so an existing key never needs re-uploading.
  const stored = new Set(await store.list(IMAGE_PREFIX));
  let copied = 0;
  for (const { key, url } of images) {
    if (stored.has(key)) continue;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Image ${url} returned ${response.status}`);
    await store.put(key, Buffer.from(await response.arrayBuffer()), {
      contentType: 'image/jpeg',
      cacheControl: 'public, max-age=31536000, immutable',
    });
    copied += 1;
  }

  await store.put('data/products.json', JSON.stringify(catalogue, null, 2) + '\n', {
    contentType: 'application/json',
    cacheControl: 'public, max-age=300',
  });

  // Etsy's API terms only allow keeping content while it's needed, so drop photos of listings that are gone.
  // Done after products.json is written so the page never points at a deleted photo.
  const current = new Set(images.map(({ key }) => key));
  const stale = [...stored].filter((key) => !current.has(key));
  for (const key of stale) await store.delete(key);

  return { products: catalogue.products.length, imagesCopied: copied, imagesDeleted: stale.length };
}
