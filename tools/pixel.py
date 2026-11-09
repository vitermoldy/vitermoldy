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


# ---------------------------------------------------------------- PixelFolio's face
def face():
    W, H = 32, 40
    c = Canvas()
    plate(c, W, H)
    cx, cy, R = 16, 27, 5
    inside = lambda x, y: x * x + y * y <= R * R + R * 0.6
    rnd = random.Random(3)
    body, eyes_open, eyes_shut, heart = Canvas(), Canvas(), Canvas(), Canvas()
    for y in range(-R, R + 1):
        for x in range(-R, R + 1):
            if inside(x, y):
                col = HOT
                if rnd.random() < 0.09:
                    col = rnd.choice([WARM, ACCENT])
                body.set(cx + x, cy + y, col)
    for x, y in ((-3, 1), (3, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)):
        body.set(cx + x, cy + y, INK)
    for ex in (-2, 2):
        eyes_open.set(cx + ex, cy - 2, INK)
        eyes_open.set(cx + ex, cy - 1, INK)
        for dx in (-1, 0, 1):
            eyes_shut.set(cx + ex + dx, cy - 1, INK)
    # the shut eyes need the open ones covered by skin
    for ex in (-2, 2):
        eyes_shut.set(cx + ex, cy - 2, HOT)
    for j, line in enumerate(HEART):
        for i, ch in enumerate(line):
            if ch == '#':
                s = (i * 7 + j * 13) % 10
                heart.set(cx - 4 + i, 9 + j, HOT if s > 7 else WARM if s > 3 else ACCENT)
    body_svg = c.svg() + body.svg() + eyes_open.svg('eo') + eyes_shut.svg('es') + heart.svg('ht')
    css = ('.es{opacity:0;animation:bk 3.2s steps(1) infinite}@keyframes bk{0%,92%{opacity:0}93%,97%{opacity:1}}'
           '.ht{animation:ht 3s steps(8) infinite}'
           '@keyframes ht{0%{transform:translateY(6px);opacity:0}10%{opacity:1}60%{transform:translateY(-2px);opacity:1}'
           '75%,100%{transform:translateY(-4px);opacity:0}}')
    write('face.svg', document(W, H, 6, "PixelFolio's pixel face, blinking, with a pixel heart rising above it.", body_svg, css))


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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print('drawing')
    banner()
    face()
    for name, icon, label in (('h-about.svg', 'face', 'ABOUT ME'), ('h-tools.svg', 'tools', 'LANGUAGES AND TOOLS'),
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
