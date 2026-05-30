#!/usr/bin/env python3
"""
novel2epub-jp: Vivliostyle CLI出力後のEPUBに対するJLREQ後処理

Vivliostyle CLIでEPUBを生成した後に実行する。
XHTMLに対して以下を一括実行:
  1. 行頭が始め括弧類の段落に class="no-indent" を付与
  2. 半角アラビア数字を縦中横(tcy)でラップ
  3. JLREQ用CSSルールを <style> タグに追記

使用例:
  python3 scripts/jlreq_postprocess.py dist/output.epub
"""

import sys
import argparse
import zipfile
import shutil
import tempfile
import pathlib
import re

# JLREQ 3.1.5: 行頭配置時に字下げ対象外とする始め括弧類
OPENING_BRACKETS = set(
    '「『（〈《【〔〖｛［'
    '〝＂\'\"'
    '‘“'
)

# JLREQ 3.2.4: 縦中横対象の追加ルール
# 半角アラビア数字1〜2桁（前後が非数字）を縦中横化
# 注: \b は日本語文字（\w）との間で機能しないため、明示的に \d で判定
TCY_PATTERN = re.compile(r'(?<!\d)(\d{1,2})(?!\d)')


def add_no_indent_classes(xhtml):
    """段落開始文字が始め括弧類の場合、no-indentクラスを追加"""
    def process_p(match):
        tag_open = match.group(1)  # <p ... >
        inner = match.group(2)     # 中身
        tag_close = match.group(3) # </p>

        # テキストのみ抽出（タグ除去）して先頭文字を確認
        text_only = re.sub(r'<[^>]+>', '', inner).strip()
        if text_only and text_only[0] in OPENING_BRACKETS:
            # class属性がある場合は追記、ない場合は追加
            if 'class=' in tag_open:
                tag_open = re.sub(
                    r'class="([^"]*)"',
                    r'class="\1 no-indent"',
                    tag_open,
                )
            else:
                tag_open = tag_open.replace('<p', '<p class="no-indent"', 1)

        return tag_open + inner + tag_close

    return re.sub(
        r'(<p[^>]*>)(.*?)(</p>)',
        process_p,
        xhtml,
        flags=re.DOTALL,
    )


def add_tate_chu_yoko(xhtml):
    """半角アラビア数字を縦中横 span class="tcy" でラップ"""
    def process_element(match):
        tag_open = match.group(1)   # <p ...>
        # group(2) = tag name (for backreference)
        inner = match.group(3)
        tag_close = match.group(4)  # </p>

        # タグを一時的にプレースホルダに置換してテキスト部分のみ処理
        tokens = re.split(r'(<[^>]+>)', inner)
        new_tokens = []
        for token in tokens:
            if token.startswith('<'):
                new_tokens.append(token)
            else:
                new_tokens.append(
                    TCY_PATTERN.sub(r'<span class="tcy">\1</span>', token)
                )
        return tag_open + ''.join(new_tokens) + tag_close

    # p, h1-h6, li のすべてに適用 (backreference \2 で同一タグマッチ)
    return re.sub(
        r'(<(p|h[1-6]|li)[^>]*>)(.*?)(</\2>)',
        process_element,
        xhtml,
        flags=re.DOTALL,
    )


# CSSルールは外部ファイルから読み込む
JLREQ_CSS_PATH = pathlib.Path(__file__).parent / 'jlreq_epub_rules.css'


def add_vrtl_class(xhtml):
    """<html>/<body> タグに class="vrtl" を追加（縦書き有効化）

    @vivliostyle/theme-epub3j は .vrtl クラスで縦書きを制御するが、
    Vivliostyle CLIのEPUB出力ではbodyにclassが付与されない。
    """
    def add_class_attr(tag_str, cls='vrtl'):
        if f'class="{cls}"' in tag_str or f"class='{cls}'" in tag_str:
            return tag_str
        if 'class="' in tag_str:
            return tag_str.replace('class="', f'class="{cls} ')
        # class属性なし → 追加（>の直前）
        return tag_str[:-1] + f' class="{cls}">'

    xhtml = re.sub(r'<html[^>]*>', lambda m: add_class_attr(m.group()), xhtml, count=1)
    xhtml = re.sub(r'<body[^>]*>', lambda m: add_class_attr(m.group()), xhtml, count=1)
    return xhtml


def inject_jlreq_css(xhtml):
    """XHTMLの <style> タグ末尾にJLREQ CSSルールを追記"""
    if not JLREQ_CSS_PATH.is_file():
        print(f"  WARNING: {JLREQ_CSS_PATH} not found, skipping CSS injection")
        return xhtml

    css_rules = JLREQ_CSS_PATH.read_text(encoding='utf-8')

    # <style>...</style> を探す（最後のものに追記）
    style_pattern = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.DOTALL)
    matches = list(style_pattern.finditer(xhtml))

    if matches:
        # 最後の <style> タグに追記
        last_match = matches[-1]
        before = xhtml[:last_match.end(2)]
        after = xhtml[last_match.start(3):]
        return before + '\n/* JLREQ rules (injected by jlreq_postprocess.py) */\n' + css_rules + '\n' + after
    else:
        # <style> がなければ </head> の直前に新規追加
        return re.sub(
            r'(</head>)',
            f'<style type="text/css">\n{css_rules}\n</style>\n\\1',
            xhtml,
            count=1,
        )


def process_epub(epub_path, dry_run=False):
    epub = pathlib.Path(epub_path)
    if not epub.is_file():
        print(f"ERROR: {epub} not found", file=sys.stderr)
        sys.exit(1)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.epub', dir=str(epub.parent))
    tmp_path = pathlib.Path(tmp_path)

    processed_count = 0

    with zipfile.ZipFile(epub, 'r') as zin, \
         zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.namelist():
            data = zin.read(item)

            if item.endswith('.xhtml') or item.endswith('.html'):
                content = data.decode('utf-8', errors='ignore')
                original = content

                # Step 1: .vrtl クラスを body に追加（縦書き有効化）
                content = add_vrtl_class(content)

                # Step 2: 行頭括弧 → no-indent
                content = add_no_indent_classes(content)

                # Step 3: 半角数字 → tcy
                content = add_tate_chu_yoko(content)

                # Step 4: JLREQ CSS追記
                content = inject_jlreq_css(content)

                if content != original:
                    data = content.encode('utf-8')
                    processed_count += 1
                    print(f"  ✓ {item}")

            zout.writestr(item, data)

    if not dry_run:
        backup = epub.with_suffix(epub.suffix + '.bak2')
        if backup.exists():
            backup.unlink()
        shutil.copy2(epub, backup)
        shutil.move(tmp_path, epub)
        print(f"\nProcessed {processed_count} XHTML file(s)")
        print(f"Backup: {backup}")
    else:
        tmp_path.unlink(missing_ok=True)
        print(f"\n[DRY-RUN] Would process {processed_count} file(s)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='JLREQ post-processing for Vivliostyle EPUB output'
    )
    parser.add_argument('epub', help='EPUB file path')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    process_epub(args.epub, args.dry_run)
