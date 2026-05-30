#!/usr/bin/env python3
"""
ruby-dict.py — キャラ設定ファイルからルビ辞書を生成し、
原稿に {漢字|よみ} 形式の VFM ルビを自動付与するスクリプト。

novel2epub-jp スキルの一部。Python 3 標準ライブラリのみ使用。

機能:
  1. character/*.md の「氏名（ふりがな）」テーブルからルビ辞書を生成
  2. novel/*.md の原稿に {漢字|よみ} 形式のルビを付与
  3. 既存のルビ（{漢字|よみ} および 漢字（よみ））は保護して二重付与を防止
  4. 最長一致で置換（複合名に対応）
  5. --dry-run で変更プレビュー、--in-place で上書き保存

使用例:
  python ruby-dict.py --project-dir /mnt/y/novel/yoko-project/
  python ruby-dict.py --project-dir /mnt/y/novel/yoko-project/ --dry-run
  python ruby-dict.py --project-dir /mnt/y/novel/yoko-project/ --in-place
  python ruby-dict.py --char-dir ./character/ --novel-dir ./novel/
"""

import re
import sys
import argparse
import pathlib
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# ルビ辞書生成: character/*.md → {漢字: よみ}
# ---------------------------------------------------------------------------

def extract_ruby_dict(char_dir: str) -> Dict[str, str]:
    """
    character/*.md を読み込み、「氏名（ふりがな）」テーブル行から
    ルビ辞書 {漢字: よみ} を生成する。

    対象行の例:
        | 氏名（ふりがな） | 灯（あかり） |
        | 氏名（ふりがな） | 焔 緋色（ほむら ひいろ） |
        | 氏名（ふりがな） | 九十九（つくも）。自ら名乗った名。… |

    1 ファイルに複数エントリがある場合もすべて抽出する。
    """
    ruby_dict: Dict[str, str] = {}
    char_path = pathlib.Path(char_dir)

    if not char_path.is_dir():
        print(f"エラー: character ディレクトリが見つかりません: {char_dir}",
              file=sys.stderr)
        sys.exit(1)

    # ふりがな行の正規表現
    # グループ1: 漢字表記 (非貪欲、最初の「（」の手前まで)
    # グループ2: よみ (非貪欲、最初の「）」の手前まで)
    # 行末の「|」は必須としない（コメントが続く場合があるため）
    pattern = re.compile(
        r'\|\s*氏名（ふりがな）\s*\|\s*'
        r'(.+?)'          # グループ1: 漢字
        r'（(.+?)）'       # グループ2: よみ
    )

    md_files = sorted(char_path.glob('*.md'))
    if not md_files:
        print(f"警告: character ディレクトリに .md ファイルがありません: {char_dir}",
              file=sys.stderr)

    for md_file in md_files:
        try:
            with open(md_file, encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"警告: 読み込みエラー {md_file.name}: {e}", file=sys.stderr)
            continue

        for match in pattern.finditer(content):
            kanji = match.group(1).strip()
            yomi = match.group(2).strip()
            if kanji and yomi:
                if kanji in ruby_dict and ruby_dict[kanji] != yomi:
                    print(f"警告: 重複エントリ（異なるよみ）: "
                          f"「{kanji}」→「{ruby_dict[kanji]}」"
                          f" / 「{yomi}」（{md_file.name}）",
                          file=sys.stderr)
                ruby_dict[kanji] = yomi

    return ruby_dict


# ---------------------------------------------------------------------------
# ルビ適用: テキストに {漢字|よみ} を付与
# ---------------------------------------------------------------------------

