"""Draws the pixel-art pieces of the profile into assets/pixel/.

Run from the repo root:  python tools/pixel.py
Needs Pillow and fontTools. Colours are PixelFolio's "Hutan" palette and the type is Tiny5, PixelFolio's
pixel face (SIL OFL 1.1, tools/fonts/Tiny5-OFL.txt). Text is drawn as real pixels from Tiny5's glyph
outlines, so it stays sharp at any size and needs no font file.
"""
import base64
import io
import math
import random
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'pixel'
SRC = ROOT / 'tools' / 'src'
FONT = ROOT / 'tools' / 'fonts' / 'Tiny5-latin.woff'

# PixelFolio "Hutan" palette, plus a leaf green, a far-forest green and a deer brown
INK, INK2, MUTED = '#121a14', '#2c3a2f', '#4f5b4d'
COLD, MID, LEAF, FAR = '#0f3d2e', '#1f6e44', '#2f8a55', '#174f35'
WARM, HOT, SOFT, ACCENT = '#f0b429', '#fff36b', '#f8de8f', '#e4572e'
PAPER, PALE = '#eef0e6', '#aab6a5'
DEER = '#b5652c'

KEYS = {'k': INK, 'i': INK2, 'm': MUTED, 'c': COLD, 'g': MID, 'l': LEAF, 'f': FAR, 'w': WARM, 'y': HOT,
        's': SOFT, 'a': ACCENT, 'p': PAPER, 'q': PALE, 'd': DEER}


# ---------------------------------------------------------------- Tiny5 as pixels
class PixelFont:
    """Tiny5 is drawn on a grid of 128 units (8 pixels to the em), so every glyph is a set of whole cells."""

    def __init__(self, path):
        f = TTFont(path)
        self.cmap = f.getBestCmap()
        self.hmtx = f['hmtx']
        self.glyphs = f.getGlyphSet()
        self.cache = {}

    def glyph(self, ch):
        if ch in self.cache:
            return self.cache[ch]
        name = self.cmap.get(ord(ch)) or self.cmap[ord('?')]
        adv = self.hmtx[name][0] // 128
        pen = RecordingPen()
        self.glyphs[name].draw(pen)
        polys, cur = [], []
        for op, pts in pen.value:
            if op == 'moveTo':
                cur = [pts[0]]
            elif op == 'lineTo':
                cur.append(pts[0])
            elif op in ('closePath', 'endPath'):
                if cur:
                    polys.append([(x / 128, y / 128) for x, y in cur])
                cur = []
        cells = set()
        if polys:
            xs = [p[0] for poly in polys for p in poly]
            ys = [p[1] for poly in polys for p in poly]
            for cy in range(math.floor(min(ys)), math.ceil(max(ys))):
                for cx in range(math.floor(min(xs)), math.ceil(max(xs))):
                    px, py = cx + 0.5, cy + 0.5
                    inside = False
                    for poly in polys:
                        n = len(poly)
                        for i in range(n):
                            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
                            if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
                                inside = not inside
                    if inside:
                        cells.add((cx, cy))
        self.cache[ch] = (adv, cells)
        return self.cache[ch]

    def width(self, text, k=1):
        return sum(self.glyph(c)[0] for c in text) * k - k  # drop the trailing space of the last glyph


T5 = PixelFont(FONT)


# ---------------------------------------------------------------- pixel canvas
class Canvas:
    def __init__(self):
        self.px = {}

    def set(self, x, y, c):
        self.px[(int(x), int(y))] = c

    def rect(self, x, y, w, h, c):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.px[(xx, yy)] = c

    def sprite(self, x, y, rows, k=1):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in KEYS:
                    self.rect(x + i * k, y + j * k, k, k, KEYS[ch])

    def text(self, x, base, s, c, k=1, shadow=None):
        """Pixel text with its baseline at `base`. Returns the width drawn."""
        if shadow:
            self.text(x + 1, base + 1, s, shadow, k)  # one unit down and right: a thin pixel shadow
        cx = x
        for ch in s:
            adv, cells = T5.glyph(ch)
            for gx, gy in cells:
                self.rect(cx + gx * k, base - (gy + 1) * k, k, k, c)
            cx += adv * k
        return cx - x - k

    def svg(self, cls=''):
        by = {}
        for (x, y), c in self.px.items():
            by.setdefault(c, {}).setdefault(y, []).append(x)
        out = []
        for c, rows in by.items():
            d = []
            for y, xs in sorted(rows.items()):
                xs.sort()
                start = prev = xs[0]
                for x in xs[1:] + [None]:
                    if x is not None and x == prev + 1:
                        prev = x
                        continue
                    d.append(f'M{start} {y}h{prev - start + 1}v1h-{prev - start + 1}z')
                    if x is not None:
                        start = prev = x
            out.append(f'<path fill="{c}" d="{"".join(d)}"/>')
        body = ''.join(out)
        return f'<g class="{cls}">{body}</g>' if cls else body


def document(w, h, scale, title, body, css=''):
    reduce = '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w * scale}" height="{h * scale}" '
            f'shape-rendering="crispEdges" role="img" aria-labelledby="t"><title id="t">{title}</title>'
            f'<style>{css}{reduce}</style>{body}</svg>')


def write(name, content):
    (OUT / name).write_text(content, encoding='utf-8')
    print(f'  {name}: {len(content.encode()) / 1024:.1f} KiB')


def plate(c, w, h, fill=INK, border=MID):
    """A panel with a one-pixel border and stepped corners."""
    c.rect(1, 1, w - 2, h - 2, fill)
    c.rect(2, 0, w - 4, 1, border)
    c.rect(2, h - 1, w - 4, 1, border)
    c.rect(0, 2, 1, h - 4, border)
    c.rect(w - 1, 2, 1, h - 4, border)
    c.set(1, 1, border)
    c.set(w - 2, 1, border)
    c.set(1, h - 2, border)
    c.set(w - 2, h - 2, border)


