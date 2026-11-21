# Visual storytelling guide

How narration becomes pictures in the reference style, and how fvs implements each device with original work.

## Translating narration into scenes

1. Split the narration into **ideas** (usually 2–3 per sentence): the noun or number that is new.
2. For each idea choose the most *concrete* picture available, in this order:
   real licensed photo/clip of the subject → photo of its context (place, object, era) → graphic that makes the
   idea physical (counter, map, blocks, meter) → kinetic text.
3. Add **one** explanatory layer if the picture alone is ambiguous: a lowercase label naming it, a red arrow at
   the detail that matters, a price tag, a handwritten aside.
4. Check honesty: does the picture show what the narration says? (No look-alikes, no unrelated "mood" stock.)

## Devices observed (and the fvs equivalent)

| Device in the references | Example timestamps | fvs |
|---|---|---|
| Name label beside a person | v8 00:00.57 "steve ballmer"; v5 02:20 "queen of england" | `label` at `@Name` |
| Red arrow at a detail + short label | v8 00:15.48 "steve jobs"; v8 00:32.05 missing plate; v2 02:15.58 "$2.4B shanghai tower" | `arrow` with `label` |
| Location pin label | v2 01:20.45 "new york city 📍"; v5 03:01 "cayo norte, puerto rico 📍" | `label` `style: pin`, `map` pins |
| Money on the object | v2 00:55.82 "$2,100 each" on a cruise ship; v2 01:22 "$100B" on a building | `label` `style: money` |
| Price-tag pill (thumb + price + name) | v3 12:16 "$150K"; v3 14:11 "$460K SLR McLaren"; v6 02:04 "$50K/week" | `pricetag` |
| Ranking board as home base | v8 00:00, 00:14, 00:40; v3 11:45; v6 02:38 | `ranking` (own design per film) |
| World map with face pins | v5 02:17, 02:50 | `map` with `pins` (labels or licensed images) |
| 3D studio object with a figure | v2 01:28 "$817,035,040,000" block; v2 02:05 money stack | `blocks3d`, `stat` |
| Document / article with highlighted phrase | v1 01:38 handbook; v3 12:02 headline; v6 01:44 news snippet | `document` (`highlight`) |
| Social post / search result mockup | v4 13:31 post card; v6 02:15 search snippet | `document` or `custom` (original layout, no real branding) |
| Phone / screen mockup | v1 01:45 video-call phone; v1 02:01 sign-up form | `custom` composition |
| Cutout person/object on white studio | v8 00:26 head + car; v1 02:37 businessman; v7 05:44 watches | `cutout` |
| Measurement graphic | v4 13:04 "6ft 1in" height bar | `custom` / `meter` |
| Collage grid with labels | v5 02:55 islands; v4 14:54 clippings | `collage` |
| Handwritten aside with arrow | v1 02:22 "she won $2m →", 02:25 "he won $149m" | `hand` (`to:` adds an arrow) |
| Progress meter to a value | v1 02:28 "$157m" | `meter` |
| Text-only beat on black | v7 05:24 "but nowadays"; v7 06:32 "and dangerous"; v4 15:28 "look:" | `kinetic` on solid |
| Word-synced quote captions | v8 00:09–00:13; v5 03:12–03:20; v7 06:28 | `captions` / `label reveal: words` |
| B&W + red graphic for a negative turn | v2 01:24 "transaction failed" stripes | `photo grade: bw-red` |
| Picture-in-picture inset with dark surround | v3 14:12; v6 02:32; v4 14:19 | `inset` |
| Vertical clip centred in 16:9 | v6 01:57, v7 05:26, v4 13:15 | `inset` (portrait asset) |
| Pixelation of what cannot be shown | v3 14:36 magazine faces | CSS filter/`custom` (use only for licensing/privacy reasons) |

## Historical periods and abstract concepts

- **Era:** B&W/sepia grade + year label (top-left) or a `timeline`; return to colour when the story reaches the
  present (the sample film does this: 1956 in B&W → modern port in colour).
- **Abstract idea → metaphor object:** cost → falling counter; scale → stacked 3D containers; inequality →
  comparison split; time → route drawing on a map.
- **Statistics:** one figure at a time, big, counted up on the spoken word, with a small lowercase unit line.

## Avoiding repetition

- Plan formats per segment before choosing assets: e.g. map → photo+label → stat → document → photo+arrow.
- Change the *camera* too: static, push-in, pull-out, pan; and the *framing*: full-bleed, inset, split, cutout.
- Give each film its own palette accents and its own home-base graphic.
