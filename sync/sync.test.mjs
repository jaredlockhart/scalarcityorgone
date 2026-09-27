import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { sync } from './sync.mjs';

const shop = { shop_id: 7, shop_name: 'ScalarOrgone', review_average: 5, review_count: 69, transaction_sold_count: 195, create_date: 1617235200 };
const listing = {
  listing_id: 1528324112,
  title: 'Quartz Rutile Cloudbuster',
  price: { amount: 77777, divisor: 100, currency_code: 'CAD' },
  images: [{ listing_image_id: 11, rank: 1, url_570xN: 'https://i.etsystatic.com/new.jpg' }],
};

function memoryStore(keys) {
  const objects = new Map(keys.map((key) => [key, 'old']));
  const log = [];
  return {
    objects,
    log,
    async list(prefix) { return [...objects.keys()].filter((key) => key.startsWith(prefix)); },
    async put(key, body) { objects.set(key, body); log.push(`put ${key}`); },
    async delete(key) { objects.delete(key); log.push(`delete ${key}`); },
  };
}

function fakeEtsy(listings) {
  return async (url) => {
    const { pathname } = new URL(url);
    const json = (body) => new Response(JSON.stringify(body));
    if (pathname.endsWith('/shops')) return json({ results: [shop] });
    if (pathname.endsWith('/listings/active')) return json({ results: listings.map(({ images, ...rest }) => rest) });
    if (pathname.endsWith('/listings/batch')) return json({ results: listings });
    if (url === 'https://i.etsystatic.com/new.jpg') return new Response('jpeg');
    return new Response('not found', { status: 404 });
  };
}

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });

test('copies new photos, writes products.json, then deletes photos of removed listings', async () => {
  globalThis.fetch = fakeEtsy([listing]);
  const store = memoryStore(['data/images/1528324112-11.jpg', 'data/images/999-5.jpg', 'data/products.json']);
  const result = await sync({ store, apiKey: 'k', sharedSecret: 's', shopName: 'ScalarOrgone' });

  assert.deepEqual(result, { products: 1, imagesCopied: 0, imagesDeleted: 1 });
  assert.deepEqual(store.log, ['put data/products.json', 'delete data/images/999-5.jpg']);
  assert.equal(JSON.parse(store.objects.get('data/products.json')).products[0].image, 'data/images/1528324112-11.jpg');
});

test('uploads photos it does not have yet', async () => {
  globalThis.fetch = fakeEtsy([listing]);
  const store = memoryStore([]);
  const result = await sync({ store, apiKey: 'k', sharedSecret: 's', shopName: 'ScalarOrgone' });

  assert.deepEqual(result, { products: 1, imagesCopied: 1, imagesDeleted: 0 });
  assert.deepEqual(store.log, ['put data/images/1528324112-11.jpg', 'put data/products.json']);
});

test('leaves everything alone when Etsy returns no listings', async () => {
  globalThis.fetch = fakeEtsy([]);
  const store = memoryStore(['data/images/1528324112-11.jpg', 'data/products.json']);
  await assert.rejects(sync({ store, apiKey: 'k', sharedSecret: 's', shopName: 'ScalarOrgone' }), /no active listings/);
  assert.deepEqual(store.log, []);
});