# ---------------------------------------------------------------- sprites (8 x 8)
ICONS = {
    'face': ['..yyyy..', '.yyyyyy.', 'yykyykyy', 'yykyykyy', 'yyyyyyyy', 'ykyyyyky', '.ykkkky.', '..yyyy..'],
    'tools': ['.....ww.', '....w..w', '....w.w.', '...www..', '..www...', '.www....', 'www.....', 'ww......'],
    'folder': ['.www....', 'wwwwwwww', 'wssssssw', 'wssssssw', 'wssssssw', 'wssssssw', 'wwwwwwww', '........'],
    'bars': ['......a.', '......a.', '...w..a.', '...w..a.', 'g..w..a.', 'g..w..a.', 'g..w..a.', 'pppppppp'],
    'heart': ['.aa..aa.', 'aaaaaaaa', 'aaaaaaaa', 'aaaaaaaa', '.aaaaaa.', '..aaaa..', '...aa...', '........'],
    'mail': ['pppppppp', 'pkppppkp', 'ppkppkpp', 'pppkkppp', 'pppppppp', 'pppppppp', '........', '........'],
    'star': ['...yy...', '...yy...', 'yyyyyyyy', '.yyyyyy.', '..yyyy..', '.yy..yy.', 'yy....yy', '........'],
    'code': ['..p..p..', '.p....p.', 'p......p', '.p....p.', '..p..p..', '........', '........', '........'],
    'globe': ['..pppp..', '.pkpkkp.', 'pppppppp', 'pkpkkpkp', 'pppppppp', '.pkpkkp.', '..pppp..', '........'],
}
HEART = ['.##...##.', '####.####', '#########', '#########', '.#######.', '..#####..', '...###...', '....#....']


