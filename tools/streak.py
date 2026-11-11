"""Draws the profile's GitHub streak card as pixel art, from the public contribution calendar.

    python tools/streak.py --out dist/streak.svg              read GitHub, draw the card
    python tools/streak.py --out dist/streak.svg --user name  someone else's calendar
    python tools/streak.py --html saved.html --out x.svg      draw from saved calendar pages (offline check)

The Pac-Man workflow runs it every hour and publishes the card to the "output" branch with the
graphs, so every number on it comes from GitHub itself. It reads the same public calendar the
profile page shows (github.com/users/<name>/contributions), year by year, so it needs no token.
Needs Pillow and fontTools (pixel.py draws the type and the plate).
"""
import argparse
import datetime as dt
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pixel import (ACCENT, COLD, HOT, INK, MID, PALE, PAPER, T5, WARM, Canvas, document, plate)  # noqa: E402

# The contribution graph's five steps in the Hutan palette, the same as the recoloured Pac-Man graph.
LEVELS = ['#1b271e', '#174f35', '#1f6e44', '#2f8a55', '#52c879']
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

DAY = re.compile(r'<td\b[^>]*\bContributionCalendar-day\b[^>]*>')
TIP = re.compile(r'<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>')


def attr(tag, name):
    m = re.search(rf'\b{name}="([^"]*)"', tag)
    return m.group(1) if m else None


def parse(html):
    """{date: (count, level)} from one calendar page."""
    tips = {}
    for for_id, text in TIP.findall(html):
        m = re.search(r'([\d,]+)\s+contribution', text)
        tips[for_id] = int(m.group(1).replace(',', '')) if m else 0
    days = {}
    for tag in DAY.findall(html):
        date, day_id, level = attr(tag, 'data-date'), attr(tag, 'id'), attr(tag, 'data-level')
        if not date:
            continue
        days[dt.date.fromisoformat(date)] = (tips.get(day_id, 0), int(level or 0))
    return days


def fetch(user, year):
    url = f'https://github.com/users/{user}/contributions?from={year}-01-01&to={year}-12-31'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (profile streak card)'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception:  # a hiccup on the network: wait and try again
            if attempt == 2:
                raise
            time.sleep(3)
    return ''


def calendar(user, today):
    """Every day from the first year with contributions to today."""
    days = {}
    year = today.year
    while year >= 2008:
        part = parse(fetch(user, year))
        if not part:
            raise SystemExit(f'No calendar found for {user} in {year}: the page may have changed.')
        days.update(part)
        if not any(c for c, _ in part.values()) and year < today.year:
            break  # a whole empty year before the activity: nothing older to count
        year -= 1
    return {d: v for d, v in days.items() if d <= today}


def stats(days, today):
    dates = sorted(days)
    active = [d for d in dates if days[d][0] > 0]
    total = sum(days[d][0] for d in dates)
    first = active[0] if active else today
    # Longest run of days with at least one contribution.
    longest, run, best_end, prev = 0, 0, None, None
    for d in active:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        prev = d
        if run > longest:
            longest, best_end = run, d
    # The current run ends today, or yesterday while today has none yet (the day is not over).
    end = today if days.get(today, (0, 0))[0] > 0 else today - dt.timedelta(days=1)
    cur, d = 0, end
    while days.get(d, (0, 0))[0] > 0:
        cur += 1
        d -= dt.timedelta(days=1)
    return {
        'total': total, 'first': first,
        'current': cur, 'cur_from': end - dt.timedelta(days=cur - 1) if cur else None, 'cur_to': end if cur else None,
        'longest': longest, 'long_from': best_end - dt.timedelta(days=longest - 1) if longest else None, 'long_to': best_end,
        'recent': [(today - dt.timedelta(days=i), days.get(today - dt.timedelta(days=i), (0, 0))) for i in range(29, -1, -1)],
        'today': days.get(today, (0, 0))[0],
    }


def day(d):
    return f'{MONTHS[d.month - 1]} {d.day}'


def span(a, b):
    if not a:
        return 'NO STREAK YET'
    return day(a) if a == b else f'{day(a)} - {day(b)}'


