---
name: Summary-Papers
description: Recursively process all PDF papers under one local folder, extract text and optional Markdown images, summarize every paper into a complete structured JSON schema, then export one Markdown file, one single-sheet Excel workbook, or both. Use when the user provides a paper folder and asks to batch summarize PDFs into Markdown or Excel.
---

# Summary-Papers

Use this skill when the user wants to batch-read PDF papers from one local folder and export paper summaries as Markdown, Excel, or both.

## Required user input

Ask for or confirm these values before doing any work:

```text
paper_root: /absolute/path/to/paper/folder
output_root: /absolute/path/to/output/folder
output: markdown | excel | all
```

Interpret the input strictly:
- `paper_root` is one local folder.
- Recursively scan `paper_root` and all subfolders for `.pdf` files.
- Ignore non-PDF files.
- `output_root` is where final Markdown, Excel, and Markdown assets are written.
- Intermediate JSON and reports are written under `<output_root>/.summary-papers/`.
- `output` controls final artifacts:
  - `markdown`: write one Markdown file.
  - `excel`: write one single-sheet `.xlsx` file.
  - `all`: write both.

## Important environment rule

Only claim that files were written when the runtime truly has filesystem access to the requested local paths.
- If the environment can access the local paths, write files directly.
- If the environment cannot access the user's local filesystem, do not pretend the write succeeded. Explain the limitation and ask for accessible files or generate content as a deliverable.

## Workflow

Follow this sequence.

1. Validate absolute `paper_root` and `output_root`.
2. Run dependency check:

```bash
python3 scripts/check_deps.py check
```

This checks both the current Python environment and the default dependency target `/tmp/summary_papers_deps`.

3. If dependencies are missing and the user approves installation, install them into a temporary target:

```bash
python3 scripts/check_deps.py install --target /tmp/summary_papers_deps
```

Then invoke later commands with:

```bash
PYTHONPATH=/tmp/summary_papers_deps python3 scripts/paper_summary_cli.py ...
```

4. Prepare the run:
   - always scan recursively;
   - extract text for every PDF;
   - extract Markdown image assets only when output is `markdown` or `all`;
   - write `manifest.json`, `extracted_text.json`, `run_report.json`, and `summary_draft.json` under `<output_root>/.summary-papers/`.

```bash
python3 scripts/paper_summary_cli.py prepare "/path/to/papers" --output-root "/path/to/output" --assets
```

Omit `--assets` when output is `excel`.

5. Read `<output_root>/.summary-papers/extracted_text.json` and summarize every paper into the complete structured JSON schema below.
6. Save the completed structured summaries as JSON, usually based on `<output_root>/.summary-papers/summary_draft.json`.
7. Export the final artifact:

```bash
python3 scripts/paper_summary_cli.py export "/path/to/output/completed_summaries.json" --output-root "/path/to/output" --output all
```

## Complete Structured JSON Schema

Create one object per paper. Preserve source fields and include these keys:

- `title`
- `authors`
- `year`
- `venue`
- `publish+time`
- `keywords`
- `github_url`
- `研究现状`
- `motivation`
- `insight`
- `核心贡献`
- `method`
- `实验结论`
- `局限性`
- `其它`
- `zotero_link`
- `pdf_link`
- `源文件`
- `源路径`
- `relative_path`
- `title_author_image`
- `framework_image`
- `status`
- `error`

Use empty strings for genuinely unavailable fields unless the Markdown field rule below says to render `未找到` or `未提供`.

## Language and Common Field Rules

Summary fields must be written in Chinese. Keep `title` and `publish+time` in the original English when the PDF provides English metadata. For `keywords`, use the paper's original English keywords when explicitly provided; if the paper has no explicit keywords, summarize exactly three English keywords or short phrases from the paper content.

Markdown and Excel share the same common summary fields and the same target lengths:

