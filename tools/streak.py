"""Draws the profile's GitHub streak card from the public contribution calendar.

    python tools/streak.py --out dist/streak.svg              read GitHub, draw the card
    python tools/streak.py --out dist/streak.svg --user name  someone else's calendar
    python tools/streak.py --html saved.html --out x.svg      draw from saved calendar pages (offline check)

The card has the classic streak-card layout (total contributions, the current streak in a ring
with a flame, the longest streak) at 495 x 195, in the profile's Hutan colours. The Pac-Man
workflow redraws it every hour and publishes it to the "output" branch with the graphs, so the
numbers come straight from GitHub and never sit in a third-party cache for hours. It reads the
same public calendar the profile page shows (github.com/users/<name>/contributions), year by
year, so it needs no token and nothing beyond Python's standard library.
"""
import argparse
import datetime as dt
import re
import time
import urllib.request
from html import escape
from pathlib import Path

# Hutan colours, the same as the stats cards above the streak card (DESIGN.md).
BG, BORDER, RING, FIRE = '#121a14', '#1f6e44', '#f0b429', '#e4572e'
CUR_NUM, SIDE_NUM, CUR_LABEL, SIDE_LABEL, DATES = '#fff36b', '#eef0e6', '#f0b429', '#aab6a5', '#aab6a5'
FONT = '"Segoe UI", Ubuntu, sans-serif'
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

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
        'today': days.get(today, (0, 0))[0],
    }


def day(d, today):
    """Nov 4 this year, Nov 4, 2025 before it."""
    return f'{MONTHS[d.month - 1]} {d.day}' + ('' if d.year == today.year else f', {d.year}')


def span(a, b, today):
    if not a:
        return 'No streak yet'
    return day(a, today) if a == b else f'{day(a, today)} - {day(b, today)}'


def text(x, y, value, colour, size, weight=400):
    return (f'<text x="{x}" y="{y}" text-anchor="middle" fill="{colour}" font-family=\'{FONT}\' '
            f'font-weight="{weight}" font-size="{size}px">{escape(value)}</text>')


def draw(s, user, today):
    first = s['first']
    since = f'{MONTHS[first.month - 1]} {first.day}, {first.year} - Present'
    cur = span(s['cur_from'], s['cur_to'], today)
    best = span(s['long_from'], s['long_to'], today)
    title = (f'{user} on GitHub: {s["total"]:,} contributions since {MONTHS[first.month - 1]} {first.day}, {first.year}; '
             f'current streak {s["current"]} days ({cur}); longest streak {s["longest"]} days ({best}).')
    # A flame drawn for this card: a teardrop with a second tongue on its left.
    flame = ('M 1.5 0 C 3 4 8.5 7.5 8.5 14 C 8.5 18.7 4.7 22.5 0 22.5 C -4.7 22.5 -8.5 18.7 -8.5 14 '
             'C -8.5 10.2 -6.6 7.4 -4.6 5.3 C -4.4 8.2 -2.9 10.2 -0.8 10.2 C 1.6 10.2 2.6 8 2.6 5.8 C 2.6 3.6 2 1.6 1.5 0 Z')
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 495 195" width="495" height="195" role="img" aria-labelledby="t">',
        f'<title id="t">{escape(title)}</title>',
        '<defs><mask id="ring-gap"><rect width="495" height="195" fill="white"/>'
        '<ellipse cx="247.5" cy="32" rx="13" ry="18" fill="black"/></mask></defs>',
        f'<rect x="0.5" y="0.5" width="494" height="194" fill="{BG}" stroke="{BORDER}"/>',
        f'<line x1="165" y1="28" x2="165" y2="170" stroke="{BORDER}"/>',
        f'<line x1="330" y1="28" x2="330" y2="170" stroke="{BORDER}"/>',
        # Left: everything counted since the first contribution.
        text(82.5, 80, f'{s["total"]:,}', SIDE_NUM, 28, 700),
        text(82.5, 116, 'Total Contributions', SIDE_LABEL, 14),
        text(82.5, 146, since, DATES, 12),
        # Middle: the current streak in a ring, the flame in the gap at the top.
        f'<circle cx="247.5" cy="71" r="40" fill="none" stroke="{RING}" stroke-width="5" mask="url(#ring-gap)"/>',
        f'<path transform="translate(247.5 19.5)" d="{flame}" fill="{FIRE}"/>',
        text(247.5, 80, str(s['current']), CUR_NUM, 28, 700),
        text(247.5, 140, 'Current Streak', CUR_LABEL, 14, 700),
        text(247.5, 166, cur, DATES, 12),
        # Right: the best run so far.
        text(412.5, 80, str(s['longest']), SIDE_NUM, 28, 700),
        text(412.5, 116, 'Longest Streak', SIDE_LABEL, 14),
        text(412.5, 146, best, DATES, 12),
        '</svg>',
    ]
    return ''.join(parts)


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
    out.write_text(draw(s, a.user, today), encoding='utf-8')
    print(f'{out}: total {s["total"]:,}, current {s["current"]}, longest {s["longest"]}, today {s["today"]:,}')


if __name__ == '__main__':
    main()
