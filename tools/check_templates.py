#!/usr/bin/env python3
"""Validate templates/ and a generated plan without spending a generation slot.

Used by tools/smoke_test.sh. Run standalone after editing recipes.json or brand.json:

    python3 tools/check_templates.py
    python3 tools/check_templates.py --plan rounds/<round-id>/plan.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# the 16 slugs shared with openai/skills imagegen - these must never disappear
UPSTREAM_SLUGS = {
    "product-mockup", "photorealistic-natural", "identity-preserve", "precise-object-edit",
    "background-extraction", "compositing", "lighting-weather", "style-transfer", "sketch-to-render",
    "text-localization", "infographic-diagram", "logo-brand", "ui-mockup", "stylized-concept",
    "illustration-story", "historical-scene",
}
PROMPT_LINE_LABELS = (
    "Use case", "Asset type", "Primary request", "Input images", "Scene/backdrop", "Subject",
    "Style/medium", "Composition/framing", "Lighting/mood", "Mood", "Color palette",
    "Materials/textures", "Text (verbatim)", "Constraints", "Avoid", "Extra direction",
)
REQUIRED_SHEET_COLUMNS = {"id", "item_name", "use_case", "description"}
PLACEHOLDERS = {
    "id", "item", "description", "asset_type", "refs", "scene", "subject", "style", "framing",
    "lighting", "mood", "palette", "materials", "text", "constraints", "avoid", "aspect", "extra",
    "brand",
}

failures: list[str] = []


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{(' - ' + detail) if detail else ''}")
        failures.append(label)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=None, help="optional plan.json to validate too")
    ap.add_argument("--sheet", default=str(REPO / "templates" / "requests.csv"))
    args = ap.parse_args()

    print("templates/recipes.json")
    recipes = json.loads((REPO / "templates" / "recipes.json").read_text(encoding="utf-8"))
    slugs = {k for k in recipes if not k.startswith("_")}
    check("all 16 upstream use-case slugs present", UPSTREAM_SLUGS <= slugs,
          f"missing {sorted(UPSTREAM_SLUGS - slugs)}")
    check(f"{len(slugs)} use cases defined", len(slugs) >= 16)
    for slug in sorted(slugs):
        recipe = recipes[slug]
        check(f"{slug}: template + defaults + aspect + format",
              bool(recipe.get("template")) and recipe.get("defaults") is not None
              and bool(recipe.get("aspect_default")) and bool(recipe.get("format_default")))
        unknown = set()
        for line in recipe["template"]:
            for key in [k for k in PLACEHOLDERS if "{" + k + "}" in line]:
                unknown.discard(key)
            for token in line.split("{")[1:]:
                field = token.split("}")[0] if "}" in token else ""
                if field and field not in PLACEHOLDERS:
                    unknown.add(field)
        check(f"{slug}: no unknown placeholders", not unknown, ", ".join(sorted(unknown)))
        check(f"{slug}: has a Constraints line", any(l.startswith("Constraints:") for l in recipe["template"]))
        check(f"{slug}: has an Avoid line", any(l.startswith("Avoid:") for l in recipe["template"]))

    print("templates/brand.json")
    brand = json.loads((REPO / "templates" / "brand.json").read_text(encoding="utf-8"))
    if "style_lock" in brand:  # v1 schema
        check("style_lock present", bool(brand["style_lock"]))
    else:
        check("look present (applies to every use case)", bool(brand.get("look")))
        check("studio present", bool(brand.get("studio")))
        check("studio_use_cases reference real slugs",
              set(brand.get("studio_use_cases", [])) <= slugs,
              str(sorted(set(brand.get("studio_use_cases", [])) - slugs)))
    check("global_constraints / global_avoid are lists",
          isinstance(brand.get("global_constraints"), list) and isinstance(brand.get("global_avoid"), list))
    check("output_defaults present", isinstance(brand.get("output_defaults"), dict))

    print(f"request sheet template ({Path(args.sheet).name})")
    header = next(csv.reader(open(args.sheet, encoding="utf-8-sig", newline="")))
    check("required columns present", REQUIRED_SHEET_COLUMNS <= set(header),
          str(sorted(REQUIRED_SHEET_COLUMNS - set(header))))
    print(f"       columns: {', '.join(header)}")

    if args.plan:
        print(f"plan ({args.plan})")
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        check("plan has items", bool(plan.get("items")))
        check("plan respects the 10-images-per-round cap", len(plan.get("items", [])) <= plan.get("round_size", 10),
              f"{len(plan.get('items', []))} items")
        for item in plan["items"]:
            check(f"{item['id']}: prompt has Constraints + Avoid",
                  "Constraints:" in item["prompt"] and "Avoid:" in item["prompt"])
            bad = [line.split(":")[0] for line in item["prompt"].splitlines()
                   if line.split(":")[0].strip() not in PROMPT_LINE_LABELS]
            check(f"{item['id']}: only labelled prompt lines", not bad, ", ".join(bad[:3]))
            check(f"{item['id']}: filename matches the id", item["id"].split("-v")[0].lower().replace("_", "-") in item["stem"],
                  item["stem"])

    print()
    if failures:
        print(f"{len(failures)} check(s) failed")
        return 1
    print("all template checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
