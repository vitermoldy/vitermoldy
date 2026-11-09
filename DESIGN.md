# vitermoldy: design direction

The GitHub profile README of Viter Moldy Kesuma, built with two rule sets: taste-skill (design-taste-frontend)
for the direction, and antislop as the filter, in `during` mode.

**Design Read.** Reading this as: a GitHub profile README for recruiters, lecturers and other developers, in the
cinematic misty-forest style of the owner's own StudyCabin and SongPlay, dial **ENERGY 3 / RHYTHM 2 / MOTION 2**.

- ENERGY 3: the name at full width, giant HUD words over a full-bleed render, as in StudyCabin.
- RHYTHM 2: every section is a dark plate followed by GitHub's own text; inside the plates the compositions change
  (hero photograph, picture strips, a one-size line-up, a card on a photograph).
- MOTION 2: one move, the hero's time-lapse of one day, played once. A README runs no CSS or script of its own, so
  everything else is still.

## The deal

- taste-skill `draw.mjs`, sector `personal-portfolio`, `--keep palette,type`, direction **The dark room**,
  seed 1004059467. Sections dealt: work (one strip per project), about, list (line-up at one type size), contact
  (visit card on a photograph). Motion dealt: slow crossfade.
- Redraw: about, from "Portrait as drop cap" to `about-side-facts-wide-paragraph`. The GitHub avatar is the default
  identicon and there is no portrait to use; antislop R-23 forbids making one.
- Hero: the direction's own first-screen composition (the name at full width along the bottom edge, one dim
  photograph above it) instead of the dealt "Navigation on the midline". StudyCabin's camera always centres the
  cabin, so a rail across the middle would cross the cabin's glass; camera drags were tried and did not move it out
  of the middle.
- Motion: the dealt slow crossfade looped every 24 seconds at first. antislop R-39 (a Hard Gate) requires a pause
  control for anything moving longer than 5 seconds, and an image in a README cannot have one, so the crossfade
  became a time-lapse that plays once and stops after 4.2 seconds.

**The idea.** On this profile, StudyCabin's clock (one game minute every real second, the resident's routine shown
as "Coffee at 07:20") becomes the dark room's one lit picture: the header plays one day of that cabin, from morning
fog to the lamps and the aurora at night, and rests there.

**The live thing.** The "Last push" line under the hero changes on its own: `.github/workflows/now.yml` runs every
night (00:00 Jakarta), asks the GitHub API which public repository was pushed last, and rewrites the line between
the `now` markers. Nothing in it is typed by hand.

## Tokens

| Role | Value | From |
| --- | --- | --- |
| Ground | `#0e1613` | StudyCabin's night forest, green-black |
| Ink | `#e4e5e1` | StudyCabin "mist" |
| Dark ink | `#171716` | StudyCabin "ink", for type over fog and bright sky |
| Muted ink | `#a3ada6` | 7.95:1 on the ground |
| Accent | `#d9a05b` | StudyCabin "lamp amber", the one warm note |
| Type | Instrument Sans 400 and 500 | StudyCabin's typeface (SIL OFL 1.1, `tools/fonts/OFL.txt`) |
| Plate width | 880 units, margin 32 | GitHub shows a plate at about 830px on desktop and 330px on a phone |
| Smallest type on a plate | 36 units | about 13.5px on a phone, 34px on desktop |

## Decisions and their reasons (R-31)

