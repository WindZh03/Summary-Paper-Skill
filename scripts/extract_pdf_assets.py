#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from paper_summary_lib import read_json, write_json

try:
    import fitz  # type: ignore
except ImportError as exc:
    raise SystemExit(
        "Missing PyMuPDF dependency. Run 'python3 scripts/check_deps.py check' first."
    ) from exc


POSITIVE_KEYWORDS = [
    "pipeline",
    "framework",
    "overall framework",
    "overview",
    "architecture",
    "method overview",
    "approach overview",
    "system overview",
    "model overview",
    "proposed method",
    "our method",
    "workflow",
    "methodology",
    "design overview",
]
NEGATIVE_KEYWORDS = [
    "result",
    "results",
    "ablation",
    "dataset",
    "statistics",
    "accuracy",
    "table",
    "appendix",
    "supplementary",
    "qualitative",
    "quantitative",
    "user study",
    "comparison",
    "benchmark",
    "error analysis",
]
CAPTION_RE = re.compile(r"^(figure|fig\.?|overview|architecture|pipeline)\b", re.I)
METHOD_TEXT_RE = re.compile(
    r"(pipeline|framework|architecture|workflow|overall|overview|method|approach|model)",
    re.I,
)


def first_page_title_author_clip(page: fitz.Page) -> fitz.Rect:
    width, height = page.rect.width, page.rect.height
    return fitz.Rect(0, 0, width, max(160, height * 0.28))


def save_clip(page: fitz.Page, rect: fitz.Rect, out_path: Path, zoom: float = 2.2) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect, alpha=False)
    pix.save(str(out_path))


def normalize_inline(text: str) -> str:
    return " ".join(text.split())


def block_text(block: dict[str, Any]) -> str:
    parts: list[str] = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = span.get("text", "")
            if text:
                parts.append(text)
    return normalize_inline(" ".join(parts))


def nearby_text_score(text: str) -> float:
    lowered = text.lower()
    score = 0.0
    for keyword in POSITIVE_KEYWORDS:
        if keyword in lowered:
            score += 2.0 if keyword != "method" else 0.6
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in lowered:
            score -= 1.5
    if CAPTION_RE.search(text):
        score += 1.5
    return score


def text_blocks(raw: dict[str, Any]) -> list[tuple[fitz.Rect, str]]:
    out = []
    for block in raw.get("blocks", []):
        if block.get("type") == 0:
            text = block_text(block)
            if text:
                out.append((fitz.Rect(block["bbox"]), text))
    return out


def image_blocks(raw: dict[str, Any], page_rect: fitz.Rect) -> list[tuple[fitz.Rect, float]]:
    images = []
    page_area = page_rect.get_area() or 1
    for block in raw.get("blocks", []):
        if block.get("type") != 1:
            continue
        bbox = fitz.Rect(block["bbox"])
        area_ratio = bbox.get_area() / page_area
        if area_ratio < 0.035:
            continue
        images.append((bbox, area_ratio))
    return images


def nearby_texts(img_bbox: fitz.Rect, texts: list[tuple[fitz.Rect, str]]) -> list[str]:
    nearby = []
    expanded = fitz.Rect(
        max(0, img_bbox.x0 - 40),
        max(0, img_bbox.y0 - 120),
        img_bbox.x1 + 40,
        img_bbox.y1 + 140,
    )
    for rect, text in texts:
        if expanded.intersects(rect):
            nearby.append(text)
    return nearby


def page_level_score(page_text: str, page_number: int) -> float:
    lowered = page_text.lower()
    score = 0.0
    for keyword in POSITIVE_KEYWORDS:
        if keyword in lowered:
            score += 0.8 if keyword != "method" else 0.3
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in lowered:
            score -= 0.6
    if 2 <= page_number <= 6:
        score += 1.2
    elif 7 <= page_number <= 10:
        score += 0.5
    elif page_number == 1:
        score -= 0.8
    return score


