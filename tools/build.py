"""Builds the profile's plates from tools/src and tools/fonts.

Run from the repo root:  python tools/build.py && node tools/rasterize.mjs
Needs Pillow and fontTools. Every plate starts as one self-contained SVG (the font a WOFF subset, the
pictures embedded JPEGs). The hero ships as that SVG, because it moves; the still plates go to
tools/plates and tools/rasterize.mjs renders them into assets/ as JPEG or PNG at twice their size.
Design decisions and their reasons are in DESIGN.md.
"""
import base64
import io
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'tools' / 'src'
OUT = ROOT / 'assets'
PLATES = ROOT / 'tools' / 'plates'  # still plates; tools/rasterize.mjs turns them into assets/*.jpg|png
VF = ROOT / 'tools' / 'fonts' / 'InstrumentSans-VF.ttf'

# ---------------------------------------------------------------- tokens
# StudyCabin's own colours (mist, ink, lamp amber) on a green-black ground from its night forest.
BG = '#0e1613'
INK = '#e4e5e1'      # StudyCabin "mist"
INK_DARK = '#171716' # StudyCabin "ink", for type over light sky or fog
MUTED = '#a3ada6'
ACCENT = '#d9a05b'   # StudyCabin "lamp amber": the one warm note
PAPER = INK

W = 880   # every plate is 880 units wide; GitHub shows it at about 830px on desktop, 330px on a phone
M = 32    # outer margin
TEXT = 36 # smallest type on any plate (about 13px on a phone)


# ---------------------------------------------------------------- colour maths
def lum(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def contrast(a, b):
    la, lb = sorted((a, b), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def region_lums(img, box):
    """Luminance of every pixel under box (in the image's own pixels), sorted."""
    crop = img.crop(tuple(int(v) for v in box)).convert('RGB').resize((60, 20))
    raw = crop.tobytes()
    return sorted(lum(raw[i:i + 3]) for i in range(0, len(raw), 3))


def best_ink(img, box):
    """Pick light or dark ink for type over a picture, by the worst pixel under it (StudyCabin does the same live)."""
    ls = region_lums(img, box)
    hi, lo = ls[int(len(ls) * 0.95) - 1], ls[int(len(ls) * 0.05)]
    light = contrast(lum(hex_rgb(INK)), hi)
    dark = contrast(lum(hex_rgb(INK_DARK)), lo)
    return (INK, light) if light >= dark else (INK_DARK, dark)


# ---------------------------------------------------------------- font
class Face:
    def __init__(self, weight):
        f = instantiateVariableFont(TTFont(VF), {'wght': weight, 'wdth': 100})
        self.upm = f['head'].unitsPerEm
        self.cmap = f.getBestCmap()
        self.hmtx = f['hmtx']
        opts = subset.Options()
        opts.flavor = 'woff'
        opts.layout_features = ['kern', 'liga', 'calt', 'tnum', 'case']
        opts.name_IDs = ['*']
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=list(range(0x20, 0x7F)) + [0xB7, 0x2019])
        sub.subset(f)
        f.flavor = 'woff'
        buf = io.BytesIO()
        f.save(buf)
        self.woff = base64.b64encode(buf.getvalue()).decode()
        self.weight = weight

    def width(self, text, size, tracking=0.0):
        units = sum(self.hmtx[self.cmap[ord(c)]][0] for c in text)
        return units / self.upm * size + tracking * size * (len(text) - 1)


REGULAR = Face(400)
MEDIUM = Face(500)


def style(extra=''):
    faces = ''.join(
        f"@font-face{{font-family:IS;font-weight:{f.weight};src:url(data:font/woff;base64,{f.woff}) format('woff')}}"
        for f in (REGULAR, MEDIUM))
    return (f'<style>{faces}'
            "text{font-family:IS,'Segoe UI',system-ui,sans-serif;font-weight:400;font-kerning:normal}"
            f'{extra}</style>')


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def text(x, y, s, size, fill, anchor='start', tracking=0.0, weight=400):
    ls = f' letter-spacing="{tracking * size:.2f}"' if tracking else ''
    fw = f' font-weight="{weight}"' if weight != 400 else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{ls}{fw}>'
            f'{esc(s)}</text>')


def jpeg(img, quality=74):
    buf = io.BytesIO()
    img.convert('RGB').save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def image(href, x, y, w, h):
    return f'<image href="{href}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" preserveAspectRatio="none"/>'


def svg(h, title, body, extra_style=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
            f'role="img" aria-labelledby="t"><title id="t">{esc(title)}</title>{style(extra_style)}'
            f'<rect width="{W}" height="{h}" fill="{BG}"/>{body}</svg>')


