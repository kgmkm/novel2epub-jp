#!/bin/bash
# novel2epub-jp: フォント自動ダウンロード・変換・配置
# しっぽり明朝（WOFF2）をプロジェクトの fonts/ に配置する
#
# 使用法:
#   bash scripts/setup.sh [--project-dir <dir>]
#
# 依存ツール:
#   - curl (ダウンロード)
#   - fonttools (pip install fonttools) - WOFF2→OTF変換用（PDF生成時に必要）
#
# 処理:
#   1. Google Fonts から ShipporiMincho Regular/Bold の WOFF2 をダウンロード
#   2. fonts/ ディレクトリに配置
#   3. (オプション) WOFF2 → OTF 変換（PDFのPyMuPDF埋め込み用）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${1:-.}"
FONT_DIR="$PROJECT_DIR/fonts"
FONT_BASE="https://fonts.gstatic.com/s/shipporimincho/v21"

# ─── ディレクトリ作成 ──────────────────────────────────────────
mkdir -p "$FONT_DIR"

# ─── WOFF2 ダウンロード ────────────────────────────────────────
download_font() {
    local variant="$1"
    local url="$2"
    local dest="$FONT_DIR/ShipporiMincho-${variant}.woff2"
    
    if [ -f "$dest" ]; then
        echo "  ✓ 既存: $dest"
        return 0
    fi
    
    echo "  ↓ ダウンロード: ShipporiMincho-${variant}.woff2"
    if curl -fSL -o "$dest" "$url"; then
        echo "  ✓ 保存: $dest ($(du -h "$dest" | cut -f1))"
    else
        echo "  ✗ ダウンロード失敗: $url"
        rm -f "$dest"
        return 1
    fi
}

echo "=== novel2epub-jp: フォントセットアップ ==="
echo "出力先: $FONT_DIR"
echo ""

# ShipporiMincho Regular
download_font "Regular" \
    "https://fonts.gstatic.com/s/shipporimincho/v21/-Wq1XQBYsEiOuoPIA0X17Eyb4a3G4GqnkpY.woff2"

# ShipporiMincho Bold
download_font "Bold" \
    "https://fonts.gstatic.com/s/shipporimincho/v21/-Wq0XQBYsEiOuoPIA0X17Eyb4HG9JBMGjn8.woff2"

echo ""

# ─── OTF変換（PDF用） ─────────────────────────────────────────
if python3 -c "import fontTools" 2>/dev/null; then
    echo "--- OTF変換（PDF生成用） ---"
    for woff in "$FONT_DIR"/*.woff2; do
        [ -f "$woff" ] || continue
        otf="${woff%.woff2}.otf"
        if [ -f "$otf" ]; then
            echo "  ✓ 既存: $(basename "$otf")"
            continue
        fi
        echo "  → 変換中: $(basename "$woff") → $(basename "$otf")"
        python3 -c "
import sys
from fontTools.ttLib import TTFont
font = TTFont('$woff')
font.flavor = None
font.save('$otf')
print(f'  ✓ 保存: $(basename "$otf")')
"
    done
else
    echo "--- OTF変換スキップ（fonttools未インストール） ---"
    echo "  PDF生成にOTFが必要な場合: pip install fonttools"
    echo "  EPUB生成にはWOFF2のみでOK"
fi

echo ""
echo "=== セットアップ完了 ==="
echo ""
ls -lh "$FONT_DIR/"
echo ""
echo "EPUB: WOFF2 で十分"
echo "PDF:  OTF が必要（build-pdf.py が自動検出）"
