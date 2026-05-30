#!/usr/bin/env python3
"""
build-epub.py: Markdown原稿 → しっぽり明朝EPUB変換（JLREQ前処理付き）

方式:
  1. novel/*.md → VFM で HTML 化
  2. jlreq_preprocess で JLREQ 準拠処理
  3. 完全な XHTML ファイル生成
  4. Vivliostyle CLI で EPUB 生成
  5. fix-epub-css.py で CSS リンク修正

前提:
  - Node.js + @vivliostyle/vfm
  - Vivliostyle CLI
  - novel/*.md（VFM記法ルビ {漢字|よみ}）
  - novel/image/（挿絵画像）

使用例:
  python3 scripts/build-epub.py --project-dir . --output dist/book.epub
"""

import sys
import os
import argparse
import subprocess
import pathlib
import shutil
import re
import glob

# jlreq_preprocess をインポート（同ディレクトリから）
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from jlreq_preprocess import preprocess_html

# ─── CLI ──────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Build EPUB with JLREQ preprocessing")
parser.add_argument("--project-dir", default=".", help="Project root")
parser.add_argument("--output", default=None, help="Output EPUB path")
parser.add_argument("--novel-dir", default="novel", help="Novel dir name")
parser.add_argument("--title", default=None, help="Book title")
parser.add_argument("--author", default=None, help="Author name")
parser.add_argument("--keep-workdir", action="store_true", help="Keep .epub-build/ temp directory")
args = parser.parse_args()

project = pathlib.Path(args.project_dir).resolve()
novel_dir = project / args.novel_dir

# タイトル・著者の取得（config.js優先→fallback→ファイル名）
config_js = project / "vivliostyle.config.js"
title = args.title
author = args.author

if not title or not author:
    if config_js.is_file():
        config_content = config_js.read_text(encoding='utf-8')
        if not title:
            m = re.search(r"title:\s*'([^']+)'", config_content)
            if m:
                title = m.group(1)
        if not author:
            m = re.search(r"author:\s*'([^']+)'", config_content)
            if m:
                author = m.group(1)

if not title:
    title = project.name
if not author:
    author = "Unknown"

output_path = pathlib.Path(args.output) if args.output else project / "dist" / f"{title}.epub"
output_path = output_path.resolve()
output_path.parent.mkdir(parents=True, exist_ok=True)

# 作業ディレクトリ
work_dir = project / ".epub-build"
work_dir.mkdir(exist_ok=True)
work_novel_dir = work_dir / "novel"
work_novel_dir.mkdir(exist_ok=True)

print(f"Project: {project}")
print(f"Title: {title}")
print(f"Author: {author}")
print(f"Output: {output_path}")
print(f"Work dir: {work_dir}")

# ─── MD ファイル取得 ────────────────────────────────────────────────

md_files = sorted(glob.glob(str(novel_dir / "*.md")))
if not md_files:
    print(f"ERROR: No .md files in {novel_dir}", file=sys.stderr)
    sys.exit(1)

print(f"\nFound {len(md_files)} markdown file(s)")

# ─── MD → VFM → JLREQ → XHTML ────────────────────────────────────

xhtml_files = []
for i, md in enumerate(md_files):
    md_path = pathlib.Path(md)
    print(f"\n[{i+1}/{len(md_files)}] {md_path.name}")

    # VFM変換（partial=true：body 内のみ）
    print(f"  VFM...")
    result = subprocess.run(
        ["npx", "--yes", "@vivliostyle/vfm", str(md_path),
         "--partial", "--language", "ja", "--hardLineBreaks"],
        capture_output=True, text=True, cwd=str(project), timeout=60
    )
    if result.returncode != 0:
        print(f"  WARNING: VFM error: {result.stderr[:200]}", file=sys.stderr)
        body_html = md_path.read_text(encoding='utf-8')  # fallback: そのまま使用
    else:
        body_html = result.stdout

    # JLREQ前処理（XHTMLモード有効）
    print(f"  JLREQ preprocess...")
    body_html = preprocess_html(body_html, xhtml_mode=True)

    # タイトル抽出（最初の h1 or ファイル名）
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', body_html, re.DOTALL)
    if h1_match:
        chapter_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
    else:
        chapter_title = md_path.stem

    # 完全なXHTMLドキュメント生成
    xhtml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <meta charset="utf-8" />
  <title>{chapter_title}</title>
  <link rel="stylesheet" type="text/css" href="epub-custom.css" />
</head>
<body>
{body_html}
</body>
</html>
"""

    # 作業ディレクトリに出力
    xhtml_name = md_path.stem + ".xhtml"
    xhtml_path = work_novel_dir / xhtml_name
    xhtml_path.write_text(xhtml_content, encoding='utf-8')
    xhtml_files.append((xhtml_name, chapter_title))
    print(f"  -> {xhtml_name}")

# ─── 画像コピー ──────────────────────────────────────────────────

image_dir = novel_dir / "image"
if image_dir.is_dir():
    work_image_dir = work_novel_dir / "image"
    if work_image_dirs_exists := work_image_dir.exists():
        shutil.rmtree(work_image_dir)
    shutil.copytree(image_dir, work_image_dir)
    img_count = len(list(work_image_dir.glob('*')))
    print(f"\nCopied {img_count} image(s) to {work_image_dir}")

# ─── epub-custom.css コピー ─────────────────────────────────────

# テンプレートのCSSを作業ディレクトリにコピー
template_css = SCRIPT_DIR.parent / "templates" / "epub-custom.css"
if template_css.is_file():
    shutil.copy2(template_css, work_dir)
    print(f"Copied {template_css.name} to {work_dir}")

# no-indent, tcy クラスのスタイルを追加
custom_css_path = work_dir / "epub-custom.css"
extra_css = """