def write(name, content):
    # The hero stays an SVG (it moves); every still plate is rasterised at 2x by tools/rasterize.mjs.
    dest = OUT if name == 'hero.svg' else PLATES
    (dest / name).write_text(content, encoding='utf-8')
    print(f'  {name}: {len(content.encode()) / 1024:.0f} KiB')


report = []


def check(label, ratio, need):
    report.append((label, ratio, need))


# ---------------------------------------------------------------- hero
def scrim(img, height, strength):
    """Neutral black scrim over the top `height` pixels: full strength at the top edge, none at the bottom."""
    img = img.convert('RGB')
    h = int(height)
    mask = Image.linear_gradient('L').resize((img.width, h)).point(lambda v: int((255 - v) * strength))
    full = Image.new('L', img.size, 0)
    full.paste(mask, (0, 0))
    return Image.composite(Image.new('RGB', img.size, (0, 0, 0)), img, full)


def hero():
    """StudyCabin-v2 through one day: the resident's real routine word, "at", the clock (StudyCabin's own HUD).
    A time-lapse played once when the image loads: morning to night in 4.2 s, then it rests on the night
    frame (antislop R-39: an image cannot carry a pause control, so nothing may move for longer than 5 s).
    Under it, the name at full width on the dark ground."""
    H, PH = 600, 424
    # (file, routine word from StudyCabin's schedule.js at that minute, clock), in the order they play.
    # The last one is where the time-lapse stops, and what shows without motion.
    frames = [('cabin-dawn.jpg', 'Coffee', '07:20'), ('cabin-day.jpg', 'Study', '09:30'),
              ('cabin-dusk.jpg', 'Reading', '20:05'), ('cabin-night.jpg', 'Journal', '22:10')]
    BIG = 72
    groups, words = [], []
    for i, (f, word, clock) in enumerate(frames):
        src = Image.open(SRC / f)
        scale = W / src.width                      # 0.55
        top = 40 / scale                           # trims the sky a little, keeps the cabin whole
        crop = src.crop((0, top, src.width, top + PH / scale))
        crop = ImageEnhance.Brightness(crop).enhance(0.9)   # the one dim photograph of the dark room
        k = crop.width / W                          # picture pixels per unit
        word_box = (M, 34, M + REGULAR.width(word, BIG, -0.03), 34 + BIG * 0.74)
        at_box = (W - M - REGULAR.width('at', BIG), 196, W - M, 196 + BIG * 0.74)
        clock_box = (W - M - REGULAR.width(clock, BIG, -0.03), PH - 32 - BIG * 0.74, W - M, PH - 32)
        # Where neither ink holds 3:1 over the picture (bright sky above dark treetops), darken the top of
        # that frame with a neutral scrim, the one gradient the house rules allow, just enough to pass.
        ink, ratio = best_ink(crop, [v * k for v in word_box])
        strength = 0.0
        while ratio < 3.5 and strength < 0.8:
            strength += 0.05
            crop = scrim(crop, (word_box[3] + 40) * k, strength)
            ink, ratio = best_ink(crop, [v * k for v in word_box])
        if strength:
            print(f'  hero {word}: top scrim {strength:.2f}')
        inks = []
        for label, box in (('word', word_box), ('at', at_box), ('clock', clock_box)):
            ink, ratio = best_ink(crop, [v * k for v in box])
            check(f'hero {word} {label} ({ink})', ratio, 3.0)
            inks.append(ink)
        pic = image(jpeg(crop.resize((1600, round(1600 * crop.height / crop.width)), Image.LANCZOS), 72), 0, 0, W, PH)
        groups.append(f'<g class="f{i}">{pic}</g>')
        hud = text(M, word_box[3], word, BIG, inks[0], tracking=-0.03)
        hud += text(W - M, at_box[3], 'at', BIG, inks[1], anchor='end')
        hud += text(W - M, PH - 32, clock, BIG, inks[2], anchor='end', tracking=-0.03)
        words.append(f'<g class="w{i}">{hud}</g>')

    role = 'Information Technology student'
    name = 'Viter Moldy Kesuma'
    size = int((W - 2 * M) / REGULAR.width(name, 1, -0.02))
    body = ''.join(groups) + ''.join(words)
    body += text(M, PH + 56, role, TEXT, MUTED)
    body += text(M, H - 34, name, size, INK, tracking=-0.02)
    check('hero role on ground', contrast(lum(hex_rgb(MUTED)), lum(hex_rgb(BG))), 4.5)
    print(f'  hero name size {size}u, width {REGULAR.width(name, size, -0.02):.0f}u of {W - 2 * M}u')

    # Each frame fades in over the one before and stays: holds of 0.8 s, fades of 0.6 s, done at 4.2 s.
    # The words never overlap: the old ones leave in the first 0.2 s of a fade, the new ones arrive in its
    # last 0.2 s, as StudyCabin swaps its activity word. Without animation (reduced motion, or a renderer
    # that does not animate) the night frame and its words show at once.
    starts = [0.8, 2.2, 3.6]
    anim = '@keyframes in{from{opacity:0}to{opacity:1}}@keyframes out{from{opacity:1}to{opacity:0}}'
    anim += '.w0,.w1,.w2{opacity:0}'
    anim += f'.w0{{animation:out .2s linear {starts[0]}s both}}'
    for i, t in enumerate(starts, start=1):
        anim += f'.f{i}{{animation:in .6s ease-in-out {t}s both}}'
        leave = f',out .2s linear {starts[i]}s forwards' if i < len(starts) else ''
        anim += f'.w{i}{{animation:in .2s linear {t + 0.4:.1f}s both{leave}}}'
    anim += ('@media (prefers-reduced-motion:reduce){.f1,.f2,.f3,.w0,.w1,.w2,.w3{animation:none}'
             '.w0,.w1,.w2{opacity:0}.f3,.w3{opacity:1}}')
    title = ('Viter Moldy Kesuma, Information Technology student. Behind the name, StudyCabin, a forest cabin from '
             'one of my projects, through one day: Coffee at 07:20, Study at 09:30, Reading at 20:05, Journal at 22:10.')
    write('hero.svg', svg(H, title, body, anim))


