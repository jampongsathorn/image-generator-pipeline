# Batching: making 10-image rounds work

The round is the atomic unit of Arena batch image work. Everything below exists to make sure a
round finishes complete: 10 requested images → 10 usable deliverables, reviewed, delivered,
and the workspace back under budget.

## Contents
- [Round anatomy](#round-anatomy)
- [Sizing a round](#sizing-a-round)
- [Ordering within a round](#ordering-within-a-round)
- [Retry budget](#retry-budget)
- [The generate phase](#the-generate-phase)
- [Naming and paths](#naming-and-paths)
- [More than 10 images](#more-than-10-images)
- [Per-round report to the user](#per-round-report-to-the-user)
- [Failure modes](#failure-modes)

## Round anatomy

| Phase | What happens | Cost |
| --- | --- | --- |
| INTAKE | sheet + refs land in `inbox/<batch>/` | free |
| PLAN | `igp.py intake` → `rounds/<id>/plan.{json,md}` | free |
| PRE-FLIGHT | read `plan.md`, fix prompts, settle questions | free |
| GENERATE | ≤10 image calls → `raw/` | **10 slots** |
| OPTIMIZE | compress/resize/upscale → `out/`, delete `raw/` | free, protects budget |
| REVIEW | `igp.py sheet` → one contact sheet | free, saves context |
| VERIFY | `igp.py verify` → coverage/spec report | free |
| DELIVER | `igp.py deliver` → zip + manifest | free |

Only GENERATE is scarce. Everything else is cheap - which is why the pre-flight review is
non-negotiable, and why "just try it again" is the expensive mistake.

## Sizing a round

- Hard cap: **10 generated images per round.** Never exceed it, even if the tool allows a
  message with more calls; the limit is per round and overruns are lost.
- Practical cap: **8 new images + 2 retries** when the sheet is risky (new product, new use case,
  unfamiliar references). Retries compete with new work for the same slots.
- First contact with a new use case or new brand: plan **1-2 probe images** first, review, then
  spend the remaining slots with the confirmed prompt pattern. This is the cheapest way to
  avoid burning a full round on a broken prompt pattern.
- Same product, many angles: keep them in one round. Splitting across rounds loses the
  set-consistency benefit of identical lock + identical reference.

## Ordering within a round

Sort by priority before slicing into rounds (`priority` column: `high` / `medium` / `low`):

1. `high` rows first - if the round is interrupted, the important images exist.
2. Group by use case, so the same reference and lock are fresh in context and the operator
   state is constant.
3. Keep one product's images adjacent, never interleaved with another product's.
4. Batch-fill: if a high-priority row needs 3 images, keep all 3 in the same round.

## Retry budget

| Situation | Action |
| --- | --- |
| Minor deviation, still usable at delivery size | accept, note it in the manifest |
| One clear defect, obvious fix | spend one retry slot with exactly one prompt change |
| Same defect twice | change strategy (different use case, different reference, typeset text) - do not re-roll |
| Subject fundamentally wrong | stop, ask the user; the row is probably under-specified |
| Priority `low` and the round is full | defer to the next round, say so explicitly |

Never quietly drop a row: every planned item ends the round either delivered, deferred (named),
or escalated with a question.

## The generate phase

- Issue the calls for one round **in a single message** (parallel calls), one call per image.
  Parallel calls belong to the same round - count them together.
- Pass the reference images listed in the row's `Input images:` line, in that order. Order matters:
  it is what the prompt's `Image 1 / Image 2` refers to.
- Save straight into the round's `raw/` folder using the `raw_file` path from `plan.json`.
  Exact filenames = zero friction later in `optimize` and `verify`.
- Do not re-describe the prompt from memory - paste the prompt from `plan.md`.
- Do not start a second round in the same message; finish GENERATE → OPTIMIZE → REVIEW first.

## Naming and paths

```
rounds/<round-id>/
  requests.csv          the sheet as received (source of truth for intent)
  plan.json             machine plan: prompts, filenames, aspects, lint
  plan.md               human plan: reviewable prompts
  refs/                 reference images copied in at intake
  raw/                  generator output, transient - emptied every round
  out/                  delivery masters (the actual deliverable)
  review/               contact-sheet.jpg, verify-report.md, <id>-manifest.csv, <id>-delivery.zip
```

Filenames come from `stem = <id>__<item-name-slug>`, e.g.
`sku-1001__classic-leather-tote.jpg`. Keep them. Renaming breaks the plan→raw→out linkage that
`optimize`, `verify` and `deliver` rely on.

Version rule: a retry that replaces an accepted image becomes a **new file** with a version
suffix (`...-v2.jpg`) plus a line in `plan.json`/manifest noting the version. The team compares,
nobody loses the earlier attempt.

## More than 10 images

```
20 rows -> 2 rounds
  i1..10  -> rounds/<date>-r01  (generate 10, optimize, verify, deliver)
  i11..20 -> rounds/<date>-r02  (repeat)
```

`igp.py plan` slices automatically by `--round-size` (default 10, never raise it) and writes one
`plan.md` per round. Rules:

- Finish a round end-to-end before generating the next one; the session workspace is shared.
- After each round: `optimize --delete-source` then `budget`. If budget says WARNING or worse,
  run `prune --scratch` before continuing.
- If the batch is large, tell the user the round count up front: "40 images → 4 rounds".

## Per-round report to the user

Keep it to a few lines plus the contact sheet:

```
Round <id> - 10/10 generated, 9 accepted, 1 retry used
  accepted : sku-1001, sku-1002, ... (see review/contact-sheet.jpg)
  retried  : sku-1007 (background too dark → relit, v2 accepted)
  escalated: sku-1009 - the sheet says "premium finish" without a reference; which finish?
  deferred : sku-1012 (priority low, next round)
  delivered: review/<id>-delivery.zip (10 files, 3.4MB)
  budget   : 12.4MB / 128MB, 84 files / 10,000
```

Then list the open questions - one line each, with a default you will use if nobody answers.

## Failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Round died halfway | slots spent on retries | pre-flight review; keep 2 slots free on risky rounds |
| Inconsistent set | prompts edited per image, or batch split across rounds | lock the style block, regenerate as one round |
| Files missing from the delivery | wrong filenames in `raw/` | use `plan.json` paths verbatim, then `igp.py verify` |
| "Workspace over budget, N files not saved" | raw files kept, many previews, no pruning | `optimize --delete-source` + `sheet` + `prune` every round |
| Same defect every round | under-specified row | escalate with a specific question, do not re-roll |
