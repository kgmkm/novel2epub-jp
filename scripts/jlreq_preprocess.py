#!/usr/bin/env python3
"""
jlreq_preprocess.py: JLREQ準拠HTML前処理（build-pdf.pyからの抽出）

VFMが出力したHTML bodyに対して適用する前処理。
PDF (build-pdf.py) と EPUB (build-epub.py) の両方で共用可能。

対応JLREQ:
  3.1.5 始め括弧類の行頭字下げ禁止
        → <p>の先頭文字が始め括弧類の場合 class="no-indent" 付与
  3.2.4 全角モノスペースの欧字・アラビア数字配置
        → テキストノード内の半角1桁数字→全角、2桁以上→span class="tcy"

使い方:
    from jlreq_preprocess import preprocess_html
    html = preprocess_html(vfm_html)
"""

import re

OPENING_BRACKETS = '「『（【＂｢'
DIGIT_FW_MAP = str.maketrans('0123456789', '０１２３４５６７８９')


def add_no_indent_class(html):
    """<p>タグの先頭文字が始め括弧類なら class='no-indent' を付与（JLREQ 3.1.5）"""
    def check_and_replace(m):
        tag = m.group(0)
        after = m.string[m.end():]
        i = 0
        while i < len(after):
            if after[i] == '<':
                gt = after.find('>', i)
                if gt == -1:
                    return tag
                inner = after[i + 1:gt]
                if inner.lower().startswith('ruby'):
                    i = gt + 1
                    continue
                ch = after[gt + 1] if gt + 1 < len(after) else ''
                if ch in OPENING_BRACKETS:
                    return tag.replace('<p', '<p class="no-indent"')
                else:
                    return tag
            else:
                if after[i] in OPENING_BRACKETS:
                    return tag.replace('<p', '<p class="no-indent"')
                else:
                    return tag
        return tag

    return re.sub(r'<p(?:\s[^>]*)?>', check_and_replace, html)


def convert_digits_in_text_nodes(html):
    """テキストノード内の半角数字を処理（1桁→全角、2桁以上→tcy）（JLREQ 3.2.4）"""
    def process_text(text):
        result = []
        i = 0
        while i < len(text):
            if text[i] in '0123456789':
                j = i
                while j < len(text) and text[j] in '0123456789':
                    j += 1
                num = text[i:j]
                if len(num) == 1:
                    result.append(num.translate(DIGIT_FW_MAP))
                else:
                    result.append(f'<span class="tcy">{num}</span>')
                i = j
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)

    result = []
    i = 0
    while i < len(html):
        if html[i] == '<':
            tag_end = html.find('>', i)
            if tag_end == -1:
                result.append(html[i:])
                break
            result.append(html[i:tag_end + 1])
            i = tag_end + 1
        else:
            j = html.find('<', i)
            if j == -1:
                result.append(process_text(html[i:]))
                break
            result.append(process_text(html[i:j]))
            i = j
    return ''.join(result)


def html_to_xhtml(html):
    """HTML5をXHTMLに変換（自己閉じタグの修正）"""
    # Void要素（自己閉じが必要なタグ）のリスト
    void_elements = [
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'
    ]
    
    # 各void要素を自己閉じに変換
    # <tag ...> → <tag ... />
    # 既に自己閉じになっているもの（<tag .../> や <tag ... />）は除外
    for tag in void_elements:
        # <tag ...> で始まり、/> で終わらないものをマッチ
        # 属性がない場合: <tag> → <tag />
        # 属性がある場合: <tag attr="value"> → <tag attr="value" />
        pattern = rf'<({tag})(\s[^>]*)?(?<!/)>'
        replacement = rf'<\1\2 />'
        html = re.sub(pattern, replacement, html, flags=re.IGNORECASE)
    
    return html


def preprocess_html(html, xhtml_mode=False):
    """全HTML前処理を適用
    
    Args:
        html: VFMが出力したHTML文字列
        xhtml_mode: Trueの場合、XHTML形式に変換（EPUB用）
    """
    html = add_no_indent_class(html)
    html = convert_digits_in_text_nodes(html)
    
    if xhtml_mode:
        html = html_to_xhtml(html)
    
    return html


if __name__ == '__main__':
    import sys
    # 簡易テスト
    test = '<section><p>「テスト」</p><p>2匹の猫が1匹になった。</p></section>'
    print("Input:")
    print(test)
    print("\nOutput:")
    print(preprocess_html(test))
