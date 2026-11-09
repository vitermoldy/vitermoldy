// Renders clean frames of StudyCabin-v2 (its built dist/) at chosen hours, UI hidden.
// usage: node tools/render-cabin.mjs <StudyCabin-v2/dist> <outDir>   (ONLY=dawn,day to render some; DRAG_Y / ZOOM move the camera)
// Hours and words follow StudyCabin's src/sim/schedule.js: Coffee 07:20, Study 09:30, Reading 20:05, Journal 22:10.
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { pathToFileURL } from 'node:url';
import { homedir } from 'node:os';

const cdp = await import(pathToFileURL(join(homedir(), '.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs')).href);
const [dist, out] = process.argv.slice(2);
await mkdir(out, { recursive: true });

const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml',
  '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2', '.json': 'application/json',
  '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav', '.glb': 'model/gltf-binary', '.webp': 'image/webp' };
const server = createServer(async (req, res) => {
  try {
    let p = normalize(decodeURIComponent(new URL(req.url, 'http://x').pathname)).replace(/^([/\\])+/, '');
    if (!p || p.endsWith('/') || p.endsWith('\\')) p += 'index.html';
    const body = await readFile(join(dist, p));
    res.writeHead(200, { 'content-type': types[extname(p)] || 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404); res.end(); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}/`;

const shots = [
  { name: 'dawn', minutes: 7 * 60 + 20, weather: 'fog' },
  { name: 'day', minutes: 9 * 60 + 30, weather: 'clear' },
  { name: 'dusk', minutes: 20 * 60 + 5, weather: 'clear' },
  { name: 'night', minutes: 22 * 60 + 10, weather: 'clear' },
];

const W = 1600, H = 900;
const browser = await cdp.Browser.launch({ width: W, height: H, extraArgs: ['--use-angle=swiftshader', '--ignore-gpu-blocklist'] });
try {
  for (const s of shots.filter((x) => !process.env.ONLY || process.env.ONLY.split(',').includes(x.name))) {
    const page = await browser.newPage({ width: W, height: H });
    const state = {
      clock: { minutes: s.minutes, day: 3, speed: 'paused' },
      climate: { season: 'summer', autoSeason: false, weatherMode: s.weather, weather: s.weather },
      view: { words: false },
      ambient: { on: false },
    };
    await page.send('Page.enable');
    await page.send('Page.addScriptToEvaluateOnNewDocument', {
      source: `try { localStorage.setItem('studycabin:v2', ${JSON.stringify(JSON.stringify(state))}); } catch (e) {}`,
    });
    await page.goto(base, { settleMs: 9000 });
    await page.eval(`(() => { const st = document.createElement('style'); st.textContent =
      'header.top, footer.controls, .hero__words, .lines, .toast, .panel, .skip-link { display: none !important; } #poster { opacity: 0 !important; }';
      document.head.appendChild(st); })()`);
    await cdp.sleep(1500);
    const dragY = Number(process.env.DRAG_Y || 0);
    const zoom = Number(process.env.ZOOM || 0);
    if (dragY) {
      const x = W / 2, y0 = H * 0.7, steps = 20;
      await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y: y0 });
      await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y: y0, button: 'left', buttons: 1, clickCount: 1 });
      for (let i = 1; i <= steps; i++) {
        await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y: y0 - (dragY * i) / steps, button: 'left', buttons: 1 });
        await cdp.sleep(30);
      }
      await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y: y0 - dragY, button: 'left', buttons: 0, clickCount: 1 });
    }
    if (zoom) {
      await page.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: W / 2, y: H / 2, deltaX: 0, deltaY: zoom });
    }
    if (dragY || zoom) await cdp.sleep(3500);
    const info = await page.eval(`(() => ({ canvas: !!document.querySelector('#scene'), poster: getComputedStyle(document.querySelector('#poster')).opacity }))()`);
    await page.screenshot({ path: join(out, `cabin-${s.name}.jpg`), format: 'jpeg', quality: 90 });
    console.log(s.name, JSON.stringify(info));
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
}
