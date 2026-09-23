# Setup notes

How this pipeline is wired, what it depends on, and how to refresh it later.
For daily operation see `docs/DAILY-FLOW.md`; for agent rules see `AGENTS.md`.

## What this setup is

A batch image pipeline for Arena Agent Mode. Data entry supplies a request sheet + reference images;
the agent plans prompts, generates in rounds of ≤10, optimizes, verifies and hands back one delivery
bundle per round - while staying inside the session workspace budget of **128 MB / 10,000 files**.

Nothing here calls an external image API. Generation happens with Arena's built-in image tool.

## Components

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | rules an agent auto-reads in this repo (read-first list, hard rules, commands) |
| `skills/arena-imagegen/SKILL.md` | the skill entry point (round loop, prompt schema, non-negotiables) |
| `skills/arena-imagegen/references/` | prompting, batching, QA, detail fidelity, storage budget, use cases |
| `tools/igp.py` | the toolkit, one file, stdlib-only Python |
| `templates/recipes.json` | 16 use-case prompt templates + defaults |
| `templates/brand.json` | the style lock (`look` everywhere, `studio` for studio use cases) |
| `templates/requests.csv` | request-sheet header + one EXAMPLE row (columns: 14) |

## Environment requirements

| Requirement | Why | Check |
| --- | --- | --- |
| Python 3.9+ | runs `tools/igp.py` | `python3 -V` |
| ImageMagick (`convert`/`magick`) **or** Pillow | resizing, compressing, contact sheets | `convert -version` or `python3 -c "import PIL"` |
| A usable font file | montage labels the contact sheet | auto-detected from `/usr/share/fonts/...` (DejaVu ships on most images) |

Sizing helper, if only Python is available:

```bash
pip install --break-system-packages Pillow   # Debian/Ubuntu may need the --break-system-packages flag
python3 tools/igp.py --engine pillow sheet --round rounds/<id>
```

ImageMagick is preferred when both are present. `igp.py` reports which engine it picked in
`optimize` output, and `--engine {auto,imagemagick,pillow}` forces the choice.

## Refreshing the upstream prompt-craft reference

The pipeline's prompting guidance is adapted from OpenAI's `imagegen` skill (Apache-2.0, see
`skills/arena-imagegen/NOTICE.md`). To compare against the current upstream text:

```bash
# option 1: the skills CLI
npx skills add openai/skills@imagegen --dir /tmp/upstream-skills

# option 2: plain git (skills repo is deprecated, plugins repo is the successor)
git clone --depth 1 https://github.com/openai/skills /tmp/openai-skills
ls /tmp/openai-skills/skills/.system/imagegen/references/
git clone --depth 1 https://github.com/openai/plugins /tmp/openai-plugins   # successor repo

# option 3: the helper script in this repo
bash tools/fetch_upstream_skill.sh
```

Then diff `references/prompting.md` against `skills/arena-imagegen/references/prompting.md` and port
anything genuinely new. **Do not port the CLI/API sections** - they require `OPENAI_API_KEY` and
must not be used here.

## Verification checklist

```bash
python3 -m py_compile tools/igp.py                  # syntax
python3 tools/igp.py --help | head -30              # CLI wired up
python3 tools/igp.py plan --requests templates/requests.example.csv \
        --round-id 2026-01-01-r01 --allow-warnings  # prompt generation + QA lint
python3 tools/igp.py budget                         # workspace guard works
python3 tools/igp.py sheet --round rounds/<id>      # labels render (font present)
```

A clean smoke test of the whole loop, without spending generation slots, uses synthesized inputs:

```bash
mkdir -p /tmp/igp-smoke && cd /tmp/igp-smoke
convert -size 1024x1024 plasma:fractal raw.png         # stand-in for a generated image
python3 /home/user/image-generator-pipeline/tools/igp.py optimize \
        --in-dir . --out-dir out --format jpeg --max-dim 2048
```

## Design decisions worth knowing

| Decision | Why |
| --- | --- |
| Request sheet is the contract | data entry states intent once; the agent never invents product facts |
| Prompts are generated, not hand-written | reproducible, reviewable, one place to fix a class of problems |
| Style lock lives in `brand.json` | the only reliable way to make 10 separate generations look like one shoot |
| Rounds of 10, finished end-to-end | matches the generation limit and stops `raw/` from eating the workspace |
| Raws deleted every round | halves workspace usage; the optimized file is the master |
| One contact sheet per round | reviewing 10 images costs one file, not ten previews |
| Delivery = zip + manifest | the prompt that produced each image stays attached for auditing |
| No OpenAI API anywhere | requirement of the environment; the built-in tool is the only generator |