# ---------------------------------------------------------------- work strips
def strip(name, files, caption, title, dim=1.0):
    """One strip per project: pictures at one height and their natural widths, the last cut by the edge.
    Under it one line: the name, a three-word descriptor at the centre, the year."""
    SH, GAP, top = 210, 10, M
    H = top + SH + 24 + 30 + 34
    x, body = M, ''
    for f in files:
        im = Image.open(SRC / f)
        if dim != 1.0:
            im = ImageEnhance.Brightness(im).enhance(dim)
        w = im.width * SH / im.height
        if x < W:
            body += image(jpeg(im, 76), x, top, w, SH)
        x += w + GAP
    base = top + SH + 24 + 26
    n, d, y = caption
    body += text(M, base, n, TEXT, INK)
    body += text(W / 2, base, d, TEXT, MUTED, anchor='middle')
    body += text(W - M, base, y, TEXT, MUTED, anchor='end')
    span = REGULAR.width(n, TEXT) + REGULAR.width(d, TEXT) + REGULAR.width(y, TEXT)
    left_end = M + REGULAR.width(n, TEXT)
    mid_start = W / 2 - REGULAR.width(d, TEXT) / 2
    mid_end = W / 2 + REGULAR.width(d, TEXT) / 2
    right_start = W - M - REGULAR.width(y, TEXT)
    assert left_end + 16 < mid_start and mid_end + 16 < right_start, f'caption collides in {name}'
    print(f'  {name}: strip ends at {x - GAP:.0f}u (cut at {W}u); caption {span:.0f}u')
    write(name, svg(H, title, body))


# ---------------------------------------------------------------- line-up
def lineup():
    """Line-up at one type size: what I use, left; where I used it, from the middle. Part headings in amber."""
    parts = [
        ('In the browser', [('three.js, Vite', 'StudyCabin, SongPlay'),
                            ('Astro, TypeScript', 'PixelFolio'),
                            ('HTML, CSS, JavaScript', 'templates, first sites')]),
        ('On the server', [('Laravel 12, Livewire', 'Viygo'),
                           ('PHP, MySQL', 'Tubes-Proweb'),
                           ('PostgreSQL, PL/pgSQL', 'msbd-2026')]),
    ]
    LEAD, COL2 = 54, 470
    y, body = M + 26, ''
    for pi, (head, rows) in enumerate(parts):
        if pi:
            y += 48
        body += text(M, y, head, TEXT, ACCENT)
        y += LEAD + 6
        for tool, where in rows:
            assert M + REGULAR.width(tool, TEXT) + 24 < COL2, tool
            assert COL2 + REGULAR.width(where, TEXT) <= W - M, where
            body += text(M, y, tool, TEXT, INK)
            body += text(COL2, y, where, TEXT, MUTED)
            y += LEAD
    H = int(y - LEAD + 40)
    check('accent on ground', contrast(lum(hex_rgb(ACCENT)), lum(hex_rgb(BG))), 4.5)
    check('ink on ground', contrast(lum(hex_rgb(INK)), lum(hex_rgb(BG))), 7.0)
    title = ('What I work with. In the browser: three.js and Vite in StudyCabin and SongPlay; Astro and TypeScript '
             'in PixelFolio; HTML, CSS and JavaScript in the templates and my first sites. On the server: Laravel 12 '
             'and Livewire in Viygo; PHP and MySQL in Tubes-Proweb; PostgreSQL and PL/pgSQL in msbd-2026.')
    write('lineup.svg', svg(H, title, body))