| Decision | Reason |
| --- | --- |
| Every picture is the owner's own: renders and screenshots of StudyCabin, SongPlay, PixelFolio, Medianta and the Modern template | Real work is the strongest proof a student has; nothing found or stock stands in for it. |
| The hero frames are rendered from StudyCabin-v2's own build at 07:20, 09:30, 20:05 and 22:10 (`tools/render-cabin.mjs`) | The same camera at four hours shows the one thing the project is about: time passing in one place. |
| The words in the hero (Coffee, Study, Reading, Journal) are the resident's routine at those minutes in `src/sim/schedule.js` | They are what StudyCabin itself shows at that hour, not an invented routine for the owner. |
| Ink over the photograph picked per word by sampling the pixels under it; a neutral scrim at the top of the 09:30 frame only | StudyCabin switches its ink the same way. At 09:30 the word sits on bright sky above dark treetops and no ink holds 3:1 without the scrim. |
| The name at full width in regular weight on the dark ground under the photograph | The direction's first screen; the name says who, the line above it says what, nothing covers either. |
| Dark plates in both GitHub themes | In dark mode they read as one dark room; in light mode as lit pictures hung on a white wall. Either way the plates carry their own ground, so contrast is fixed. |
| One strip of pictures per project, at one height and natural widths, the last cut by the edge | The dealt work section. Desktop and phone screenshots side by side show that each project was built for both. |
| Strip captions: name, a three-word descriptor, the year | The dealt caption line; it names the project inside the plate, so the plate stands on its own when shared. |
| The line-up at one type size, part headings in amber | The dealt list section: what is used, and where, read as a programme rather than a row of logos. |
| No logo badges, no stats cards, no streak counters, no typing banner | Badges are the pill and icon rows both skills reject; third-party stats cards show numbers in someone else's design. |
| The contact card in the calm upper-left of SongPlay's rainy-night frame, the TV left clear | The dealt closing section; the TV is the focal point and stays uncovered. |
| The card's one action in amber, and the whole plate links to the repositories tab | A picture of a button must lead where it says (R-26). |
| Still plates shipped as 2x JPEG or PNG, rendered from SVG by Chrome (`tools/rasterize.mjs`) | They render the same everywhere GitHub shows a README, including the mobile app, and count as pictures. |
| The hero shipped as SVG with the font and frames embedded | Its time-lapse needs CSS animation, which only an SVG image can carry inside a README. |
| Section headings are GitHub `###` headings | `#` and `##` draw a hairline under themselves on GitHub; `###` does not. |
| Text written in English | The project READMEs it links to are in English. |

## What a README cannot do (inspector findings, kept on purpose)

`inspect.mjs` on a local preview rendered by GitHub's markdown API with GitHub's stylesheet (1440, 768, 390):
0 broken images, no horizontal overflow, and these findings, each a limit of the medium:

- **no-title (FAIL).** The profile page already has its own `h1` (the name in GitHub's sidebar). A second `h1`
  inside the README would be a second `h1` on the page, and GitHub draws a hairline under it. The hero image
  carries the name and its alt text says it.
- **still-page (FAIL).** A README runs no CSS or script. The one move lives inside the hero SVG, where the
  inspector cannot see it; it was checked frame by frame instead (`.work/shots/timelapse.jpg` while building).
- **untitled-section @390 (FAIL).** The SongPlay and Templates paragraphs continue the Work section under their
  own plates, which name them; the rule exempts continuations.
- **first-action, no-hero, measure, no-footage (WARN).** No buttons, styles or video in a README; the line length
  is set by GitHub's column.

## Critique

```
ROUND 1
Seen in one second: a forest cabin at dusk with "Reading at 20:05" and a large name; dark plates of real work.
Idea (one sentence): StudyCabin's clock runs the header, one day from morning to night.
Live thing: the Last push line, rewritten every night from the GitHub API.
Layout words by section: hero=photograph over name / work=strips / about=facts and paragraph / list=line-up / contact=card on photograph
Scores: design 7 · usability 7 · creativity 8 · content 8 → overall 7.3
Caps applied: inspector FAILs (medium limits above) hold the skill's arithmetic at 6.0; still-page holds design at 7.
Top three problems (most visible first), each with the screenshot it shows in and the fix:
1. hero cycle: during each crossfade two words overlap ("Jouradiang"); the old word must leave before the new one arrives.
2. contact plate, top-left: a corner mark from SongPlay's viewfinder shows; crop below it.
3. work strips: the last picture is cut by only 7 units, which reads as a mistake; make the strips taller so it is cut near half.

ROUND 2 (after the fixes and the switch to a once-played time-lapse)
Seen in one second: the cabin runs from fog to aurora in four seconds and rests at "Journal at 22:10" over the name.
Scores: design 7 · usability 7 · creativity 8 · content 8 → overall 7.3 (6.0 under the inspector cap)
Still short: on a phone the strip pictures are about 80px tall, too small to read the interfaces in them; the
paragraphs run about 110 characters per line on desktop (GitHub's column).
```

## antislop Delivery Gate

Block 1, Hard Gate:

- R-02 PASS: no em dash in README.md, DESIGN.md or any plate (`grep` count 0).
- R-03 PASS: at 390px the page is 390px wide (no overflow); plates scale to 358px and their smallest type is about 14px.
- R-17 PASS: no statistics. Dates and times come from the repositories, StudyCabin's code and the GitHub API.
- R-18 PASS: no testimonials.
- R-23 PASS: no logo, avatar or portrait made; the name is set in type; the about section was redrawn to one without a portrait.
- R-24 PASS: no navigation bar.
- R-25 PASS: measured, `python tools/build.py`: hero words 3.04 to 15.51:1 (large type, needs 3), muted ink 7.95:1, ink 14.52:1, accent 7.99:1, card text 6.61:1, button text 7.80:1.
- R-26 PASS: every image is a link to a real page; the drawn button's plate links to the repositories tab.
- R-27 PASS: no data view on the page. The updater leaves the line as it is when the API fails or finds nothing.
- R-28 PASS: no FAQ.
- R-32 PASS: every control is a native link inside GitHub's page, with GitHub's focus styles.
- R-33 PASS: no feature is patched into source. `tools/now.mjs` refreshes data inside the README's marked block and `tools/build.py` writes assets; neither edits styles or code.
- R-34 PASS: checked in GitHub's light and dark stylesheets at 1280px and 390px.
- R-35 PASS: built, rendered through GitHub's markdown API, opened in Chrome. Click-through: all 16 links answer 200 (12 repositories, the repositories tab, the old portfolio site, taste-skill, anti-slop); all 6 images load; the hero plays once and stops (0 animations running at 7 s); the updater ran against the live API and wrote "Last push: StudyCabin-v1, 10 November 2026."
- R-36 PASS: no security, performance or customer claims.
- R-37 PASS: direction from the owner's own StudyCabin design (palette, typeface) and the dealt direction; Design Read above.
- R-38 PASS, with sample lines to confirm: the about paragraph's sentences about what the owner cares about are written for him.
- R-39 PASS: every image has alt text; motion stops within 5 s; reduced motion shows the final frame at once. The page-level items (lang, title, landmarks) belong to GitHub's page.
- R-40 CONFLICT, not met: images carry `width` but no `height`. With a `height` attribute, GitHub's stylesheet stretches the image (tested at 390px: 342x330 instead of 342x128), and a README cannot set `aspect-ratio`. No third-party script; no performance number reported.

Block 2, Purpose-Gate: R-01 one neutral scrim on one hero frame, for contrast (reason above); no other gradient or glow. R-04 no icons. R-06 Instrument Sans, StudyCabin's face; no monospace; no tracked capitals. R-07 no background pattern. R-08 no arrows. R-09 no badges. R-10 no glass. R-12 no shadows. R-13 no glow. R-14 no feature cards. R-19 one move, purpose written above. R-22 no illustrations. All PASS.

Block 3, Liveliness: dials declared; one focal point per plate; one accent (amber: the line-up's part headings, the contact button); identity motif: StudyCabin's "word at time" set in giant type; Design Read declared before building. All PASS.

Block 4, Craftsmanship: no AI-template layout (no bento, no logo bar, no 3-step row); one radius (8, the card); no generic CTA ("My repositories" says where it goes); no buzzwords; palette is three colours and one accent; the swap test fails for any other student, because every picture is this owner's work. All PASS.

## Rebuild

```bash
python tools/build.py        # plates; prints every contrast check and fails on any below its minimum
node tools/rasterize.mjs     # still plates to assets/*.jpg|png at 2x (needs Chrome and taste-skill installed)
node tools/now.mjs           # refresh the Last push line by hand
```

`tools/render-cabin.mjs <StudyCabin-v2/dist> <out>` re-renders the hero frames from StudyCabin's build.
`tools/src/` holds the cropped source pictures, so the plates rebuild without the other repositories.
