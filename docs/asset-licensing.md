# Asset licensing

Every downloaded or generated file is recorded in `assets/asset-licence-register.csv` with: asset id, filename,
type, original URL, landing page, creator, source platform, licence (+ raw licence code), licence URL, commercial
use, attribution required, attribution text, modification allowed, date accessed, scene, intended usage, width,
height, SHA-256, notes.

## Accepted automatically (verified per asset from the source's own metadata)

| Licence | Attribution | Notes |
|---|---|---|
| CC0, Public Domain Mark, public-domain works | no | |
| US federal works (e.g. NASA) | no | no logos/insignia, no implied endorsement; third-party NASA items flagged for review |
| CC BY (any version) | **yes** — `reports/attributions.txt` goes in the video description | |
| Pexels License | no | no implied endorsement by identifiable people/brands |
| Pixabay Content License | no | same |

Refused: CC BY-SA (share-alike can extend to the whole video; opt in with `FVS_ALLOW_SHARE_ALIKE=1` only after
reading the licence), any NC or ND licence, missing or unrecognised licences. Never: pirated media, DRM/paywall
circumvention, watermark removal, YouTube rips. Company logos and product photos are trademarks: use only
editorially and record it in `notes`.

## Sources

| Source | Key | Status in this build |
|---|---|---|
| Openverse (aggregates Flickr, Wikimedia, rawpixel, museums…) | none | ✅ tested |
| NASA Image and Video Library | none | ✅ search tested |
| Wikimedia Commons API | none (needs a contact User-Agent: `FVS_HTTP_USER_AGENT`) | ⚠️ HTTP 429 from the cloud test session's shared IP |
| Pexels (photos + video) | `PEXELS_API_KEY` (free) | implemented, untested (no key) |
| Pixabay (photos + video) | `PIXABAY_API_KEY` (free) | implemented, untested (no key) |
| Internet Archive / Library of Congress | — | manual: rights vary per item; add with `pick` after checking |

Ranking: relevance (query words in the title, the source's own order) → resolution → 16:9 shape; watermark hints
are penalised. Claude must look at the candidate sheet (`fvs asset-search --sheet`) before choosing.

Original work (synthesised SFX, procedural music, code-drawn graphics) is registered as `Original work`.
Paid stock or paid AI generation: only after the user approves the cost.
