---
name: novel2epub-jp
description: Markdown小説 → A6縦書きPDF/EPUB変換（Puppeteer+PyMuPDF / Vivliostyle CLI）。しっぽり明朝埋め込み、章ヘッダ/ノンブル/挿絵制御、JLREQ前処理、VFMルビ対応。
version: 1.5.0
tags: [novel, pdf, epub, puppeteer, pymupdf, vivliostyle, japanese]
---

# novel2epub-jp（AI向け仕様）

## 致命的禁止事項（絶対に守ること）

### PDF生成: Vivliostyle CLI でのPDF出力は**完全禁止**

```
✗ vivliostyle build でPDFを生成（横書き・フォント崩壊の原因）
✗ bunko-custom.css 等で縦書き強制を試みる（効かない）
○ build-pdf.py（Puppeteer + PyMuPDF）でPDF生成（唯一の正解）
```

**理由**: Chromiumの `@page margin box` と `position: fixed` が `writing-mode: vertical-rl` と両立しないため、Vivliostyle CLI経由のPDFは**必ず横書きになる**（2026-05-30実証済）。フォント埋め込みも失敗する。

### CSS安易書き換え禁止

`bunko-custom.css` の `writing-mode` 設定だけでは縦書きは強制できない。HTMLの構造（`<html lang="ja">` + `direction: rtl` + `writing-mode: vertical-rl`）と `@viewport` の両方が必要。安易なCSS書き換えはEPUB/PDF両方の組版を壊す。

---

## セットアップ（フォント自動配置）

```bash
# WOFF2 ダウンロード（EPUB用・これだけでOK）
python3 scripts/setup.py --project-dir /path/to/project

# WOFF2 + OTF 変換（PDF用）
python3 scripts/setup.py --project-dir /path/to/project --otf

# またはシェルスクリプト版
bash scripts/setup.sh --project-dir /path/to/project
```

セットアップスクリプトが以下を自動実行:
1. Google Fonts から ShipporiMincho Regular/Bold の WOFF2 をダウンロード
2. `fonts/` ディレクトリに配置
3. `--otf` 指定時: fonttools で WOFF2 → OTF 変換（PDFのPyMuPDF埋め込み用）

**依存ツール**:
- `curl` / `urllib.request`（ダウンロード）
- `fonttools`（OTF変換時のみ）: `pip install fonttools`

---

## 必須前提

- 入力: `novel/*.md`（VFM記法ルビ `{漢字|よみ}` 使用）
- 挿絵: `novel/image/*.webp`（Markdown内で `![alt](image/xxx.webp)`）
- フォント: `fonts/ShipporiMincho-{Regular,Bold}.woff2`（`setup.sh` で自動配置）

---

## PDF生成

```bash
python3 scripts/build-pdf.py \
  --project-dir . \
  --output dist/book.pdf \
  [--preset <name>] \
  [--image-size small|medium|large] \
  [--image-caption on|off] \
  [--chapter-header-position left|center|right] \
  [--chapter-header-display all|even|odd|none] \
  [--page-number-position center|left|right|odd-right-even-left|odd-left-even-right] \
  [--page-number-display all|even|odd]
```

### プリセット一覧

`--list-presets` で確認できる出力例:

```
Available presets:

  showcase-small       image-size=small, caption=on, header=even/left, page-num=all/odd-right-even-left
  showcase-medium      image-size=medium, caption=on, header=even/left, page-num=all/odd-right-even-left
  showcase-large       image-size=large, caption=off, header=even/left, page-num=all/odd-right-even-left
  clean-small          image-size=small, caption=off, header=even/left, page-num=all/odd-right-even-left
  clean-medium         image-size=medium, caption=off, header=even/left, page-num=all/odd-right-even-left
  clean-large          image-size=large, caption=off, header=even/left, page-num=all/odd-right-even-left
  minimal              image-size=small, caption=off, header=none/?, page-num=all/center

Usage: python build-pdf.py --preset <name> --project-dir .
```

### プリセット早見表

| プリセット名      | 挿絵 | caption | ヘッダ    | ページ番号       | 用途                     |
|-------------------|------|---------|-----------|------------------|--------------------------|
| showcase-small    | 小   | ✓ on    | even/left | 交互             | 扱いやすいプレビュー     |
| showcase-medium   | 中   | ✓ on    | even/left | 交互             | バランス重視             |
| **showcase-large**| **大** | **✗ off** | even/left | 交互           | **見開き挿絵（注: large=強制caption off）** |
| clean-small       | 小   | ✗ off   | even/left | 交互             | 本文集中・シンプル       |
| clean-medium      | 中   | ✗ off   | even/left | 交互             | 本文集中・やや大きめ     |
| **clean-large**   | **大** | **✗ off** | even/left | 交互           | **本文集中・フルページ（注: large=強制caption off）** |
| minimal           | 小   | ✗ off   | なし      | 中央             | 最小構成                 |

