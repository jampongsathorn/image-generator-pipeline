#!/usr/bin/env bash
# Environment + pipeline self-check. Uses synthetic images and a throwaway round id,
# so it works in a fresh Arena session and never spends a generation slot.
#
#   bash tools/smoke_test.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
IGP=(python3 tools/igp.py)
ROUND="smoke-test-round"
PASS=0
FAIL=0

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
check() { # check <description> <command...>
  local desc="$1"; shift
  if "$@" >/tmp/igp-smoke.out 2>&1; then
    printf '  \033[32mPASS\033[0m %s\n' "$desc"; PASS=$((PASS + 1))
  else
    printf '  \033[31mFAIL\033[0m %s\n' "$desc"; sed 's/^/       /' /tmp/igp-smoke.out | tail -8; FAIL=$((FAIL + 1))
  fi
}

step "Environment"
check "python3 available"        python3 -V
check "doctor reports readiness"  "${IGP[@]}" doctor
check "tools/igp.py compiles"    python3 -m py_compile tools/igp.py
if command -v magick >/dev/null || command -v convert >/dev/null; then
  echo "  INFO image engine: $(command -v magick || command -v convert)"
elif python3 -c 'import PIL' 2>/dev/null; then
  echo "  INFO image engine: Pillow (pip) - install imagemagick for faster montage/contact sheets"
else
  echo "  WARN no image engine found: install imagemagick or 'pip install --break-system-packages Pillow'"
  FAIL=$((FAIL + 1))
fi
if ls /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf >/dev/null 2>&1; then
  echo "  INFO contact-sheet labels: font found"
else
  echo "  WARN no TrueType font found - contact sheets will render without labels"
fi

step "Templates"
check "recipes.json is valid JSON"  python3 -c "import json;json.load(open('templates/recipes.json'))"
check "brand.json is valid JSON"    python3 -c "import json;json.load(open('templates/brand.json'))"
check "template + brand validation"  python3 tools/check_templates.py
check "request sheet template has the required columns" python3 -c "
import csv;h=next(csv.reader(open('templates/requests.csv')))
assert {'id','item_name','use_case','description'} <= set(h), h"

step "Plan (no generation spent)"
rm -rf "rounds/$ROUND"
check "plan builds from the example sheet" \
  "${IGP[@]}" plan --requests templates/requests.example.csv --round-id "$ROUND" --allow-warnings
check "plan.json written"    test -f "rounds/$ROUND/plan.json"
check "plan.md written"      test -f "rounds/$ROUND/plan.md"
check "plan content validation" python3 tools/check_templates.py --plan "rounds/$ROUND/plan.json"
check "unknown use_case is reported, not silently ignored" bash -c "
printf 'id,item_name,use_case,description\nX1,Test,not-a-real-slug,made up\n' > /tmp/igp-bad.csv
python3 tools/igp.py plan --requests /tmp/igp-bad.csv --round-id smoke-bad 2>&1 | grep -q 'unknown use_case'"
rm -rf rounds/smoke-bad
check "template EXAMPLE row is skipped by default" bash -c "
python3 tools/igp.py plan --requests templates/requests.csv --round-id smoke-example 2>&1 | grep -q 'example row'"
rm -rf rounds/smoke-example
check "intake prefers requests.csv when the drop folder has several sheets" bash -c "
rm -rf /tmp/igp-intake && mkdir -p /tmp/igp-intake
printf 'id,category,item_name,price_thb,mark\nA1,Salads,Inventory Row,199,redo\n' > /tmp/igp-intake/inventory.csv
printf 'id,item_name,use_case,description\nR1,Requested Row,product-mockup,a dish on a plate\n' > /tmp/igp-intake/requests.csv
python3 tools/igp.py intake --source /tmp/igp-intake --round-id smoke-intake >/dev/null 2>&1
grep -q 'Requested Row' rounds/smoke-intake/requests.csv &&
  ! grep -q 'Inventory Row' rounds/smoke-intake/requests.csv"
rm -rf rounds/smoke-intake /tmp/igp-intake

step "Round mechanics"
if command -v convert >/dev/null; then
  # plan paths are relative to the round folder - synthesize a stand-in for each generation
  for item in $(python3 -c "
import json;d=json.load(open('rounds/$ROUND/plan.json'))
print(' '.join('rounds/$ROUND/' + i['raw_file'] for i in d['items']))"); do
    convert -size 1024x1024 plasma:fractal "$item" 2>/dev/null
  done
  echo "  INFO synthesized $(ls -1 rounds/$ROUND/raw | wc -l) stand-in raw file(s)"
  check "optimize writes finals and deletes raws" \
    "${IGP[@]}" optimize --round "rounds/$ROUND" --delete-source --upscale-to-spec
  check "raw/ is empty after optimize" bash -c "test -z \"\$(ls -A rounds/$ROUND/raw)\""
  check "contact sheet renders" "${IGP[@]}" sheet --round "rounds/$ROUND"
  # plasma noise compresses badly, so raise the size cap: this checks coverage/pixels, not size
  check "verify reports coverage" "${IGP[@]}" verify --round "rounds/$ROUND" --max-kb 60000
  check "verify exits non-zero when an item is flagged" bash -c \
    "! python3 tools/igp.py verify --round rounds/$ROUND --max-kb 10 >/dev/null 2>&1"
  check "deliver builds a zip + manifest" "${IGP[@]}" deliver --round "rounds/$ROUND"
  check "delivery zip exists" bash -c "ls rounds/$ROUND/review/*-delivery.zip >/dev/null"
else
  echo "  SKIP round mechanics (no ImageMagick in this environment)"
fi

step "Budget guard"
check "budget runs"           "${IGP[@]}" budget
check "budget --json emits numbers" bash -c "${IGP[*]} budget --json | tail -1 | python3 -c 'import json,sys;json.loads(sys.stdin.read())'"
check "status lists rounds"   "${IGP[@]}" status
check "prune cleans up"       "${IGP[@]}" prune --round "rounds/$ROUND" --scratch

step "Cleanup"
rm -rf "rounds/$ROUND" /tmp/igp-bad.csv /tmp/igp-smoke.out /tmp/igp-batch.csv
echo "  removed the throwaway round"

printf '\n\033[1m%d passed, %d failed\033[0m\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