def candidate_framework_regions(page: fitz.Page, page_number: int) -> list[dict[str, Any]]:
    raw = page.get_text("dict")
    texts = text_blocks(raw)
    images = image_blocks(raw, page.rect)
    page_text = normalize_inline(page.get_text())
    page_bias = page_level_score(page_text, page_number)
    candidates = []

    for bbox, area_ratio in images:
        score = area_ratio * 10.0 + page_bias
        score -= abs(0.32 - bbox.y0 / max(page.rect.height, 1)) * 0.8
        local_texts = nearby_texts(bbox, texts)
        local_blob = " ".join(local_texts)
        score += nearby_text_score(local_blob)

        if any(CAPTION_RE.search(text) for text in local_texts):
            score += 1.0
        if page_number == 1 and bbox.y1 < page.rect.height * 0.45:
            score -= 3.0
        if area_ratio > 0.55 and page_number == 1:
            score -= 2.5

        candidates.append(
            {
                "score": score,
                "bbox": bbox,
                "page_number": page_number,
                "area_ratio": area_ratio,
                "context": local_blob[:500],
            }
        )

    if not candidates and METHOD_TEXT_RE.search(page_text):
        height = page.rect.height
        width = page.rect.width
        clip = fitz.Rect(width * 0.05, height * 0.18, width * 0.95, height * 0.78)
        candidates.append(
            {
                "score": page_bias,
                "bbox": clip,
                "page_number": page_number,
                "area_ratio": clip.get_area() / (page.rect.get_area() or 1),
                "context": page_text[:500],
            }
        )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates


def choose_framework_region(doc: fitz.Document, max_pages: int) -> dict[str, Any] | None:
    all_candidates = []
    for idx in range(min(max_pages, len(doc))):
        all_candidates.extend(candidate_framework_regions(doc[idx], idx + 1))
    if not all_candidates:
        return None
    best = all_candidates[0]
    if best["score"] < 1.8:
        return None
    return best


def extract_assets(pdf_path: Path, out_dir: Path, base_name: str, max_pages: int = 12) -> dict[str, Any]:
    doc = fitz.open(pdf_path)
    assets = {
        "pdf_path": str(pdf_path),
        "page_count": len(doc),
        "title_author_image": "",
        "framework_image": "",
        "framework_page": None,
        "framework_score": None,
        "asset_base_name": base_name,
        "asset_status": "pending",
        "asset_error": "",
    }
    try:
        page0 = doc[0]
        title_out = out_dir / f"{base_name}__title.png"
        save_clip(page0, first_page_title_author_clip(page0), title_out)
        assets["title_author_image"] = str(title_out)

        best = choose_framework_region(doc, max_pages=max_pages)
        if best is not None:
            page = doc[best["page_number"] - 1]
            bbox = best["bbox"]
            pad = 8
            clip = fitz.Rect(
                max(0, bbox.x0 - pad),
                max(0, bbox.y0 - pad),
                min(page.rect.width, bbox.x1 + pad),
                min(page.rect.height, bbox.y1 + pad),
            )
            framework_out = out_dir / f"{base_name}__framework.png"
            save_clip(page, clip, framework_out, zoom=2.0)
            assets["framework_image"] = str(framework_out)
            assets["framework_page"] = best["page_number"]
            assets["framework_score"] = round(best["score"], 3)

        assets["asset_status"] = "assets_extracted"
        return assets
    finally:
        doc.close()


def extract_assets_from_manifest(
    manifest: dict[str, Any],
    assets_root: Path,
    max_pages: int,
) -> dict[str, Any]:
    assets_root.mkdir(parents=True, exist_ok=True)
    for paper in manifest.get("papers", []):
        pdf_path = Path(paper["pdf_path"])
        try:
            result = extract_assets(
                pdf_path,
                assets_root,
                base_name=paper.get("asset_basename") or f"paper_{paper['paper_index']:03d}",
                max_pages=max_pages,
            )
            paper.update(result)
        except Exception as exc:
            paper.update(
                {
                    "title_author_image": "",
                    "framework_image": "",
                    "asset_status": "asset_failed",
                    "asset_error": f"{type(exc).__name__}: {exc}",
                }
            )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract title and framework images from PDFs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    one = subparsers.add_parser("one", help="Extract assets for one PDF.")
    one.add_argument("pdf_path")
    one.add_argument("assets_root")
    one.add_argument("--base-name", required=True)
    one.add_argument("--max-pages", type=int, default=12)

    manifest = subparsers.add_parser("manifest", help="Extract assets for all PDFs in a manifest.")
    manifest.add_argument("manifest")
    manifest.add_argument("--assets-root", required=True)
    manifest.add_argument("--output", required=True)
    manifest.add_argument("--max-pages", type=int, default=12)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "one":
        result = extract_assets(
            Path(args.pdf_path).expanduser().resolve(),
            Path(args.assets_root).expanduser().resolve(),
            base_name=args.base_name,
            max_pages=args.max_pages,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    manifest = read_json(Path(args.manifest).expanduser().resolve())
    data = extract_assets_from_manifest(
        manifest,
        assets_root=Path(args.assets_root).expanduser().resolve(),
        max_pages=args.max_pages,
    )
    write_json(Path(args.output).expanduser().resolve(), data)
    print(str(Path(args.output).expanduser().resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