def centred(c, cx, base, text, colour, k=1):
    c.text(cx - (T5.width(text, k) + 1) // 2, base, text, colour, k)


def fit(options, width, k=1):
    """The first wording that fits the column."""
    for o in options:
        if T5.width(o, k) <= width:
            return o
    return options[-1]


# 8 x 10 flame, two frames that flicker.
FLAME = [
    ['...a....', '..aa....', '..aaa.a.', '.aaaaaa.', '.aawaaa.', 'aawwwaaa', 'aawywwaa', 'aawyywaa', '.awyywa.', '..aaaa..'],
    ['....a...', '....aa..', '.a.aaa..', '.aaaaaa.', '.aaawaa.', 'aaawwwaa', 'aawwywaa', 'aawyywaa', '.awyywa.', '..aaaa..'],
]
FLAME_KEYS = {'a': ACCENT, 'w': WARM, 'y': HOT}


def draw(s, user):
    W, H = 300, 104
    col = W // 3
    c = Canvas()
    plate(c, W, H)
    for x in (col, col * 2):
        c.rect(x, 10, 1, 58, MID)
    c.rect(8, 78, W - 16, 1, MID)

    # Left: everything counted.
    centred(c, col // 2, 34, f'{s["total"]:,}', PAPER, 2)
    centred(c, col // 2, 48, fit(['TOTAL CONTRIBUTIONS', 'CONTRIBUTIONS'], col - 8), PALE)
    since = fit([f'{day(s["first"])}, {s["first"].year} - NOW', f'{MONTHS[s["first"].month - 1]} {s["first"].year} - NOW'], col - 8)
    centred(c, col // 2, 60, since, PALE)

    # Middle: the current streak in a ring, a flame on top.
    cx, cy, r = col + col // 2, 32, 19
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            dd = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
            if r - 2 <= dd < r and not (abs(x + 0.5 - cx) < 6 and y < cy):
                c.set(x, y, WARM)
    centred(c, cx, cy + 8, str(s['current']), HOT, 3)
    centred(c, cx, 62, 'CURRENT STREAK', WARM)
    centred(c, cx, 73, span(s['cur_from'], s['cur_to']), PALE)

    # Right: the best run so far.
    rx = col * 2 + col // 2
    centred(c, rx, 34, str(s['longest']), PAPER, 2)
    centred(c, rx, 48, 'LONGEST STREAK', PALE)
    centred(c, rx, 60, span(s['long_from'], s['long_to']), PALE)

    # Bottom: the last 30 days, oldest to today, coloured like the graph.
    label = 'LAST 30 DAYS'
    today_txt = f'TODAY {s["today"]:,}'
    c.text(10, 95, label, PALE)
    tw = T5.width(today_txt)
    c.text(W - 10 - tw, 95, today_txt, HOT if s['today'] else PALE)
    x0 = 10 + T5.width(label) + 8
    room = W - 10 - tw - 8 - x0
    step = max(4, min(7, room // 30))
    size = step - 1
    x = x0 + (room - step * 30 + 1) // 2
    for i, (d, (count, level)) in enumerate(s['recent']):
        c.rect(x + i * step, 89, size, size, LEVELS[max(0, min(4, level))] if count else LEVELS[0])
        if i == 29:
            c.rect(x + i * step, 89 + size + 1, size, 1, WARM)

    flames = []
    for frame in FLAME:
        f = Canvas()
        for j, row in enumerate(frame):
            for i, ch in enumerate(row):
                if ch in FLAME_KEYS:
                    f.set(cx - 4 + i, cy - r - 6 + j, FLAME_KEYS[ch])
        flames.append(f)

    title = (f'{user} on GitHub: {s["total"]:,} contributions since {day(s["first"]).title()}, {s["first"].year}; '
             f'current streak {s["current"]} days ({span(s["cur_from"], s["cur_to"]).title()}); '
             f'longest streak {s["longest"]} days; {s["today"]:,} today.')
    # The two flame frames take turns; with motion reduced only the first one shows.
    css = ('.f1{opacity:0}.f0,.f1{animation:fl .9s steps(1) infinite}.f1{animation-delay:-.45s}'
           '@keyframes fl{0%{opacity:1}50%{opacity:0}100%{opacity:0}}')
    body = c.svg() + flames[0].svg('f0') + flames[1].svg('f1')
    return document(W, H, 3, title, body, css)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user', default='vitermoldy')
    ap.add_argument('--out', default='dist/streak.svg')
    ap.add_argument('--tz', type=float, default=7, help="the owner's UTC offset in hours, for 'today' (default 7, WIB)")
    ap.add_argument('--html', nargs='*', help='saved calendar pages instead of reading GitHub')
    a = ap.parse_args()
    today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=a.tz)).date()
    if a.html:
        days = {}
        for p in a.html:
            days.update(parse(Path(p).read_text(encoding='utf-8')))
        days = {d: v for d, v in days.items() if d <= today}
    else:
        days = calendar(a.user, today)
    s = stats(days, today)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(draw(s, a.user), encoding='utf-8')
    print(f'{out}: total {s["total"]:,}, current {s["current"]}, longest {s["longest"]}, today {s["today"]:,}')


if __name__ == '__main__':
    main()
