#!/usr/bin/env python3
"""
novel2epub-jp: フォント自動ダウンロード・変換・配置

Google Fonts から ShipporiMincho の WOFF2 をダウンロードし、
必要に応じて OTF に変換する（PDF生成用）。

使用法:
  python3 scripts/setup.py [--project-dir .] [--otf]

依存:
  - fonttools (OTF変換時のみ): pip install fonttools
"""
import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

FONTS = {
    "Regular": "https://fonts.gstatic.com/s/shipporimincho/v21/-Wq1XQBYsEiOuoPIA0X17Eyb4a3G4GqnkpY.woff2",
    "Bold":    "https://fonts.gstatic.com/s/shipporimincho/v21/-Wq0XQBYsEiOuoPIA0X17Eyb4HG9JBMGjn8.woff2",
}


def download(url: str, dest: Path) -> bool:
    """URL からファイルをダウンロード"""
    if dest.exists():
        print(f"  ✓ 既存: {dest.name}")
        return False
    print(f"  ↓ ダウンロード: {dest.name}")
    try:
        urllib.request.urlretrieve(url, dest)
        size = dest.stat().st_size / 1024
        print(f"  ✓ 保存: {dest.name} ({size:.0f} KB)")
        return True
    except Exception as e:
        print(f"  ✗ 失敗: {e}")
        dest.unlink(missing_ok=True)
        return False


def convert_woff2_to_otf(woff2: Path) -> bool:
    """WOFF2 → OTF 変換（fonttools使用）"""
    otf = woff2.with_suffix("").with_suffix(".otf")
    if otf.exists():
        print(f"  ✓ 既存: {otf.name}")
        return False
    try:
        from fontTools.ttLib import TTFont
        print(f"  → 変換: {woff2.name} → {otf.name}")
        font = TTFont(str(woff2))
        font.flavor = None  # WOFF2ヘッダ除去 → OTF
        font.save(str(otf))
        print(f"  ✓ 保存: {otf.name}")
        return True
    except ImportError:
        print(f"  ✗ fonttools 未インストール (pip install fonttools)")
        return False
    except Exception as e:
        print(f"  ✗ 変換失敗: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="novel2epub-jp: フォント自動セットアップ"
    )
    parser.add_argument(
        "--project-dir", default=".",
        help="プロジェクトルート (デフォルト: カレントディレクトリ)"
    )
    parser.add_argument(
        "--otf", action="store_true",
        help="WOFF2 → OTF 変換も実行する (PDF生成用)"
    )
    args = parser.parse_args()

    font_dir = Path(args.project_dir) / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== novel2epub-jp: フォントセットアップ ===")
    print(f"出力先: {font_dir}\n")

    # ダウンロード
    downloaded = 0
    for variant, url in FONTS.items():
        dest = font_dir / f"ShipporiMincho-{variant}.woff2"
        if download(url, dest):
            downloaded += 1

    print()

    # OTF変換
    if args.otf:
        print("--- OTF変換 (PDF用) ---")
        for woff2 in font_dir.glob("*.woff2"):
            convert_woff2_to_otf(woff2)
    else:
        print("--- OTF変換スキップ ---")
        print("  PDF生成にOTFが必要な場合: python3 scripts/setup.py --otf")
        print("  EPUB生成にはWOFF2のみでOK")

    print(f"\n=== セットアップ完了 ===\n")
    for f in sorted(font_dir.iterdir()):
        size = f.stat().st_size / 1024
        print(f"  {f.name:<40s} {size:>8.0f} KB")

    print(f"\nEPUB: WOFF2 で十分")
    print(f"PDF:  OTF が必要（--otf フラグまたは手動変換）")


if __name__ == "__main__":
    main()
