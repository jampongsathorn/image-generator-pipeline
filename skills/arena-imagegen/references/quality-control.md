# Quality control and defect fixing

A round is only finished when every generated image has been inspected against the row that
requested it. This file is the checklist, the defect → fix table, and the escalation rules.

## Contents
- [Inspection workflow](#inspection-workflow)
- [Acceptance rubric](#acceptance-rubric)
- [Per-use-case hotspots](#per-use-case-hotspots)
- [Defect → prompt fix](#defect--prompt-fix)
- [Escalation rules](#escalation-rules)
- [What to record](#what-to-record)

## Inspection workflow

1. **Contact sheet first** (`igp.py sheet --round rounds/<id>`). One 200-500KB file shows the whole
   round. Use it to spot the obvious rejects without filling the session budget with 10 full-size
   previews.
2. **Zoom the candidates.** Anything with text, a logo, fine hardware, stitching, or a face must be
   inspected at 100% before acceptance. Thumbnails hide exactly the defects that get complained about.
3. **Compare against the reference**, side by side, for identity-locked rows: shape, proportions,
   colour, label, hardware, count of parts.
4. **Check the numbers** (`igp.py verify`): pixels vs spec, file size vs cap, coverage vs the plan.
5. **Record the verdict** in the round manifest (accepted / retried / rejected + why).

Never approve from a contact sheet alone; never reject from a contact sheet alone either.

## Acceptance rubric

| # | Check | Fail means |
| --- | --- | --- |
| 1 | Subject matches the row (product, colour, material, quantity) | row intent not met - the one defect that always fails |
| 2 | No invented text, logos, watermarks or props | commercial risk; regenerate with a tighter Avoid line |
| 3 | Framing/aspect matches the plan | layout unusable downstream |
| 4 | Product identity preserved vs reference | listing no longer matches the product |
| 5 | No anatomy/geometry defects (hands, warped edges, duplicated parts) | visibly AI; regenerate |
| 6 | Detail acceptable at delivery size (text, stitching, label) | detail loss; see `detail-fidelity.md` |
| 7 | Lighting/perspective physically plausible | looks pasted; regenerating with matched light is cheaper than fixing in post |
| 8 | Batch consistency (same background, light, grade as the rest of the round) | set looks mismatched |

Points 1-5 are hard fails. 6-8 can be accepted with a note if the row is low priority and the
image is still usable - but say so explicitly.

## Per-use-case hotspots

| Use case | Most common failure | Check specifically |
| --- | --- | --- |
| `product-mockup` | product drifts from reference | silhouette, label position, hardware, colour cast |
| `photorealistic-natural` | over-smoothed, staged look | skin/fabric texture, plausible environment clutter, hands |
| `background-extraction` | halos, leftover shadow, clipped edges | edge zoom at 400%, thin parts (handles, straps, reeds) |
| `identity-preserve` | product restyled while relighting | any change beyond the requested scene |
| `precise-object-edit` | unintended global changes | background pixels vs the original, crop shift |
| `compositing` | wrong shadow direction/scale | ground contact, shadow angle, reflection |
| `text-localization` | misspelled text, reflowed layout | every character, baseline alignment, spacing |
| `infographic-diagram` | garbled or missing labels | each label verbatim, arrow targets, reading flow |
| `logo-brand` | cluttered mark, unreadable small | silhouette, negative space, one-colour readability |
| `ui-mockup` | unreadable micro-text, sci-fi styling | realistic density, legible headings, no fake chrome |
| `stylized-concept` | mixed art styles in one frame | consistent rendering, single light logic |
| `illustration-story` | inconsistent characters across panels | face/hair/clothing continuity panel to panel |
| `lighting-weather` | geometry changed with the light | framing identical to input, no new objects |
| `sketch-to-render` | invented details not in the sketch | element count vs the drawing, proportions |
| `style-transfer` | style drift, half-styled regions | whole frame styled consistently, subject intact |
| `historical-scene` | anachronisms | modern objects, fabrics, tools, signage |
| `food-hero` | food looks dry, plastic or staged | crumb/crust texture, gloss on liquid, garnish placement, steam vs condensation |
| `packaging-shot` | invented badges, claims, or misspelled labels | label spelling verbatim, no nutrition/certification marks, label unobstructed |
| `flat-lay` | overlapping or cropped items, busy layout | spacing, hero dominance, everything inside frame, no tilt |

## Food & drink specifics

- **Appetite appeal is a hard requirement, not a nicety.** If the dish/drink does not look appetizing
  in the first second, reject it even when every other check passes.
- **Freshness cues:** crumb and crust structure on baked goods, oil sheen on hot food, condensation
  and ice on cold drinks, glossy glaze on pastries. Steam only on hot dishes; condensation only on
  cold drinks - mixing them reads as fake.
- **Garnish must match the row**, including placement and quantity. A garnish the row did not ask for
  is an invented detail.
- **Claims are a legal risk, not a style issue.** Never add health, nutrition, "organic", "sugar-free"
  or certification wording that the sheet did not supply verbatim. If a generated label contains
  invented claims, reject it - do not crop around it and hope.
- **Packaging text**: treat every label as `Text (verbatim)` work. Spell the wording letter-by-letter
  in the prompt when it is short, inspect at 100%, and prefer typesetting the final label in post.
- **Props:** for food, tasteful props are wanted (unlike hard-goods catalogues). The avoid list
  targets *clutter* and props that compete with the subject, not props in general.
- **Portion realism:** portions must match what the product actually serves; oversized portions on a
  packaging shot misrepresent the product.

## Defect → prompt fix

| Defect seen | Prompt fix (change one thing) |
| --- | --- |
| Product shape/proportion wrong | add `identity lock` wording, attach the clearest reference as `Image 1`, switch to `identity-preserve` |
| Product re-designed during an edit | add `change only X; keep the product, its label, hardware and proportions unchanged` |
| Background crept in / wrong backdrop | move the backdrop clause into `Scene/backdrop:` explicitly, add `identical background across the batch` |
| Text misspelled | quote it verbatim, spell letter-by-letter, or plan a typeset overlay in post |
| Text reflowed or spacing off | add `preserve layout, baseline and spacing; change only the characters` |
| Over-smoothed / plastic | add `natural skin texture with visible pores, unretouched, no beauty retouching` |
| Harsh highlights / flat light | name the modifier: `large softbox key slightly camera-left, soft fill, gentle contact shadow` |
| Looks pasted (composite) | add `match perspective, scale, shadow direction and colour temperature of the scene` |
| Extra props or people | tighten `Avoid` (`no extra products, no hands, no props`), and stop implying them in the subject line |
| Cropped product | add `whole product inside frame with even padding, nothing cut off` + check the aspect matches the reference |
| Warped geometry / duplicated parts | add `correct single-point perspective, straight edges, symmetrical hardware` |
| Grainy/low detail at delivery size | regenerate at native max, then `igp.py upscale --to-px`, then one unsharp pass |
| Set looks mismatched | verify the brand lock was identical for all rows; regenerate the odd one out in the next round |
| Food looks dry / unappetizing | add `glossy highlights, fresh garnish, visible crumb or condensation` - do not just say "appetizing" |
| Dish/drink looks plastic or fake | add `real food texture, natural imperfections, no plastic-looking surfaces` |
| Invented label claims or badges | list the allowed wording verbatim in `Text (verbatim)` and add `no other badges, seals, nutrition or health claims` |
| Steam on a cold drink / ice in a hot dish | state the serving temperature explicitly in the constraints |

**One change per retry.** Two changes at once and you learn nothing about which one worked.

## Escalation rules

Ask the user (with a proposed default) when:

- the row's intent cannot be satisfied by any prompt (missing reference, contradictory description);
- the same defect survives two different prompt strategies;
- the row implies a brand/trademark/text the image cannot legally or safely carry;
- the request needs more than 10 images and the priority order is unclear;
- the sheet references a file that was never uploaded.

Never silently substitute a different product, colour, or text. Never mark a row delivered when it
is not.

## What to record

Per round, in `review/`:

- `contact-sheet.jpg` - the visual index (one file, cheap to review).
- `verify-report.md` - coverage, pixels, file sizes, flags (`igp.py verify`).
- `<round-id>-manifest.csv` - per-image metadata including the prompt that produced it.
- `<round-id>-delivery.zip` - finals + manifest + plan (`igp.py deliver`).

The manifest is the audit trail. When someone asks "where did this image come from?", the answer
is in the row's prompt, the reference, and the round id.