- `研究现状`: about 100 Chinese characters.
- `motivation`: about 100 Chinese characters.
- `insight`: about 100 Chinese characters.
- `核心贡献`: about 200 Chinese characters.
- `method`: about 500 Chinese characters.
- `实验结论`: about 200 Chinese characters.
- `局限性`: about 200 Chinese characters.
- `其它`: about 200 Chinese characters.

## Excel Output Rules

Excel is always one workbook with one sheet named `papers`.

Columns:

- `源文件`
- `源路径`
- `title`
- `publish+time`
- `keywords`
- `研究现状`
- `motivation`
- `insight`
- `核心贡献`
- `method`
- `实验结论`
- `局限性`
- `其它`

Field rules:
- `源文件` and `源路径` are required traceability columns.
- `title`: English paper title from the PDF when available.
- `publish+time`: only information stated in the PDF. Prefer `Venue Year`, for example `AAAI 2024`.
- `keywords`: use explicit English keywords from the paper when available. If the paper has no explicit keywords, summarize exactly three English keywords or short phrases yourself. Separate keywords with semicolons.
- Common summary fields must follow the target lengths in `Language and Common Field Rules`.

Do not embed images in Excel. Do not add image-path columns unless the user explicitly asks.

## Markdown Output Rules

Markdown is always one `.md` file containing all processed papers.

For each paper, include:
- 标题
- 作者
- 年份
- 发表的期刊/会议
- keywords
- GitHub 链接
- PDF 链接
- Zotero 链接
- title/authors image if extracted
- method/framework image if extracted
- 研究现状
- motivation
- insight
- 核心贡献
- 方法
- 实验结论
- 局限性
- 其它

Use `未找到` for unavailable bibliographic or content fields. Use `未提供` for Zotero/PDF links only when no useful link/path is available.

## Image Rules

Only extract and use images for Markdown output.
- Always include the title/authors image if extraction succeeded.
- Include the method/framework image only if extraction succeeded and looks plausibly relevant to the paper's method.
- Do not fabricate or hallucinate an image.
- If a framework image is missing, omit that image block.
- Prefer one framework image per paper.
- When uncertain, prefer omitting the framework image over using a likely wrong teaser, result chart, or first-page illustration.

Image filenames must be ASCII-safe and manifest-driven:

```text
assets/20260701_143015_paper_001_safe_stem__title.png
assets/20260701_143015_paper_001_safe_stem__framework.png
```

The leading `YYYYMMDD_HHMMSS` timestamp is generated at scan time. Do not use arbitrary paper titles or original Unicode filenames as generated image filenames.

## Run Reports

Every run must preserve machine-readable status files under `<output_root>/.summary-papers/`:

- `manifest.json`: recursive PDF inventory.
- `extracted_text.json`: inventory plus extracted text and title guesses.
- `run_report.json`: per-paper status, errors, text extraction status, and asset extraction status.
- `summary_draft.json`: blank complete-schema draft that can be filled by the agent.

Keep final user-facing outputs in `output_root`:

- `paper_summaries.md`
- `paper_summaries.xlsx`
- `assets/`

For each paper, record failures conservatively instead of stopping the whole batch whenever possible.

## Quality Bar

- Base every field only on the PDF itself unless the user explicitly asks for external enrichment.
- Do not use web search by default.
- Prefer empty strings over guesses in structured JSON.
- Do not copy long sentences from the paper. Compress into concise, high-density summaries.
- Keep Markdown and Excel common summary fields aligned in content and target length.
- Keep the output language Chinese except `title`, `publish+time`, and `keywords`. Preserve English originals when available; for missing keywords, write exactly three English keywords or short phrases yourself.
- Mention uncertainty when metadata, text extraction, or figure extraction is ambiguous.

## Example

```text
请使用 Summary-Papers 处理这个目录，递归总结所有 PDF，并同时输出 Markdown 和 Excel。

paper_root: /Users/me/Documents/papers
output_root: /Users/me/Documents/paper-output
output: all
```
