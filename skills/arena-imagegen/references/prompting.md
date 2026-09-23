# Prompting best practices

Adapted from the `imagegen` skill in `openai/skills` (Apache-2.0) and re-tuned for Arena
batch work. Everything here is in service of one outcome: **a prompt whose first generation is
usable**, because a wasted generation costs one of the 10 slots in the round.

## Contents
- [Structure](#structure)
- [The three layers](#the-three-layers)
- [Specificity policy](#specificity-policy)
- [Allowed and disallowed augmentation](#allowed-and-disallowed-augmentation)
- [Composition and framing](#composition-and-framing)
- [Constraints and invariants](#constraints-and-invariants)
- [Text in images](#text-in-images)
- [Reference images](#reference-images)
- [Lighting, materials and realism](#lighting-materials-and-realism)
- [Consistency across a batch](#consistency-across-a-batch)
- [Length discipline](#length-discipline)
- [Iterating](#iterating)
- [Anti-patterns](#anti-patterns)

## Structure

Use labelled lines, not one long paragraph. Order matters - generators weight early tokens more:

```text
Use case -> Asset type -> Primary request -> Input images -> Scene -> Subject
-> Style/medium -> Composition/framing -> Lighting/mood -> Palette -> Materials
-> Text (verbatim) -> Constraints -> Avoid
```

Labeled lines also make prompts reviewable: a human can scan `Constraints:` and `Avoid:` in
seconds, which is exactly what the pre-flight review in `batches.md` needs.

Why this order: intent first (what the image is for), then the subject, then the craft details,
then the guardrails. Putting guardrails last prevents them from being dropped when generation
truncates long prompts.

## The three layers

| Layer | File / source | Who edits it | How often |
| --- | --- | --- | --- |
| Per-image intent | the request-sheet row | data entry | every row |
| Use-case structure | `templates/recipes.json` | you (rarely) | when a use case needs rework |
| Style lock | `templates/brand.json` | you / brand owner | once per campaign |

`tools/igp.py plan` merges them in that resolution order: **row → brand lock → recipe default**.
If a row sets `scene`, it wins; otherwise the brand lock's `scene` applies (studio use cases only);
otherwise the recipe default. Empty values drop out of the prompt entirely.

## Specificity policy

- Row already specific and detailed → **normalise**, do not expand. Reordering into the labelled
  format is a real improvement; adding invented props is not.
- Row generic ("a nice photo of the mug") → add only the detail that materially improves output:
  framing, light quality, polish level, and scene concreteness that supports the stated request.
- Never invent: extra characters, props, brand names, slogans, palettes or story beats that the
  row does not imply. If the image needs a detail the row does not have, **ask the user**.

The `lint_prompt()` QA in `igp.py plan` already flags the mechanical problems (missing
Constraints/Avoid, edit use cases without `must_keep`, text use cases without `text_verbatim`,
prompts over 1,500 chars). Judgment problems are yours.

## Allowed and disallowed augmentation

Allowed: composition/framing cues, intended-use or polish hints, practical layout guidance,
scene concreteness that supports the request.

Disallowed: extra characters or objects, brand palettes/slogans not implied, arbitrary
left/right placement unless the surrounding layout needs it, restyling an identity-locked product.

## Composition and framing

- State the framing explicitly: `close-up`, `medium shot`, `wide`, `top-down`, `eye level`,
  `three-quarter angle`. Vague framing is the most common cause of "correct image, unusable crop".
- State the aspect in words **and** ratio: `square 1:1 format`, `vertical portrait 4:5 format`.
  `igp.py plan` does this automatically from the row's `aspect` column.
- If the asset needs copy space, say where: `generous negative space on the upper half for page copy`.
- Ask for the whole product inside frame with even padding - cropping in post loses detail.

## Constraints and invariants

- Constraints = what must stay true. Avoid = what must not appear. Keep them separate; mixing them
  is how "keep the label sharp" ends up as a thing the model tries to remove.
- For edits, the invariant sentence is mandatory:
  `change only the background; keep the product, its edges, lighting, geometry and framing unchanged`.
- **Repeat invariants on every iteration.** Drift between iterations is the norm, not the exception.
- 5-8 constraint clauses and 5-10 avoid clauses is the useful range (food & drink rows run 1-2
  higher: freshness, garnish and claim limits are all real requirements); beyond that they compete.

## Text in images

Generators still misspell. Treat in-image text as a risk with mitigations:

1. Quote it exactly: `Text (verbatim): "ACME Home" - render exactly these characters`.
2. Spell short/unusual words letter-by-letter: `spell it A-C-M-E`.
3. Generate the artwork with room for text, then place real type afterwards when the text matters
   commercially (packaging, labels, posters). A perfect image with typeset text beats a generated
   garble.
4. Verify by zooming into the returned image at 100%. Do not approve label text from a thumbnail.
5. If text fails twice, stop regenerating - switch strategy (typeset overlay or a cleaner crop).

## Reference images

- Label every input by index and role: `Image 1: product reference (identity lock)`,
  `Image 2: style reference`, `Image 3: background plate`.
- Max ~3 references; more dilutes each one's influence.
- Editing a supplied image? Then it is an **edit**, and the reference is the edit target - say so.
- Supplying images for style or mood only? That is **generation with references**; say
  `use Image 2 only for the look - do not copy its subject`.
- For identity preservation, name the features: `same shape, proportions, material, colour,
  hardware, stitching, label placement`.

## Lighting, materials and realism

- Realism comes from naming light and surface, not from the word "realistic":
  `large softbox key slightly camera-left, soft fill, gentle contact shadow` beats `good lighting`.
- Ask for material micro-texture when detail matters: `visible leather grain`,
  `woven fabric texture`, `brushed metal anisotropy`.
- Name the flaw-avoiders for people: `natural skin texture with pores`, `no plastic skin`,
  `unretouched` - this is what stops the over-smoothed look.
- Same light direction across a batch is what makes set-consistency believable; it lives in the
  brand lock's `lighting` line.
- **Food & drink:** appetite appeal comes from texture and light, not adjectives - name crumb/crust,
  condensation, ice, oil sheen and glossy highlights, and match the serving temperature.

## Consistency across a batch

The generator has no seed control, so consistency is engineered:

1. One locked `look` + `studio` block for the whole batch (`templates/brand.json`).
2. The same reference image for every image of the same product.
3. Identical framing words across the batch (`centred product, mid-height, mild three-quarter angle`).
4. Generate the whole batch in one round, in one message, so the same operator state applies.
5. Keep aspect and background identical - variety comes from angle/scene choice per row, not from
   restyling.

## Length discipline

- Sweet spot: 8-16 labelled lines, ~700-1,400 characters.
- Over 1,500 characters: cut adjectives and duplicate clauses before cutting requirements.
- The prompt builder de-duplicates near-identical constraint/avoid clauses automatically
  (`join_unique`) - if you see repetition in `plan.md`, fix the source (row, recipe, or brand),
  not the rendered prompt.

## Iterating

- One targeted change per iteration, then re-check.
- Prefer prompt surgery over re-rolling the same prompt - a re-roll without a change is a wasted slot.
- Keep the version that scored best; never overwrite it.
- After two failed attempts on a row, switch strategy or ask the user (see `quality-control.md`).

## Anti-patterns

| Anti-pattern | Why it fails | Do instead |
| --- | --- | --- |
| "high quality, 8k, masterpiece" | no operational meaning | name lighting, lens feel, material detail |
| negative-only prompt | no subject to render | state the subject first, then Avoid |
| 40 stacked avoid clauses | dilutes the instruction | 5-10 clauses that matter |
| editing without invariants | everything drifts | restate `change only X; keep Y` |
| restyling an identity-locked product | product no longer matches the listing | lock identity, change the scene only |
| regenerating the same prompt | same failure, one slot spent | change exactly one clause |
| embedding brand text and hoping | misspellings | typeset text after generation |
