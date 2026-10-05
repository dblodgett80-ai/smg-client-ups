# UPS Activity Tracker

Live site: https://dblodgett80-ai.github.io/smg-client-ups/
Prepared by SMG Entertainment for UPS. Same layout as the Chosen Foods and General Mills trackers.

## How it's built

`index.html` is generated — never edit it by hand. Edit the data in `build.py`, then run:

```
python3 build.py
```

| What you're updating | Where in `build.py` |
|---|---|
| Aired placements (Secured Integrations) | `TITLES` — one entry per show; each scene points at a `pNN` clip folder |
| Nielsen impressions | `NIELSEN` — `"pNN": (broadcast, streaming)` Live+30, Persons 2+ |
| Pipeline (product sent / propped) | `SHOWS` — from Camille's monthly A-List status report; newest order first |
| Pipeline posters | `showcards/<key>.jpg`; add the key to `CAST_PHOTOS` if it's an actor photo |

Page styling lives in `template.html`.

### Clips

Each placement's video and poster live in `clips/` (e.g. `clips/p02-1.mp4`), listed in `clips/index.json`.
To add a new placement:

1. Download the clip (.mp4) and its screenshots (.jpg) from productplacementblog.com, keeping the original
   filenames (they contain the timestamps).
2. Put them in a new folder `source-media/pNN/` (next unused number).
3. Add a `TITLES` entry pointing at `pNN`, then run `python3 build.py`.

`source-media/` is not published (it's in `.gitignore`); the build works without it using the clips already
in `clips/`.

## Publishing

```
git pull
python3 build.py
git add -A && git commit -m "Describe the update" && git push
```

The live site updates about a minute after the push. Always `git pull` first so you don't overwrite a
teammate's changes.

## Sources

- Placements: productplacementblog.com, United Parcel Service (UPS) tag, 2026 posts
- Pipeline: A-List Placements UPS Status Report (Camille, monthly) + "Propped UPS" titles in the Production Radar
- Impressions: Nielsen monthly pulls (forwarded by Erin / Anne)
