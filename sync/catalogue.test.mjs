import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildCatalogue, decodeEntities, guessCategory } from './catalogue.mjs';

const shop = {
  shop_name: 'ScalarOrgone',
  review_average: 5,
  review_count: 69,
  transaction_sold_count: 195,
  create_date: Date.UTC(2021, 3, 1) / 1000,
};

function listing(overrides) {
  return {
    listing_id: 1528324112,
    title: 'Quartz Rutile Cloudbuster Orgonite &ndash; Tensor Rings, EMF Protection',
    price: { amount: 77777, divisor: 100, currency_code: 'CAD' },
    images: [
      { listing_image_id: 22, rank: 2, url_570xN: 'https://i.etsystatic.com/second.jpg' },
      { listing_image_id: 11, rank: 1, url_570xN: 'https://i.etsystatic.com/first.jpg' },
    ],
    ...overrides,
  };
}

test('builds products and shop stats from Etsy responses', () => {
  const { catalogue, images } = buildCatalogue({ shop, listings: [listing()], now: new Date(Date.UTC(2026, 8, 27)) });
  assert.deepEqual(catalogue.shop, { url: 'https://www.etsy.com/shop/ScalarOrgone', rating: 5, reviews: 69, sales: 195, years: 5 });
  assert.deepEqual(catalogue.products[0], {
    id: '1528324112',
    name: 'Quartz Rutile Cloudbuster Orgonite &ndash; Tensor Rings, EMF Protection',
    category: 'Cloudbusters',
    price: { amount: 777.77, currency: 'CAD' },
    url: 'https://www.etsy.com/listing/1528324112',
    image: 'data/images/1528324112-11.jpg',
  });
  assert.deepEqual(images, [{ key: 'data/images/1528324112-11.jpg', url: 'https://i.etsystatic.com/first.jpg' }]);
});

test('overrides replace the Etsy title and category', () => {
  const overrides = { 1528324112: { name: 'Quartz Rutile Cloudbuster', category: 'Specials' } };
  const { catalogue } = buildCatalogue({ shop, listings: [listing()], overrides });
  assert.equal(catalogue.products[0].name, 'Quartz Rutile Cloudbuster');
  assert.equal(catalogue.products[0].category, 'Specials');
});

test('listings without photos get no image', () => {
  const { catalogue, images } = buildCatalogue({ shop, listings: [listing({ images: [] })] });
  assert.equal(catalogue.products[0].image, null);
  assert.deepEqual(images, []);
});

test('decodes the entities Etsy puts in titles', () => {
  assert.equal(decodeEntities('Quartz &amp; Pyrite &quot;Sky&quot; &#39;22 &#x2014; &nbsp;'), 'Quartz & Pyrite "Sky" \'22 — &nbsp;');
});

test('guesses categories from titles', () => {
  assert.equal(guessCategory('8-sided Cheops Orgone Pyramid'), 'Pyramids');
  assert.equal(guessCategory('Earthpipe Cloudbuster'), 'Cloudbusters');
  assert.equal(guessCategory('Orgone Cellphone Sticker'), 'Accessories');
});
