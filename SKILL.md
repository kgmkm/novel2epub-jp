---
name: novel2epub-jp
description: Markdown小説 → A6縦書きPDF/EPUB変換（Puppeteer+PyMuPDF）。しっぽり明朝埋め込み、章ヘッダ/ノンブル/挿絵制御、JLREQ前処理、VFMルビ対応。
version: 1.3.0
tags: [novel, pdf, epub, puppeteer, pymupdf, vivliostyle, japanese]
---

# novel2epub-jp（AI向け仕様）

## 必須前提

- 入力: `novel/*.md`（VFM記法ルビ `{漢字|よみ}` 使用）
- 挿絵: `novel/image/*.webp`（Markdown内で `![alt](image/xxx.webp)`）
- フォント: `fonts/ShipporiMincho-{Regular,Bold}.woff2`（プロジェクトルート）

## PDF生成コマンド

```bash
python3 scripts/build-pdf.py \
  --project-dir . \
  --output dist/book.pdf \
  [--image-size small|medium|large] \
  [--image-caption on|off] \
  [--chapter-header-position left|center|right] \
  [--chapter-header-display all|even|odd|none] \
  [--page-number-position center|left|right|odd-right-even-left|odd-left-even-right] \
  [--page-number-display all|even|odd]
```

**重要制約**:
- `image-size=large` の場合、captionは常に非表示
- Vivliostyle CLIのPDF出力は**禁止**（Chromiumの@page margin box + OTF埋め込みが破綻するため）
- ヘッダ/フッタはPyMuPDFで後付け（しっぽり明朝TTF使用）

## 出力仕様

- A6（105×148mm）、縦書き右綴じ、14行35字想定
- しっぽり明朝埋め込み
- 始め括弧類の行頭字下げ禁止（JLREQ 3.1.5）
- 半角1桁数字→全角、2桁以上→縦中横（JLREQ 3.2.3）

## EPUB生成

```bash
vivliostyle build   # vivliostyle.config.js が必要
```

## ファイル

- `scripts/build-pdf.py` — メインPDF生成（Puppeteer + PyMuPDF）
- `scripts/print-pdf.cjs` — Puppeteerラッパー
- `references/` — VFM記法・CSS調整・ワークフロー（必要時参照）