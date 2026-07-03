#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_TEXT_LIMIT = 24000
DEFAULT_DEPS_TARGET = "/tmp/summary_papers_deps"

DEPENDENCIES = {
    "pypdf": {
        "package": "pypdf",
        "purpose": "PDF text extraction",
        "required_for": "text",
    },
    "fitz": {
        "package": "PyMuPDF",
        "purpose": "PDF image extraction and text fallback",
        "required_for": "markdown images",
    },
    "openpyxl": {
        "package": "openpyxl",
        "purpose": "Excel export",
        "required_for": "excel",
    },
}

COMMON_SUMMARY_FIELDS = [
    "研究现状",
    "motivation",
    "insight",
    "核心贡献",
    "method",
    "实验结论",
    "局限性",
    "其它",
]

FULL_SUMMARY_FIELDS = [
    "title",
    "authors",
    "year",
    "venue",
    "publish+time",
    "keywords",
    "github_url",
    "abstract_summary",
    *COMMON_SUMMARY_FIELDS,
    "zotero_link",
    "pdf_link",
    "源文件",
    "源路径",
    "source_file",
    "source_path",
    "relative_path",
    "title_author_image",
    "framework_image",
    "status",
    "error",
]

EXCEL_COLUMN_MAP = [
    ("源文件", ("源文件", "source_file")),
    ("源路径", ("源路径", "source_path")),
    ("title", ("title",)),
    ("publish+time", ("publish+time",)),
    ("keywords", ("keywords",)),
    ("研究现状", ("研究现状",)),
    ("motivation", ("motivation",)),
    ("insight", ("insight",)),
    ("核心贡献", ("核心贡献", "core_contributions")),
    ("method", ("method",)),
    ("实验结论", ("实验结论",)),
    ("局限性", ("局限性", "limitation")),
    ("其它", ("其它", "other")),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def filename_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_cell(value: object) -> str:
    if value is None:
        return ""
    return normalize_text(str(value))


def first_nonempty(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = clean_cell(row.get(key, ""))
        if value:
            return value
    return ""


def safe_stem(value: str, fallback: str = "paper") -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return stem or fallback


def iter_pdf_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() == ".pdf":
            yield path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sanitize_json_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.encode("utf-8", errors="replace").decode("utf-8")
    if isinstance(value, list):
        return [sanitize_json_value(item) for item in value]
    if isinstance(value, dict):
        return {sanitize_json_value(key): sanitize_json_value(item) for key, item in value.items()}
    return value


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_json_value(data), ensure_ascii=False, indent=2), encoding="utf-8")


def load_summary_rows(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    if isinstance(data, dict) and isinstance(data.get("papers"), list):
        rows = data["papers"]
    elif isinstance(data, list):
        rows = data
    else:
        raise SystemExit("Summary JSON must be a list or an object with a 'papers' list.")

    if not all(isinstance(row, dict) for row in rows):
        raise SystemExit("Each summary row must be a JSON object.")
    return rows


def guess_title(text: str, metadata_title: str | None, fallback: str) -> str:
    if metadata_title:
        cleaned = normalize_text(metadata_title)
        if cleaned and cleaned.lower() != "untitled":
            return cleaned

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:25]:
        if len(line) < 12 or len(line) > 300:
            continue
        if re.search(r"^arxiv|^abstract\b|^introduction\b", line, flags=re.I):
            continue
        if sum(ch.isalpha() for ch in line) < 8:
            continue
        return line
    return fallback


def blank_summary_from_inventory(paper: dict[str, Any]) -> dict[str, Any]:
    row = {field: "" for field in FULL_SUMMARY_FIELDS}
    row.update(
        {
            "title": paper.get("title_guess", "") or paper.get("stem", ""),
            "源文件": paper.get("filename", "") or paper.get("source_file", ""),
            "源路径": paper.get("pdf_path", "") or paper.get("source_path", ""),
            "source_file": paper.get("filename", "") or paper.get("source_file", ""),
            "source_path": paper.get("pdf_path", "") or paper.get("source_path", ""),
            "relative_path": paper.get("relative_path", ""),
            "pdf_link": paper.get("pdf_path", "") or paper.get("source_path", ""),
            "title_author_image": paper.get("title_author_image", ""),
            "framework_image": paper.get("framework_image", ""),
            "status": paper.get("status", "pending_summary"),
            "error": paper.get("error", ""),
        }
    )
    return row
