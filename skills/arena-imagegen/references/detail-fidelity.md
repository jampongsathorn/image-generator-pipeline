# Detail fidelity: don't lose details

Rule zero: **detail you did not generate cannot be recovered later.** Every step below protects
pixels that already exist; none of them create new information.

## Contents
- [The detail ladder](#the-detail-ladder)
- [Resolution policy](#resolution-policy)
- [Upscaling policy](#upscaling-policy)
- [Avoiding re-encode loss](#avoiding-re-encode-loss)
- [Creating perceived sharpness](#creating-perceived-sharpness)
- [Per-format settings](#per-format-settings)
- [Detail-critical cases](#detail-critical-cases)
- [Verification](#verification)

## The detail ladder

Ordered from best to worst outcome. Always take the highest rung available.

| Rung | Action | Detail outcome |
| --- | --- | --- |
| 1 | Generate at the largest native size the tool offers, at final aspect | full generated detail, no resampling |
| 2 | Downscale a larger generation to the delivery size (Lanczos) | free sharpness - the safest transform |
| 3 | Deliver at native size even if below spec, and say so | no invented detail, honest file |
| 4 | Upscale (Lanczos + unsharp) to reach the spec | pixels interpolated, edges sharpened, no new texture |
| 5 | Stretch/nearest/simple 2x blur upscale | soft, unacceptable for product work |

Never do: generate small → JPEG compress hard → re-open the JPEG → upscale → re-encode. Each arrow
in that chain destroys detail.

## Resolution policy

| Target | Recommendation |
| --- | --- |
| Marketplace/catalogue listing | 2048px long edge, 1:1 or 4:5 - default in `templates/brand.json` |
| Print (A4 at 300dpi) | 2480x3508px, TIFF/PNG master then JPEG for delivery |
| Web hero | 2400px wide, JPEG q92, 4:4:4 supersampled from ≥2400px generation |
| Thumbnails/social | generate large, downscale - never generate small and upscale |
| Transparent cutouts | PNG at the largest size generated; keep alpha, avoid re-compression |

If a row asks for more than the generator's native maximum, that is a **plan** signal: generate at
native max, then `igp.py upscale --to-px <target>` (rung 4), and note in the manifest that the file
was upscaled. `igp.py plan` warns about this in the prompt QA section.

## Upscaling policy

```bash
# one image
python3 tools/igp.py upscale rounds/<id>/out/<file>.jpg --to-px 2048

# automatically, to the spec in plan.json, during the round
python3 tools/igp.py optimize --round rounds/<id> --delete-source --upscale-to-spec
```

What the pipeline does: Lanczos resampling (best general-purpose kernel; preserves edges better than
bicubic/bilinear) followed by **one** adaptive unsharp pass whose strength scales with the factor
(0.6-1.3). Not done: sharpening twice, generative "enhance", repeated resampling.

Limits to state honestly:
- up to ~2x is usually acceptable for product photography, especially when the image is viewed at
  less than 100%;
- text, thin hardware, and fine patterns degrade first - if those matter, regenerate instead;
- a 4x upscale is a stopgap, not a delivery strategy;
- if a real detail-restoration model is ever installed in the session (e.g. Real-ESRGAN), use it for
  photographic upscales and keep the Lanczos path for logos/text where generative upscalers hallucinate.

## Avoiding re-encode loss

- **Optimize from the raw master, once.** `igp.py optimize --round ... --delete-source` writes the
  final directly from the raw file - one decode, one encode.
- **Never re-edit a delivered JPEG.** If it needs a change, go back to the raw file; if the raw is
  gone, regenerate. Editing a JPEG means decode → edit → re-encode, and each generation of JPEG
  compression visibly softens fine texture.
- **Keep one master per image.** `out/` holds exactly one file per item. Working copies belong in
  `raw/` or `review/` and get pruned.
- **PNG for alpha/text, JPEG for photographs.** Converting a PNG cutout to JPEG destroys transparency
  and adds ringing around edges - that is detail loss, not compression.

## Creating perceived sharpness

Legitimate transforms that make an image *look* sharper without inventing detail:

1. **Supersample:** generate at the largest available size and downscale to delivery size. Reduces
   aliasing, increases edge contrast - works especially well for logos, UI mockups and text.
2. **Single unsharp pass** with a small radius: `0x0.6+0.6+0.008` is a good default for 2048px output.
   Large amounts (`0x2.0+...`) create halos that look worse than softness.
3. **Mild contrast in the grade** (per brand lock), not per-image, so the set stays consistent.
4. **JPEG 4:4:4 chroma** (`-sampling-factor 4:4:4`, Pillow `subsampling=0`) - default 4:2:0 blurring of
   saturated edges is invisible on landscapes and obvious on product edges and coloured text.

Not legitimate: generative "enhance" that reinvents texture on an identity-locked product;
upscaling logos to hero size and calling it a master; triple-sharpening to fake crispness.

## Per-format settings

| Format | When | Settings used by `igp.py` |
| --- | --- | --- |
| JPEG | photography, catalogue, web | q92 default (`--quality`), 4:4:4, progressive, no metadata strip-out beyond EXIF |
| PNG | cutouts, logos, UI, text, anything with alpha | compression level 9; optional `--png-colors N` quantisation for cutouts (big win, still visually lossless at 256 for flat art) |
| WebP | when the destination wants small files | method 6, q92 - lossy; keep a JPEG/PNG master |
| TIFF/PNG master | print or when typesetting happens downstream | keep, deliver alongside JPEG |

## Detail-critical cases

| Case | Approach |
| --- | --- |
| Packaging label text | generate artwork with clean label space, typeset real text in post; verify at 100% |
| Small hardware (clasps, zips, stitching) | generate large, downscale to delivery; inspect at 200-400% |
| Fabric weave / leather grain | name the material in `Materials/textures:`; do not let Avoid lines kill texture |
| Faces (lifestyle rows) | `natural skin texture, visible pores, no beauty retouching`; inspect hands and eyes closely |
| Transparent cutouts (straps, reeds, handles) | PNG only; check edge anti-aliasing at 400%; no drop shadow unless requested |
| Thin UI strokes / icons | supersample from 2x generation, then downscale; never upscale a mockup |

## Verification

```bash
python3 tools/igp.py verify --round rounds/<id>            # pixels vs spec, size vs cap, coverage
identify -format "%f %wx%h %[colorspace]\n" rounds/<id>/out/*   # independent check
```

Then look, don't just measure: open the contact sheet for the overview and the full-size file for
anything with text, labels or fine hardware. "It looks fine small" is the beginning of a rework
request, not a sign-off.
