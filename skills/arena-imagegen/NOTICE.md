# Attribution and third-party notices

## Adapted material

`references/prompting.md` is adapted from the `imagegen` skill in the
[`openai/skills`](https://github.com/openai/skills) repository (path `skills/.system/imagegen`,
`references/prompting.md` and `SKILL.md`), licensed under the **Apache License 2.0**.
Copyright OpenAI. The adaptation restructures the guidance for Arena batch work (rounds of 10,
workspace budget, request sheets) and rewrites the sections that describe Codex/OpenAI-API-specific
execution so they do not apply here.

The use-case slug taxonomy (`product-mockup`, `photorealistic-natural`, `identity-preserve`,
`precise-object-edit`, `background-extraction`, `lighting-weather`, `style-transfer`, `compositing`,
`sketch-to-render`, `text-localization`, `logo-brand`, `ui-mockup`, `infographic-diagram`,
`illustration-story`, `stylized-concept`, `historical-scene`) is reused from the same source so
prompts remain portable between tools.

## What is deliberately NOT used

The upstream skill documents a fallback CLI (`scripts/image_gen.py`) that calls the OpenAI Images
API with an `OPENAI_API_KEY`. **This repository does not use it, does not vendor it, and must not
use it.** All images in this pipeline are produced by Arena's built-in image generation tool.

The upstream `scripts/image_gen.py`, `references/cli.md`, `references/image-api.md` and
`references/codex-network.md` files are therefore not copied here - only the prompt-craft material
that is tool-agnostic.

## Source status

- `openai/skills` is marked deprecated upstream; the successor is
  [`openai/plugins`](https://github.com/openai/plugins) (see `plugins/creative-production`,
  `plugins/game-studio/skills/sprite-pipeline`).
- `npx skills add openai/skills@imagegen` remains useful for pulling the upstream `imagegen` skill
  into a scratch directory to compare prompt practices. See `docs/SETUP.md` for the refresh script.

## License of this repository

Repository code (`tools/igp.py`) and the pipeline documentation are part of this project. The
adapted prompt-craft sections remain under Apache-2.0 terms as above; keep this notice with any
copy of `references/prompting.md`.