def apply_ruby(text: str, ruby_dict: Dict[str, str]) -> Tuple[str, int]:
    """
    テキストに {漢字|よみ} 形式の VFM ルビを付与する。

    戻り値: (変換後テキスト, 変更箇所数)

    保護ロジック:
      1. 既存の {漢字|よみ} を保護（二重付与防止）
      2. 既存の 漢字（よみ） を保護（括弧書きふりがなの二重付与防止）
      3. 最長一致で辞書キーを置換
      4. 置換後に新規ルビを保護（部分文字列の誤置換防止）
      5. すべての保護を復元
    """
    protected: List[str] = []  # 保護文字列の退避先

    def _protect(m: re.Match) -> str:
        """マッチした文字列を退避し、プレースホルダに置き換える"""
        idx = len(protected)
        protected.append(m.group(0))
        return f"\x00RUBYPROTECT{idx}\x00"

    # ---- 1. 既存 VFM ルビ {漢字|よみ} を保護 ----
    text = re.sub(r'\{[^}]+\|[^}]+\}', _protect, text)

    # ---- 2. 既存の 漢字（よみ）を保護 ----
    # CJK 統合漢字 + 日本語繰り返し記号「々」＋任意の空白、の後に
    # 全角括弧でふりがなが続くパターン
    text = re.sub(
        r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff々\s]+（[^）]+）',
        _protect, text
    )

    # ---- 3. 最長一致で辞書キーを置換 ----
    changes = 0
    sorted_keys = sorted(ruby_dict.keys(), key=len, reverse=True)

    for kanji in sorted_keys:
        count = text.count(kanji)
        if count == 0:
            continue

        yomi = ruby_dict[kanji]
        replacement = '{' + kanji + '|' + yomi + '}'

        # ---- 4. 置換＆新規ルビを即座に保護 ----
        text = text.replace(kanji, replacement)
        changes += count

        # 新しく作った {漢字|よみ} を保護し、
        # より短いキーによる部分文字列誤置換を防ぐ
        idx = len(protected)
        protected.append(replacement)
        placeholder = f"\x00RUBYPROTECT{idx}\x00"
        text = text.replace(replacement, placeholder)

    # ---- 5. 保護を復元 ----
    for i, original in enumerate(protected):
        text = text.replace(f"\x00RUBYPROTECT{i}\x00", original)

    return text, changes


# ---------------------------------------------------------------------------
# novel/*.md の一括処理
# ---------------------------------------------------------------------------