# ---------------------------------------------------------------- banner
def pine(c, cx, base, h, col):
    """A pixel fir: three tiers, each wider than the one above, on a short trunk."""
    tiers = 3
    th = max(3, h // tiers)
    for t in range(tiers):
        top = base - h + t * (th - 1)
        for r in range(th + 1):
            half = r // 2 + t
            c.rect(cx - half, top + r, half * 2 + 1, 1, col)
    c.rect(cx, base - 1, 1, 2, INK)


def banner():
    W, H = 240, 96
    G = 70  # top of the ground
    rnd = random.Random(7)
    base, stars = Canvas(), [Canvas(), Canvas(), Canvas()]
    aur = [Canvas(), Canvas()]
    smoke = [Canvas(), Canvas(), Canvas()]
    flies = [Canvas(), Canvas(), Canvas()]
    water = [Canvas(), Canvas()]
    fire = [Canvas(), Canvas()]
    cursor = Canvas()

    # sky: ink above, cold below, dithered where they meet
    base.rect(0, 0, W, G, INK)
    for y in range(57, G):
        for x in range(W):
            t = (y - 57) / (G - 57)
            if t > 0.5 or (x + y) % 2 == 0 and t > 0.25 or (x % 2 == 0 and y % 2 == 0 and t > 0.05):
                base.set(x, y, COLD)

    # moon
    for y in range(-5, 6):
        for x in range(-5, 6):
            if x * x + y * y <= 26:
                base.set(222 + x, 13 + y, SOFT)
    for x, y in ((220, 11), (221, 11), (224, 15), (223, 16), (219, 15)):
        base.set(x, y, WARM)

    # text block on the left (also keeps stars off the words)
    name1, name2 = 'VITER MOLDY', 'KESUMA'
    sub = 'INFORMATION TECHNOLOGY STUDENT'
    prompt = '> BUILDING SMALL WORLDS'
    assert 8 + T5.width(name1, 2) <= 140 and 8 + T5.width(sub) <= 140, 'title too wide'
    text = Canvas()
    text.text(8, 22, name1, PAPER, 2, shadow=ACCENT)
    text.text(8, 36, name2, PAPER, 2, shadow=ACCENT)
    text.text(8, 46, sub, WARM)
    pw = text.text(8, 55, prompt, PALE)
    cursor.rect(8 + pw + 2, 50, 4, 5, PALE)
    keep_out = lambda x, y: (x < 150 and y < 58) or (x > 210 and y < 22)

    # stars, in three twinkle groups
    for i in range(60):
        x, y = rnd.randrange(2, W - 2), rnd.randrange(2, 52)
        if keep_out(x, y):
            continue
        stars[i % 3].set(x, y, PAPER if rnd.random() < 0.6 else SOFT)

    # aurora over the forest, as in StudyCabin at night: curtains of light hanging from a wavy edge,
    # bright at the top and thinning out below; two frames that swap make it ripple
    for f, cv in enumerate(aur):
        for x in range(148, 214):
            top = 6 + round(3 * math.sin((x + f * 4) / 9.0) + 1.5 * math.sin(x / 4.3))
            length = 7 + round(3 * math.sin((x + f * 6) / 5.0))
            if (x + f) % 7 == 0:
                length -= 3
            for j in range(length):
                if j == 0:
                    cv.set(x, top, LEAF)
                elif j < length * 0.55 or (x + top + j) % 2 == 0:
                    cv.set(x, top + j, MID if j < length * 0.8 else FAR)

    # far forest along the whole horizon, then the near firs round the cabin
    for x in range(0, W, 3):
        h = 5 + rnd.randrange(0, 6)
        pine(base, x, G - 1, h, FAR)
    for cx, h in ((124, 14), (214, 30), (224, 24), (234, 32), (2, 12)):
        pine(base, cx, G, h, COLD)
    for cx, h in ((131, 10), (230, 18)):
        pine(base, cx, G + 1, h, INK2)

    # ground
    base.rect(0, G, W, H - G, MID)
    for _ in range(420):
        x, y = rnd.randrange(0, W), rnd.randrange(G + 1, H)
        base.set(x, y, COLD if rnd.random() < 0.7 else LEAF)
    for x in range(0, W, 2):
        base.set(x, G - 1, LEAF) if rnd.random() < 0.5 else None

    # the cabin (StudyCabin: glass on every side, standing-seam roof, deck, fire bowl, annex)
    base.rect(146, G - 3, 66, 2, MUTED)                 # deck
    base.rect(148, G - 1, 1, 2, INK2)
    base.rect(209, G - 1, 1, 2, INK2)
    base.rect(140, G - 13, 12, 10, INK2)                # annex
    base.rect(143, G - 10, 4, 7, COLD)
    base.rect(152, G - 15, 52, 12, INK)                 # main room
    for i in range(5):
        x = 154 + i * 10
        lit = i in (1, 2, 4)
        base.rect(x, G - 13, 8, 9, WARM if lit else COLD)
        if lit:
            base.rect(x + 1, G - 8, 6, 4, HOT)
            base.rect(x + 3, G - 13, 1, 9, INK)
    for r in range(10):                                 # roof
        x0, x1 = 148 + r * 0, 208
        y = G - 16 - r
        inset = r * 2
        if x0 + inset >= x1 - inset:
            break
        base.rect(x0 + inset, y, (x1 - inset) - (x0 + inset), 1, INK2)
        for sx in range(x0 + inset, x1 - inset, 4):
            base.set(sx, y, MUTED)
    base.rect(194, G - 27, 3, 6, INK2)                  # chimney
    fire[0].rect(160, G - 5, 3, 2, WARM)
    fire[0].set(161, G - 6, HOT)
    fire[1].rect(160, G - 5, 3, 2, ACCENT)
    fire[1].set(160, G - 6, WARM)
    fire[1].set(162, G - 7, HOT)
    for i, cv in enumerate(smoke):
        for j in range(3):
            cv.rect(194 + (j % 2), G - 30 - j * 3, 2, 2, PALE if j < 2 else MUTED)

    # pond in front, with the lit windows in it
    for y in range(-4, 5):
        for x in range(-24, 25):
            if (x / 24) ** 2 + (y / 4.5) ** 2 <= 1:
                base.set(178 + x, G + 11 + y, COLD)
    for f, cv in enumerate(water):
        for x in range(166, 196, 3):
            if (x // 3 + f) % 2 == 0:
                cv.rect(x, G + 9 + (x % 2) + f, 2, 1, WARM)
        cv.rect(200 - f * 2, G + 12, 3, 1, SOFT)

    # a doe by the water
    base.sprite(150, G + 2, ['....dd', '....dk', 'ddddd.', 'ddddd.', 'd...d.', 'd...d.'])

    # fireflies
    for i in range(12):
        x, y = rnd.randrange(10, W - 10), rnd.randrange(G - 8, H - 4)
        if 140 < x < 212 and y < G:
            continue
        flies[i % 3].set(x, y, HOT)

    body = base.svg() + ''.join(s.svg(f'tw tw{i}') for i, s in enumerate(stars))
    body += aur[0].svg('au au0') + aur[1].svg('au au1') + text.svg() + cursor.svg('cur')
    body += ''.join(s.svg(f'sm sm{i}') for i, s in enumerate(smoke))
    body += fire[0].svg('fi fi0') + fire[1].svg('fi fi1') + water[0].svg('wa wa0') + water[1].svg('wa wa1')
    body += ''.join(s.svg(f'ff ff{i}') for i, s in enumerate(flies))
    css = ('.tw{animation:tw 3s steps(1) infinite}.tw1{animation-delay:-1s}.tw2{animation-delay:-2s}'
           '@keyframes tw{0%{opacity:1}50%{opacity:.2}}'
           '.au1,.fi1,.wa1{opacity:0}.au0,.fi0,.wa0{animation:sw 2s steps(1) infinite}'
           '.au1,.fi1,.wa1{animation:sw 2s steps(1) -1s infinite}'
           '.fi0{animation-duration:.6s}.fi1{animation-duration:.6s;animation-delay:-.3s}'
           '@keyframes sw{0%{opacity:1}50%{opacity:0}}'
           '.cur{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}'
           '.sm{animation:up 3s steps(6) infinite;opacity:0}.sm1{animation-delay:-1s}.sm2{animation-delay:-2s}'
           '@keyframes up{0%{transform:translateY(0);opacity:.9}100%{transform:translateY(-12px);opacity:0}}'
           '.ff{animation:tw 2.2s steps(1) infinite}.ff1{animation-delay:-.7s}.ff2{animation-delay:-1.5s}')
    title = ('Pixel art: Viter Moldy Kesuma, Information Technology student, building small worlds. '
             'A pixel StudyCabin at night: lit glass cabin, smoke from the chimney, aurora, stars, a doe by the pond, fireflies.')
    write('banner.svg', document(W, H, 4, title, body, css))


# ---------------------------------------------------------------- section headers and buttons
def tab(name, icon, label, fill=INK, border=MID, ink=HOT, shade=False):
    tw = T5.width(label)
    W, H = 4 + 8 + 4 + tw + 5, 16 if not shade else 18
    c = Canvas()
    if shade:
        c.rect(1, 3, W - 1, H - 3, INK)  # the button's pixel shadow
    plate(c, W - (1 if shade else 0), 16, fill, border)
    c.sprite(4, 4, ICONS[icon])
    c.text(16, 11, label, ink)
    write(name, document(W, H, 4, label.capitalize(), c.svg()))


# ---------------------------------------------------------------- project cards
def pixelate(img, w, h, colours=40):
    """Crop to w:h, shrink to w x h cells, keep a small palette, blow up with hard edges."""
    r = w / h
    iw, ih = img.size
    if iw / ih > r:
        nw = int(ih * r)
        img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw / r)
        img = img.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
    small = img.convert('RGB').resize((w, h), Image.BOX).quantize(colours, dither=Image.Dither.NONE).convert('RGB')
    big = small.resize((w * 4, h * 4), Image.NEAREST)
    buf = io.BytesIO()
    big.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def viygo_art(w, h):
    """No screenshot of Viygo exists here, so a pixel map: blocks, roads, a park, and salon pins."""
    img = Image.new('RGB', (w, h), (15, 61, 46))
    px = img.load()
    rnd = random.Random(11)
    for y in range(h):
        for x in range(w):
            if x % 16 in (0, 1) or y % 12 in (0, 1):
                px[x, y] = (79, 91, 77)
            elif 30 <= x < 46 and 14 <= y < 34:
                px[x, y] = (31, 110, 68)
            elif rnd.random() < 0.04:
                px[x, y] = (44, 58, 47)
    for (x, y) in ((12, 9), (52, 20), (70, 36), (24, 40), (84, 10)):
        for dy, row in enumerate(['.aaa.', 'aapaa', 'aaaaa', '.aaa.', '..a..']):
            for dx, ch in enumerate(row):
                if ch != '.' and 0 <= x + dx - 2 < w and 0 <= y + dy - 5 < h:
                    px[x + dx - 2, y + dy - 5] = (228, 87, 46) if ch == 'a' else (238, 240, 230)
    return img


def card(name, title, stack, picture):
    W, H = 200, 136
    TW, TH = 94, 50  # picture cells, drawn at 2 units each
    c = Canvas()
    plate(c, W, H)
    c.rect(4, 4, TW * 2 + 4, TH * 2 + 4, MID)  # picture frame
    over = Canvas()
    assert 8 + T5.width(title, 2) <= W - 8, title
    assert 8 + T5.width(stack) <= W - 8, stack
    over.text(8, 125, title, HOT, 2)
    over.text(8, 133, stack, PALE)
    href = pixelate(picture, TW, TH)
    body = c.svg() + f'<image href="{href}" x="6" y="6" width="{TW * 2}" height="{TH * 2}" preserveAspectRatio="none" image-rendering="pixelated"/>' + over.svg()
    write(name, document(W, H, 4, f'{title}: {stack}', body))


# ---------------------------------------------------------------- footer
def footer():
    W, H = 240, 24
    rnd = random.Random(5)
    c, flies = Canvas(), [Canvas(), Canvas()]
    c.rect(0, 0, W, H, INK)
    c.rect(0, 16, W, 8, MID)
    for x in range(0, W, 3):
        pine(c, x, 16, 3 + rnd.randrange(0, 5), FAR)
    for _ in range(80):
        c.set(rnd.randrange(0, W), rnd.randrange(17, H), COLD if rnd.random() < 0.7 else LEAF)
    msg = 'THANKS FOR STOPPING BY'
    w = T5.width(msg)
    x0 = (W - w - 12) // 2
    c.sprite(x0, 3, ICONS['heart'])
    c.text(x0 + 12, 10, msg, WARM)
    for i in range(10):
        flies[i % 2].set(rnd.randrange(4, W - 4), rnd.randrange(12, 22), HOT)
    css = '.f1{opacity:0;animation:fl 1.6s steps(1) infinite}.f0{animation:fl 1.6s steps(1) -.8s infinite}@keyframes fl{50%{opacity:0}}'
    body = c.svg() + flies[0].svg('f0') + flies[1].svg('f1')
    write('footer.svg', document(W, H, 4, 'Thanks for stopping by.', body, css))


# ---------------------------------------------------------------- the room
def blend(a, b, t):
    """Mix colour a into colour b by t (0 = b, 1 = a)."""
    a, b = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x * t + y * (1 - t)):02x}' for x, y in zip(a, b))


