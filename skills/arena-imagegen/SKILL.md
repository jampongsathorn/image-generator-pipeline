---
name: "arena-imagegen"
description: "Run batch image generation for data-entry requests inside Arena Agent Mode. Use when the team drops a request sheet plus reference photos and expects finished images back: product shots, lifestyle scenes, cutouts, infographics, logos, UI mockups, or edits of supplied images. Covers prompt construction, the 10-images-per-round limit, detail preservation and upscaling, per-round review, and the 128MB session workspace budget. Do not use for vector/SVG/code-native artwork or when an existing vector asset should be matched instead."
---

# Arena batch image generation

Operating skill for producing **many finished images from a data-entry request sheet** in
Arena Agent Mode, where four constraints decide everything:

| Constraint | Value | Consequence |
| --- | --- | --- |
| Generated images | **10 per round** (not per session) | work in planned rounds of ≤10; a retry spends a slot |
| Workspace | **128 MB / 10,000 files per session** | raw files are transient; compress, then delete; never open 30 previews |
| Generator | Arena's built-in image tool (no OpenAI API, no API key) | one call per image; reference images are passed as inputs |
| Requests arrive as rows | request sheet + reference photos | the sheet is the contract; one row = one image |

**Golden rule: plan the whole batch as text BEFORE generating anything.** Generation is the
scarce resource; prompt review is free. A round of 10 generated with unreviewed prompts wastes
the round; the same round after a 2-minute prompt pass usually lands 8-10 usable images.

## Non-negotiables

1. **Never use the OpenAI API for images.** No `OPENAI_API_KEY`, no `image_gen.py` CLI fallback.
   The vendored upstream skill's CLI sections are reference material only - see `NOTICE.md`.
   If the built-in tool is unavailable, say so; do not substitute an API path.
2. **Never generate more than 10 images per round.** Count them. Parallel calls in one message
   count against the same round.
3. **Never overwrite a delivered final.** Iterations become a new version suffix
   (`sku-1001-v2.jpg`), so the team can always compare.
4. **Never let a raw/ file survive the round.** Optimize into `out/`, then delete the raw.
5. **Never shrink below the delivery spec and call it done.** If the generator returns less than
   the spec, upscale deliberately (`igp.py upscale`) or regenerate - see `references/detail-fidelity.md`.
6. **Always keep the request sheet as the single source of truth** for what a row asked for.
   If the sheet is ambiguous, ask; do not silently invent a product detail.

## The round loop

```
INTAKE      data entry drops sheet + refs        -> inbox/<batch>/
PLAN        python3 tools/igp.py intake ...      -> rounds/<id>/{plan.md,plan.json,refs/}
REVIEW      read plan.md, fix prompts,           (free - no generation spent)
            confirm open questions with the user
GENERATE    <=10 image calls into raw/           (this is the round)
OPTIMIZE    python3 tools/igp.py optimize --round rounds/<id> --delete-source --upscale-to-spec
REVIEW      python3 tools/igp.py sheet --round rounds/<id>   (ONE contact sheet)
VERIFY      python3 tools/igp.py verify --round rounds/<id>
DELIVER     python3 tools/igp.py deliver --round rounds/<id>  -> one zip + manifest
BUDGET      python3 tools/igp.py budget          (before starting the next round)
```

If more than 10 images are requested, the loop repeats per round. Rounds are independent: finish
(optimize + verify + deliver) one before starting the next, so nothing accumulates in `raw/`.

## Prompt construction

Prompts are built from three layers and assembled by `tools/igp.py plan`:

```
request-sheet row  -> per-image intent (the only part data entry writes)
templates/recipes.json -> use-case structure (19 slugs: 16 shared with openai/skills + 3 food & drink) + defaults
templates/brand.json   -> style lock: 'look' everywhere, 'studio' for studio use cases only
```

Every prompt is a labelled spec, in this order (see `references/prompting.md` for the reasoning):

```text
Use case: <slug>
Asset type: <where the image is used>
Primary request: <what the row asked for>
Input images: Image 1: refs/xxx.jpg        (role-labelled)
Scene/backdrop: ...
Subject: ...
Style/medium: ...
Composition/framing: <aspect words> ...
Lighting/mood: ...  Mood: ...
Color palette: ...  Materials/textures: ...
Text (verbatim): "EXACT TEXT"              (quoted, literal)
Constraints: <5-8 clauses: what must stay true>
Avoid: <5-10 clauses: what must not appear>
```

Rules that pay for themselves:
- **Locked style block on every image in a batch** - that is what makes 10 separate generations
  look like one photoshoot. Change it per campaign, never per image.
- **Reference images get roles**: `Image 1: edit target`, `Image 2: style reference`. Never leave
  the tool guessing.
- **Edits repeat their invariants every iteration** (`change only X; keep Y unchanged`).
- **Text is always quoted verbatim**, and spelled letter-by-letter when it is short or unusual.
- Keep prompts under ~1,500 characters; bloat dilutes the important clauses.

## Quality control

Check every returned image against the row's intent before accepting it:

```text
[ ] subject matches the row (product, colour, material, count)
[ ] no invented text, logos or props
[ ] framing/aspect matches the plan
[ ] product identity preserved vs the reference (shape, label, hardware)
[ ] no anatomy/geometry defects (hands, warped edges, duplicated parts)
[ ] detail level is acceptable at delivery size (zoom in, do not trust the thumbnail)
```

Any failure -> fix the prompt, not the review standard (`references/quality-control.md` has a
defect → prompt-fix table). Spend retries only on priority rows.

## Where to read more

| File | Read it when |
| --- | --- |
| `references/prompting.md` | writing or fixing any prompt |
| `references/use-cases.md` | choosing a use-case slug / knowing its key levers |
| `references/batches.md` | batching, retry budgets, reporting per round |
| `references/quality-control.md` | an image came back wrong and you need the fix |
| `references/detail-fidelity.md` | resolution, upscaling, "do not lose detail" work |
| `references/storage-budget.md` | before a big batch, or when `igp.py budget` warns |
| `../../AGENTS.md` | the machine-readable rules this skill assumes |
