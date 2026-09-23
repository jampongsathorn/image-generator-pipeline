# Use-case taxonomy and key levers

16 slugs, matching the naming used by `openai/skills` imagegen so prompts stay portable between
tools. The slug goes in the request sheet's `use_case` column; `tools/igp.py plan` picks the recipe
from `templates/recipes.json` and applies its defaults.

## Contents
- [Generate](#generate)
- [Edit](#edit)
- [Quick chooser](#quick-chooser)
- [Adding or changing a use case](#adding-or-changing-a-use-case)

## Generate

### `product-mockup`
Clean studio shot of a product. Default for catalogue/listing work.
- Levers: `Scene/backdrop` (seamless or set), `Lighting/mood`, `Materials/textures`, exact label wording.
- Watch: product drifting from the reference → strengthen the `Subject:` identity line.
- Default output: 1:1 JPEG 2048px.

### `photorealistic-natural`
Lifestyle / in-use / candid photo (product on a street, in a kitchen, in someone's hands).
- Levers: real-world environment, natural light, `unretouched` texture wording.
- Watch: studio gloss creeping in, plastic skin, distorted hands.
- Default output: 4:5 JPEG 2048px.

### `background-extraction`
Cutout on transparent (or pure white) background.
- Levers: crisp silhouette, no halo, whole product in frame, keep label text exactly.
- Watch: thin parts (straps, reeds, handles) - inspect at 400%.
- Default output: 1:1 PNG 2048px. Quantize with `--png-colors 256` when flat.

### `compositing`
Place a product from a reference into a new scene/plate.
- Levers: matched perspective, scale, ground contact, shadow direction, colour temperature.
- Watch: the pasted look - shadow direction is the giveaway.
- Default output: 1:1 JPEG 2048px. Requires 2 references (product + scene).

### `logo-brand`
Logo/mark exploration.
- Levers: strong silhouette, balanced negative space, flat colour, readable small.
- Watch: clutter, gradients, 3D bevels; trademarks.
- Default output: 1:1 PNG 2048px. Supersample + downscale for crisp edges.

### `ui-mockup`
App or web screen mockups.
- Levers: realistic density, hierarchy, consistent spacing/radius.
- Watch: unreadable micro-text and sci-fi chrome.
- Default output: 9:16 PNG 2048px.

### `infographic-diagram`
Diagram/infographic with labels and flow.
- Levers: explicit labelled parts, reading flow, `Text (verbatim)` for every label.
- Watch: garbled labels → spell key words letter-by-letter or typeset afterwards.
- Default output: 4:5 PNG 2048px.

### `stylized-concept`
Concept art, stylized 3D/clay/painterly renders.
- Levers: style cues, material finish, rendering approach.
- Watch: mixing styles in one frame.
- Default output: 16:9 JPEG 2048px.

### `illustration-story`
Illustrations, comics, children's book art, multi-panel scenes.
- Levers: per-panel beats, consistent character design.
- Watch: character continuity across panels.
- Default output: 1:1 JPEG 2048px.

### `historical-scene`
Period-accurate scenes.
- Levers: date/place, period-accurate clothing, props, materials.
- Watch: anachronisms.
- Default output: 3:2 JPEG 2048px.

## Edit

### `identity-preserve`
Keep the exact product/person, change the scene or context.
- Invariant: shape, proportions, material, colour, hardware, label stay identical; relight to the new scene.
- Default output: 1:1 JPEG 2048px. Requires the `must_keep` column.

### `precise-object-edit`
Change or remove one specific element; everything else stays pixel-faithful.
- Invariant: `change only X; keep framing, background, lighting, geometry, colours, shadows`.
- Default output: native size of the input (`delivery_px` = 0 = keep native).

### `lighting-weather`
Time-of-day / season / atmosphere change only.
- Invariant: geometry, framing, subject identity unchanged.
- Default output: native size.

### `style-transfer`
Apply a reference look while keeping the subject.
- Invariant: copy palette/texture/finish only; subject unchanged.
- Default output: 1:1 JPEG 2048px. Requires 2 references (subject + style).

### `sketch-to-render`
Line art / CAD / sketch → photoreal render.
- Invariant: respect the drawing's proportions, layout, element count.
- Watch: invented details not in the sketch.
- Default output: native size or 2048px.

### `text-localization`
Replace/translate in-image text, keep layout.
- Invariant: only the glyphs change; layout, typography weight, spacing, hierarchy stay.
- Default output: native size PNG.
- Best practice: if the text matters commercially, generate clean artwork and typeset the real text.

## Quick chooser

| The row says... | Use |
| --- | --- |
| "clean catalogue shot", "on white" | `product-mockup` |
| "in use", "lifestyle", "on a person", "at home" | `photorealistic-natural` |
| "cutout", "transparent", "no background" | `background-extraction` |
| "put our product in this scene" | `compositing` |
| "same product, new background only" | `identity-preserve` |
| "remove the logo", "change this one thing" | `precise-object-edit` |
| "make it evening", "summer version" | `lighting-weather` |
| "in this style", "match our other brand's look" | `style-transfer` |
| "from this sketch/drawing" | `sketch-to-render` |
| "translate the label", "change the text" | `text-localization` |
| "logo", "mark", "brand symbol" | `logo-brand` |
| "app screen", "website mockup" | `ui-mockup` |
| "diagram", "infographic", "explainer" | `infographic-diagram` |
| "concept art", "3D render look" | `stylized-concept` |
| "illustration", "comic", "storybook" | `illustration-story` |
| "vintage", "period", "19th century" | `historical-scene` |

If the row's `use_case` is unknown, `igp.py plan` warns and suggests the closest slug, then falls
back to `product-mockup`. Fix the sheet rather than accepting the fallback when the row was meant
to be an edit.

## Adding or changing a use case

1. Add the slug to `templates/recipes.json` with `template`, `defaults`, `aspect_default`,
   `format_default`, `delivery_px_default`.
2. Placeholders available in templates: `{id} {item} {description} {asset_type} {refs} {scene}
   {subject} {style} {framing} {lighting} {mood} {palette} {materials} {text} {constraints}
   {avoid} {aspect} {extra} {brand}`. Empty values vanish from the output.
3. If the use case is a clean studio setup, add it to `studio_use_cases` in `templates/brand.json`,
   otherwise it keeps the recipe's own scene/lighting and only inherits the brand `look`.
4. If it is an edit type that drifts, add it to `EDIT_USE_CASES` in `tools/igp.py` so the QA lint
   requires `must_keep`.
5. If it carries in-image text, add it to `TEXT_USE_CASES` so the lint requires `text_verbatim`.
