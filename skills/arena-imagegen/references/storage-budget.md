# Session workspace budget: 128 MB / 10,000 files

Arena counts **every file the session creates**. Cross the limit and the excess is silently not
saved - which is how a finished round disappears. Plan the budget like a physical constraint,
because it is one.

## Contents
- [The arithmetic](#the-arithmetic)
- [Where the bytes actually go](#where-the-bytes-actually-go)
- [Non-negotiable habits](#non-negotiable-habits)
- [Budget playbook by batch size](#budget-playbook-by-batch-size)
- [Warning signs](#warning-signs)
- [Recovery when already over](#recovery-when-already-over)

## The arithmetic

| Item | Typical size | Notes |
| --- | --- | --- |
| Generator output (raw PNG, 1024-2048px) | 1.5-6 MB | full-colour PNG is the worst offender |
| → optimized JPEG 2048px q92 | 250-450 KB | ~93% smaller than the raw, no visible loss |
| → optimized PNG cutout 2048px | 1.5-2.5 MB | use `--png-colors 256` where flat → often <1 MB |
| Contact sheet per round | 80-150 KB | one file replaces 10 full-size previews |
| Delivery zip per round | ≈ sum of finals | keep old zips only if the team still needs them |

Budget math for a full session (assume **10 images per round**, JPEG delivery):

```
10 finals x 350KB              = 3.5MB  per round
+ contact sheet                = 0.15MB
+ plan/sheet/manifest          = ~0.05MB
=> ~3.7MB per round delivered
128MB / 3.7MB                  ~= 34 rounds if raws are deleted every round
128MB / 3.7MB - raws kept(40MB) ~= 20 rounds if raws are kept
```

So: **raws kept = half your capacity gone.** Deleting them is the single highest-value habit.
File count is rarely the binding limit (a round costs ~15 files; 10,000 files ≈ 650 rounds), but
stray temp files, per-image working copies and previews add up if you let them.

## Where the bytes actually go

| Source | Share of budget when uncontrolled |
| --- | --- |
| Raw generator output left in place | 50-70% |
| Full-size previews opened for review | 10-20% |
| Unquantized PNG cutouts | 10-25% |
| Old delivery zips never pruned | 5-15% |
| Duplicate "just in case" copies | 5% |

## Non-negotiable habits

1. **`optimize --delete-source` every round.** Raws are transient by design.
2. **One contact sheet per round**, not N inline previews.
3. **`igp.py budget` before each new round** - it is a 100ms command that prevents a lost round.
4. **One master per image** in `out/`. No `final-final-v2` copies; versions use the `-v2` suffix on
   the item id, and superseded files are pruned.
5. **Quantize flat-art PNGs** (`--png-colors 256`) - cutouts, logos, UI screens lose nothing visible.
6. **Archive by round, not by image.** A round is one zip (`igp.py deliver`); prune the round folder
   afterwards if it is already delivered and acknowledged.
7. **Never commit raw/ to git** - it is in `.gitignore`, keep it that way.

## Budget playbook by batch size

| Batch | Rounds | Session budget used (raws deleted) | Extra action |
| --- | --- | --- | --- |
| ≤10 | 1 | ~4 MB | none |
| 20-40 | 2-4 | 8-15 MB | prune between rounds |
| 50-100 | 5-10 | 20-37 MB | `deliver` each round, archive after acknowledgement |
| 200+ | 20+ | >75 MB | deliver + archive + delete per round; consider splitting across sessions |

If a batch cannot fit one session, say so up front and split it: rounds are self-contained, so a
second session can continue from `rounds/<id>/requests.csv` and `plan.json` without redoing prompts.

## Warning signs

- `igp.py budget` reports WARNING (>70%) or CRITICAL (>90%).
- More than ~2 rounds' worth of files in `raw/` - someone skipped optimize.
- `sheet` output larger than 300KB - too many images or thumbnails too big (`--thumb 380`).
- Multiple files per item in `out/` - versioning without pruning.
- The platform message "N files were not saved" - the budget was already exceeded; recover below.

## Recovery when already over

```bash
python3 tools/igp.py budget                 # see what is heavy
python3 tools/igp.py prune --scratch        # drop raw/ + work/ everywhere
python3 tools/igp.py prune --round rounds/<id> --scratch
python3 tools/igp.py prune --archive-older-than 7    # zip + remove delivered old rounds
```

Then re-verify the affected rounds (`verify`) so the team knows exactly which images survived, and
report the loss honestly: which rows need regeneration, and how many slots that costs.
