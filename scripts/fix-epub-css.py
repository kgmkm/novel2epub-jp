#!/usr/bin/env python3
"""
novel2epub-jp: epub-custom.css をEPUBの各XHTMLにリンクする後処理スクリプト

Vivliostyle CLIがEPUB出力時に `style` で指定したCSSをOPF manifestに登録するが
XHTMLの<head>に<link>を追加しない問題を修正する。

使用例:
  python3 scripts/fix-epub-css.py dist/妖狐は、嗤う-distribution.epub
  
オプション:
  --css-name epub-custom.css  (デフォルト) リンク対象CSSファイル名
  --dry-run                   書き込まずに確認のみ
"""

import sys
import argparse
import zipfile
import shutil
import tempfile
import pathlib
import re
from xml.etree import ElementTree as ET

def fix_epub(epub_path, css_name='epub-custom.css', dry_run=False):
    epub = pathlib.Path(epub_path)
    if not epub.is_file():
        print(f"ERROR: {epub} not found", file=sys.stderr)
        sys.exit(1)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.epub', dir=str(epub.parent))
    tmp_path = pathlib.Path(tmp_path)

    fixed_count = 0
    skipped_count = 0

    with zipfile.ZipFile(epub, 'r') as zin, zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.namelist():
            data = zin.read(item)

            # XHTMLファイルを検出してcssをリンク
            if item.endswith('.xhtml') or item.endswith('.html'):
                content = data.decode('utf-8', errors='ignore')

                # CSSパスを計算（XHTMLからの相対パス）
                # EPUB/index.xhtml → epub-custom.css (depth 0)
                # EPUB/novel/file.xhtml → ../epub-custom.css (depth 1)
                item_path = pathlib.PurePosixPath(item)
                # partsから「EPUB/」部分とファイル名を除いたディレクトリ深さを計算
                depth = len(item_path.parts) - 2  # -2: EPUB + filename
                if depth < 0:
                    depth = 0
                css_href = '../' * depth + css_name if depth > 0 else css_name

                # すでにリンク済みならスキップ
                if css_name in content:
                    skipped_count += 1
                else:
                    # <head>の末尾、</head>直前にリンクを挿入
                    link_tag = f'<link rel="stylesheet" type="text/css" href="{css_href}" />'
                    # </head> の直前に挿入
                    new_content = re.sub(
                        r'(\s*</head>)',
                        f'    {link_tag}\\1',
                        content,
                        count=1,
                    )
                    if new_content != content:
                        data = new_content.encode('utf-8')
                        fixed_count += 1
                        if not dry_run:
                            print(f"  ✓ {item}: added link to {css_href}")

            zout.writestr(item, data)

    if not dry_run:
        # バックアップ作成
        backup = epub.with_suffix(epub.suffix + '.bak')
        if backup.exists():
            backup.unlink()
        shutil.copy2(epub, backup)
        # 置き換え
        shutil.move(tmp_path, epub)
        print(f"Fixed {fixed_count} XHTML file(s) (skipped {skipped_count})")
        print(f"Backup saved to: {backup}")
    else:
        tmp_path.unlink(missing_ok=True)
        print(f"[DRY-RUN] Would fix {fixed_count}, skip {skipped_count}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fix CSS links in EPUB files')
    parser.add_argument('epub', help='EPUB file path')
    parser.add_argument('--css-name', default='epub-custom.css', help='CSS filename to link (default: epub-custom.css)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without modifying')
    args = parser.parse_args()
    fix_epub(args.epub, args.css_name, args.dry_run)