def glow(src, colour):
    """A one-pixel halo round every lit pixel, for neon."""
    g = Canvas()
    for (x, y) in src.px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            if (x + dx, y + dy) not in src.px:
                g.set(x + dx, y + dy, colour)
    return g


def room():
    """An original pixel room for the owner: coding at night, with the rest of what they do around them
    (camera and tripod, a softbox, an event staff pass, a video edit on the second screen, a photo
    grid on the laptop). A neon sign on the wall changes between their roles."""
    W, H = 256, 144
    rnd = random.Random(21)
    WALL, MORTAR = '#15241d', '#101c16'
    FLOOR, PLANK = '#2c3a2f', '#243128'
    WOOD, WOOD2 = '#7a4a2a', '#9a6438'
    SCREEN = '#0b1410'
    CYAN = '#22b8cf'  # PixelFolio's "Bara" accent
    base = Canvas()

    # wall with a quiet brick pattern, wooden floor, a rug
    base.rect(0, 0, W, 108, WALL)
    for y in range(5, 108, 6):
        base.rect(0, y, W, 1, MORTAR)
        for x in range(0 if (y // 6) % 2 else 6, W, 12):
            base.rect(x, y - 5, 1, 5, MORTAR)
    base.rect(0, 108, W, 36, FLOOR)
    for y in range(113, H, 6):
        base.rect(0, y, W, 1, PLANK)
    for y in range(-6, 7):
        for x in range(-46, 47):
            if (x / 46) ** 2 + (y / 6.5) ** 2 <= 1:
                base.set(128 + x, 136 + y, COLD if (abs(x) + abs(y)) % 9 else MID)

    # window: night sky, moon, firs, and a lit cabin far away
    x0, y0, ww, wh = 190, 8, 56, 46
    base.rect(x0 - 2, y0 - 2, ww + 4, wh + 4, INK2)
    for y in range(wh):
        base.rect(x0, y0 + y, ww, 1, INK if y < wh * 0.45 else COLD)
    for y in range(-3, 4):
        for x in range(-3, 4):
            if x * x + y * y <= 10:
                base.set(234 + x, 17 + y, SOFT)
    for x in range(x0, x0 + ww, 4):
        pine(base, x + 1, y0 + wh - 1, 5 + rnd.randrange(0, 6), FAR)
    base.rect(206, y0 + wh - 7, 8, 4, INK)
    base.set(208, y0 + wh - 6, WARM)
    base.set(211, y0 + wh - 6, WARM)
    base.rect(x0 + ww // 2, y0, 1, wh, INK2)
    base.rect(x0, y0 + wh // 2, ww, 1, INK2)
    base.rect(x0 - 4, y0 + wh + 2, ww + 8, 2, MUTED)
    stars = [Canvas(), Canvas()]
    for i in range(14):
        x, y = rnd.randrange(x0 + 1, x0 + ww - 1), rnd.randrange(y0 + 1, y0 + 20)
        if (x - 234) ** 2 + (y - 17) ** 2 > 20 and x != x0 + ww // 2 and y != y0 + wh // 2:
            stars[i % 2].set(x, y, PAPER)

    # poster: StudyCabin at night
    px0, py0 = 128, 8
    base.rect(px0, py0, 50, 48, INK)
    base.rect(px0 + 2, py0 + 2, 46, 36, COLD)
    base.rect(px0 + 2, py0 + 2, 46, 14, INK)
    for x in range(px0 + 6, px0 + 44):
        base.set(x, py0 + 8 + round(2 * math.sin(x / 3)), MID)
    base.set(px0 + 41, py0 + 6, SOFT)
    base.rect(px0 + 40, py0 + 5, 2, 2, SOFT)
    for x in range(px0 + 2, px0 + 48, 4):
        pine(base, x + 1, py0 + 31, 4 + rnd.randrange(0, 4), FAR)
    base.rect(px0 + 2, py0 + 32, 46, 6, MID)
    base.rect(px0 + 14, py0 + 26, 22, 6, INK)
    for r in range(4):
        base.rect(px0 + 13 + r * 2, py0 + 25 - r, 24 - r * 4, 1, INK2)
    for wx in (16, 21, 26, 31):
        base.rect(px0 + wx, py0 + 28, 3, 3, WARM)
    label = 'CABIN'
    base.text(px0 + (50 - T5.width(label)) // 2, py0 + 45, label, WARM)

    # shelf: camera, lens, film, a plant, PixelFolio's face, books
    base.rect(10, 62, 92, 1, WOOD2)
    base.rect(10, 63, 92, 2, WOOD)
    base.rect(16, 65, 2, 4, INK2)
    base.rect(94, 65, 2, 4, INK2)
    base.rect(14, 53, 16, 9, INK)                      # camera body
    base.rect(19, 51, 6, 2, INK)
    base.rect(14, 53, 3, 9, INK2)
    base.set(27, 52, ACCENT)
    for y in range(-3, 4):
        for x in range(-3, 4):
            if x * x + y * y <= 10:
                base.set(23 + x, 57 + y, MUTED if x * x + y * y > 3 else COLD)
    base.set(22, 56, PAPER)
    base.rect(34, 54, 6, 8, INK2)                      # lens
    base.rect(34, 55, 6, 1, MUTED)
    base.rect(34, 58, 6, 1, MUTED)
    base.rect(44, 56, 5, 6, WARM)                      # film can
    base.rect(44, 55, 5, 1, INK)
    base.rect(54, 57, 8, 5, DEER)                      # plant
    for _ in range(26):
        base.set(54 + rnd.randrange(-2, 10), 48 + rnd.randrange(0, 9), LEAF if rnd.random() < 0.6 else MID)
    for y in range(-3, 4):                             # PixelFolio face figurine
        for x in range(-3, 4):
            if x * x + y * y <= 10:
                base.set(72 + x, 57 + y, HOT)
    for p in ((71, 56), (73, 56), (70, 58), (74, 58), (71, 59), (72, 59), (73, 59)):
        base.set(*p, INK)
    for i, (hgt, col) in enumerate(((9, ACCENT), (8, COLD), (10, WARM), (7, MID), (9, PAPER), (8, CYAN))):
        base.rect(80 + i * 3, 62 - hgt, 2, hgt, col)

    # event staff pass on a hook under the window
    base.set(213, 58, PALE)
    for i in range(6):
        base.set(213 - i, 59 + i, ACCENT)
        base.set(213 + i, 59 + i, ACCENT)
    base.rect(206, 65, 15, 12, PAPER)
    base.rect(206, 65, 15, 3, ACCENT)
    base.text(208, 75, 'EO', INK)

    # softbox on a stand, far right
    base.rect(250, 70, 1, 70, INK2)
    base.rect(241, 60, 15, 13, INK2)
    base.rect(242, 61, 13, 11, SOFT)
    base.rect(243, 62, 11, 9, PAPER)
    for dx in (-5, 0, 5):
        base.set(250 + dx, 140, INK2)
        base.set(250 + dx // 2, 139, INK2)

    # left screen: a video edit (multimedia)
    base.rect(28, 70, 58, 30, INK)
    base.rect(30, 72, 54, 26, SCREEN)
    base.rect(54, 100, 6, 2, INK2)
    for y in range(74, 86):                            # preview: a sunset over firs
        base.rect(32, y, 26, 1, ACCENT if y < 78 else WARM if y < 81 else COLD)
    base.rect(49, 76, 3, 3, HOT)
    for x in range(32, 58, 3):
        pine(base, x + 1, 85, 3 + rnd.randrange(0, 3), INK)
    for i in range(5):                                 # effect panel
        base.rect(60, 75 + i * 2, 6 + (i * 5) % 14, 1, PALE if i % 2 else MUTED)
    for x, w, col in ((32, 12, MID), (45, 8, WARM), (54, 14, ACCENT), (69, 13, MID)):
        base.rect(x, 88, w, 2, col)
    for x, w, col in ((36, 10, CYAN), (50, 18, SOFT)):
        base.rect(x, 91, w, 1, col)
    for x in range(32, 82):                            # audio waveform
        h = 1 + int(abs(math.sin(x * 0.7) * 2 + math.sin(x * 0.23)))
        base.rect(x, 96 - h, 1, h, LEAF)

    # main screen: the code editor (lines drawn in the animated frames below)
    base.rect(98, 64, 60, 38, INK)
    base.rect(100, 66, 56, 32, SCREEN)
    base.rect(124, 102, 8, 1, INK2)
    for y in range(68, 97, 3):
        base.set(101, y, MUTED)

    # desk, laptop with a photo grid, mug, lamp, keyboard, mouse
    base.rect(24, 102, 224, 1, WOOD2)
    base.rect(24, 103, 224, 5, WOOD)
    base.rect(26, 108, 3, 32, INK2)
    base.rect(242, 108, 3, 32, INK2)
    base.rect(166, 100, 34, 2, MUTED)
    base.rect(168, 82, 30, 18, INK)
    base.rect(170, 84, 26, 14, SCREEN)
    base.rect(170, 84, 26, 2, INK2)
    thumbs = [ACCENT, MID, WARM, CYAN, SOFT, COLD, LEAF, HOT, PAPER]
    for r in range(2):
        for c in range(3):
            base.rect(172 + c * 8, 87 + r * 5, 6, 4, thumbs[(r * 3 + c * 2) % len(thumbs)])
    base.rect(214, 94, 6, 8, PAPER)
    base.rect(214, 94, 6, 1, INK2)
    base.rect(220, 96, 2, 1, PAPER)
    base.rect(221, 96, 1, 3, PAPER)
    base.rect(220, 98, 2, 1, PAPER)
    base.rect(232, 100, 10, 2, INK2)
    for i in range(14):
        base.set(237 - i // 3, 100 - i, INK2)
    base.rect(224, 84, 8, 3, INK2)
    base.rect(226, 87, 4, 1, WARM)
    for y in range(88, 102):
        for x in range(222 - (y - 88) // 2, 234 + (y - 88) // 2):
            if (x + y) % 3 == 0 and (x, y) not in base.px:
                base.set(x, y, blend(WARM, WALL, 0.35))
    base.rect(104, 100, 36, 2, INK2)
    for x in range(105, 139, 2):
        base.set(x, 100, PALE)
    base.rect(146, 100, 4, 2, PAPER)

    # tripod and camera on the floor, the computer under the desk
    for leg in (-9, 0, 9):
        for i in range(30):
            base.set(13 + round(leg * i / 30), 110 + i, MUTED)
    base.rect(12, 108, 2, 3, MUTED)
    base.rect(6, 100, 14, 9, INK2)
    base.rect(6, 100, 14, 1, MUTED)
    base.rect(8, 98, 6, 2, INK2)
    base.rect(20, 101, 4, 7, MUTED)
    base.rect(23, 102, 1, 5, PALE)
    base.set(9, 99, ACCENT)
    base.rect(206, 110, 16, 28, INK)
    base.rect(208, 112, 12, 24, INK2)
    for y in range(116, 132, 3):
        base.rect(210, y, 8, 1, INK)

    # animated frames
    code = [Canvas(), Canvas()]
    toks = [LEAF, WARM, PAPER, ACCENT, CYAN, PALE]
    lines = []
    for i in range(14):
        indent = (0, 3, 6, 3, 6, 9)[rnd.randrange(0, 6)]
        segs, x = [], 103 + indent
        for _ in range(rnd.randrange(1, 4)):
            w = rnd.randrange(3, 12)
            segs.append((x, w, rnd.choice(toks)))
            x += w + 2
        lines.append([s for s in segs if s[0] + s[1] < 155])
    for f, cv in enumerate(code):
        for row in range(10):
            for x, w, col in lines[(row + f * 2) % len(lines)]:
                cv.rect(x, 68 + row * 3, w, 1, col)
    cursor = Canvas()
    cursor.rect(140, 95, 2, 2, PAPER)
    playhead = Canvas()
    playhead.rect(32, 86, 1, 12, PAPER)
    steam = [Canvas(), Canvas()]
    for f, cv in enumerate(steam):
        for i in range(5):
            cv.set(216 + (i + f) % 2 + (1 if i > 2 else 0), 92 - i * 2, PALE)
    leds = [Canvas(), Canvas()]
    leds[0].set(210, 114, LEAF)
    leds[1].set(213, 114, HOT)
    leds[0].set(216, 114, CYAN)
    # string lights along the top of the wall, in swags, blinking in two sets
    bulbs = [WARM, ACCENT, CYAN, HOT, '#7cf29a']
    for x in range(W):
        sag = round(3 * abs(math.sin(math.pi * x / 32)))
        base.set(x, 2 + sag, INK2)
    for i, x in enumerate(range(4, W, 8)):
        y = 3 + round(3 * abs(math.sin(math.pi * x / 32)))
        cv = leds[i % 2]
        cv.set(x, y, bulbs[i % len(bulbs)])
        cv.set(x, y + 1, blend(bulbs[i % len(bulbs)], WALL, 0.45))

    # neon sign: one group per role, each with its own colour and glow
    roles = [(['VITERMOLDY'], HOT), (['FRONTEND', 'FULL STACK'], '#7cf29a'), (['PHOTOGRAPHY'], '#ff7a4d'),
             (['EVENT', 'ORGANIZER'], WARM), (['MULTIMEDIA'], CYAN)]
    neon_groups, css = [], []
    for i, (words, col) in enumerate(roles):
        lit = Canvas()
        lit.rect(8, 10, 112, 1, col)
        lit.rect(8, 44, 112, 1, col)
        lit.rect(6, 12, 1, 31, col)
        lit.rect(121, 12, 1, 31, col)
        for p in ((7, 11), (120, 11), (7, 43), (120, 43)):
            lit.set(*p, col)
        bases = [32] if len(words) == 1 else [25, 39]
        for wd, b in zip(words, bases):
            wdt = T5.width(wd, 2)
            assert wdt <= 108, wd
            lit.text(10 + (108 - wdt) // 2, b, wd, col, 2)
        halo = glow(lit, blend(col, WALL, 0.32))
        neon_groups.append(f'<g class="n n{i}">{halo.svg()}{lit.svg()}</g>')
        a, b = i * 20, i * 20 + 20
        css.append(f'@keyframes k{i}{{0%{{opacity:0}}{a}%{{opacity:1}}{a + 1}%{{opacity:.25}}{a + 2}%{{opacity:1}}'
                   f'{b - 0.01:.2f}%{{opacity:1}}{b}%{{opacity:0}}100%{{opacity:0}}}}'
                   f'.n{i}{{animation:k{i} 12.5s steps(1) infinite}}')
    css[0] = css[0].replace('0%{opacity:0}0%{opacity:1}', '0%{opacity:1}')

    # the owner, from behind, in a hoodie with headphones; and the chair
    front, head = Canvas(), Canvas()
    front.rect(110, 104, 36, 24, INK2)                 # chair back
    front.rect(112, 106, 32, 20, MUTED)
    front.rect(126, 128, 4, 8, INK)
    for dx in (-10, 0, 10):
        front.rect(128 + dx - 1, 136, 3, 2, INK)
    for y in range(92, 122):                           # hoodie: round shoulders, then straight down
        half = (7, 12, 15, 17, 18)[y - 92] if y < 97 else 19
        front.rect(128 - half, y, half * 2, 1, MID)
    for y in range(98, 121):                           # sleeves, set off by a darker seam
        front.set(128 - 12, y, COLD)
        front.set(128 + 11, y, COLD)
    front.rect(109, 120, 38, 1, COLD)                  # hem
    front.rect(121, 92, 14, 2, LEAF)                   # hood, bunched at the neck
    front.rect(123, 94, 10, 2, LEAF)
    for y in range(-8, 9):                             # head: dark hair, a little shine on top
        for x in range(-8, 9):
            if (x / 8) ** 2 + (y / 9) ** 2 <= 1:
                head.set(128 + x, 84 + y, INK)
    for x, y in ((-3, -6), (-2, -7), (2, -6), (3, -5), (0, -8), (4, -7)):
        head.set(128 + x, 84 + y, INK2)
    for x in range(-9, 10):                            # headphone band and cups
        y = 84 - round(math.sqrt(max(0, 81 - x * x)))
        head.set(128 + x, y, ACCENT)
    head.rect(117, 81, 3, 7, ACCENT)
    head.rect(136, 81, 3, 7, ACCENT)
    head.rect(118, 82, 1, 5, INK2)
    head.rect(137, 82, 1, 5, INK2)

    body = base.svg() + ''.join(neon_groups)
    body += stars[0].svg('st0') + stars[1].svg('st1')
    body += code[0].svg('c0') + code[1].svg('c1') + cursor.svg('cur') + playhead.svg('ph')
    body += steam[0].svg('sm0') + steam[1].svg('sm1') + leds[0].svg('ld0') + leds[1].svg('ld1')
    body += front.svg() + head.svg('hd')
    css += ['.n{opacity:0}',
            '.st1,.c1,.sm1,.ld1{opacity:0}',
            '.st0,.c0,.sm0,.ld0{animation:sw 2s steps(1) infinite}.st1,.c1,.sm1,.ld1{animation:sw 2s steps(1) -1s infinite}',
            '.c0,.c1{animation-duration:1.6s}.c1{animation-delay:-.8s}.sm0,.sm1{animation-duration:.8s}.sm1{animation-delay:-.4s}',
            '@keyframes sw{0%{opacity:1}50%{opacity:0}}',
            '.cur{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}',
            '.ph{animation:ph 5s steps(25) infinite}@keyframes ph{from{transform:translateX(0)}to{transform:translateX(50px)}}',
            '.hd{animation:nod 1.6s steps(1) infinite}@keyframes nod{50%{transform:translateY(1px)}}',
            '@media (prefers-reduced-motion:reduce){.n0{opacity:1}}']
    title = ('Pixel art: Viter at the desk at night, coding on the main screen, a video edit on the second screen and '
             'a photo grid on the laptop, a camera on a tripod, a softbox, an event staff pass and a StudyCabin poster. '
             'A neon sign changes between VITERMOLDY, FRONTEND / FULL STACK, PHOTOGRAPHY, EVENT ORGANIZER and MULTIMEDIA.')
    write('room.svg', document(W, H, 4, title, body, ''.join(css)))


# ---------------------------------------------------------------- the character in the field
def hair_colours(img):
    """The three hair tones of the picture (dark, mid, light), taken from its most common purple-pink pixels."""
    from collections import Counter
    counts = Counter()
    for r, gr, b, a in img.getdata():
        if a and r > gr + 30 and b > gr + 10:
            counts[(r // 8 * 8, gr // 8 * 8, b // 8 * 8)] += 1
    tones = sorted((c for c, _ in counts.most_common(6)), key=lambda c: sum(c))
    hexes = ['#%02x%02x%02x' % c for c in tones]
    return hexes[0], hexes[len(hexes) // 2], hexes[-1]


def character():
    """The sunset field with the character the owner chose standing in it: a chibi pixel girl with long
    magenta hair (not drawn for this profile; credit pending), brought back to her own pixel grid (78 x 109)
    and cut out of her white background (tools/src/chibi-cutout.png). The wind blows to the right: extra
    strands drawn in her own hair colours stream out to the right, and petals and clouds go the same way."""
    W, H = 128, 96
    rnd = random.Random(33)
    HORIZON = 70
    PINK = '#f2a38a'
    sky = [(0, INK), (12, INK2), (24, '#4a2f2a'), (35, '#8a3b26'), (45, ACCENT), (55, WARM), (63, SOFT)]
    base = Canvas()
    for y in range(HORIZON):                                 # sunset sky in dithered bands
        band = max(i for i, (top, _) in enumerate(sky) if y >= top)
        col = sky[band][1]
        if band + 1 < len(sky) and sky[band + 1][0] - y <= 2:
            nxt = sky[band + 1][1]
            for x in range(W):
                base.set(x, y, nxt if (x + y) % 2 == 0 else col)
        else:
            base.rect(0, y, W, 1, col)
    for y in range(-13, 1):                                  # the sun, half down, on the right
        for x in range(-13, 14):
            d = x * x + y * y
            if d <= 169:
                base.set(104 + x, HORIZON + y, HOT if d <= 100 else PAPER if d <= 132 else SOFT)
    clouds = Canvas()
    for cx, cy, w in ((14, 30, 22), (62, 22, 30), (96, 38, 18), (44, 44, 16)):
        clouds.rect(cx, cy, w, 1, blend(SOFT, '#8a3b26', 0.55))
        clouds.rect(cx + 3, cy - 1, w - 8, 1, blend(SOFT, '#8a3b26', 0.4))
    for x in range(W):                                       # far hills and firs
        h = 3 + round(2 * math.sin(x / 9) + 1.5 * math.sin(x / 4.1))
        base.rect(x, HORIZON - h, 1, h, FAR)
    for x in range(2, W, 5):
        pine(base, x, HORIZON, 4 + rnd.randrange(0, 4), COLD)
    base.rect(0, HORIZON, W, H - HORIZON, MID)               # the field, flowers denser towards the front
    for y in range(HORIZON, H):
        for x in range(W):
            r = rnd.random()
            depth = (y - HORIZON) / (H - HORIZON)
            if r < 0.10:
                base.set(x, y, LEAF)
            elif r < 0.13:
                base.set(x, y, COLD)
            elif r < 0.13 + 0.10 * depth:
                base.set(x, y, rnd.choice([ACCENT, WARM, HOT, PAPER, PINK]))

    # where she stands: half a scene unit per pixel of hers, feet in the grass
    cut = Image.open(SRC / 'chibi-cutout.png').convert('RGBA')
    S = 0.5
    GX, GY = 22.0, 92 - cut.height * S
    for x in range(-11, 12):                                 # her shadow on the grass
        for y in (-1, 0, 1):
            if (x / 11) ** 2 + (y / 1.6) ** 2 <= 1:
                base.set(round(GX + 39 * S) + x, 92 + y, COLD)

    dark, mid, light = hair_colours(cut)

    def strands(phase, front=False):
        """Hair blown out to the right, in her own pixel grid: thick at the root, thin at the tip, a wave
        that grows towards the tip and travels outwards, a darker edge underneath."""
        cv = Canvas()
        if front:
            roots = [(50, 15, -6), (53, 19, 2)]
        else:
            roots = [(58 + k % 3, 12 + round(k * 2.6), 2 + k * 1.4) for k in range(22)]
        for k, (sx, sy, deg) in enumerate(roots):
            theta = math.radians(deg)
            length = (34 + (k * 5) % 18) if not front else 24
            for t in range(length):
                amp = 0.3 + t * 0.07
                wav = amp * math.sin(t * 0.2 - phase + k * 0.45)
                x = sx + t * math.cos(theta) - wav * math.sin(theta)
                y = sy + t * math.sin(theta) + wav * math.cos(theta) + t * t * 0.0025
                width = 3 if t < length * 0.5 else 2 if t < length - 6 else 1
                shine = k % 6 == 2 and length * 0.2 < t < length * 0.6
                cv.rect(round(x), round(y), width, 1, light if shine else mid)
                cv.set(round(x) + width - 1, round(y) + 1, dark)
        return cv

    def placed(cv, cls):
        return f'<g class="{cls}" transform="translate({GX} {GY}) scale({S})">{cv.svg()}</g>'

    back = [placed(strands(p), f'wf wf{i}') for i, p in enumerate((0.0, 2.1, 4.2))]
    fore = [placed(strands(p, True), f'wf wf{i}') for i, p in enumerate((0.0, 2.1, 4.2))]
    big = cut.resize((cut.width * 4, cut.height * 4), Image.NEAREST)
    buf = io.BytesIO()
    big.save(buf, 'PNG', optimize=True)
    href = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    girl = (f'<image href="{href}" x="{GX}" y="{GY}" width="{cut.width * S}" height="{cut.height * S}" '
            f'preserveAspectRatio="none" image-rendering="pixelated"/>')

    front = Canvas()
    for x in range(0, W, 2):                                 # tall flowers in front
        if rnd.random() < 0.55:
            h = rnd.randrange(2, 6)
            front.rect(x, H - h, 1, h, LEAF if rnd.random() < 0.5 else MID)
            front.set(x, H - h - 1, rnd.choice([ACCENT, WARM, HOT, PAPER, PINK]))
    birds = Canvas()
    for bx, by in ((10, 18), (20, 22)):
        for q in ((0, 0), (1, 1), (2, 0), (3, 1), (4, 0)):
            birds.set(bx + q[0], by + q[1], INK)
    petal_back, petal_front, css = [], [], []
    for i in range(16):
        x, y = rnd.randrange(-40, W - 30), rnd.randrange(-10, 70)
        cv = Canvas()
        cv.rect(x, y, 2 if i % 3 else 1, 1, rnd.choice([PINK, PAPER, SOFT, ACCENT, light]))
        dur = 7 + (i % 5) * 1.3
        (petal_front if i % 3 == 0 else petal_back).append(cv.svg(f'pt pt{i}'))
        css.append(f'.pt{i}{{animation:pt {dur:.1f}s steps({int(dur * 20)}) {-rnd.random() * dur:.1f}s infinite}}')

    body = (base.svg() + clouds.svg('cl') + birds.svg('bd') + ''.join(petal_back) + ''.join(back)
            + f'<g class="girl">{girl}</g>' + ''.join(fore) + front.svg() + ''.join(petal_front))
    css += ['.wf1,.wf2{opacity:0}',
            '.wf{animation:wf 1.5s steps(1) infinite}.wf1{animation-delay:-1s}.wf2{animation-delay:-.5s}',
            '@keyframes wf{0%{opacity:1}33.33%,100%{opacity:0}}',
            '.cl{animation:cl 40s steps(40) infinite}@keyframes cl{50%{transform:translateX(20px)}}',
            '.bd{animation:bd 16s steps(160) infinite}@keyframes bd{from{transform:translate(-30px,6px)}to{transform:translate(130px,-6px)}}',
            '@keyframes pt{from{transform:translate(0,0)}to{transform:translate(150px,52px)}}',
            '.girl{animation:br 2.4s steps(1) infinite}@keyframes br{50%{transform:translateY(.5px)}}']
    title = ('Pixel art: a chibi girl with long magenta hair, a white blouse, a pink sash and a navy skirt stands in a '
             'flower field at sunset; the wind blows her hair to the right, petals drift past and two birds cross the sky.')
    write('character.svg', document(W, H, 4, title, body, ''.join(css)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print('drawing')
    banner()
    room()
    character()
    # a transparent strip, 100% wide: placed after a floated picture it can never fit beside it, so the next
    # section always starts below the picture (GitHub strips the clear attribute from <br>)
    write('clear.svg', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 1" width="8" height="1" aria-hidden="true"/>')
    for name, icon, label in (('h-about.svg', 'face', 'ABOUT ME'), ('h-tools.svg', 'tools', 'SKILLS AND TOOLS'),
                              ('h-projects.svg', 'folder', 'PROJECTS'), ('h-stats.svg', 'bars', 'GITHUB STATS'),
                              ('h-graph.svg', 'heart', 'CONTRIBUTIONS'), ('h-contact.svg', 'mail', 'CONNECT WITH ME')):
        tab(name, icon, label)
    card('card-studycabin.svg', 'STUDYCABIN', 'THREE.JS + VITE',
         Image.open(SRC / 'cabin-day.jpg').crop((300, 250, 1300, 780)))
    card('card-songplay.svg', 'SONGPLAY', 'THREE.JS + YOUTUBE', Image.open(SRC / 'sp-autumn.jpg'))
    card('card-pixelfolio.svg', 'PIXELFOLIO', 'ASTRO + TYPESCRIPT', Image.open(SRC / 'tp-pixelfolio-art.jpg'))
    card('card-viygo.svg', 'VIYGO', 'LARAVEL 12 + MYSQL', viygo_art(94, 50))
    footer()


if __name__ == '__main__':
    main()