> **注意**: `image-size=large` の場合、ページ全体に画像が表示されるため **caption は強制的にオフ** になります。プリセット指定や `--image-caption on` で上書きしても large では無視されます。

個別オプションはプリセットをオーバーライド可能。

**重要制約**:
- `image-size=large` の場合、captionは常に非表示（上書き不可）
- Vivliostyle CLIのPDF出力は**禁止**（Chromiumの@page margin box + OTF埋め込みが破綻するため）
- ヘッダ/フッタはPyMuPDFで後付け（しっぽり明朝TTF使用）

---

## EPUB生成

### ビルド手順

```bash
# 1. Vivliostyle CLI で EPUB をビルド
cd /path/to/novel-project
npx vivliostyle build

# 2. JLREQ後処理を適用
python3 /path/to/novel2epub-jp/scripts/jlreq_postprocess.py \
  dist/book-distribution.epub
```

### `jlreq_postprocess.py` が行うこと

Vivliostyle CLI出力のEPUBを後処理し、日本語組版ルールを適用:

1. `.vrtl` クラス付与 — `<html>` と `<body>` に `class="vrtl"` を追加
   - theme-epub3j は `.vrtl` クラスで縦書きを制御するが、Vivliostyle CLIのEPUB出力では自動付与されない
2. JLREQ 3.1.5 — 行頭が始め括弧類（「『（など）の段落に `no-indent` クラスを付与
3. JLREQ 3.2.4 — 半角アラビア数字1〜2桁を `<span class="tcy">` で縦中横化
   - `<p>`, `<h1>`-`<h6>`, `<li>` のすべてに適用
4. CSS注入 — `jlreq_epub_rules.css` を `<style>` タグ内に直接追記

**注意**: `\b` (word boundary) は日本語文字と数字の間で機能しないため、`(?<!\d)(\d{1,2})(?!\d)` のパターンを使用。

### vivliostyle.config.js の例

```javascript
module.exports = {
  title: '作品タイトル',
  author: '著者名',
  language: 'ja',
  readingProgression: 'rtl',  // 縦書き右綴じ

  entry: [
    'novel/序章.md',
    'novel/第1章.md',
  ],

  output: {
    path: 'dist/作品タイトル-distribution.epub',
    format: 'epub',
  },

  theme: '@vivliostyle/theme-epub3j',
  toc: true,

  copyAsset: {
    includes: ['novel/image/**'],
  },
};
```

**重要**: `style: 'epub-custom.css'` は指定しないこと。Vivliostyle CLIが既存のtheme CSSへのリンクを上書きし、横書き化する原因になる。CSSルールはすべて `jlreq_postprocess.py` で注入する。

---

## 出力仕様

- A6（105×148mm）、縦書き右綴じ、14行35字想定
- しっぽり明朝埋め込み（WOFF2 for EPUB / OTF for PDF）
- 始め括弧類の行頭字下げ禁止（JLREQ 3.1.5）
- 半角アラビア数字 → 縦中横（JLREQ 3.2.4）

---

## ファイル構成

| ファイル | 用途 |
|---------|------|
| `scripts/setup.sh` | フォント自動ダウンロード・配置 |
| `scripts/setup.py` | フォント自動ダウンロード・配置（Python版） |
| `scripts/build-pdf.py` | PDF生成（Puppeteer + PyMuPDF） |
| `scripts/jlreq_postprocess.py` | EPUB後処理（JLREQルール注入） |
| `scripts/jlreq_epub_rules.css` | EPUB注入用CSSルール |
| `scripts/fix-epub-css.py` | CSSリンク修正ユーティリティ |
| `scripts/jlreq_preprocess.py` | Markdown変換時のJLREQ前処理 |
| `scripts/build-epub.py` | EPUBビルド自動化スクリプト |
| `scripts/print-pdf.cjs` | Puppeteerラッパー |
| `templates/` | HTML/CSSテンプレート |
| `references/` | CSS調整・ワークフロー |

---

## 関連スキル

- [vfm-syntax](https://github.com/kgmkm/vfm-syntax) — VFM (Vivliostyle Flavored Markdown) 記法リファレンス。Markdown原稿の記法はこちらを参照
- [jlreq-skill](https://github.com/kgmkm/jlreq-skill) — W3C JLREQ（日本語組版処理の要件）のAIエージェント向けリファレンス。組版ルールの詳細はこちらを参照

## ライセンス

- **スクリプト・コード**: MIT License
- **しっぽり明朝フォント**: SIL Open Font License 1.1
  - ShipporiMincho © 本山ゆき (Google Fonts)
  - 商用利用可能、改変・再配布可能（OFL準拠）
- **theme-epub3j**: 電書協 EPUB3 制作ガイド準拠（各CSSファイルにライセンス表記あり）
