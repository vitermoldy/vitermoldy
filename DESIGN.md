# vitermoldy: design direction

The GitHub profile README of Viter Moldy Kesuma, in pixel art.

**Direction (from the owner).** A decorated profile in the classic GitHub style (animated banner, typing line,
visitor counter, emoji bullets, tool badges, stats cards, a contribution game, social badges), drawn as pixel art.
The owner sent reference screenshots and asked for it to be built with GPRM (GitHub Profile README Maker,
https://gprm.itsvg.in).

**Design Read.** Reading this as: a GitHub profile README for classmates, lecturers and recruiters, in the pixel
style of the owner's own PixelFolio, dial **ENERGY 3 / RHYTHM 2 / MOTION 3**.

## One palette, one typeface

Everything uses PixelFolio's "Hutan" (forest) palette, so the profile reads as one piece with the owner's work:

| Role | Value |
| --- | --- |
| Ink, plates and card backgrounds | `#121a14` |
| Cold green, badge background | `#0f3d2e` |
| Mid green, borders | `#1f6e44` |
| Warm yellow | `#f0b429` |
| Hot yellow, titles and logos | `#fff36b` |
| Accent, hearts and pins | `#e4572e` |
| Paper | `#eef0e6` |

The type is **Tiny5**, PixelFolio's pixel face (SIL OFL 1.1, `tools/fonts/Tiny5-OFL.txt`). In the drawn pieces the
letters are real pixels taken from Tiny5's glyph outlines, so they stay sharp at any size.

## Where each piece comes from

| Piece | Source |
| --- | --- |
| Banner, the room, the sunset field, section headers, project cards, footer | Drawn by `tools/pixel.py` into `assets/pixel/` |
| Creative skill badges (photography, event organizer, multimedia) | shields.io with small icons drawn for them (simple-icons has none) |
| Typing line | readme-typing-svg (demolab), in Tiny5, yellow in dark mode and green in light mode |
| Visitor counter | komarev, as GPRM uses it |
| Tool and social badges | shields.io `for-the-badge`, as GPRM uses it, all in the Hutan colours |
| Stats and top languages | github-readme-stats on GPRM's mirror (`github-readme-stats.shion.dev`), Hutan colours |
| Streak | The classic streak-card layout (495 x 195, Hutan colours) drawn by `tools/streak.py` from the public contribution calendar; `pacman.yml` redraws it every hour and publishes it to the `output` branch. It replaced streak-stats (demolab), whose cache kept showing old totals for hours (17,231 against GitHub's 36,586 on 12 November 2026) |
| Pac-Man graph | `.github/workflows/pacman.yml`, recoloured in the Hutan palette by a `sed` step, published to the `output` branch |
| Profile picture (`avatar.png`, `avatar-sunset.png`) | Drawn by `tools/pixel.py`, uploaded by hand in GitHub settings |

The banner is StudyCabin at night as pixel art (lit glass cabin, chimney smoke, aurora, stars, a doe by the pond,
fireflies). The project cards show
the owner's real screenshots, reduced to pixels; Viygo has no screenshot here, so its card is a drawn pixel map.
Lanskara (LandingPage-sitev1) and CloudStead share the last row: Lanskara from its hero at 1440
(`tools/src/lanskara-hero.jpg`), CloudStead from its finished island at sunset without the interface
(`tools/src/cloudstead-island.jpg`, the `?pratinjau=1400` view at 1600 x 1000). The two newest share the top
row, so the table is a whole 2 x 5 grid. Since 15 November 2026 that row is Mixer Simulation on the left, the
Analog 16 console while its demo song plays, all 16 strips from GAIN down to AUX 2 so the red, green and yellow
rows of knobs read as a mixer at 94 x 50 (`tools/src/mixer-analog.jpg`), and Network Simulation on the right,
its 3D lab bench with the interface and device labels hidden and the camera two steps closer
(`tools/src/netsim-bench.jpg`), both shot at 1600 x 1000. The owner's rule for private repositories (15 November
2026): name them as in development, in English. Mixer-Simulation is private, so its card follows the Nyxborne
pattern below (no link, a closing note that the repository is private for now); when it goes public, wrap the
picture in a link and end the text with a Repo link like the others. The second row holds Nyxborne on the left,
and Agentic Factory (idle-Agent-factory) on the right, the Studio Video machine with the game interface hidden (`tools/src/agentic-factory.jpg`, 1600 x 852),
cropped to its five stations. The Nyxborne card shows v2 (repository Nyxborn-v2), which is pixel art itself, so
its picture is not reduced at all: one frame of the arena canvas at art resolution (`tools/src/nyxborne-v2-arena.png`,
352 x 211), the hunter in the eclipse mantle inside his shadow legion as the Crimson Breach demons close in, cropped
to exactly 94 x 50 so each card cell is one pixel of the game. While Nyxborn and Nyxborn-v2 are private (the owner's decision,
the game is still in development) the card has no links: the picture is not wrapped in a link, the text ends with
a plain note that the repository is private, and the About list's "currently building" line names Nyxborne v2
without a link, so nothing leads to a page visitors cannot open. When both repositories go public, wrap the
picture in a link to Nyxborn-v2 and link both versions in the text, like StudyCabin. DBMS Simulation is left out
while its repository is private.

The room is original pixel art in the spirit of the owner's reference (a pixel gamer room), with no characters from
existing games: the owner from behind at the desk, code on the main screen, a video edit on the second, a photo grid
on the laptop, a camera on a tripod, a softbox, an event staff pass, a StudyCabin poster and PixelFolio's face on
the shelf. Its neon sign changes every 2.5 seconds between VITERMOLDY, FRONTEND / FULL STACK, PHOTOGRAPHY, EVENT
ORGANIZER and MULTIMEDIA, each in its own colour.

In About, the same person from the room (green hoodie, headphones round the neck) stands in a flower field at
sunset, seen from behind, photographing it, while the wind lifts the hair, the hood and the camera strap and petals
and birds cross the sky. It floats to the right of the list, and a transparent strip 100% wide after the list (`assets/pixel/clear.svg`) keeps the next section below the picture,
because GitHub removes the `clear` attribute from `<br>`.

The profile picture is the same person again, now facing the viewer: head and shoulders, the green hoodie with
the hood round the neck and the headphones resting on it, in front of a big moon over the forest at night
(`avatar.png`) or the sun at sunset (`avatar-sunset.png`). The disc sits behind the head so the dark hair stands
out. GitHub takes no SVG for an avatar, so it is a PNG, 64 x 64 pixels saved at 512 x 512, with everything that
matters inside the circle GitHub crops it to.

Checked on 10 November 2026: the public github-readme-stats, activity-graph and trophy servers were down, so none of
them is used.

## Rules the owner chose to keep

antislop and taste-skill reject some of what this style is made of. The owner asked for this style with references,
so these are kept on purpose (antislop R-37):

- emoji in the About list, rows of tool badges, stats cards and a visitor counter;
- animations that loop (banner, face, typing line, Pac-Man) with no pause control (antislop R-39). The drawn pieces
  stop moving under `prefers-reduced-motion`;
- pictures without a `height` attribute: with one, GitHub's stylesheet stretches them on a phone (antislop R-40).

Still held: every number comes from GitHub itself, every tool listed is used in a public repository, every link was
checked, every picture has alt text, and no text was invented about the owner beyond the About list, which the owner should
confirm.

## Rebuild

```bash
python tools/pixel.py   # redraws everything in assets/pixel/
```
