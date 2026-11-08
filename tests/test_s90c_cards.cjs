// Tests render the real card code in a minimal DOM stand-in; no browser or HA.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const registered = new Map();
const context = vm.createContext({
  HTMLElement: class {}, window: {}, console,
  customElements: { define: (name, cls) => registered.set(name, cls), get: name => registered.get(name) },
});
const folder = path.join(__dirname, '../custom_components/samsungtv_smart/www');
for (const name of ['folder-gallery-card.js', 'samsung-art-upload-card.js']) {
  vm.runInContext(fs.readFileSync(path.join(folder, name), 'utf8'), context);
}
const hostile = '"><img src=x onerror="unexpected()">&';
const escaped = '&quot;&gt;&lt;img src=x onerror=&quot;unexpected()&quot;&gt;&amp;';
const upload = Object.create(registered.get('samsung-art-upload-card').prototype);
upload._config = { title: hostile };
upload._hass = { states: {
  'media_player.one': { attributes: { art_mode_status: 'off', friendly_name: hostile } },
  'media_player.two': { attributes: { art_mode_status: 'off', friendly_name: 'Normal' } },
}};
upload.querySelector = () => ({ addEventListener() {}, style: {} });
upload._render();
assert(!upload.innerHTML.includes(hostile));
assert(upload.innerHTML.includes(`header="${escaped}"`));
assert(upload.innerHTML.includes(`>${escaped}</option>`));

const gallery = Object.create(registered.get('folder-gallery-card').prototype);
const container = { innerHTML: '', querySelectorAll: () => [] };
gallery.shadowRoot = { querySelector: selector => selector === '.gallery-container' ? container : null };
gallery._config = { show_filename: true, server_thumbnails: false };
gallery._images = [{ path: hostile, name: hostile, content_id: hostile }];
gallery._folderSelectorHtml = () => '';
gallery._wireFolderSelector = () => {};
gallery.renderGallery();
assert(!container.innerHTML.includes(hostile));
assert(container.innerHTML.includes(`alt="${escaped}"`));
assert(container.innerHTML.includes(`data-path="${escaped}"`));
assert(container.innerHTML.includes(`data-content-id="${escaped}"`));
gallery.render = () => {};
gallery.setConfig({ folder: '/local/art', title: 'Test', columns: hostile, gap: '</style><img>',
  border_radius: hostile, image_height: hostile, aspect_ratio: hostile });
assert.equal(gallery._config.columns, 4);
assert.equal(gallery._config.gap, '8px');
assert.equal(gallery._config.border_radius, '8px');
assert.equal(gallery._config.image_height, '150px');
assert.equal(gallery._config.aspect_ratio, null);
gallery.setConfig({ folder: '/local/art', columns: 5, image_height: '12rem', aspect_ratio: '16/9' });
assert.equal(gallery._config.columns, 5);
assert.equal(gallery._config.image_height, '12rem');
assert.equal(gallery._config.aspect_ratio, '16/9');
console.log('PASS: upload/gallery HTML escaping and CSS validation');


