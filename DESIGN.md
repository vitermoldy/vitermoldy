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
| Streak | streak-stats (demolab), Hutan colours |
| Pac-Man graph | `.github/workflows/pacman.yml`, published to the `output` branch |

The banner is StudyCabin at night as pixel art (lit glass cabin, chimney smoke, aurora, stars, a doe by the pond,
fireflies). The project cards show
the owner's real screenshots, reduced to pixels; Viygo has no screenshot here, so its card is a drawn pixel map.

The room is original pixel art in the spirit of the owner's reference (a pixel gamer room), with no characters from
existing games: the owner from behind at the desk, code on the main screen, a video edit on the second, a photo grid
on the laptop, a camera on a tripod, a softbox, an event staff pass, a StudyCabin poster and PixelFolio's face on
the shelf. Its neon sign changes every 2.5 seconds between VITERMOLDY, FRONTEND / FULL STACK, PHOTOGRAPHY, EVENT
ORGANIZER and MULTIMEDIA, each in its own colour.

In About, the sunset flower field (drawn by `tools/pixel.py`) has the character the owner chose standing in it: a
chibi pixel girl with long magenta hair, a white blouse, a pink sash and a navy skirt. That picture was not drawn
for this profile and its artist is not known here, so its credit is still to be added (there is a comment for it
in the README). It was brought back to its own pixel grid (78 x 109) and cut out of its white background
(`tools/src/chibi-cutout.png`); petals and clouds drift to the right. The scene floats to the right of the list, and a transparent strip 100% wide after the list (`assets/pixel/clear.svg`) keeps the next section below the picture,
because GitHub removes the `clear` attribute from `<br>`.

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
