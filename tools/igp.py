#!/usr/bin/env python3
"""
igp - Image Generation Pipeline toolkit  (schema: igp/v1)

Built for Arena Agent Mode batch image work where the hard limits are:
  * 10 generated images per round
  * 128 MB / 10,000 files per session workspace

Subcommands
-----------
  doctor      check this session is ready (python, image engine, font, templates)
  new-round   scaffold a fresh round folder (requests.csv + folders + HOWTO)
  plan        read a request sheet -> build prompts -> split into rounds of <=N images
  optimize    compress/resize raw generations into delivery masters (budget guard)
  upscale     detail-preserving upscale (Lanczos + adaptive unsharp)
  sheet       build ONE contact sheet per round for fast review
  verify      check every request has a valid output (coverage + spec + budget)
  intake      turn a data-entry drop folder (sheet + refs) into a planned round
  deliver     bundle a round's finals into one zip + manifest for the team
  status      per-round overview
  budget      workspace file-count / MB report with warnings
  prune       delete raw/scratch files, optionally archive old rounds to .zip

Run `python3 tools/igp.py <cmd> --help` for options.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
import zipfile
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROUNDS = REPO / "rounds"
INBOX = REPO / "inbox"
ARCHIVE = REPO / "archive"
TEMPLATES = REPO / "templates"

WORKSPACE_LIMIT_MB = 128.0
WORKSPACE_LIMIT_FILES = 10_000
ROUND_SIZE = 10  # hard cap: generated images per Arena round

# rough bytes-per-image used for budget projection
EST_KB = {"jpeg": 420, "jpg": 420, "webp": 260, "png": 2200}

REQUIRED_FIELDS = ("id", "item_name", "use_case", "description")
KNOWN_FIELDS = (
    "id", "item_name", "use_case", "description", "ref_images", "aspect",
    "delivery_px", "format", "text_verbatim", "must_keep", "must_avoid",
    "asset_type", "priority", "notes", "scene", "style", "lighting",
    "palette", "materials", "extra", "variants",
)

ASPECT_WORDS = {
    "1:1": "square", "4:5": "vertical portrait", "5:4": "horizontal portrait",
    "3:2": "landscape", "2:3": "portrait", "4:3": "landscape",
    "16:9": "wide landscape", "9:16": "tall vertical", "2:1": "wide banner",
}

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff")

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


def find_font() -> str | None:
    """ImageMagick/Pillow fail without a real font file in a bare sandbox."""
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None
EDIT_USE_CASES = {
    "identity-preserve", "precise-object-edit", "lighting-weather",
    "style-transfer", "compositing", "sketch-to-render", "text-localization",
}
TEXT_USE_CASES = {"text-localization", "infographic-diagram", "logo-brand", "ui-mockup"}


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def die(msg: str, code: int = 2):
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def warn(msg: str):
    print(f"  ! {msg}")


def ok(msg: str):
    print(f"  + {msg}")


def slugify(text: str, maxlen: int = 40) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return (text[:maxlen].rstrip("-")) or "item"


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def today() -> str:
    return date.today().isoformat()


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path}: {exc}")


def strip_json_comments(data: dict) -> dict:
    """Drop the _schema/_notes documentation keys so they never reach a prompt."""
    return {k: v for k, v in data.items() if not k.startswith("_")}


def as_text(value) -> str:
    """Recipe/brand values may be a string or a list of clauses."""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return str(value or "").strip()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9#]+", text.lower()))


def _near_duplicate(clause: str, kept: list[str]) -> bool:
    """True when a clause is already covered by an earlier one.

    Exact match always counts. Fuzzy matching (containment / heavy token overlap) only
    applies to clauses with 3+ tokens, so short atoms like 'ice', 'text' or 'garnish'
    survive next to a longer clause that happens to mention them.
    """
    tokens = _tokens(clause)
    for other in kept:
        if clause == other:
            return True
        other_tokens = _tokens(other)
        if len(tokens) < 3 or len(other_tokens) < 3:
            continue
        if len(clause) >= 12 and (clause in other or other in clause):
            return True
        if len(tokens & other_tokens) / min(len(tokens), len(other_tokens)) >= 0.6:
            return True
    return False


def join_unique(parts) -> str:
    """Join clause lists (constraints / avoid) with near-duplicate collapse.

    The separator is ';' only. Clauses routinely contain commas ('wilted, dry or
    plastic-looking food', 'visible texture (crumb, crust, condensation, ice)'), and
    splitting on those corrupts the meaning. Nothing is truncated either: silently
    dropping a requirement is worse than a slightly long prompt - `lint_prompt`
    reports over-long lists so a human can trim the source instead.
    """
    out: list[str] = []
    for part in parts:
        for clause in as_text(part).split(";"):
            clause = " ".join(clause.split()).strip().strip(".").strip()
            if not clause or _near_duplicate(clause, out):
                continue
            out.append(clause)
    return "; ".join(out)


def split_refs(value: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;|]", value or "") if p.strip()]


def label_refs(refs: list[str], roles: str = "") -> str:
    if not refs:
        return ""
    if roles:
        return f"{'; '.join(f'Image {i + 1}: {name}' for i, name in enumerate(refs))}; roles: {roles}"
    return "; ".join(f"Image {i + 1}: {name}" for i, name in enumerate(refs))


def frame_words(aspect: str) -> str:
    aspect = (aspect or "").strip()
    if not aspect or aspect.lower() in ("same-as-input", "native"):
        return "keep the composition of the reference"
    return f"{ASPECT_WORDS.get(aspect, 'custom')} {aspect} format"


# --------------------------------------------------------------------------- #
# image engine: ImageMagick first, Pillow fallback
# --------------------------------------------------------------------------- #
class Engine:
    def __init__(self, preferred: str = "auto"):
        self.magick = shutil.which("magick")
        self.im6_convert = shutil.which("convert")
        self.im6_identify = shutil.which("identify")
        self.pillow = False
        if preferred in ("auto", "pillow") and not (self.magick or self.im6_convert):
            try:
                import PIL  # noqa: F401
                self.pillow = True
            except ModuleNotFoundError:
                pass
        if preferred == "pillow":
            try:
                import PIL  # noqa: F401
                self.pillow = True
                self.magick = None
                self.im6_convert = None
            except ModuleNotFoundError:
                die("engine 'pillow' requested but Pillow is not installed\n"
                    "    pip install --break-system-packages Pillow")

    @property
    def name(self) -> str:
        if self.pillow:
            return "pillow"
        if self.magick:
            return "imagemagick-7"
        if self.im6_convert:
            return "imagemagick-6"
        return "none"

    def _run(self, args: list[str]) -> None:
        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode != 0:
            die(f"image command failed: {' '.join(args[:3])} ...\n{proc.stderr.strip()}")

    # -- convert ------------------------------------------------------------
    def convert(self, src: Path, dst: Path, *, quality: int, resize: tuple[int, int] | None,
                unsharp: str | None = None, max_kb: int | None = None, fmt: str = "jpeg",
                png_colors: int | None = None) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if self.pillow:
            return self._convert_pillow(src, dst, quality=quality, resize=resize, fmt=fmt,
                                        unsharp=unsharp, max_kb=max_kb, png_colors=png_colors)
        base = [self.magick] if self.magick else [self.im6_convert]
        args = base + [str(src), "-auto-orient", "-strip", "-colorspace", "sRGB"]
        if resize:
            args += ["-filter", "Lanczos", "-resize", f"{resize[0]}x{resize[1]}"]
        if unsharp:
            args += ["-unsharp", unsharp]
        if fmt in ("jpeg", "jpg"):
            args += ["-sampling-factor", "4:4:4", "-interlace", "Plane", "-quality", str(quality)]
            if max_kb:
                args += ["-define", f"jpeg:extent={max_kb}kb"]
        elif fmt == "png":
            args += ["-quality", str(min(quality + 3, 100)), "-define", "png:compression-level=9"]
            if png_colors:
                args += ["-colors", str(png_colors), "-depth", "8"]
        elif fmt == "webp":
            args += ["-define", "webp:method=6", "-quality", str(quality)]
        args.append(str(dst))
        self._run(args)

    def _convert_pillow(self, src: Path, dst: Path, *, quality: int, resize, fmt: str,
                        unsharp: str | None, max_kb: int | None, png_colors: int | None = None) -> None:
        from PIL import Image, ImageFilter  # type: ignore

        with Image.open(src) as im:
            im = im.convert("RGBA" if fmt == "png" else "RGB")
            if resize:
                im = im.resize(resize, Image.LANCZOS)
            if fmt == "png" and png_colors:
                im = im.quantize(colors=png_colors, method=Image.MEDIANCUT).convert("RGBA")
            if unsharp:
                match = re.match(r"0x([\d.]+)", unsharp)
                amount = float(match.group(1)) if match else 0.8
                im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=int(amount * 100), threshold=3))
            if fmt in ("jpeg", "jpg"):
                save_kwargs = {"quality": quality, "subsampling": 0, "optimize": True, "progressive": True}
            elif fmt == "webp":
                save_kwargs = {"quality": quality, "method": 6}
            else:
                save_kwargs = {"optimize": True, "compress_level": 9}
            if max_kb:
                for _ in range(8):
                    im.save(dst, **save_kwargs)
                    if dst.stat().st_size <= max_kb * 1024:
                        break
                    save_kwargs["quality"] = max(60, save_kwargs.get("quality", quality) - 6)
            else:
                im.save(dst, **save_kwargs)

    # -- identify -----------------------------------------------------------
    def identify(self, path: Path) -> tuple[int, int]:
        if self.pillow:
            from PIL import Image  # type: ignore
            with Image.open(path) as im:
                return im.size
        cmd = [self.magick, "identify", "-format", "%w %h"] if self.magick \
            else [self.im6_identify, "-format", "%w %h"]
        proc = subprocess.run(cmd + [str(path)], capture_output=True, text=True)
        if proc.returncode != 0:
            die(f"could not read image: {path}\n{proc.stderr.strip()}")
        w, h = proc.stdout.strip().split()[:2]
        return int(w), int(h)

    # -- contact sheet ------------------------------------------------------
    def sheet(self, files: list[Path], dst: Path, cols: int, thumb: int, label: bool,
              quality: int = 82) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if self.pillow or not (self.magick or self.im6_convert):
            return self._sheet_pillow(files, dst, cols, thumb, label, quality)
        rows = (len(files) + cols - 1) // cols
        # ImageMagick requires -font/-label/-pointsize BEFORE the input files,
        # otherwise the label is silently dropped (and it needs a real font path).
        cmd = [self.magick, "montage"] if self.magick else ["montage"]
        if label:
            font = find_font()
            if font:
                cmd += ["-font", font]
            cmd += ["-pointsize", str(max(14, thumb // 26)), "-label", "%t"]
        cmd += [str(f) for f in files]
        cmd += ["-tile", f"{cols}x{rows}", "-geometry", f"{thumb}x{thumb}+10+10",
                "-background", "#FFFFFF", "-fill", "#222222", "-quality", str(quality), str(dst)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            if label:  # font problems are the usual cause - retry unlabelled
                warn("montage failed, retrying the contact sheet without labels")
                return self.sheet(files, dst, cols, thumb, False, quality)
            die(proc.stderr.strip())

    def _sheet_pillow(self, files, dst, cols, thumb, label, quality):
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
        pad, lab = 10, 26
        cell_h = thumb + (lab if label else 0)
        rows = (len(files) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (thumb + pad) + pad, rows * (cell_h + pad) + pad), "white")
        draw = ImageDraw.Draw(sheet)
        font = None
        if label:
            try:
                path = find_font()
                font = ImageFont.truetype(path, 18) if path else ImageFont.load_default()
            except Exception:  # noqa: BLE001 - any font problem just means no labels
                font = None
        for i, f in enumerate(files):
            with Image.open(f) as im:
                im = im.convert("RGB")
                im.thumbnail((thumb, thumb), Image.LANCZOS)
                x = pad + (i % cols) * (thumb + pad) + (thumb - im.width) // 2
                y = pad + (i // cols) * (cell_h + pad)
                sheet.paste(im, (x, y))
                if label and font:
                    draw.text((x, y + im.height + 6), f.stem[:34], fill=(40, 40, 40), font=font)
        sheet.save(dst, quality=quality, optimize=True)


# --------------------------------------------------------------------------- #
# request sheets
# --------------------------------------------------------------------------- #
def read_requests(path: Path) -> list[dict]:
    if not path.exists():
        die(f"request sheet not found: {path}")
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data["items"] if isinstance(data, dict) else data
        return [{str(k): ("" if v is None else str(v)) for k, v in row.items()} for row in rows]
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return [{(k or "").strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(fh, delimiter=delimiter)]


def validate_rows(rows: list[dict], sheet_dir: Path) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for i, row in enumerate(rows, start=2):
        for field in REQUIRED_FIELDS:
            if not row.get(field):
                problems.append(f"row {i}: missing required field '{field}'")
        rid = row.get("id", "")
        if rid in seen:
            problems.append(f"row {i}: duplicate id '{rid}'")
        seen.add(rid)
        for ref in split_refs(row.get("ref_images", "")):
            if Path(ref).is_absolute():
                exists = Path(ref).exists()
            else:
                exists = (sheet_dir / ref).exists() or (REPO / ref).exists()
            if not exists:
                problems.append(f"row {i} ({rid}): reference image not found -> {ref}")
    return problems


# --------------------------------------------------------------------------- #
# prompt builder
# --------------------------------------------------------------------------- #
def brand_locks(brand: dict, use_case: str) -> dict:
    """Brand values that apply to this use case.

    v2 schema: `look` applies everywhere, `studio` only to `studio_use_cases`.
    v1 schema (`style_lock`) is still accepted and applies everywhere.
    """
    if "style_lock" in brand:
        return brand.get("style_lock") or {}
    lock = dict(brand.get("look") or {})
    if use_case in (brand.get("studio_use_cases") or []):
        lock.update(brand.get("studio") or {})
    return lock


def build_prompt(row: dict, recipe: dict, brand: dict, brand_name: str, use_case: str) -> str:
    lock = brand_locks(brand, use_case)
    defaults = recipe.get("defaults", {}) or {}

    def pick(field: str, fallback: str = "") -> str:
        return (row.get(field) or "").strip() or fallback

    def resolve(field: str, fallback: str = "") -> str:
        """request sheet -> brand lock -> recipe default."""
        return pick(field) or as_text(lock.get(field)) or as_text(defaults.get(field)) or fallback

    refs = split_refs(row.get("ref_images", ""))
    aspect = pick("aspect", recipe.get("aspect_default",
                                       brand.get("output_defaults", {}).get("aspect", "1:1")))
    lock_framing = as_text(lock.get("framing"))
    framing = pick("framing") or "; ".join(p for p in (lock_framing, frame_words(aspect)) if p)
    constraints = join_unique([
        pick("must_keep"),
        as_text(defaults.get("constraints")),
        as_text(brand.get("global_constraints")),
    ])
    avoid = join_unique([
        pick("must_avoid"),
        as_text(defaults.get("avoid")),
        as_text(brand.get("global_avoid")),
    ])
    text_verbatim = pick("text_verbatim")
    values = {
        "id": row.get("id", ""),
        "item": pick("item_name"),
        "description": pick("description", pick("item_name")),
        "asset_type": pick("asset_type", "product asset"),
        "refs": label_refs(refs),
        "scene": resolve("scene"),
        "subject": pick("item_name"),
        "style": resolve("style"),
        "framing": framing,
        "lighting": resolve("lighting"),
        "mood": resolve("mood"),
        "palette": resolve("palette"),
        "materials": resolve("materials"),
        "text": f'"{text_verbatim}"' if text_verbatim else "",
        "constraints": constraints,
        "avoid": avoid,
        "aspect": aspect,
        "extra": pick("extra"),
        "brand": brand_name,
    }
    lines: list[str] = []
    for raw in recipe.get("template", []):
        try:
            line = raw.format(**values)
        except KeyError as exc:
            die(f"unknown placeholder {exc} in recipe template")
        body = line.split(":", 1)[1].strip() if ":" in line else line.strip()
        if not body or body in (";", '""'):
            continue
        lines.append(re.sub(r"\s*;\s*$", "", line.rstrip()).rstrip("; "))
    if values["extra"] and "{extra}" not in "".join(recipe.get("template", [])):
        lines.append(f"Extra direction: {values['extra']}")
    return "\n".join(lines)


def constraints_of(prompt: str) -> str:
    for line in prompt.splitlines():
        if line.startswith("Constraints:"):
            return line.split(":", 1)[1]
    return ""


def avoid_of(prompt: str) -> str:
    for line in prompt.splitlines():
        if line.startswith("Avoid:"):
            return line.split(":", 1)[1]
    return ""


def lint_prompt(prompt: str, use_case: str, row: dict, delivery_px: int) -> list[str]:
    """Cheap prompt QA - every warning here is a known cause of a wasted generation."""
    issues: list[str] = []
    if len(prompt) > 1500:
        issues.append(f"prompt is {len(prompt)} chars - trim the description, long prompts dilute the important parts")
    if "Constraints:" not in prompt:
        issues.append("no Constraints line - state what must stay the same")
    if "Avoid:" not in prompt:
        issues.append("no Avoid line - state what must not appear")
    if use_case in EDIT_USE_CASES and not (row.get("must_keep") or "").strip():
        issues.append("edit use case without must_keep - edits drift unless invariants are stated explicitly")
    if use_case in TEXT_USE_CASES and not (row.get("text_verbatim") or "").strip():
        issues.append("text-bearing use case without text_verbatim - in-image spelling must be literal")
    if delivery_px > 2048:
        issues.append(f"delivery {delivery_px}px is above what generators produce natively - "
                      f"generate at native size and run `igp.py upscale --to-px {delivery_px}`")
    if len(split_refs(row.get("ref_images", ""))) > 3:
        issues.append("more than 3 reference images - label each one's role or quality drops")
    # food/drink rows legitimately carry 1-2 more clauses than hard-goods rows
    for label, text, limit in (("Constraints", constraints_of(prompt), 9), ("Avoid", avoid_of(prompt), 12)):
        count = len([a for a in text.split(";") if a.strip()])
        if count > limit:
            issues.append(f"{label} list has {count} clauses - trim the {label.lower()} in the sheet/brand/recipe "
                          f"source to the {limit} that matter most")
    return issues


def load_recipes() -> dict:
    return strip_json_comments(load_json(TEMPLATES / "recipes.json"))


def load_brand(path: Path | None) -> dict:
    return strip_json_comments(load_json(path or (TEMPLATES / "brand.json")))


def pick_recipe(recipes: dict, slug: str) -> tuple[str, dict]:
    slug = (slug or "").strip().lower()
    if slug in recipes:
        return slug, recipes[slug]
    guess = difflib.get_close_matches(slug, list(recipes), n=1, cutoff=0.4)
    warn(f"unknown use_case '{slug}'"
         + (f" - did you mean '{guess[0]}'?" if guess else "")
         + " -> falling back to product-mockup")
    return "product-mockup", recipes["product-mockup"]


def plan_item(row: dict, recipes: dict, brand: dict, brand_name: str, variant: int | None = None) -> dict:
    slug, recipe = pick_recipe(recipes, row.get("use_case", ""))
    out_defaults = brand.get("output_defaults", {}) or {}
    rid = row.get("id", "item") + (f"-v{variant}" if variant is not None else "")
    fmt = ((row.get("format") or "").strip().lower()
           or recipe.get("format_default")
           or ("png" if slug in out_defaults.get("png_use_cases", []) else out_defaults.get("format", "jpeg")))
    fmt = {"jpg": "jpeg"}.get(fmt, fmt)
    try:
        delivery_px = int(row.get("delivery_px") or recipe.get("delivery_px_default")
                          or out_defaults.get("delivery_px", 2048))
    except ValueError:
        delivery_px = int(out_defaults.get("delivery_px", 2048))
    stem = f"{slugify(rid, 24)}__{slugify(row.get('item_name', ''), 40)}"
    prompt = build_prompt(row, recipe, brand, brand_name, slug)
    return {
        "id": rid,
        "source_id": row.get("id", ""),
        "item_name": row.get("item_name", ""),
        "use_case": slug,
        "use_case_requested": row.get("use_case", ""),
        "priority": row.get("priority", ""),
        "notes": row.get("notes", ""),
        "ref_images": split_refs(row.get("ref_images", "")),
        "aspect": (row.get("aspect") or "").strip() or recipe.get("aspect_default", "1:1"),
        "delivery_px": delivery_px,
        "format": fmt,
        "stem": stem,
        "raw_file": f"raw/{stem}.png",
        "out_file": f"out/{stem}.{'jpg' if fmt == 'jpeg' else fmt}",
        "prompt": prompt,
        "lint": lint_prompt(prompt, slug, row, delivery_px),
    }


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def engine_hint() -> str:
    return ("no image engine available - install one of:\n"
            "    pip install --break-system-packages Pillow        (works in a bare Arena session)\n"
            "    apt-get install -y imagemagick                    (needs root; enables montage labels)")


def cmd_doctor(args) -> int:
    """Environment readiness report for a fresh session - run this first."""
    engine = Engine("auto")
    font = find_font()
    print("\nEnvironment")
    print(f"  python      : {sys.version.split()[0]}")
    print(f"  image engine: {engine.name}"
          + ("" if engine.name != "none" else "   <- " + engine_hint().splitlines()[0]))
    if engine.name == "none":
        print("    " + engine_hint().splitlines()[-2].strip())
        print("    " + engine_hint().splitlines()[-1].strip())
    print(f"  sheet font  : {font or 'not found (contact sheets render without labels)'}")
    print(f"  templates   : {TEMPLATES / 'recipes.json'}")
    print(f"  workspace   : {REPO}")
    problems: list[str] = []
    if engine.name == "none":
        problems.append(engine_hint())
    if not (TEMPLATES / "recipes.json").exists() or not (TEMPLATES / "brand.json").exists():
        problems.append(f"templates missing under {TEMPLATES} - is this a full checkout of the repo?")
    if not (ROUNDS).exists():
        problems.append(f"no rounds/ folder - run `igp.py new-round` or `igp.py intake` first")
    brand = load_brand(None) if (TEMPLATES / "brand.json").exists() else {}
    if str(brand.get("brand_name", "")).startswith("YOUR BRAND"):
        print("\n  note: templates/brand.json still has the placeholder brand name - set it once for your brand")
    print("\nVerdict: " + ("ready - you can run a round" if not problems else "NOT ready"))
    for problem in problems:
        warn(problem)
    return 1 if problems else 0


def cmd_plan(args) -> int:
    requests_path = Path(args.requests)
    rows = read_requests(requests_path)
    if not rows:
        die("request sheet has no data rows")
    examples = [r for r in rows if str(r.get("id", "")).upper().startswith("EXAMPLE")]
    if examples and not args.include_examples:
        rows = [r for r in rows if r not in examples]
        print(f"  - skipped {len(examples)} example row(s) from the template "
              f"(pass --include-examples to plan them anyway)")
    if not rows:
        die("request sheet only contains the template example row - data entry needs to fill it in")
    recipes, brand = load_recipes(), load_brand(Path(args.brand) if args.brand else None)
    brand_name = brand.get("brand_name", "")

    unknown = [c for c in (rows[0].keys()) if c and c not in KNOWN_FIELDS]
    if unknown:
        warn(f"unknown columns ignored by the prompt builder: {', '.join(unknown)}")

    problems = validate_rows(rows, requests_path.parent)
    missing_refs = [p for p in problems if "not found" in p]
    fatal = [p for p in problems if "not found" not in p]
    for p in problems:
        warn(p)
    if fatal:
        die(f"{len(fatal)} blocking problem(s) in {requests_path} - fix the sheet and re-run")
    if missing_refs and not args.allow_warnings:
        warn(f"{len(missing_refs)} reference image(s) missing - those prompts will describe the product from "
             f"text only. Add the files to refs/ before generating, or re-run with --allow-warnings to silence.")

    items: list[dict] = []
    for row in rows:
        try:
            variants = max(1, int(row.get("variants") or 1))
        except ValueError:
            variants = 1
        if variants > 1:
            items += [plan_item(row, recipes, brand, brand_name, v) for v in range(1, variants + 1)]
        else:
            items.append(plan_item(row, recipes, brand, brand_name))

    size = args.round_size or ROUND_SIZE
    base_id = args.round_id or f"{args.date}-r01"
    chunks = [items[i:i + size] for i in range(0, len(items), size)]
    rounds: list[dict] = []
    for index, chunk in enumerate(chunks, start=1):
        if len(chunks) == 1:
            rid = base_id
        elif re.search(r"r\d+$", base_id):
            rid = re.sub(r"r\d+$", f"r{index:02d}", base_id)
        else:
            rid = f"{base_id}-r{index:02d}"
        rounds.append({"round_id": rid, "items": chunk})

    est_kb = sum(EST_KB.get(it["format"], 500) for it in items)
    print(f"\nPlan: {len(items)} image(s) from {len(rows)} request(s)")
    print(f"  use cases : {', '.join(sorted({i['use_case'] for i in items}))}")
    print(f"  rounds    : {len(rounds)} x <= {size} images  ->  {', '.join(r['round_id'] for r in rounds)}")
    print(f"  est. size : ~{human(est_kb * 1024)} of delivery files (budget {WORKSPACE_LIMIT_MB:.0f}MB/session)")
    linted = [(it["id"], it["lint"]) for it in items if it["lint"]]
    if linted:
        print(f"\nPrompt QA: {len(linted)} item(s) worth a look before generating")
        for rid, issues in linted:
            for issue in issues:
                print(f"  ~ {rid}: {issue}")
    if est_kb / 1024 > 40:
        warn(f"projected {human(est_kb * 1024)} of outputs - deliver in rounds and prune raw/ between rounds "
             f"(see skills/arena-imagegen/references/storage-budget.md)")

    for rnd in rounds:
        rdir = Path(args.out_root) / rnd["round_id"]
        for sub in ("refs", "raw", "out", "review"):
            (rdir / sub).mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "igp-round/v1",
            "round_id": rnd["round_id"],
            "created": datetime.now().isoformat(timespec="seconds"),
            "brand": brand_name,
            "campaign": brand.get("campaign", ""),
            "source_sheet": str(requests_path),
            "round_size": size,
            "items": rnd["items"],
        }
        (rdir / "plan.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                                        encoding="utf-8")
        (rdir / "plan.md").write_text(render_plan_md(payload), encoding="utf-8")
        keep = {it["source_id"] for it in rnd["items"]}
        with (rdir / "requests.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                if row.get("id") in keep:
                    writer.writerow(row)
        ok(f"{rnd['round_id']}: {len(rnd['items'])} item(s) -> {rdir}/plan.json")

    print(f"\nNext: generate into each round's raw/ folder ({size} images per round max), then:")
    print(f"  python3 tools/igp.py optimize --round rounds/<round> --delete-source")
    print(f"  python3 tools/igp.py sheet --round rounds/<round>")
    print(f"  python3 tools/igp.py verify --round rounds/<round>")
    return 0


def render_plan_md(payload: dict) -> str:
    out = [f"# Prompt plan - {payload['round_id']}", ""]
    out.append(f"- brand/campaign: **{payload['brand']}** - {payload['campaign']}")
    out.append(f"- source sheet: `{payload['source_sheet']}`")
    out.append(f"- items: **{len(payload['items'])}** (generate at most {payload['round_size']} per round)")
    out.append("")
    for i, it in enumerate(payload["items"], 1):
        out.append(f"## {i}. `{it['id']}` - {it['item_name']}")
        out.append(f"- use case: `{it['use_case']}`  |  aspect: {it['aspect']}  |  "
                   f"delivery: {it['delivery_px'] or 'native'}px {it['format']}")
        out.append(f"- raw: `{it['raw_file']}`  ->  final: `{it['out_file']}`")
        if it["ref_images"]:
            out.append(f"- references: {', '.join('`' + r + '`' for r in it['ref_images'])}")
        if it["priority"] or it["notes"]:
            out.append(f"- priority: {it['priority'] or '-'}  |  notes: {it['notes'] or '-'}")
        for issue in it.get("lint", []):
            out.append(f"- **QA**: {issue}")
        out.append("")
        out.append("```text")
        out.append(it["prompt"])
        out.append("```")
        out.append("")
    out.append("---")
    out.append("Generated by `tools/igp.py plan`. If data entry mis-specified something, fix the prompt "
               "lines here and pass the corrected text straight to the image tool.")
    return "\n".join(out) + "\n"


def find_raw(round_dir: Path, item: dict) -> Path | None:
    raw_dir = round_dir / "raw"
    if not raw_dir.exists():
        return None
    wanted = Path(item["raw_file"]).stem
    files = sorted(p for p in raw_dir.iterdir() if p.is_file())
    for cand in files:
        if cand.stem == wanted:
            return cand
    for cand in files:  # loose match on the id prefix
        if cand.stem.startswith(slugify(item["id"], 24)):
            return cand
    return None


def cmd_optimize(args) -> int:
    engine = Engine(args.engine)
    if engine.name == "none":
        die(engine_hint())

    jobs: list[tuple[Path, Path, dict]] = []
    if args.round:
        rdir = Path(args.round)
        plan = load_json(rdir / "plan.json")
        missing = []
        for item in plan["items"]:
            src = find_raw(rdir, item)
            if not src:
                missing.append(item["id"])
                continue
            jobs.append((src, rdir / item["out_file"],
                         {"format": item["format"], "delivery_px": item["delivery_px"],
                          "aspect": item["aspect"], "id": item["id"]}))
        if missing:
            warn(f"no raw file yet for: {', '.join(missing)}")
    else:
        if not (args.in_dir and args.out_dir):
            die("pass either --round, or both --in-dir and --out-dir")
        for src in sorted(p for p in Path(args.in_dir).rglob("*")
                          if p.is_file() and p.suffix.lower() in IMAGE_EXTS):
            fmt = args.format or ("jpeg" if src.suffix.lower() in (".jpg", ".jpeg") else "png")
            jobs.append((src, Path(args.out_dir) / f"{src.stem}.{'jpg' if fmt == 'jpeg' else fmt}",
                         {"format": fmt, "delivery_px": args.max_dim or 0, "aspect": "", "id": src.stem}))

    if not jobs:
        die("nothing to optimize")

    total_before = total_after = upscaled = 0
    rows_out = []
    for src, dst, spec in jobs:
        before = src.stat().st_size
        w, h = engine.identify(src)
        target = spec["delivery_px"] or 0
        resize = None
        if target and max(w, h) > target:
            scale = target / max(w, h)
            resize = (max(1, round(w * scale)), max(1, round(h * scale)))
        elif target and max(w, h) < target * 0.98:
            if args.upscale_to_spec:
                scale = target / max(w, h)
                resize = (max(1, round(w * scale)), max(1, round(h * scale)))
                amount = args.unsharp or max(0.6, min(1.3, 0.45 + 0.25 * scale))
                keep_unsharp = f"0x{amount:.2f}+{amount:.2f}+0.008"
                upscaled += 1
            else:
                warn(f"{spec['id']}: generated {w}x{h} is smaller than the {target}px delivery spec - "
                     f"re-run with --upscale-to-spec (Lanczos + unsharp) or regenerate at a larger native size")
        engine.convert(src, dst, quality=args.quality, resize=resize, fmt=spec["format"],
                       max_kb=args.max_kb,
                       unsharp=keep_unsharp if resize and max(w, h) < (target or 0) else (args.unsharp or None),
                       png_colors=args.png_colors if spec["format"] == "png" else None)
        after = dst.stat().st_size
        total_before += before
        total_after += after
        nw, nh = engine.identify(dst)
        rows_out.append((spec["id"], f"{w}x{h}", f"{nw}x{nh}", human(before), human(after),
                         f"-{100 * (1 - after / before):.0f}%" if before else "-"))
        if args.delete_source:
            src.unlink()

    width = max(len(r[0]) for r in rows_out)
    print(f"\nOptimized {len(rows_out)} image(s) with {engine.name} (quality {args.quality})")
    print(f"  {'id'.ljust(width)}  {'from':>11}  {'to':>11}  {'raw':>9}  {'final':>9}  saved")
    for r in rows_out:
        print(f"  {r[0].ljust(width)}  {r[1]:>11}  {r[2]:>11}  {r[3]:>9}  {r[4]:>9}  {r[5]}")
    print(f"  total: {human(total_before)} -> {human(total_after)} "
          f"(saved {human(total_before - total_after)}, {100 * (1 - total_after / max(total_before, 1)):.0f}%)")
    if upscaled:
        print(f"  {upscaled} image(s) upscaled to the delivery spec with Lanczos + adaptive unsharp")
    if args.delete_source:
        print("  raw/ sources deleted - the optimized file in out/ is now the master copy")
    return 0


def cmd_upscale(args) -> int:
    engine = Engine(args.engine)
    src = Path(args.input)
    srcs = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS) \
        if src.is_dir() else [src]
    if not srcs:
        die(f"no images found at {src}")
    out_dir = Path(args.out_dir) if args.out_dir else (src if src.is_dir() else src.parent)
    out_dir.mkdir(parents=True, exist_ok=True)

    for path in srcs:
        w, h = engine.identify(path)
        scale = (args.to_px / max(w, h)) if args.to_px else args.scale
        if scale <= 1.001:
            warn(f"{path.name}: already {w}x{h}, nothing to upscale")
            continue
        nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
        fmt = args.format or ("jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "png")
        dst = out_dir / f"{path.stem}{args.suffix}.{'jpg' if fmt == 'jpeg' else fmt}"
        amount = args.unsharp if args.unsharp else max(0.6, min(1.3, 0.45 + 0.25 * scale))
        engine.convert(path, dst, quality=args.quality, resize=(nw, nh),
                       unsharp=f"0x{amount:.2f}+{amount:.2f}+0.008", fmt=fmt)
        print(f"  {path.name}: {w}x{h} -> {nw}x{nh} ({scale:.2f}x) {human(dst.stat().st_size)} -> {dst}")
    print("\nNote: optical upscaling (Lanczos + unsharp) adds pixels, not real detail.")
    print("      Generate at the largest native size the tool offers, then upscale only to hit a delivery spec.")
    return 0


def cmd_sheet(args) -> int:
    engine = Engine(args.engine)
    if args.round:
        rdir = Path(args.round)
        files = sorted(p for p in (rdir / "out").glob("*") if p.suffix.lower() in IMAGE_EXTS)
        dst = Path(args.out) if args.out else rdir / "review" / "contact-sheet.jpg"
    else:
        if not args.in_dir:
            die("pass --round or --in-dir")
        files = sorted(p for p in Path(args.in_dir).rglob("*")
                       if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
        dst = Path(args.out) if args.out else Path(args.in_dir) / "contact-sheet.jpg"
    if not files:
        die("no images to put on the contact sheet")
    engine.sheet(files, dst, args.cols, args.thumb, not args.no_label)
    print(f"  contact sheet: {len(files)} image(s), {human(dst.stat().st_size)} -> {dst}")
    print("  one file to review the whole round instead of opening every image in the session")
    return 0


def cmd_verify(args) -> int:
    engine = Engine(args.engine)
    rdir = Path(args.round)
    plan = load_json(rdir / "plan.json")
    rows, flagged = [], 0
    planned_out = set()
    for item in plan["items"]:
        out = rdir / item["out_file"]
        planned_out.add(out.name)
        if not out.exists():
            rows.append((item["id"], "MISSING", "-", "-", "not generated yet / wrong filename"))
            flagged += 1
            continue
        w, h = engine.identify(out)
        kb = out.stat().st_size / 1024
        issues = []
        if item["delivery_px"] and item["delivery_px"] > 0 and max(w, h) < item["delivery_px"] * 0.98:
            issues.append(f"below {item['delivery_px']}px spec")
        if args.max_kb and kb > args.max_kb:
            issues.append(f"{kb:.0f}KB > {args.max_kb}KB cap")
        if item["format"] == "jpeg" and out.suffix.lower() not in (".jpg", ".jpeg"):
            issues.append("wrong extension for jpeg")
        rows.append((item["id"], "OK" if not issues else "REVIEW", f"{w}x{h}", f"{kb:.0f}KB",
                     "; ".join(issues) or item["use_case"]))
        flagged += 1 if issues else 0
    out_dir, raw_dir = rdir / "out", rdir / "raw"
    orphans = [p.name for p in out_dir.glob("*") if p.is_file() and p.name not in planned_out]
    raws_left = [p.name for p in raw_dir.glob("*") if p.is_file()] if raw_dir.exists() else []
    delivered = sum(1 for r in rows if r[1] != "MISSING")

    width = max(len(r[0]) for r in rows) if rows else 4
    print(f"\nVerify {rdir.name}: {len(plan['items'])} planned, {delivered} delivered, {flagged} flagged")
    print(f"  {'id'.ljust(width)}  {'status':<7}  {'size':>11}  {'file':>8}  notes")
    for r in rows:
        print(f"  {r[0].ljust(width)}  {r[1]:<7}  {r[2]:>11}  {r[3]:>8}  {r[4]}")
    if orphans:
        warn(f"{len(orphans)} file(s) in out/ are not in the plan: {', '.join(orphans)}")
    if raws_left:
        warn(f"{len(raws_left)} raw file(s) still in raw/ - run `igp.py optimize --round {rdir} "
             f"--delete-source` to keep the session under budget")

    report = [f"# Verify report - {rdir.name}", "",
              f"- planned: {len(plan['items'])}", f"- delivered: {delivered}", f"- flagged: {flagged}",
              f"- created: {datetime.now().isoformat(timespec='seconds')}", "",
              "| id | status | pixels | file | notes |", "| --- | --- | --- | --- | --- |"]
    report += [f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in rows]
    if orphans:
        report += ["", f"Orphans in out/: {', '.join(orphans)}"]
    if raws_left:
        report += ["", f"Raw files still present: {len(raws_left)}"]
    (rdir / "review").mkdir(parents=True, exist_ok=True)
    (rdir / "review" / "verify-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\n  report -> {rdir / 'review' / 'verify-report.md'}")
    return 1 if flagged else 0


def skeleton_sheet(src: Path) -> Path:
    """No request sheet in the drop folder? Build a skeleton, one row per image.

    This is the 'the team just uploaded photos' path: the images become rows with an id and a
    placeholder description that data entry (or the agent, with the user) must fill in.
    """
    images = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    if not images:
        die(f"no request sheet and no images found in {src}")
    header = list(KNOWN_FIELDS[:14])
    rows = []
    for path in images:
        item = re.sub(r"[-_]+", " ", path.stem).strip().title()
        rows.append({
            "id": slugify(path.stem, 24).upper(),
            "item_name": item,
            "use_case": "product-mockup",
            "description": f"TODO describe the exact {item} (product, colour, material, finish)",
            "ref_images": f"refs/{path.name}",
            "aspect": "1:1", "delivery_px": "2048", "format": "jpeg",
            "asset_type": "catalogue image", "priority": "medium",
            "notes": "auto-generated row - fill in the description and delete this note",
        })
    out = src / "requests.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in header})
    warn(f"no request sheet found - wrote a skeleton sheet with {len(rows)} row(s): {out}")
    warn("descriptions are placeholders: fill them in and re-run for usable prompts")
    return out


def cmd_intake(args) -> int:
    """Take a drop folder from data entry (sheet + reference images) and turn it into a planned round."""
    src = Path(args.source) if args.source else INBOX / args.name
    if not src.is_dir():
        die(f"nothing to intake at {src}")
    sheets = sorted(p for p in src.iterdir()
                    if p.is_file() and p.suffix.lower() in (".csv", ".tsv", ".json"))
    sheet = sheets[0] if sheets else None
    if len(sheets) > 1:
        warn(f"{len(sheets)} sheets found, using {sheet.name}")
    if sheet is None:
        sheet = skeleton_sheet(src)

    round_id = args.round_id or args.name or f"{args.date}-r01"
    rdir = ROUNDS / round_id
    for sub in ("refs", "raw", "out", "review"):
        (rdir / sub).mkdir(parents=True, exist_ok=True)
    moved = copied = 0
    for path in sorted(src.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            target = rdir / "refs" / path.name
            if args.move:
                shutil.move(str(path), target)
                moved += 1
            else:
                shutil.copy2(path, target)
                copied += 1
    shutil.copy2(sheet, rdir / "requests.csv")
    print(f"  intake: {sheet.name} + {copied + moved} reference image(s) -> {rdir}/")

    from argparse import Namespace
    plan_args = Namespace(requests=str(rdir / "requests.csv"), out_root=str(ROUNDS),
                          round_id=round_id, date=args.date, round_size=args.round_size,
                          brand=args.brand, allow_warnings=True, include_examples=False)
    rc = cmd_plan(plan_args)
    if rc == 0 and args.clean and not args.move:
        shutil.rmtree(src, ignore_errors=True)
        print(f"  cleaned up {src}")
    return rc


def cmd_deliver(args) -> int:
    """Bundle a round's finals for the team: zip + manifest, one file to hand over."""
    rdir = Path(args.round)
    plan = load_json(rdir / "plan.json")
    engine = Engine(args.engine)
    rname = rdir.name
    manifest = [["id", "item_name", "use_case", "file", "pixels", "kb", "priority", "notes", "prompt"]]
    missing = []
    for item in plan["items"]:
        out = rdir / item["out_file"]
        if not out.exists():
            missing.append(item["id"])
            continue
        w, h = engine.identify(out)
        manifest.append([item["id"], item["item_name"], item["use_case"], out.name, f"{w}x{h}",
                         f"{out.stat().st_size / 1024:.0f}", item["priority"], item["notes"],
                         item["prompt"].replace("\n", " | ")])
    if not manifest[1:]:
        die(f"nothing delivered yet in {rdir / 'out'}")
    if missing:
        warn(f"{len(missing)} item(s) not generated yet and left out of the bundle: {', '.join(missing)}")

    review = rdir / "review"
    review.mkdir(parents=True, exist_ok=True)
    man_path = review / f"{rname}-manifest.csv"
    with man_path.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(manifest)
    zip_path = Path(args.out) if args.out else review / f"{rname}-delivery.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for row in manifest[1:]:
            zf.write(rdir / "out" / row[3], arcname=f"{rname}/{row[3]}")
        zf.write(man_path, arcname=f"{rname}/{man_path.name}")
        plan_md = rdir / "plan.md"
        if plan_md.exists():
            zf.write(plan_md, arcname=f"{rname}/plan.md")
    total = sum((rdir / "out" / row[3]).stat().st_size for row in manifest[1:])
    print(f"\nDelivery bundle: {len(manifest) - 1} image(s), {human(total)} of image data")
    print(f"  zip      : {zip_path} ({human(zip_path.stat().st_size)})")
    print(f"  manifest : {man_path}")
    print(f"  contents : finals + manifest + the prompts that produced them")
    return 0


def cmd_status(args) -> int:
    if not ROUNDS.exists():
        die(f"no rounds yet (expected {ROUNDS})")
    print(f"\n{'round':<26} {'items':>5} {'out':>4} {'raw':>4} {'size':>9}  use cases")
    for rdir in sorted(p for p in ROUNDS.iterdir() if p.is_dir()):
        plan_file = rdir / "plan.json"
        items = json.loads(plan_file.read_text(encoding="utf-8"))["items"] if plan_file.exists() else []
        out_files = [p for p in (rdir / "out").glob("*") if p.is_file()]
        raw_files = [p for p in (rdir / "raw").glob("*") if p.is_file()]
        size = sum(p.stat().st_size for p in rdir.rglob("*") if p.is_file())
        slugs = ",".join(sorted({i["use_case"] for i in items}))[:34]
        print(f"{rdir.name:<26} {len(items):>5} {len(out_files):>4} {len(raw_files):>4} {human(size):>9}  {slugs}")
    return 0


def cmd_budget(args) -> int:
    root = Path(args.root)
    skip = {".git", ".venv", "node_modules", "__pycache__"}
    files = [p for p in root.rglob("*") if p.is_file() and not any(part in skip for part in p.parts)]
    total = sum(p.stat().st_size for p in files)
    mb, count = total / 1024 / 1024, len(files)
    pct_mb, pct_files = 100 * mb / WORKSPACE_LIMIT_MB, 100 * count / WORKSPACE_LIMIT_FILES
    print(f"\nWorkspace budget  ({root})")
    print(f"  size : {mb:8.1f} MB / {WORKSPACE_LIMIT_MB:.0f} MB   ({pct_mb:.1f}% used)")
    print(f"  files: {count:8d}    / {WORKSPACE_LIMIT_FILES:,}     ({pct_files:.1f}% used)")
    level = max(pct_mb, pct_files)
    if level > 90:
        print("  status: CRITICAL - run `igp.py prune --scratch`, archive old rounds, deliver via one contact sheet")
    elif level > 70:
        print("  status: WARNING - run `igp.py prune --scratch` after every round")
    else:
        print("  status: healthy")
    print("\n  largest files:")
    for p in sorted(files, key=lambda x: x.stat().st_size, reverse=True)[:10]:
        print(f"    {human(p.stat().st_size):>9}  {p.relative_to(root)}")
    by_dir: dict[str, list[int]] = {}
    for p in files:
        parts = p.relative_to(root).parts
        key = parts[0] if len(parts) > 1 else "(root)"
        by_dir.setdefault(key, []).append(p.stat().st_size)
    print("\n  by top-level folder:")
    for key, sizes in sorted(by_dir.items(), key=lambda kv: -sum(kv[1])):
        print(f"    {human(sum(sizes)):>9}  {len(sizes):>6} file(s)  {key}")
    if args.json:
        print(json.dumps({"mb": round(mb, 2), "files": count, "pct_mb": round(pct_mb, 1),
                          "pct_files": round(pct_files, 1)}))
    return 0 if level <= 90 else 1


def cmd_prune(args) -> int:
    targets: list[Path] = []
    rounds = [Path(args.round)] if args.round else [p for p in ROUNDS.iterdir() if p.is_dir()] \
        if ROUNDS.exists() else []
    for rdir in rounds:
        if (rdir / "raw").exists():
            targets += [p for p in (rdir / "raw").rglob("*") if p.is_file()]
        if args.scratch:
            for name in ("work", "tmp", ".tmp"):
                if (rdir / name).exists():
                    targets += [p for p in (rdir / name).rglob("*") if p.is_file()]
    freed_bytes = freed_files = 0
    for path in targets:
        freed_bytes += path.stat().st_size
        freed_files += 1
        path.unlink()
    for d in sorted({p.parent for p in targets}, key=lambda x: -len(x.parts)):
        if d.exists() and not any(d.iterdir()):
            d.rmdir()
    print(f"  pruned {freed_files} file(s), freed {human(freed_bytes)}")

    if args.archive_older_than is not None and ROUNDS.exists():
        cutoff = datetime.now().timestamp() - args.archive_older_than * 86400
        ARCHIVE.mkdir(exist_ok=True)
        for rdir in sorted(p for p in ROUNDS.iterdir() if p.is_dir()):
            if rdir.stat().st_mtime >= cutoff or not any((rdir / "out").glob("*")):
                continue
            zip_path = ARCHIVE / f"{rdir.name}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in sorted((rdir / "out").glob("*")):
                    zf.write(f, arcname=f"{rdir.name}/{f.name}")
            shutil.rmtree(rdir)
            print(f"  archived {rdir.name} -> {zip_path} ({human(zip_path.stat().st_size)})")
    return 0


def cmd_new_round(args) -> int:
    rdir = Path(args.out_root) / args.round_id
    if rdir.exists() and not args.force:
        die(f"{rdir} already exists (use --force to reuse it)")
    for sub in ("refs", "raw", "out", "review"):
        (rdir / sub).mkdir(parents=True, exist_ok=True)
    sheet = rdir / "requests.csv"
    if not sheet.exists():
        shutil.copyfile(TEMPLATES / "requests.csv", sheet)
    (rdir / "HOWTO.txt").write_text(
        f"Round {args.round_id}\n"
        f"{'=' * (6 + len(args.round_id))}\n\n"
        "1. Data entry fills requests.csv (one row per image) and drops reference images\n"
        "   into refs/ using the filenames the sheet points at.\n"
        "2. Agent:  python3 tools/igp.py plan --requests "
        f"{sheet} --round-id {args.round_id}\n"
        "   -> writes plan.json + plan.md (one ready-to-use prompt per image)\n"
        "3. Images are generated into raw/ - max 10 per round, never more.\n"
        f"4. Agent:  python3 tools/igp.py optimize --round {rdir} --delete-source\n"
        f"           python3 tools/igp.py sheet --round {rdir}\n"
        f"           python3 tools/igp.py verify --round {rdir}\n"
        "   -> finals in out/, contact sheet + verify report in review/, raw/ emptied.\n",
        encoding="utf-8")
    ok(f"round ready: {rdir}")
    print(f"  request sheet: {sheet}   references: {rdir}/refs/")
    return 0


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="igp", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", default="auto", choices=["auto", "imagemagick", "pillow"],
                   help="image backend (default: auto-detect)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("doctor", help="check this session is ready to run a round")
    s.set_defaults(func=cmd_doctor)

    s = sub.add_parser("new-round", help="scaffold a round folder")
    s.add_argument("--round-id", default=f"{today()}-r01")
    s.add_argument("--out-root", default=str(ROUNDS))
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_new_round)

    s = sub.add_parser("plan", help="requests -> prompts -> rounds")
    s.add_argument("--requests", required=True, help="CSV/TSV/JSON request sheet")
    s.add_argument("--out-root", default=str(ROUNDS))
    s.add_argument("--round-id", default=None, help="default: <today>-r01")
    s.add_argument("--date", default=today())
    s.add_argument("--round-size", type=int, default=ROUND_SIZE)
    s.add_argument("--brand", default=None, help="style-lock JSON (default templates/brand.json)")
    s.add_argument("--allow-warnings", action="store_true", help="continue when a reference image is missing")
    s.add_argument("--include-examples", action="store_true", help="plan the EXAMPLE row too")
    s.set_defaults(func=cmd_plan)

    s = sub.add_parser("optimize", help="compress raw generations into delivery masters")
    s.add_argument("--round", default=None, help="round folder containing plan.json")
    s.add_argument("--in-dir", default=None)
    s.add_argument("--out-dir", default=None)
    s.add_argument("--format", default=None, choices=["jpeg", "png", "webp"])
    s.add_argument("--quality", type=int, default=92)
    s.add_argument("--max-dim", type=int, default=0, help="long-edge cap when not using --round")
    s.add_argument("--max-kb", type=int, default=None, help="force a per-file size cap")
    s.add_argument("--unsharp", default=None, help="e.g. 0x0.6+0.6+0.008")
    s.add_argument("--upscale-to-spec", action="store_true",
                   help="Lanczos-upscale anything smaller than the planned delivery size instead of warning")
    s.add_argument("--png-colors", type=int, default=None, metavar="N",
                   help="quantize PNG output to N colours (big win for cutouts; off by default)")
    s.add_argument("--delete-source", action="store_true", help="delete raw/ after a successful write")
    s.set_defaults(func=cmd_optimize)

    s = sub.add_parser("upscale", help="Lanczos + unsharp upscale for delivery sizes")
    s.add_argument("input", help="image file or folder")
    s.add_argument("--out-dir", default=None)
    s.add_argument("--to-px", type=int, default=0, help="target long edge in pixels")
    s.add_argument("--scale", type=float, default=2.0)
    s.add_argument("--format", default=None, choices=["jpeg", "png", "webp"])
    s.add_argument("--quality", type=int, default=95)
    s.add_argument("--unsharp", type=float, default=None)
    s.add_argument("--suffix", default="-2x")
    s.set_defaults(func=cmd_upscale)

    s = sub.add_parser("sheet", help="one contact sheet per round")
    s.add_argument("--round", default=None)
    s.add_argument("--in-dir", default=None)
    s.add_argument("--out", default=None)
    s.add_argument("--cols", type=int, default=5)
    s.add_argument("--thumb", type=int, default=460)
    s.add_argument("--no-label", action="store_true")
    s.set_defaults(func=cmd_sheet)

    s = sub.add_parser("verify", help="coverage + spec + budget check")
    s.add_argument("--round", required=True)
    s.add_argument("--max-kb", type=int, default=1200)
    s.set_defaults(func=cmd_verify)

    s = sub.add_parser("intake", help="turn a data-entry drop folder into a planned round")
    s.add_argument("--name", default=None, help="folder name under inbox/")
    s.add_argument("--source", default=None, help="explicit drop folder path")
    s.add_argument("--round-id", default=None, help="default: <name>")
    s.add_argument("--date", default=today())
    s.add_argument("--round-size", type=int, default=ROUND_SIZE)
    s.add_argument("--brand", default=None)
    s.add_argument("--move", action="store_true", help="move references instead of copying")
    s.add_argument("--clean", action="store_true", help="delete the inbox folder after a successful plan")
    s.set_defaults(func=cmd_intake)

    s = sub.add_parser("deliver", help="bundle a round's finals into one zip + manifest")
    s.add_argument("--round", required=True)
    s.add_argument("--out", default=None)
    s.set_defaults(func=cmd_deliver)

    s = sub.add_parser("status", help="per-round overview")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("budget", help="workspace 128MB / 10k-file guard")
    s.add_argument("--root", default=str(REPO))
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_budget)

    s = sub.add_parser("prune", help="delete raw/scratch files, optionally archive old rounds")
    s.add_argument("--round", default=None)
    s.add_argument("--scratch", action="store_true")
    s.add_argument("--archive-older-than", type=int, default=None, metavar="DAYS")
    s.set_defaults(func=cmd_prune)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
