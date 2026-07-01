#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from paper_summary_lib import filename_timestamp, iter_pdf_files, safe_stem, utc_now_iso, write_json


def scan_papers(paper_root: Path) -> dict:
    paper_root = paper_root.expanduser().resolve()
    if not paper_root.exists() or not paper_root.is_dir():
        raise SystemExit(f"paper_root not found or not a directory: {paper_root}")

    run_timestamp = filename_timestamp()
    papers = []
    for index, pdf in enumerate(iter_pdf_files(paper_root), start=1):
        rel = pdf.relative_to(paper_root)
        asset_basename = f"{run_timestamp}_paper_{index:03d}_{safe_stem(pdf.stem, fallback='pdf')}"
        papers.append(
            {
                "paper_index": index,
                "pdf_path": str(pdf),
                "relative_path": str(rel),
                "filename": pdf.name,
                "stem": pdf.stem,
                "asset_basename": asset_basename,
                "safe_title_image_name": f"{asset_basename}__title.png",
                "safe_framework_image_name": f"{asset_basename}__framework.png",
                "status": "discovered",
                "error": "",
            }
        )

    return {
        "generated_at": utc_now_iso(),
        "asset_timestamp": run_timestamp,
        "paper_root": str(paper_root),
        "pdf_count": len(papers),
        "papers": papers,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recursively scan a folder for PDF papers.")
    parser.add_argument("paper_root")
    parser.add_argument("--manifest", default="", help="Path to write manifest JSON.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    data = scan_papers(Path(args.paper_root))
    if args.manifest:
        output = Path(args.manifest).expanduser().resolve()
        write_json(output, data)
        print(str(output))
    else:
        import json

        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