/* ── Added by build-epub.py ────────────────────────────────── */

/* JLREQ 3.1.5: 始め括弧類の行頭字下げ禁止 */
p.no-indent {
  text-indent: 0;
  padding-left: 1em;
  text-indent: -1em;
}

/* JLREQ 3.2.4: 縦中横（2桁以上の半角数字） */
.tcy {
  -epub-text-combine: horizontal;
  text-combine-upright: all;
}
"""
with open(custom_css_path, 'a', encoding='utf-8') as f:
    f.write(extra_css)
print("Appended JLREQ CSS rules to epub-custom.css")

# 目次(index)XHTML生成
toc_items = ""
for xhtml_name, chapter_title in xhtml_files:
    toc_items += f'    <li><a href="novel/{xhtml_name}">{chapter_title}</a></li>\n'

index_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="epub-custom.css" />
</head>
<body>
<h1>{title}</h1>
<nav id="toc" role="doc-toc" epub:type="toc">
  <h2>目次</h2>
  <ol>
{toc_items}  </ol>
</nav>
</body>
</html>
"""

(work_dir / "index.xhtml").write_text(index_xhtml, encoding='utf-8')
print("Generated index.xhtml (Table of Contents)")

# ─── vivliostyle.config.js 生成（作業ディレクトリ用） ──────────────

def json_repr(s):
    """Simple JS-safe string representation"""
    return "'" + s.replace("'", "\\'").replace("\\", "\\\\") + "'"

entry_list = ["'index.xhtml'"]
for xhtml_name, _ in xhtml_files:
    entry_list.append(f"'novel/{xhtml_name}'")
entry_str = ",\n    ".join(entry_list)

vivliostyle_config = f"""/**
 * Generated by build-epub.py (temporary config for EPUB build)
 */
module.exports = {{
  title: {json_repr(title)},
  author: {json_repr(author)},
  language: 'ja',
  readingProgression: 'rtl',

  entry: [
    {entry_str},
  ],

  output: {{
    path: 'dist/epub-output.epub',
    format: 'epub',
  }},

  theme: '@vivliostyle/theme-epub3j',
  style: 'epub-custom.css',
  toc: true,

  copyAsset: {{
    includes: ['novel/image/**'],
    excludes: ['.git/**', 'node_modules/**', 'dist/**'],
  }},
}};
"""

config_path = work_dir / "vivliostyle.config.js"
config_path.write_text(vivliostyle_config, encoding='utf-8')
print(f"\nGenerated vivliostyle.config.js")

# ─── dist/ ディレクトリ確保 ─────────────────────────────────────

(work_dir / "dist").mkdir(exist_ok=True)

# ─── Vivliostyle CLI で EPUB ビルド ──────────────────────────────

print(f"\n{'='*60}")
print("Building EPUB with Vivliostyle CLI...")
print(f"{'='*60}")

build_result = subprocess.run(
    ["vivliostyle", "build", "--config", str(config_path)],
    cwd=str(work_dir),
    timeout=600,
)

if build_result.returncode != 0:
    print(f"\nERROR: Vivliostyle build failed (exit code {build_result.returncode})", file=sys.stderr)
    sys.exit(build_result.returncode)

# ─── 出力ファイル移動 ─────────────────────────────────────────

built_epub = work_dir / "dist" / "epub-output.epub"
if not built_epub.is_file():
    print(f"ERROR: EPUB not generated: {built_epub}", file=sys.stderr)
    sys.exit(1)

# 目的の場所に移動
shutil.move(str(built_epub), str(output_path))
print(f"\n{'='*60}")
print(f"✅ EPUB built successfully!")
print(f"   Output: {output_path}")
print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.1f}MB")

# ─── 後処理: fix-epub-css.py 実行 ─────────────────────────────

print(f"\nRunning post-processing (CSS link fix)...")
fix_script = SCRIPT_DIR / "fix-epub-css.py"
if fix_script.is_file():
    fix_result = subprocess.run(
        [sys.executable, str(fix_script), str(output_path)],
        cwd=str(project),
        timeout=60,
    )
    if fix_result.returncode != 0:
        print(f"  WARNING: CSS fix returned error {fix_result.returncode}")
else:
    print(f"  Note: fix-epub-css.py not found (skipping)")

# ─── 作業ディレクトリ クリーンアップ ────────────────────────

if not args.keep_workdir:
    shutil.rmtree(work_dir)
    print(f"\nCleaned up {work_dir}")
else:
    print(f"\nKept work dir: {work_dir}")

print(f"\n{'='*60}")
print("Done!")
print(f"{'='*60}")
