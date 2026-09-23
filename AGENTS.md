# Agent instructions - image-generator-pipeline

This repo is a **batch image production pipeline**. Data entry drops a request sheet plus reference
photos; the agent turns them into finished images and hands back one delivery bundle per round.

## Read this first

Before any image-related work in this repo, read:

1. `skills/arena-imagegen/SKILL.md` - the operating procedure (mandatory).
2. `skills/arena-imagegen/references/batches.md` - if more than 10 images are involved.
3. `skills/arena-imagegen/references/prompting.md` - before writing or editing a prompt.
4. `skills/arena-imagegen/references/detail-fidelity.md` - before resizing or upscaling anything.
5. `skills/arena-imagegen/references/storage-budget.md` - before a large batch or when budget warns.

## Hard rules

1. **Images are generated with Arena's built-in image tool only.** Never use the OpenAI API for
   image generation. Never ask for, or use, `OPENAI_API_KEY`. The vendored upstream skill's CLI
   sections exist for reference only (`skills/arena-imagegen/NOTICE.md`).
2. **Maximum 10 generated images per round.** Parallel calls in one message share the same round.
   Count before sending. Retries spend slots from the same budget.
3. **Plan before generating.** Prompts come from `templates/recipes.json` + `templates/brand.json`
   via `tools/igp.py plan` / `intake`. Review `plan.md` before spending a round.
4. **Keep the session workspace under 128 MB / 10,000 files.** Run the round loop's optimize step
   with `--delete-source`, use one contact sheet per round for review, and check
   `python3 tools/igp.py budget` before each round.
5. **Never lose details.** Generate at the largest native size, downscale rather than upscale,
   upscale only via `igp.py upscale`/`--upscale-to-spec`, and never re-encode a delivered JPEG.
6. **Never overwrite a delivered final.** New attempt → new version suffix + manifest note.
7. **Filenames come from `plan.json`.** Do not rename; `optimize`, `verify` and `deliver` depend on
   the plan → raw → out linkage.

## Session start (do this first)

```bash
python3 tools/igp.py doctor          # python, image engine, font, templates
python3 tools/check_templates.py     # recipe/brand/plan sanity
```

If `doctor` reports NOT ready and no image engine exists, install one:
`pip install --break-system-packages Pillow` (works without root), or `apt-get install -y imagemagick`.
Do not start a round without an image engine: optimize/sheet/verify all need it.

## Command reference

```bash
# intake a drop folder from data entry (sheet + refs) and build the plan
python3 tools/igp.py intake --name <batch> --round-id <YYYY-MM-DD-rNN> --clean

# or plan from an explicit sheet
python3 tools/igp.py plan --requests <sheet.csv> --round-id <YYYY-MM-DD-rNN> [--allow-warnings]

# ... generate <=10 images into rounds/<id>/raw/ (the round) ...

# finish the round
python3 tools/igp.py optimize --round rounds/<id> --delete-source --upscale-to-spec
python3 tools/igp.py sheet    --round rounds/<id>          # ONE contact sheet to review
python3 tools/igp.py verify   --round rounds/<id>          # coverage + spec + budget report
python3 tools/igp.py deliver  --round rounds/<id>          # zip + manifest for the team
python3 tools/igp.py budget                                # workspace usage before the next round

# maintenance
python3 tools/igp.py status
python3 tools/igp.py prune --scratch [--archive-older-than DAYS]
python3 tools/igp.py upscale <file|dir> --to-px 2048
```

## Repo layout

```
AGENTS.md                 rules for agents working here
README.md                 team-facing overview + quickstart
templates/                recipes.json (use-case prompts), brand.json (style lock), request sheet template
tools/igp.py              the whole toolkit (plan/optimize/upscale/sheet/verify/intake/deliver/budget)
skills/arena-imagegen/    the skill: SKILL.md + references/ + NOTICE.md
rounds/<id>/              one round: requests.csv, plan.*, refs/, raw/, out/, review/
inbox/<batch>/            where data entry drops a sheet + references
archive/                  zipped delivered rounds (kept out of the working tree)
docs/DAILY-FLOW.md        the human procedure (TH/EN)
docs/TEAM-ONBOARDING.md   how teammates connect a session and follow this skill (TH/EN)
docs/QUICKSTART-TH.md     Thai quickstart one-pager
docs/SETUP.md             how this was set up and how to refresh it
```

## What to report back each round

- Round id, images generated, accepted / retried / deferred counts.
- Path to the contact sheet and the delivery zip.
- Open questions, each with the default you will use if nobody replies.
- Current workspace budget (`igp.py budget`).

## Style of work

- Batch, not one-off: think in rows and rounds, never in single images.
- Ask when a row is ambiguous; do not invent product details, brand text or claims.
- Prefer regenerating a wrong image over patching it in post; prefer planning over regenerating.
