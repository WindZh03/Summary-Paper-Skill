#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from extract_text import extract_from_manifest
from export_excel import export_excel
from export_markdown import export_markdown
from paper_summary_lib import (
    DEFAULT_TEXT_LIMIT,
    blank_summary_from_inventory,
    read_json,
    utc_now_iso,
    write_json,
)
from scan_papers import scan_papers


def prepare_run(args: argparse.Namespace) -> int:
    paper_root = Path(args.paper_root).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    work_root = output_root / ".summary-papers"
    work_root.mkdir(parents=True, exist_ok=True)

    manifest = scan_papers(paper_root)
    manifest["output_root"] = str(output_root)
    manifest["work_root"] = str(work_root)
    manifest["run_status"] = "scanned"

    manifest_path = work_root / "manifest.json"
    write_json(manifest_path, manifest)

    manifest = extract_from_manifest(manifest, max_chars=args.max_chars)
    text_path = work_root / "extracted_text.json"
    write_json(text_path, manifest)

    if args.assets:
        from extract_pdf_assets import extract_assets_from_manifest

        assets_root = output_root / "assets"
        manifest = extract_assets_from_manifest(manifest, assets_root=assets_root, max_pages=args.max_pages)

    manifest["run_status"] = "prepared_for_summary"
    manifest["updated_at"] = utc_now_iso()
    run_report_path = work_root / "run_report.json"
    write_json(run_report_path, manifest)

    drafts = [blank_summary_from_inventory(paper) for paper in manifest.get("papers", [])]
    draft_path = work_root / "summary_draft.json"
    write_json(
        draft_path,
        {
            "generated_at": utc_now_iso(),
            "paper_root": str(paper_root),
            "papers": drafts,
        },
    )

    print(f"manifest: {manifest_path}")
    print(f"extracted_text: {text_path}")
    print(f"run_report: {run_report_path}")
    print(f"summary_draft: {draft_path}")
    return 0


def export_outputs(args: argparse.Namespace) -> int:
    summary_json = Path(args.summary_json).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    output_mode = args.output
    if output_mode in {"markdown", "all"}:
        markdown_path = Path(args.markdown_output).expanduser().resolve() if args.markdown_output else output_root / "paper_summaries.md"
        export_markdown(summary_json, markdown_path, title=args.title)
        print(f"markdown: {markdown_path}")

    if output_mode in {"excel", "all"}:
        excel_path = Path(args.excel_output).expanduser().resolve() if args.excel_output else output_root / "paper_summaries.xlsx"
        export_excel(summary_json, excel_path)
        print(f"excel: {excel_path}")

    return 0


def run_all(args: argparse.Namespace) -> int:
    prepare_run(args)
    if not args.summary_json:
        print()
        print("Prepare step complete. Fill .summary-papers/summary_draft.json with full structured summaries,")
        print("then run the 'export' command to generate Markdown, Excel, or both.")
        return 0

    export_args = argparse.Namespace(
        summary_json=args.summary_json,
        output_root=args.output_root,
        output=args.output,
        markdown_output=args.markdown_output,
        excel_output=args.excel_output,
        title=args.title,
    )
    return export_outputs(export_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summary-Papers helper CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Scan PDFs, extract text, optionally extract Markdown assets, and write run reports.",
    )
    prepare.add_argument("paper_root")
    prepare.add_argument("--output-root", required=True)
    prepare.add_argument("--max-chars", type=int, default=DEFAULT_TEXT_LIMIT)
    prepare.add_argument("--max-pages", type=int, default=12)
    prepare.add_argument("--assets", action="store_true")
    prepare.set_defaults(func=prepare_run)

    export = subparsers.add_parser("export", help="Export completed structured summaries.")
    export.add_argument("summary_json")
    export.add_argument("--output-root", required=True)
    export.add_argument("--output", choices=["markdown", "excel", "all"], default="all")
    export.add_argument("--markdown-output", default="")
    export.add_argument("--excel-output", default="")
    export.add_argument("--title", default="Paper Summaries")
    export.set_defaults(func=export_outputs)

    run = subparsers.add_parser("run", help="Prepare a run and optionally export a provided summary JSON.")
    run.add_argument("paper_root")
    run.add_argument("--output-root", required=True)
    run.add_argument("--output", choices=["markdown", "excel", "all"], default="all")
    run.add_argument("--summary-json", default="")
    run.add_argument("--markdown-output", default="")
    run.add_argument("--excel-output", default="")
    run.add_argument("--title", default="Paper Summaries")
    run.add_argument("--max-chars", type=int, default=DEFAULT_TEXT_LIMIT)
    run.add_argument("--max-pages", type=int, default=12)
    run.add_argument("--assets", action="store_true")
    run.set_defaults(func=run_all)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
