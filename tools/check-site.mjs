import { realpathSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = realpathSync(process.cwd());
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright');
const base = 'http://127.0.0.1:8035';
const browser = await chromium.launch({ headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
const output = join(root, 'reports');
mkdirSync(output, { recursive: true });
const paths = ['/', '/about/', '/guide/', '/guide/super-admin/', '/guide/admin/', '/guide/teacher/', '/guide/accountant/', '/guide/guardian/', '/404.html'];
const checks = [];
const links = new Set();
try {
  for (const [device, viewport] of [['desktop', { width: 1440, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
    const context = await browser.newContext({ viewport, reducedMotion: 'reduce' });
    const externalRequests = [];
    await context.route('**/*', route => {
      if (new URL(route.request().url()).origin !== base) {
        externalRequests.push(route.request().url());
        return route.abort();
      }
      return route.continue();
    });
    for (const path of paths) {
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const response = await page.goto(base + path, { waitUntil: 'networkidle' });
      for (const img of await page.locator('img').all()) {
        await img.scrollIntoViewIfNeeded();
        await img.evaluate(image => image.decode());
      }
      const state = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth > innerWidth,
        h1: document.querySelectorAll('h1').length,
        title: document.title,
        description: document.querySelector('meta[name="description"]')?.content,
        canonical: document.querySelector('link[rel="canonical"]')?.href,
        images: [...document.images].every(image => image.complete && image.naturalWidth > 0 && image.alt.trim()),
        ids: [...document.querySelectorAll('[id]')].map(element => element.id),
        links: [...document.querySelectorAll('a[href]')].map(element => element.href),
        hasMain: !!document.querySelector('main#main'),
        scriptCount: document.scripts.length,
      }));
      if (response.status() !== 200 || state.overflow || state.h1 !== 1 || !state.title || !state.description || !state.canonical || !state.images || !state.hasMain || state.scriptCount || errors.length || new Set(state.ids).size !== state.ids.length) {
        throw new Error(JSON.stringify({ device, path, status: response.status(), state, errors }));
      }
      for (const href of state.links) if (new URL(href).origin === base) links.add(href);
      await page.evaluate(() => scrollTo(0, 0));
      if (['/', '/guide/admin/', '/guide/accountant/', '/about/'].includes(path)) {
        const slug = path === '/' ? 'home' : path.replaceAll('/', '-').replace(/^-|-$/g, '');
        await page.screenshot({ path: join(output, slug + '-' + device + '-preview.png'), fullPage: true, animations: 'disabled' });
      }
      checks.push({ device, path, ...viewport, status: response.status(), overflow: state.overflow, imagesLoaded: state.images, scriptCount: state.scriptCount, jsErrors: errors });
      await page.close();
    }
    if (externalRequests.length) throw new Error('Unexpected external subresources: ' + externalRequests.join(', '));
    await context.close();
  }
  const context = await browser.newContext();
  for (const href of links) {
    const url = new URL(href);
    const response = await context.request.get(href);
    if (response.status() !== 200) throw new Error('Broken internal link: ' + href);
    if (url.hash) {
      const page = await context.newPage();
      await page.goto(href);
      if (!await page.locator('[id=' + JSON.stringify(decodeURIComponent(url.hash.slice(1))) + ']').count()) throw new Error('Broken anchor: ' + href);
      await page.close();
    }
  }
  await context.close();
  writeFileSync(join(output, 'browser-checks.json'), JSON.stringify({ checks, internalLinksChecked: links.size, externalSubresources: 0 }, null, 2) + '\n');
  console.log(`Passed ${checks.length} page/viewport checks and ${links.size} internal links. No horizontal overflow, broken images, tracking scripts or external subresources.`);
} finally {
  await browser.close();
}
