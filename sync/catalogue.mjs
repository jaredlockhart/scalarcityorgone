// Turns Etsy API responses into the site's data/products.json. Pure: no network or storage.

export const IMAGE_PREFIX = 'data/images/';

const YEAR_MS = 365.25 * 24 * 60 * 60 * 1000;

const CATEGORY_KEYWORDS = [
  [/pyramid/i, 'Pyramids'],
  [/cloudbuster/i, 'Cloudbusters'],
];

// Etsy returns titles with HTML entities (&amp;, &#39;, ...).
export function decodeEntities(text) {
  const named = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" };
  return text.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (match, entity) => {
    if (entity[0] === '#') {
      const code = entity[1].toLowerCase() === 'x' ? parseInt(entity.slice(2), 16) : parseInt(entity.slice(1), 10);
      return String.fromCodePoint(code);
    }
    return named[entity.toLowerCase()] ?? match;
  });
}

export function guessCategory(title) {
  const match = CATEGORY_KEYWORDS.find(([pattern]) => pattern.test(title));
  return match ? match[1] : 'Accessories';
}

function primaryImage(listing) {
  const images = [...(listing.images ?? [])].sort((a, b) => a.rank - b.rank);
  return images[0];
}

export function buildCatalogue({ shop, listings, overrides = {}, now = new Date() }) {
  const images = [];
  const products = listings.map((listing) => {
    const id = String(listing.listing_id);
    const title = decodeEntities(listing.title).replace(/\s+/g, ' ').trim();
    const override = overrides[id] ?? {};
    const image = primaryImage(listing);
    let imagePath = null;
    if (image) {
      imagePath = `${IMAGE_PREFIX}${id}-${image.listing_image_id}.jpg`;
      images.push({ key: imagePath, url: image.url_570xN });
    }
    return {
      id,
      name: override.name ?? title,
      category: override.category ?? guessCategory(title),
      price: {
        amount: listing.price.amount / listing.price.divisor,
        currency: listing.price.currency_code,
      },
      url: `https://www.etsy.com/listing/${id}`,
      image: imagePath,
    };
  });

  return {
    catalogue: {
      updated: now.toISOString(),
      shop: {
        url: `https://www.etsy.com/shop/${shop.shop_name}`,
        rating: shop.review_average ?? 0,
        reviews: shop.review_count ?? 0,
        sales: shop.transaction_sold_count ?? 0,
        years: Math.max(1, Math.floor((now.getTime() - shop.create_date * 1000) / YEAR_MS)),
      },
      products,
    },
    images,
  };
}
