# Menu-audit intake (screenshots with tick / cross marks)

Real-world input from the data-entry team is often **not** a clean sheet: they photograph the
restaurant's ordering-app menu (Grab, LINE MAN, Wongnai, the shop's own app) and mark each dish.

Two marks, two meanings - confirm this with the team once, then keep using it:

| Mark | Meaning | What the agent does |
| --- | --- | --- |
| green tick ✅ | the photo is good, keep it | leave it alone - do **not** spend generate budget on it |
| red cross ❌ | the photo must be replaced | candidate for a round; needs a real reference photo from the kitchen |

**Read the mark, never the pixel.** Screenshots arrive at phone resolution and the mark is often
drawn on by hand, so an agent cannot reliably detect it. Transcribe the marked list into a CSV in
the same turn the screenshots arrive, show it back to the team, and let them correct it. That CSV -
not the screenshot - is the source of truth for the round.

## Step 1 - build two CSVs, not one

```
inbox/<batch-name>/
  inventory.csv   every item seen on the menu, with its mark   <- the audit record
  requests.csv    only the rows for the next round (<= 10)      <- the pipeline input
```

`igp.py intake` picks the sheet named `requests.csv` when a folder holds several sheets, so keep
that filename for whatever should be generated next.

`inventory.csv` columns: `id, category, item_name, price_thb, mark, description_seen, confirm_with_kitchen`

- `mark` is `good` / `redo` / `redo_na` (marked for redo but listed as unavailable, so out of scope).
- `confirm_with_kitchen` holds the parts of the description the screenshot cut off. Fill it, don't
  guess - inventing an ingredient on a real menu is a factual error the team has to catch.

Then build `requests.csv` (14-column pipeline sheet) from the `redo` rows only, highest-value first
(signature dishes, promo prices, "most ordered", cheapest high-volume items, worst current photos).

## Step 2 - descriptions become prompts, not claims

On a menu screenshot the app text is the **only** record of what the dish is: photo + Thai/English
name + price + description. Use it verbatim-ish for `description`, keep any `[Vegan]`-style tags in
`must_keep`, and never add an ingredient that was not written down.

## Step 3 - reference photos are the thing to ask for

A menu screenshot contains the **old photo plus a text list**. That old photo is exactly what the
team marked as wrong - do not hand it to the generator as a reference and expect something different.
For `food-hero` / `packaging-shot` / `flat-lay` the reference is used as inspiration only, so a fresh
photo of the dish as the kitchen actually serves it is what improves the result:

- ask for the new/replacement photo per item, renamed to the request `id` (e.g. `F4T-013.jpg`);
- if the team only sends screenshots, generate from the description and label the round
  "no reference photo yet" so nobody assumes the plating is verified;
- keep the labelled reference rule from `references/quality-control.md`.

## Step 4 - record the outcome

After the round, the `good`/`redo` columns in `inventory.csv` are the team's progress report:
`igp.py status` for the session, and the table of counts (keep / redo / unavailable / rounds left)
for the team chat. Update the marks when the restaurant swaps a photo out on the app.
