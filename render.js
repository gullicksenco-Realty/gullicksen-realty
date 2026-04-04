const { chromium } = require('playwright');

const files = [
  { html: 'gullicksen-banner-dual-eagle.html', png: 'gullicksen-banner-dual-eagle.png', selector: '.banner' },
  { html: 'gullicksen-banner-dark.html', png: 'gullicksen-banner-dark.png', selector: '.banner' },
  { html: 'gullicksen-logo.html', png: 'gullicksen-logo.png', selector: '.logo-shield' },
];

(async () => {
  const browser = await chromium.launch();
  for (const f of files) {
    const page = await browser.newPage();
    await page.goto('file://' + __dirname + '/' + f.html, { waitUntil: 'networkidle' });
    const el = await page.$(f.selector);
    if (el) {
      await el.screenshot({ path: f.png });
      console.log('Rendered (element):', f.png);
    } else {
      await page.screenshot({ path: f.png, fullPage: true });
      console.log('Rendered (full):', f.png);
    }
    await page.close();
  }
  await browser.close();
})();
