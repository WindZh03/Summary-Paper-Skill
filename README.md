# Summary-Papers

`Summary-Papers` 是一个合并后的论文批量总结 skill：输入一个本地论文目录，递归处理目录及子目录下所有 PDF，先生成完整结构化 JSON，再导出一个 Markdown 文件、一个单 sheet Excel，或两者同时输出。

它合并了原先两个方向：

- Obsidian/Markdown：保留论文标题作者截图、method/framework 图和完整论文笔记。
- Paper2Excel：保留单表 Excel、固定字段和溯源列。

## 功能

- 递归扫描目录下所有 PDF
- 提取 PDF 文本
- 为 Markdown 尝试提取：
  - 标题/作者截图
  - 方法/framework/pipeline 图
- 保存的图片文件名包含运行日期和时间，例如 `20260701_143015_paper_001_xxx__title.png`
- 生成每篇论文的完整结构化 JSON
- 导出一个 Markdown 文件
- 导出一个单 sheet Excel 文件
- 中间状态文件默认放在 `.summary-papers/` 隐藏目录
- Excel 保留 `源文件`、`源路径` 溯源列

## 输出语言和字段

总结内容统一使用中文。`title`、`publish+time` 保持论文中的英文原文。`keywords` 优先使用论文明确给出的英文关键词；如果论文没有明确关键词，则根据论文内容自己总结 3 个英文关键词或短语，并用分号分隔。

Markdown 和 Excel 共用以下公共字段，并使用同一套字数要求：

- `研究现状`：100 字左右
- `motivation`：100 字左右
- `insight`：100 字左右
- `核心贡献`：200 字左右
- `method`：500 字左右
- `实验结论`：200 字左右
- `局限性`：200 字左右
- `其它`：200 字左右

Markdown 输出字段：标题、作者、年份、发表期刊/会议、关键词、GitHub、PDF/Zotero 链接、图片，以及上述公共字段。

Excel 输出字段：`源文件`、`源路径`、`title`、`publish+time`、`keywords`，以及上述公共字段。

## 项目结构

```text
Summary-Papers/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── framework_selection.md
│   └── markdown_template.md
└── scripts/
    ├── check_deps.py
    ├── extract_pdf_assets.py
    ├── extract_text.py
    ├── export_excel.py
    ├── export_markdown.py
    ├── paper_summary_cli.py
    ├── paper_summary_lib.py
    └── scan_papers.py
```

## 依赖

- `pypdf`：PDF 文本提取
- `PyMuPDF` / `fitz`：图片截图和 framework 图提取
- `openpyxl`：Excel 输出

检查依赖：

```bash
python3 scripts/check_deps.py check
```

该命令会同时检查当前 Python 环境和默认依赖目录 `/tmp/summary_papers_deps`。如果依赖只安装在默认目录中，后续命令需要带上 `PYTHONPATH=/tmp/summary_papers_deps`。

安装缺失依赖到临时目录：

```bash
python3 scripts/check_deps.py install --target /tmp/summary_papers_deps
```

之后使用：

```bash
PYTHONPATH=/tmp/summary_papers_deps python3 scripts/paper_summary_cli.py ...
```

## 使用流程

### 1. 准备运行

```bash
python3 scripts/paper_summary_cli.py prepare "/path/to/papers" --output-root "/path/to/output" --assets
```

如果只输出 Excel，可以不加 `--assets`：

```bash
python3 scripts/paper_summary_cli.py prepare "/path/to/papers" --output-root "/path/to/output"
```

该步骤会生成：

- `.summary-papers/manifest.json`
- `.summary-papers/extracted_text.json`
- `.summary-papers/run_report.json`
- `.summary-papers/summary_draft.json`
- `assets/`，仅在加 `--assets` 时生成

### 2. 填写完整结构化总结

Codex 读取 `.summary-papers/extracted_text.json`，按 `SKILL.md` 的字段要求为每篇论文生成完整 JSON。通常可以基于 `.summary-papers/summary_draft.json` 填写。

### 3. 导出

导出 Markdown：

```bash
python3 scripts/paper_summary_cli.py export "/path/to/output/completed_summaries.json" --output-root "/path/to/output" --output markdown
```

导出 Excel：

```bash
python3 scripts/paper_summary_cli.py export "/path/to/output/completed_summaries.json" --output-root "/path/to/output" --output excel
```

同时导出：

```bash
python3 scripts/paper_summary_cli.py export "/path/to/output/completed_summaries.json" --output-root "/path/to/output" --output all
```

## 输出规则

Markdown：

- 一个 `.md` 文件包含所有论文
- 包含图片
- 字段更完整，适合 Obsidian 阅读

Excel：

- 一个 `.xlsx`
- 一个 sheet：`papers`
- 不包含图片
- 保留溯源列
- 与 Markdown 使用相同公共字段和字数要求，便于横向比较

默认输出结构：

```text
output_root/
├── paper_summaries.md
├── paper_summaries.xlsx
├── assets/
└── .summary-papers/
    ├── manifest.json
    ├── extracted_text.json
    ├── run_report.json
    └── summary_draft.json
```

## 当前限制

- 不自动 OCR 扫描版 PDF
- 不默认联网补全元数据
- 不直接连接 Zotero
- 结构化总结仍由 Codex/LLM 根据提取文本生成
