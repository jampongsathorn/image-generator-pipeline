# image-generator-pipeline

Batch image production for Arena AI: **data entry drops a request sheet + reference photos →
the agent returns finished images, one delivery bundle per round.**

Built around the environment's real limits:

| Limit | Value | How this repo handles it |
| --- | --- | --- |
| Generated images | **10 per round** | requests are planned and sliced into rounds of ≤10; retries spend slots |
| Session workspace | **128 MB / 10,000 files** | raws are compressed then deleted each round; review = one contact sheet; `igp.py budget` guards |
| Image generator | Arena's built-in tool | no OpenAI API, no API key, ever |
| Requests | one row = one image | the sheet is the contract; prompts are generated, reviewable text |

📄 **Daily procedure: [`docs/DAILY-FLOW.md`](docs/DAILY-FLOW.md)** (TH + EN) ·
🤖 **Agent rules: [`AGENTS.md`](AGENTS.md)** ·
🎯 **Skill: [`skills/arena-imagegen/SKILL.md`](skills/arena-imagegen/SKILL.md)**

## The round loop

```
INTAKE    inbox/<batch>/  (requests.csv + reference photos)
  |
PLAN      python3 tools/igp.py intake --name <batch> --round-id <YYYY-MM-DD-rNN>
          -> rounds/<id>/plan.md   (one reviewable prompt per image, QA-linted)
  |
REVIEW    read plan.md, fix prompts, settle open questions      <- free, do it every time
  |
GENERATE  <=10 image calls into rounds/<id>/raw/                <- this is the round
  |
OPTIMIZE  python3 tools/igp.py optimize --round rounds/<id> --delete-source --upscale-to-spec
REVIEW    python3 tools/igp.py sheet    --round rounds/<id>     <- one contact sheet
VERIFY    python3 tools/igp.py verify   --round rounds/<id>
DELIVER   python3 tools/igp.py deliver  --round rounds/<id>     <- zip + manifest
BUDGET    python3 tools/igp.py budget
```

## Quickstart

```bash
# 1. data entry: one row per image + the reference photos
mkdir -p inbox/2026-09-24-catalogue && cp templates/requests.csv inbox/2026-09-24-catalogue/
#    edit requests.csv, drop reference images into the same folder

# 2. plan the round
python3 tools/igp.py intake --name 2026-09-24-catalogue --round-id 2026-09-24-r01 --clean
#    -> review rounds/2026-09-24-r01/plan.md

# 3. after generating <=10 images into rounds/<id>/raw/
python3 tools/igp.py optimize --round rounds/2026-09-24-r01 --delete-source --upscale-to-spec
python3 tools/igp.py sheet    --round rounds/2026-09-24-r01
python3 tools/igp.py verify   --round rounds/2026-09-24-r01
python3 tools/igp.py deliver  --round rounds/2026-09-24-r01
python3 tools/igp.py budget
```

## What the team receives

```
rounds/<id>/review/
  contact-sheet.jpg          the whole round in one image
  verify-report.md           delivered / flagged / missing, with pixel and size checks
  <id>-manifest.csv          every image + the exact prompt that produced it
  <id>-delivery.zip          finals + manifest + plan   <- the handover file
```

## Request sheet columns

Required: `id`, `item_name`, `use_case`, `description`.
Then: `ref_images`, `aspect`, `delivery_px`, `format`, `text_verbatim`, `must_keep`, `must_avoid`,
`asset_type`, `priority`, `notes`, `variants`.
Full column guide: [`docs/DAILY-FLOW.md`](docs/DAILY-FLOW.md) · use-case list:
[`skills/arena-imagegen/references/use-cases.md`](skills/arena-imagegen/references/use-cases.md).

## Tuned for food & drink

The style lock and recipes ship configured for **food & drink** imagery (rename `brand_name` in
`templates/brand.json` and adjust the palette once):

- 3 food-specific use cases on top of the 16 shared ones: `food-hero` (styled dish/drink, appetite
  appeal), `packaging-shot` (bottle/jar/pouch with a legible label) and `flat-lay` (overhead layout).
- The brand `look` (palette, materials, mood) applies to every image; the clean **studio** setup
  applies only to `product-mockup`, `packaging-shot`, `background-extraction` and `sketch-to-render`.
  Styled food shots keep their own scene and light, so a tabletop never inherits a seamless backdrop.
- Guardrails that matter for food: no invented labels, badges, nutrition or health claims; freshness
  cues (crumb, condensation, ice, oil sheen) named explicitly; steam only on hot, condensation only
  on cold; portions that match the product.

## Prompt quality is the product

Every prompt is assembled from three layers so that ten separate generations look like one shoot:

```
request row  ->  templates/recipes.json  ->  templates/brand.json
(intent)          (use-case structure)      (style lock + global rules)
```

- **Style lock**: `look` applies to every image; `studio` (backdrop, softbox lighting, framing)
  applies only to studio use cases, so a street scene never inherits a seamless backdrop.
- **Prompt QA** (`igp.py plan`) flags missing constraints, missing invariants on edits, missing
  verbatim text, over-long constraint lists, and delivery sizes above what the generator produces.
- **Detail fidelity**: generate at the largest native size, downscale rather than upscale, upscale
  only via Lanczos + one unsharp pass, never re-encode a delivered JPEG.
  See [`references/detail-fidelity.md`](skills/arena-imagegen/references/detail-fidelity.md).

## Repository layout

```
AGENTS.md                 agent rules: read-first list, hard limits, command reference
README.md                 this file
templates/                recipes.json (19 use cases), brand.json (food & drink style lock), request sheets
tools/igp.py              toolkit: intake/plan/optimize/upscale/sheet/verify/deliver/status/budget/prune
tools/fetch_upstream_skill.sh   vendor OpenAI's imagegen prompt reference for comparison (Apache-2.0)
skills/arena-imagegen/    the skill: SKILL.md, references/, NOTICE.md
rounds/<id>/              requests.csv, plan.json, plan.md, refs/, raw/, out/, review/
inbox/<batch>/            drop zone for new requests
archive/                  zipped delivered rounds
docs/                     DAILY-FLOW.md (TH/EN), SETUP.md
```

## Setup

No install step: `tools/igp.py` is stdlib-only Python and uses ImageMagick if present (Pillow as a
fallback). Requirements, refresh instructions and the verification checklist live in
[`docs/SETUP.md`](docs/SETUP.md).

## Scope and limits

- **Used for:** raster assets from request sheets - product/catalogue shots, lifestyle scenes,
  cutouts, mockups, diagrams, logos, illustrations, and edits of supplied images.
- **Not used for:** vector/SVG/code-native artwork that should match an existing icon or logo system.
- **No external image API.** The upstream OpenAI imagegen CLI is intentionally not vendored
  ([`NOTICE.md`](skills/arena-imagegen/NOTICE.md)).
- Generated images are AI output: check text, logos and product identity before publishing.