def process_novel_files(
    novel_dir: str,
    ruby_dict: Dict[str, str],
    dry_run: bool = False,
    in_place: bool = False,
) -> int:
    """
    novel/*.md を読み込み、ルビ付与を適用する。

    dry_run=True  : 変更内容を表示するだけでファイルは変更しない
    in_place=True : ファイルを上書き保存する
    （どちらも False の場合は変更内容の表示のみ）
    """
    novel_path = pathlib.Path(novel_dir)

    if not novel_path.is_dir():
        print(f"エラー: novel ディレクトリが見つかりません: {novel_dir}",
              file=sys.stderr)
        sys.exit(1)

    md_files = sorted(novel_path.glob('*.md'))
    if not md_files:
        print(f"エラー: novel ディレクトリに .md ファイルがありません: {novel_dir}",
              file=sys.stderr)
        sys.exit(1)

    total_changes = 0
    separator = "=" * 60

    for md_file in md_files:
        try:
            with open(md_file, encoding='utf-8') as f:
                original = f.read()
        except Exception as e:
            print(f"警告: 読み込みエラー {md_file.name}: {e}", file=sys.stderr)
            continue

        converted, changes = apply_ruby(original, ruby_dict)

        if changes == 0:
            print(f"  {md_file.name}: 変更なし")
            continue

        total_changes += changes
        print(f"\n{separator}")
        print(f"ファイル: {md_file.name}  ({changes} 箇所変更)")
        print(separator)

        if dry_run or not in_place:
            # 差分表示: 変更のあった行のみ
            orig_lines = original.split('\n')
            conv_lines = converted.split('\n')
            for i, (ol, cl) in enumerate(zip(orig_lines, conv_lines), 1):
                if ol != cl:
                    # 表示用にトリミング（長すぎる行は省略）
                    ol_disp = ol.strip()[:100]
                    cl_disp = cl.strip()[:100]
                    print(f"  行 {i}:")
                    print(f"    - {ol_disp}")
                    print(f"    + {cl_disp}")
            print()

        if in_place and not dry_run:
            # 上書き保存（競合チェック付き）
            try:
                with open(md_file, encoding='utf-8') as f:
                    current = f.read()
                if current == original:
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(converted)
                    print(f"  → 保存完了: {md_file}")
                else:
                    print(f"  → 警告: 処理中にファイルが変更されたため"
                          f"保存をスキップ: {md_file.name}",
                          file=sys.stderr)
            except Exception as e:
                print(f"  → エラー: 保存失敗 {md_file.name}: {e}",
                      file=sys.stderr)

    return total_changes


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='キャラ設定からルビ辞書を生成し、原稿に {漢字|よみ} を付与する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # プロジェクトディレクトリ指定
  python ruby-dict.py --project-dir /mnt/y/novel/yoko-project/

  # ディレクトリ個別指定
  python ruby-dict.py --char-dir ./character/ --novel-dir ./novel/

  # ドライラン（表示のみ、ファイル変更なし）
  python ruby-dict.py --project-dir /mnt/y/novel/yoko-project/ --dry-run

  # ファイルを上書き保存
  python ruby-dict.py --project-dir /mnt/y/novel/yoko-project/ --in-place
        """,
    )

    parser.add_argument(
        '--project-dir', type=str,
        help='プロジェクトルート（character/ と novel/ を自動検出）',
    )
    parser.add_argument(
        '--char-dir', type=str,
        help='character/ ディレクトリ（--novel-dir と併用）',
    )
    parser.add_argument(
        '--novel-dir', type=str,
        help='novel/ ディレクトリ（--char-dir と併用）',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='変更内容を表示するだけでファイルは変更しない',
    )
    parser.add_argument(
        '--in-place', action='store_true',
        help='ファイルを上書き保存する',
    )

    args = parser.parse_args()

    # ---- 引数検証 ----
    if args.dry_run and args.in_place:
        print("エラー: --dry-run と --in-place は同時に指定できません",
              file=sys.stderr)
        sys.exit(1)

    # ---- ディレクトリ決定 ----
    if args.project_dir:
        project_root = pathlib.Path(args.project_dir)
        char_dir = project_root / 'character'
        novel_dir = project_root / 'novel'
    elif args.char_dir and args.novel_dir:
        char_dir = pathlib.Path(args.char_dir)
        novel_dir = pathlib.Path(args.novel_dir)
    else:
        print("エラー: --project-dir または "
              "(--char-dir と --novel-dir) を指定してください",
              file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # ---- 辞書生成 ----
    print(f"character/ : {char_dir}")
    ruby_dict = extract_ruby_dict(str(char_dir))

    if not ruby_dict:
        print("エラー: ルビ辞書のエントリが抽出されませんでした", file=sys.stderr)
        print("character/*.md に「氏名（ふりがな）」行があるか確認してください",
              file=sys.stderr)
        sys.exit(1)

    print(f"\nルビ辞書 ({len(ruby_dict)} エントリ):")
    for kanji, yomi in sorted(ruby_dict.items()):
        print(f"  「{kanji}」 → 「{yomi}」")

    # ---- 原稿処理 ----
    print(f"\nnovel/     : {novel_dir}")
    if args.dry_run:
        print("*** ドライランモード: ファイルは変更されません ***\n")

    total_changes = process_novel_files(
        str(novel_dir),
        ruby_dict,
        dry_run=args.dry_run,
        in_place=args.in_place,
    )

    # ---- 結果サマリ ----
    print(f"\n{'-' * 40}")
    print(f"合計変更箇所: {total_changes}")
    if args.dry_run:
        print("ドライランのため、ファイルは変更されていません。")
        print("適用するには --in-place を指定してください。")
    elif args.in_place:
        print("ファイルを更新しました。")
    else:
        print("変更を保存するには --in-place を指定してください。")


if __name__ == '__main__':
    main()
