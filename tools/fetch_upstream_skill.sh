#!/usr/bin/env bash
# Vendor the upstream OpenAI imagegen skill into /tmp for comparison.
#
# PURPOSE: prompt-craft reference only.
# This repo generates images with Arena's built-in image tool.
# Do NOT use the upstream CLI fallback (scripts/image_gen.py) - it requires OPENAI_API_KEY.
#
#   bash tools/fetch_upstream_skill.sh [target-dir]
set -euo pipefail

TARGET="${1:-/tmp/upstream-imagegen}"

if command -v npx >/dev/null 2>&1; then
  echo "==> trying: npx skills add openai/skills@imagegen"
  if npx --yes skills add openai/skills@imagegen --dir "$TARGET" 2>/dev/null; then
    echo "==> vendored via skills CLI into $TARGET"
    find "$TARGET" -maxdepth 3 -name 'SKILL.md' -o -maxdepth 3 -name 'prompting.md' | sed 's/^/    /'
    exit 0
  fi
  echo "    (skills CLI path failed, falling back to git)"
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "==> cloning openai/skills (deprecated but still the imagegen source)"
git clone --depth 1 --quiet https://github.com/openai/skills "$WORK/skills"
mkdir -p "$TARGET"
cp -r "$WORK/skills/skills/.system/imagegen/SKILL.md" "$TARGET/"
cp -r "$WORK/skills/skills/.system/imagegen/references" "$TARGET/"
cp -r "$WORK/skills/skills/.system/imagegen/LICENSE.txt" "$TARGET/"
echo "==> vendored into $TARGET"

echo "==> successor repo (openai/plugins) also has imagegen material:"
echo "    git clone --depth 1 https://github.com/openai/plugins /tmp/openai-plugins"

cat <<'NOTE'

Next steps:
  1. diff the upstream prompting guidance against ours:
       diff -u tools/../skills/arena-imagegen/references/prompting.md <TARGET>/references/prompting.md
       (ours is adapted for Arena rounds + workspace budget - port only what is genuinely better)
  2. never copy references/cli.md, references/image-api.md, references/codex-network.md or
     scripts/image_gen.py into this repo: they require OPENAI_API_KEY and are out of scope.
NOTE
