#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from paper_summary_lib import clean_cell, first_nonempty, load_summary_rows


def rel_link(path_value: str, markdown_output: Path) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    try:
        return str(path.resolve().relative_to(markdown_output.parent.resolve()))
    except ValueError:
        try:
            return str(path.resolve().relative_to(markdown_output.parent.resolve()))
        except Exception:
            return str(path_value)


def image_block(label: str, image_path: str, markdown_output: Path) -> str:
    if not image_path:
        return ""
    link = rel_link(image_path, markdown_output)
    return f"![{label}]({link})\n"


def bullet(name: str, value: Any, default: str = "未找到") -> str:
    text = clean_cell(value)
    if not text:
        text = default
    return f"- {name}: {text}"


def section(title: str, value: Any) -> str:
    text = clean_cell(value) or "未找到"
    return f"#### {title}\n{text}\n"


def list_section(title: str, value: Any) -> str:
    if isinstance(value, list):
        lines = [f"- {clean_cell(item)}" for item in value if clean_cell(item)]
        body = "\n".join(lines) if lines else "未找到"
    else:
        body = clean_cell(value) or "未找到"
    return f"#### {title}\n{body}\n"


def render_paper(row: dict[str, Any], index: int, markdown_output: Path) -> str:
    title = clean_cell(row.get("title")) or first_nonempty(row, "源文件", "source_file") or f"Paper {index}"
    parts = [f"### {index}. {title}\n"]
    parts.extend(
        [
            bullet("作者", row.get("authors")),
            bullet("年份", row.get("year")),
            bullet("发表期刊/会议", row.get("venue") or row.get("publish+time")),
            bullet("关键词", row.get("keywords")),
            bullet("GitHub", row.get("github_url")),
            bullet("PDF", row.get("pdf_link") or first_nonempty(row, "源路径", "source_path"), default="未提供"),
            bullet("Zotero", row.get("zotero_link"), default="未提供"),
        ]
    )
    parts.append("")

    title_image = image_block("Title and authors", clean_cell(row.get("title_author_image")), markdown_output)
    if title_image:
        parts.append(title_image)
    framework_image = image_block(
        "Method pipeline / overall framework",
        clean_cell(row.get("framework_image")),
        markdown_output,
    )
    if framework_image:
        parts.append(framework_image)

    parts.extend(
        [
            section("研究现状", row.get("研究现状")),
            section("Motivation", row.get("motivation")),
            section("Insight", row.get("insight")),
            list_section("核心贡献", row.get("核心贡献") or row.get("core_contributions")),
            section("方法", row.get("method")),
            section("实验结论", row.get("实验结论")),
            section("局限性", row.get("局限性") or row.get("limitation")),
            section("其它", row.get("其它") or row.get("other")),
        ]
    )
    return "\n".join(parts).rstrip() + "\n"


def export_markdown(summary_json: Path, output: Path, title: str = "Paper Summaries") -> None:
    rows = load_summary_rows(summary_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = [
        "---",
        f"title: {title}",
        f"paper_count: {len(rows)}",
        "generated_by: Summary-Papers",
        "---",
        "",
        f"# {title}",
        "",
        "## Overview",
        f"- Total papers: {len(rows)}",
        "",
        "## Papers",
        "",
    ]
    body = [render_paper(row, index, output) for index, row in enumerate(rows, start=1)]
    output.write_text("\n".join(frontmatter + body), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export structured paper summaries to Markdown.")
    parser.add_argument("summary_json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Paper Summaries")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    export_markdown(Path(args.summary_json).expanduser().resolve(), output, title=args.title)
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
