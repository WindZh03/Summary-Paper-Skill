#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from paper_summary_lib import (
    DEFAULT_TEXT_LIMIT,
    guess_title,
    normalize_text,
    read_json,
    write_json,
)


def import_pdf_reader():
    try:
        from pypdf import PdfReader  # type: ignore

        return PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore

            return PdfReader
        except ImportError as exc:
            raise SystemExit(
                "Missing PDF reader dependency. Run "
                "'python3 scripts/check_deps.py check' first."
            ) from exc


def extract_pdf_text(pdf_path: Path, max_chars: int) -> dict[str, Any]:
    PdfReader = import_pdf_reader()
    reader = PdfReader(str(pdf_path))
    metadata = getattr(reader, "metadata", None)
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    full_text = normalize_text("\n\n".join(pages))
    title = guess_title(
        full_text,
        getattr(metadata, "title", None) if metadata else None,
        pdf_path.stem,
    )
    return {
        "title_guess": title,
        "text": full_text[:max_chars],
        "text_chars": min(len(full_text), max_chars),
        "text_truncated": len(full_text) > max_chars,
        "page_count": len(reader.pages),
        "status": "text_extracted" if full_text else "empty_text",
        "error": "",
    }


def extract_from_manifest(manifest: dict[str, Any], max_chars: int) -> dict[str, Any]:
    for paper in manifest.get("papers", []):
        pdf_path = Path(paper["pdf_path"])
        try:
            paper.update(extract_pdf_text(pdf_path, max_chars=max_chars))
        except Exception as exc:
            paper.update(
                {
                    "title_guess": paper.get("stem", ""),
                    "text": "",
                    "text_chars": 0,
                    "text_truncated": False,
                    "status": "text_failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract text from PDFs listed in a manifest.")
    parser.add_argument("manifest", help="Input manifest JSON from scan_papers.py.")
    parser.add_argument("--output", required=True, help="Path to write extracted JSON.")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_TEXT_LIMIT)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = read_json(manifest_path)
    data = extract_from_manifest(manifest, max_chars=args.max_chars)
    output = Path(args.output).expanduser().resolve()
    write_json(output, data)
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

