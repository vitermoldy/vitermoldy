// Turns the still plates (tools/plates/*.svg, written by tools/build.py) into assets/*.jpg or *.png,
// rendered by headless Chrome at twice their size so the type stays sharp on high-density screens.
// Uses the zero-dependency Chrome client that ships with taste-skill (design-taste-frontend).
//   node tools/rasterize.mjs
import { readdir, readFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const cdp = await import(pathToFileURL(join(homedir(), '.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs')).href);
const root = fileURLToPath(new URL('..', import.meta.url));
const plates = join(root, 'tools', 'plates');
const assets = join(root, 'assets');

// Plates made of flat colour and type compress better as PNG; plates carrying photographs as JPEG.
const PNG = new Set(['lineup']);

const files = (await readdir(plates)).filter((f) => f.endsWith('.svg'));
const browser = await cdp.Browser.launch({ width: 880, height: 600 });
try {
  for (const f of files) {
    const svg = await readFile(join(plates, f), 'utf8');
    const [, w, h] = svg.match(/viewBox="0 0 (\d+) (\d+)"/).map(Number);
    const name = f.replace(/\.svg$/, '');
    const png = PNG.has(name);
    const out = join(assets, `${name}.${png ? 'png' : 'jpg'}`);
    const page = await browser.newPage({ width: w, height: h, dsf: 2 });
    await page.goto(pathToFileURL(join(plates, f)).href, { settleMs: 600 });
    await page.screenshot({ path: out, format: png ? 'png' : 'jpeg', quality: 86, clip: { x: 0, y: 0, width: w, height: h, scale: 1 } });
    await page.close();
    console.log(`  ${name}: ${w * 2}x${h * 2} -> ${out.slice(root.length)}`);
  }
} finally {
  await browser.close();
}
