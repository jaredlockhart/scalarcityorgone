// Loads data/products.json (written by the sync Lambda, see sync/) and renders the collection.

const CATEGORY_ORDER = ['Pyramids', 'Cloudbusters', 'Accessories'];

const grid = document.getElementById('grid');
const filters = document.getElementById('filters');
const template = document.getElementById('card-template');

function categoryRank(category) {
  const index = CATEGORY_ORDER.indexOf(category);
  return index === -1 ? CATEGORY_ORDER.length : index;
}

function formatPrice({ amount, currency }) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
}

function renderStats(shop) {
  if (!shop || !shop.reviews) return;
  const values = {
    rating: `${shop.rating.toFixed(1)} ★`,
    reviews: shop.reviews.toLocaleString('en-US'),
    sales: shop.sales.toLocaleString('en-US'),
    years: shop.years === 1 ? '1 year' : `${shop.years} years`,
  };
  for (const [key, value] of Object.entries(values)) {
    document.querySelector(`[data-stat="${key}"]`).textContent = value;
  }
  document.getElementById('stats').hidden = false;
}

function renderCard(product) {
  const card = template.content.firstElementChild.cloneNode(true);
  card.dataset.category = product.category;
  card.querySelector('.card-link').href = product.url;
  const img = card.querySelector('img');
  img.src = product.image;
  img.alt = product.name;
  card.querySelector('.card-category').textContent = product.category;
  card.querySelector('.card-name').textContent = product.name;
  card.querySelector('.card-price').textContent = formatPrice(product.price);
  return card;
}

function applyFilter(category) {
  for (const button of filters.children) {
    button.setAttribute('aria-pressed', String(button.value === category));
  }
  for (const card of grid.children) {
    card.hidden = category !== 'All' && card.dataset.category !== category;
  }
}

function renderFilters(categories) {
  for (const category of ['All', ...categories]) {
    const button = document.createElement('button');
    button.type = 'button';
    button.value = category;
    button.textContent = category;
    button.addEventListener('click', () => applyFilter(category));
    filters.append(button);
  }
  applyFilter('All');
}

function renderProducts(products) {
  const sorted = products
    .map((product, index) => ({ product, index }))
    .sort((a, b) => categoryRank(a.product.category) - categoryRank(b.product.category) || a.index - b.index)
    .map(({ product }) => product);
  grid.replaceChildren(...sorted.map(renderCard));
  const categories = [...new Set(sorted.map((product) => product.category))];
  renderFilters(categories);
}

async function load() {
  try {
    const response = await fetch('data/products.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const { shop, products } = await response.json();
    renderStats(shop);
    renderProducts(products);
  } catch (error) {
    console.error('Could not load products', error);
    grid.replaceChildren();
    document.getElementById('grid-message').hidden = false;
  }
}

load();