# ---------------------------------------------------------------- contact
def contact():
    """Visit card on a photograph: SongPlay's TV glowing in the rain, one solid card in the calm upper-left."""
    src = Image.open(SRC / 'tv-night-rain.jpg')
    H = round(W * src.height / src.width)
    CX, CY, CW, PAD = M, M, 320, 28
    body = image(jpeg(src, 74), 0, 0, W, H)
    t1 = CY + PAD + 38
    l1 = t1 + 50
    l2 = l1 + 44
    btn_top = l2 + 30
    BH = 60
    card_h = btn_top + BH - CY
    body += f'<rect x="{CX}" y="{CY}" width="{CW}" height="{card_h}" rx="8" fill="{PAPER}"/>'
    body += text(CX + PAD, t1, 'Say hello', 52, INK_DARK, tracking=-0.02)
    body += text(CX + PAD, l1, 'on GitHub as', TEXT, '#4a4f4b')
    body += text(CX + PAD, l2, 'vitermoldy', TEXT, INK_DARK)
    # the button spans the card's width and sits flush with its bottom edge; square top, card's radius below
    body += (f'<path d="M{CX} {btn_top} H{CX + CW} V{btn_top + BH - 8} a8 8 0 0 1 -8 8 H{CX + 8} '
             f'a8 8 0 0 1 -8 -8 Z" fill="{ACCENT}"/>')
    body += text(CX + PAD, btn_top + 40, 'My repositories', TEXT, INK_DARK)
    assert REGULAR.width('My repositories', TEXT) <= CW - 2 * PAD
    assert REGULAR.width('Say hello', 52, -0.02) <= CW - 2 * PAD
    check('card body on paper', contrast(lum(hex_rgb('#4a4f4b')), lum(hex_rgb(PAPER))), 4.5)
    check('button text on amber', contrast(lum(hex_rgb(INK_DARK)), lum(hex_rgb(ACCENT))), 4.5)
    print(f'  contact: card {CW}x{card_h}u at ({CX},{CY}); plate {W}x{H}u')
    title = ('Say hello: on GitHub as vitermoldy. Button: my repositories. Behind the card, the TV from '
             'SongPlay glows in a forest clearing on a rainy night.')
    write('contact.svg', svg(H, title, body))


def main():
    OUT.mkdir(exist_ok=True)
    PLATES.mkdir(exist_ok=True)
    print('building plates')
    hero()
    strip('studycabin.svg', ['sc-study.jpg', 'sc-phone-walk.jpg', 'sc-journal.jpg', 'sc-phone-dinner.jpg'],
          ('StudyCabin', 'cabin keeps time', '2026'),
          'StudyCabin, 2026. Study at 09:20 at the desk, a walk at 11:30 on a phone, Journal at 22:00, '
          'dinner at 18:45 on a phone: the interface over the live 3D cabin.')
    strip('songplay.svg', ['sp-landing.jpg', 'sp-phone-playing.jpg', 'sp-autumn.jpg', 'sp-phone-rain.jpg'],
          ('SongPlay', 'forest TV player', '2026'),
          'SongPlay, 2026. The landing page with a glowing TV on a knoll; a phone playing a video on the TV; '
          'the player at an autumn sunset; the player on a phone in the rain.')
    strip('templates.svg', ['tp-pixelfolio.jpg', 'tp-pixelfolio-phone.jpg', 'tp-medianta.jpg', 'tp-modern-phone.jpg'],
          ('Templates', 'pages to reuse', '2026'),
          'Page templates, 2026. A PixelFolio project page with its pixel drawing; PixelFolio on a phone; '
          'the Medianta product page; the Modern portfolio template on a phone.', dim=0.9)
    lineup()
    contact()
    print('contrast')
    bad = 0
    for label, ratio, need in report:
        ok = ratio >= need
        bad += not ok
        print(f'  {"PASS" if ok else "FAIL"} {ratio:5.2f}:1 (needs {need}) {label}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
