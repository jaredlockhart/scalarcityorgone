// Keeps the 90s page (this page) in sync with data/products.json without ever regenerating it
// (retro/build.py only runs again for a real layout/copy change). On load this:
//   - fills the Etsy stats (rating, reviews, sales, years) in the masthead's [data-stat] spans
//   - updates each known static listing's price and ingredients, and its photo if Etsy's photo changed
//   - hides a static listing whose product is no longer in the feed (sold / deactivated)
//   - adds a plain listing, at the top of its category, for a product with no static listing yet
// If the fetch fails or the JSON is malformed, it does nothing: the static 17 listings stand, the
// same as with JavaScript off. This is the only JavaScript on this page.
(function () {
  'use strict';

  var CATEGORY_SECTION = { Pyramids: 'section-pyramids', Cloudbusters: 'section-cloudbusters' };
  var FALLBACK_SECTION = 'section-accessories'; // anything that isn't Pyramids/Cloudbusters
  function formatPrice(price) {
    try {
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: price.currency }).format(price.amount);
    } catch (error) {
      return price.currency + ' ' + price.amount;
    }
  }
  function fillStats(shop) {
    if (!shop) return;
    var values = { rating: Number(shop.rating).toFixed(1), reviews: shop.reviews, sales: shop.sales, years: shop.years };
    for (var key in values) {
      var el = document.querySelector('[data-stat="' + key + '"]');
      if (el) el.textContent = values[key];
    }
  }
  // One small GIF from the page's own retro/assets/, same style as the static listings.
  function gifImg(pool, i, maxdim) {
    var el = document.createElement('img');
    el.src = 'retro/assets/' + pool[i % pool.length];
    el.loading = 'lazy';
    el.style.maxWidth = maxdim + 'px';
    el.style.margin = '0 4px';
    el.alt = '';
    return el;
  }

  function gifStrip(pool, start, count, maxdim) {
    var wrap = document.createElement('center');
    for (var i = 0; i < count && pool.length; i++) wrap.append(gifImg(pool, start + i, maxdim));
    return wrap;
  }

  function styledFont(text, face, color, size, bold) {
    var f = document.createElement('font');
    f.face = face; f.color = color; f.size = String(size);
    var host = f;
    if (bold) { var b = document.createElement('b'); f.append(b); host = b; }
    host.textContent = text; // always text, never HTML -- product data comes straight from Etsy
    return f;
  }

  function buildMaterialsTable(materials) {
    var table = document.createElement('table');
    table.className = 'materials';
    table.border = '1'; table.cellPadding = '3'; table.cellSpacing = '1'; table.bgColor = '#6688BB'; table.width = '230';
    var head = table.insertRow().insertCell();
    head.colSpan = 2; head.bgColor = '#000066'; head.align = 'center';
    head.append(styledFont("WHAT'S INSIDE", 'Impact, Arial', '#FFFFFF', 2, true));
    materials.forEach(function (m) {
      var row = table.insertRow();
      var bulletCell = row.insertCell();
      bulletCell.bgColor = '#001040'; bulletCell.width = '18';
      bulletCell.append(gifImg(['bullet-spark.gif'], 0, 16));
      var textCell = row.insertCell();
      textCell.bgColor = '#001040';
      textCell.append(styledFont(m, 'Courier New', '#CCE6FF', 2, false));
    });
    return table;
  }

  // Rebuilds a static listing's WHAT'S INSIDE table when Etsy's materials differ from what was built
  // in. The table's own rows are reused as the pattern, so the bullets and styling stay the same.
  function updateMaterials(container, materials) {
    var table = container.querySelector('table.materials');
    if (!table || !Array.isArray(materials) || !materials.length) return;
    var rows = Array.prototype.slice.call(table.rows, 1); // row 0 is the heading
    if (!rows.length) return;
    var current = rows.map(function (row) { return row.cells[1].textContent.trim(); });
    if (current.join('|') === materials.join('|')) return;
    var patterns = rows.map(function (row) { return row.cloneNode(true); });
    rows.forEach(function (row) { row.remove(); });
    materials.forEach(function (material, i) {
      var row = patterns[i % patterns.length].cloneNode(true);
      (row.cells[1].querySelector('font') || row.cells[1]).textContent = material; // text, never HTML
      table.rows[0].parentNode.append(row);
    });
  }

  // Updates a static listing already on the page: price, ingredients, and the photo if Etsy's changed it.
  function updateKnownListing(container, product) {
    updateMaterials(container, product.materials);
    var priceEl = container.querySelector('[data-price]');
    if (priceEl) priceEl.textContent = formatPrice(product.price);
    var photo = container.querySelector('.hero-photo');
    if (photo && product.image && photo.dataset.image !== product.image) {
      photo.src = product.image;
      photo.dataset.image = product.image;
    }
  }

  // Builds a plain listing (same slim 440px table) for a product with no static listing yet.
  function buildNewListing(product, pools) {
    var pool = pools[product.category] || pools.Accessories || [];
    var container = document.createElement('div');
    container.className = 'listing';
    container.id = 'listing-' + product.id;
    container.dataset.id = String(product.id);
    container.dataset.category = product.category;

    var table = document.createElement('table');
    table.className = 'hero';
    table.border = '3'; table.cellPadding = '6'; table.cellSpacing = '2'; table.bgColor = '#6688BB';
    table.width = '440'; table.align = 'center';

    table.insertRow().insertCell().append(gifStrip(pool, 0, 3, 40));
    table.insertRow().insertCell().append(styledFont(String(product.name).toUpperCase(), 'Times New Roman', '#FFFFFF', 4, true));

    var priceCell = table.insertRow().insertCell();
    priceCell.align = 'center';
    var priceFont = styledFont(formatPrice(product.price), 'Impact, Arial', '#FFFFFF', 7, true);
    priceFont.querySelector('b').className = 'price';
    priceFont.querySelector('b').dataset.price = '';
    priceCell.append(priceFont);

    var buyCell = table.insertRow().insertCell();
    buyCell.align = 'center';
    var buyCenter = document.createElement('center');
    var link = document.createElement('a');
    link.href = product.url;
    link.append(styledFont('BUY / VIEW ON ETSY', 'Comic Sans MS, Arial', '#FFFFFF', 5, true));
    var button = document.createElement('a');
    button.href = product.url;
    button.append(gifImg(['buy-button-blue.gif'], 0, 90));
    buyCenter.append(gifImg(['bullet-arrow-cyan.gif'], 0, 24), ' ', link, ' ', gifImg(['bullet-arrow-ice.gif'], 0, 24),
      document.createElement('br'), button);
    buyCell.append(buyCenter);

    if (product.image) {
      var photoCell = table.insertRow().insertCell();
      var photoLink = document.createElement('a');
      photoLink.href = product.url;
      var photo = document.createElement('img');
      photo.className = 'hero-photo';
      photo.src = product.image;
      photo.dataset.image = product.image;
      photo.width = '100%'; photo.border = '3'; photo.loading = 'lazy';
      photo.alt = product.name; // textContent/alt only: never trust Etsy's name as markup
      photoLink.append(photo);
      photoCell.append(photoLink);
    }

    table.insertRow().insertCell().append(styledFont(
      'New in the shop, handmade in Toronto from authentic stones, crystals, metals and powders.',
      'Times New Roman', '#CCE6FF', 2, false));

    if (Array.isArray(product.materials) && product.materials.length) {
      var matsCell = table.insertRow().insertCell();
      matsCell.align = 'center';
      matsCell.append(buildMaterialsTable(product.materials));
    }

    table.insertRow().insertCell().append(gifStrip(pool, 3, Math.min(5, pool.length), 40));

    container.append(table);
    return container;
  }

  function gifPools() {
    var el = document.getElementById('retro-gif-pools');
    if (!el) return {};
    try {
      return JSON.parse(el.textContent) || {};
    } catch (error) {
      return {};
    }
  }

  async function run() {
    var data;
    try {
      var response = await fetch('data/products.json', { cache: 'no-cache' });
      if (!response.ok) return;
      data = await response.json();
    } catch (error) {
      return; // network/JSON trouble: leave the static page exactly as built
    }
    // An empty list would hide every listing; the sync never writes one, so treat it as a bad feed.
    if (!data || !Array.isArray(data.products) || !data.products.length) return;

    try {
      fillStats(data.shop);

      var byId = {};
      data.products.forEach(function (p) { byId[String(p.id)] = p; });
      var seen = {};
      document.querySelectorAll('.listing[data-id]').forEach(function (container) {
        var id = container.dataset.id;
        seen[id] = true;
        var product = byId[id];
        if (product) updateKnownListing(container, product);
        else container.hidden = true;
      });

      var pools = gifPools();
      data.products.forEach(function (product) {
        if (seen[String(product.id)]) return;
        var section = document.getElementById(CATEGORY_SECTION[product.category] || FALLBACK_SECTION);
        if (section) section.prepend(buildNewListing(product, pools));
      });
    } catch (error) {
      // an unexpected shape in an otherwise-valid feed shouldn't break the page further
    }
  }

  run();
})();
