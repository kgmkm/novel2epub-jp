# CSS変数・縦書き組版微調整ガイド

Vivliostyle CLI + `@vivliostyle/theme-bunko` を使用した日本語縦書き小説のCSS組版ガイドです。
行数・字数・余白・フォント・ノンブル・挿絵レイアウトなど、組版の微調整に必要なCSSカスタマイズを網羅します。
各項目は実践的なコード例付きで、実際のプロジェクト（`templates/bunko-custom.css` / `templates/epub-custom.css`）で使用されている設定と整合しています。

---

## 目次

1. [はじめに](#1-はじめに)
2. [theme-bunkoのCSS変数一覧](#2-theme-bunkoのcss変数一覧)
3. [用紙サイズ変更](#3-用紙サイズ変更)
4. [フォント設定](#4-フォント設定)
5. [縦書き固有のCSS](#5-縦書き固有のcss)
6. [ページレイアウト](#6-ページレイアウト)
7. [見出しスタイル](#7-見出しスタイル)
8. [段落スタイル](#8-段落スタイル)
9. [挿絵スタイル](#9-挿絵スタイル)
10. [ノンブル（ページ番号）](#10-ノンブルページ番号)
11. [EPUB向けの注意事項](#11-epub向けの注意事項)
12. [トラブルシューティング](#12-トラブルシューティング)
13. [実践例: A6文庫14行35字の完全CSS設定](#13-実践例-a6文庫14行35字の完全css設定)

---

## 1. はじめに

### 1.1 Vivliostyle CLI と日本語縦書き組版

Vivliostyle CLI は、HTML+CSS を入力として PDF/EPUB を出力するオープンソースの組版エンジンです。
`@vivliostyle/theme-bunko` テーマは、日本語文庫本の組版に特化した公式テーマで、以下の基本設定を内包しています：

- 縦書き右綴じ（`writing-mode: vertical-rl`）
- デフォルト 15行×39字（A5判想定）
- CSS変数による行数・字数・ノンブルのカスタマイズ

本スキル（novel2epub-jp）では、`theme-bunko` の変数を上書きして **A6判 14行×35字** の文庫本組版を実現します。
カスタマイズ用CSS（`bunko-custom.css`）を用意し、`vivliostyle.config.js` の `style` フィールドで読み込ませることで適用されます。

### 1.2 CSSカスタマイズの基本構造

```
@vivliostyle/theme-bunko（基本テーマ）
        ↓
bunko-custom.css（theme変数の上書き + 追加スタイル）
        ↓
PDF出力
```

CSSファイルの先頭で `@page` と `@viewport` を宣言し、`:root` でテーマ変数を上書き、その後に要素別のスタイルを記述します。

### 1.3 縦書き組版の基本概念

| 用語 | 意味 |
|------|------|
| **書字方向** | 縦書き右綴じ。`writing-mode: vertical-rl` で指定。行は右から左へ、文字は上から下へ |
| **ノド** | 綴じる側の余白。右綴じの場合、右側を広く取る |
| **小口** | 綴じない側の余白。右綴じの場合、左側 |
| **ノンブル** | ページ番号。`counter(page)` で自動採番 |
| **柱** | ページ上部の章タイトル表示。`string-set` で設定 |
| **字下げ** | 段落先頭の空白。日本語組版では1字下げが標準 |
| **縦中横** | 縦書き中で数字などを横倒しにする処理。`text-combine-upright: all` |

---

## 2. theme-bunkoのCSS変数一覧

`@vivliostyle/theme-bunko` は `:root` で以下のCSS変数を受け付けます。`bunko-custom.css` で上書き指定することで組版をカスタマイズできます。

### 2.1 行数・字数

| CSS変数 | デフォルト | 推奨値(A6文庫) | 説明 |
|---------|-----------|----------------|------|
| `--vs-theme--num-of-line` | 15 | 14 | 1ページあたりの行数 |
| `--vs-theme--num-of-character` | 39 | 35 | 1行あたりの文字数 |

```css
:root {
  --vs-theme--num-of-line: 14;      /* A6文庫: 14行 */
  --vs-theme--num-of-character: 35; /* A6文庫: 35字 */
}
```

**選択の目安**:

| 判型 | 推奨行数 | 推奨字数 | 用途 |
|------|----------|----------|------|
| A6文庫 (105×148mm) | 14 | 35 | 標準文庫本 |
| A6文庫 (読みやすさ重視) | 13 | 33 | 高齢者・大きな文字 |
| A5 (148×210mm) | 15 | 39 | theme-bunkoデフォルト（文芸誌） |
| B6 (128×182mm) | 14 | 37 | 単行本・新書 |
| B5 (182×257mm) | 18 | 44 | 大判書籍 |

### 2.2 ノンブル（ページ番号）関連

| CSS変数 | デフォルト | 説明 |
|---------|-----------|------|
| `--vs-theme--page-top-left-content` | なし | 左（ノド側）ページ上部のコンテンツ |
| `--vs-theme--page-top-right-content` | なし | 右（小口側）ページ上部のコンテンツ |

```css
:root {
  /* 右ページ（小口側）: ページ番号のみ */
  --vs-theme--page-top-right-content: counter(page);

  /* 左ページ（ノド側）: ページ番号 + 作品タイトル */
  --vs-theme--page-top-left-content: counter(page) "　" env(doc-title);
}
```

`env(doc-title)` は `vivliostyle.config.js` の `title` フィールドから自動取得される環境変数です。

### 2.3 その他のCSS変数

| CSS変数 | 説明 | 使用例 |
|---------|------|--------|
| `--vs-theme--subsection-text-indent` | サブセクションの字下げ幅 | `--vs-theme--subsection-text-indent: 1em;` |
| `--vs-theme--anchor-color-body` | 本文中のリンク色 | `--vs-theme--anchor-color-body: #333;` |

```css
:root {
  /* サブセクションも1字下げ */
  --vs-theme--subsection-text-indent: 1em;

  /* リンク色を本文と同じに（EPUB出力時） */
  --vs-theme--anchor-color-body: inherit;
}
```

---

## 3. 用紙サイズ変更

### 3.1 規定サイズ（A判・B判）

`@page` ルールの `size` プロパティで指定します。

```css
/* A6判（文庫本標準） */
@page {
  size: 105mm 148mm;
}

/* A5判 */
@page {
  size: 148mm 210mm;
}

/* B6判（単行本） */
@page {
  size: 128mm 182mm;
}

/* B5判 */
@page {
  size: 182mm 257mm;
}
```

### 3.2 カスタムmm指定

任意のサイズをmm単位で指定できます。

```css
/* カスタム: 新書判 (110mm x 176mm) */
@page {
  size: 110mm 176mm;
}

/* カスタム: 大判文庫 (120mm x 160mm) */
@page {
  size: 120mm 160mm;
}
```

**注意**: `vivliostyle.config.js` の `size` フィールドとCSSの `@page { size: }` が競合する場合、CSS側が優先されます。
基本的にはCSS側に `@page` を記述し、`vivliostyle.config.js` の `size` は削除またはコメントアウトしてください。

### 3.3 用紙サイズと行数・字数のバランス

用紙サイズを変更する場合、`--vs-theme--num-of-line` と `--vs-theme--num-of-character` も併せて調整する必要があります。

```css
/* B6単行本 14行×37字 の設定例 */
@page {
  size: 128mm 182mm;
}

:root {
  --vs-theme--num-of-line: 14;
  --vs-theme--num-of-character: 37;
}
```

---

## 4. フォント設定

### 4.1 フォントの優先順位指定

日本語縦書き本文に適したフォントを `font-family` で指定します。

```css
/* 游明朝 → 標準明朝 → 明朝系の順でフォールバック */
body {
  font-family: "游明朝", "YuMincho", "ヒラギノ明朝 ProN W3",
               "Hiragino Mincho ProN", "MS 明朝", "MS Mincho",
               serif;
}

/* Noto Serif CJK JP ベースの指定（Webフォント埋め込み向け） */
body {
  font-family: "Noto Serif CJK JP", "游明朝", "YuMincho",
               "ヒラギノ明朝 ProN W3", serif;
}
```

### 4.2 フォントの種類と特徴

| フォント名 | 特徴 | 入手 |
|------------|------|------|
| **游明朝** | Windows/macOS標準。縦書き対応。明朝体の定番 | OSバンドル |
| **Noto Serif CJK JP** | Google提供。全7ウェイト。縦書き対応。Webフォント可 | Google Fonts / GitHub |
| **ヒラギノ明朝 ProN** | macOS/iOS標準。高品質な明朝体 | OSバンドル（macOS） |
| **源ノ明朝 (Source Han Serif)** | Adobe提供。Noto Serif CJK と同一書体 | GitHub |

### 4.3 @font-face によるWebフォント埋め込み

EPUBにフォントを埋め込む場合や、クロスプラットフォームで一貫した表示を実現する場合に使用します。

```css
/* Noto Serif CJK JP をローカルファイルから埋め込む例 */
@font-face {
  font-family: "Noto Serif CJK JP";
  font-weight: 400;
  font-style: normal;
  src: local("Noto Serif CJK JP"),
       url("fonts/NotoSerifCJKjp-Regular.otf") format("opentype");
}

@font-face {
  font-family: "Noto Serif CJK JP";
  font-weight: 700;
  font-style: normal;
  src: local("Noto Serif CJK JP Bold"),
       url("fonts/NotoSerifCJKjp-Bold.otf") format("opentype");
}

/* 本文に適用 */
body {
  font-family: "Noto Serif CJK JP", serif;
  font-weight: 400;
}

/* 見出しに太字を適用 */
h2 {
  font-family: "Noto Serif CJK JP", serif;
  font-weight: 700;
}
```

### 4.4 フォントサイズ

`theme-bunko` は行数・字数から自動的にフォントサイズを計算するため、通常は手動指定不要です。
手動指定する場合は以下のように記述します（非推奨。自動計算との競合に注意）。

```css
body {
  font-size: 10pt; /* 手動指定（自動計算の上書き） */
  line-height: 1.8;
}
```

**推奨**: フォントサイズは行数・字数と余白から自動計算させ、`line-height` のみ明示指定する。

```css
body {
  line-height: 1.8; /* 行送りのみ指定。フォントサイズは自動 */
}
```

### 4.5 EPUBでのフォント埋め込み（電書協ガイド準拠）

```css
/* EPUBでは相対パスでフォントファイルを参照 */
@font-face {
  font-family: "Noto Serif CJK JP";
  font-weight: 400;
  src: url("../fonts/NotoSerifCJKjp-Regular.otf") format("opentype");
}
```

フォントファイルをプロジェクトの `fonts/` ディレクトリに配置し、`vivliostyle.config.js` の `includeAssets` でビルド時にコピーします：

```js
module.exports = {
  // ...
  includeAssets: ['fonts/*.otf'],
};
```

---

## 5. 縦書き固有のCSS

### 5.1 writing-mode: vertical-rl

縦書きの基本指定です。`html` 要素または `body` 要素に指定します。

```css
html {
  writing-mode: vertical-rl;
  -epub-writing-mode: vertical-rl; /* EPUB向けベンダープレフィックス */
}

body {
  writing-mode: vertical-rl;
  -epub-writing-mode: vertical-rl;
}
```

**値の意味**:
- `vertical-rl`: 縦書き・右から左へ行が進む（右綴じ）
- `vertical-lr`: 縦書き・左から右へ行が進む（左綴じ。中国語などで使用）

### 5.2 text-orientation

縦書き時の文字の向きを制御します。

```css
body {
  text-orientation: mixed; /* デフォルト。CJKは縦、欧文は横倒し */
}
```

| 値 | 効果 |
|----|------|
| `mixed` | CJK文字は縦、欧文・数字は90度回転（デフォルト・推奨） |
| `upright` | すべての文字を縦向きに |
| `sideways` | すべての文字を横向きに（使う機会は稀） |

### 5.3 text-combine-upright: all（縦中横）

縦書き中で2〜4桁の数字や単位を横倒しにして1文字分の幅に収めます。

```css
/* 手動でクラス指定する場合 */
.tcy {
  text-combine-upright: all;
}

/* 2桁の数字を自動縦中横にする（EPUB用） */
.tatechuyoko {
  -epub-text-combine: horizontal;
  text-combine-upright: all;
}
```

HTMLでの使用例：
```html
<span class="tcy">2026</span>年<span class="tcy">5</span>月
```

VFMでは縦中横の専用記法がないため、HTML直書きで対応します。

### 5.4 ruby-align / ruby-position

ルビ（ふりがな）の配置を制御します。

```css
/* ルビを親文字の先頭に揃える */
ruby {
  ruby-align: start;
}

/* ルビ文字のサイズを親文字の半分に */
rt {
  font-size: 0.5em;
  font-weight: normal;
}
```

| `ruby-align` 値 | 効果 |
|------------------|------|
| `start` | ルビを親文字の先頭に揃える（日本語組版の標準） |
| `center` | 親文字の中央に揃える |
| `space-between` | 親文字の幅全体に均等配置 |
| `space-around` | 両端に余白を付けて均等配置 |

```css
/* ルビの位置を明示（縦書き時は右側に） */
ruby {
  ruby-position: over; /* 縦書きでは右側 */
}
```

### 5.5 縦中横のよくあるパターン

```css
/* 2桁数字の自動縦中横（汎用） */
.tcy-2 {
  text-combine-upright: all;
  -epub-text-combine: horizontal;
}

/* 3桁以上の数字 */
.tcy-3 {
  text-combine-upright: all;
  -epub-text-combine: horizontal;
  letter-spacing: -0.05em; /* 多少詰める */
}

/* 欧文単位（kg, cm, km など） */
.tcy-unit {
  text-combine-upright: all;
  text-transform: uppercase;
}
```

---

## 6. ページレイアウト

### 6.1 @page ルール

`@page` で用紙サイズと余白を指定します。

```css
@page {
  size: 105mm 148mm;
  margin: 15mm 12mm 15mm 15mm;
  /* 順序: 上 右 下 左（縦書き右綴じの場合） */
}
```

### 6.2 @viewport ルール

ビューポートの書字方向を指定します。ブラウザプレビュー時に影響します。

```css
@viewport {
  writing-mode: vertical-rl;
}
```

### 6.3 ノドと小口の余白設定

縦書き右綴じの場合：
- **ノド（綴じ側）**: 右側の余白を広く取る（綴じ代確保）
- **小口（非綴じ側）**: 左側の余白は狭めでよい

```css
@page {
  size: 105mm 148mm;
  /* 上マージン 15mm, ノド(右) 18mm, 下マージン 15mm, 小口(左) 12mm */
  margin: 15mm 18mm 15mm 12mm;
}
```

**見開きページ（左右で余白を変える場合）**:

```css
/* 右ページ（小口=左）: ノド広め */
@page :right {
  margin: 15mm 18mm 15mm 12mm;
}

/* 左ページ（小口=右）: ノド広め */
@page :left {
  margin: 15mm 12mm 15mm 18mm;
}
```

トンボ（裁ち落とし）付きPDFが必要な場合は `bleed` と `marks` を指定：

```css
@page {
  size: 105mm 148mm;
  margin: 15mm;
  bleed: 3mm;
  marks: crop cross;
}
```

### 6.4 page-break-before / page-break-after の使い方

改ページ制御はCSSの `page-break-*` プロパティを使用します。

```css
/* 章見出しの前で改ページ */
h2 {
  page-break-before: always;
}

/* 挿絵の前後で改ページ（独立ページ化） */
img[src*="image/"] {
  page-break-before: always;
  page-break-after: always;
}

/* 水平線（シーンブレイク）を改ページとして扱う */
hr {
  page-break-after: always;
  visibility: hidden;
  margin: 0;
  padding: 0;
  border: none;
}

/* 改ページ禁止（見出しと本文が分離しないように） */
h3 {
  page-break-after: avoid;
}
```

| 値 | 効果 |
|----|------|
| `always` | 常に改ページ |
| `avoid` | 可能な限り改ページを避ける |
| `left` | 次のページを左ページに |
| `right` | 次のページを右ページに |
| `auto` | 自動（デフォルト） |

---

## 7. 見出しスタイル

### 7.1 h1（作品タイトル）

表紙または大扉用。作品の顔となる部分です。

```css
h1 {
  writing-mode: vertical-rl;
  text-align: center;
  font-size: 1.8em;
  font-weight: bold;
  margin-top: 3em;
  margin-bottom: 1em;
  line-height: 1.6;
  page-break-before: avoid;
  page-break-after: always;
}
```

### 7.2 h2（章見出し）

各章のタイトル。改ページで章を区切ります。`string-set` で柱に章タイトルを表示します。

```css
h2 {
  writing-mode: vertical-rl;
  text-align: center;
  page-break-before: always;
  string-set: chapter content();  /* 柱に章タイトルを設定 */
  margin-top: 2em;
  margin-bottom: 2em;
  font-size: 1.3em;
  font-weight: bold;
}
```

### 7.3 h3（節見出し）

章内のセクション区切り。改ページは不要です。

```css
h3 {
  writing-mode: vertical-rl;
  text-align: left;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-size: 1.1em;
  font-weight: bold;
}
```

### 7.4 見出し番号（全角数字）

```css
h2::before {
  content: "第" counter(chapter, cjk-ideographic) "章　";
}

h2 {
  counter-increment: chapter;
}
```

---

## 8. 段落スタイル

### 8.1 基本設定

日本語縦書き組版の基本：文頭1字下げ、行送り均一。

```css
p {
  text-indent: 1em;     /* 文頭1字下げ */
  margin-top: 0;        /* 上下マージンなし */
  margin-bottom: 0;     /* 行送りのリズムを保つ */
  line-height: 1.8;     /* 行送り（theme-bunkoの自動計算に任せる場合は省略可） */
}
```

### 8.2 字下げのバリエーション

```css
/* 字下げなし（会話文の冒頭など） */
p.no-indent {
  text-indent: 0;
}

/* 2字下げ（改段落の強調） */
p.deep-indent {
  text-indent: 2em;
}

/* 章の先頭段落は字下げなし（ドロップキャップ風にする場合） */
h2 + p {
  text-indent: 0;
}
```

### 8.3 行送りと行間

```css
/* 標準的な行送り */
p {
  line-height: 1.8;
}

/* やや詰め気味 */
p {
  line-height: 1.7;
}

/* ゆったり（読みやすさ重視） */
p {
  line-height: 2.0;
}
```

**注意**: `theme-bunko` の自動計算では、行数と余白からフォントサイズが決まります。
`line-height` を明示指定すると、行あふれやページ下部の空白が発生する可能性があるため、
基本的には指定せず、theme-bunkoの自動計算に任せることを推奨します。
調整が必要な場合は `line-height` より先に `--vs-theme--num-of-line` の変更を検討してください。

### 8.4 会話文・地の文の区別

```css
/* 会話文（かぎ括弧始まり）の直後の段落を字下げなしに */
p + p {
  /* 連続する段落はすべて字下げ（地の文） */
  text-indent: 1em;
}
```

---

## 9. 挿絵スタイル

### 9.1 全画面挿絵（デフォルト）

本スキルのデフォルト挙動。挿絵を1ページ全面に表示します。

```css
img[src*="image/"] {
  page-break-before: always;
  page-break-after: always;
  width: 100%;
  height: 100%;
  object-fit: contain;
  margin: 0 auto;
}
```

VFM（Markdown）での埋め込み：
```markdown
---

![狐火の夜](image/序章2.webp)

---
```

水平線 `---` が改ページを生成し、挿絵の前後でページが区切られます。

### 9.2 インライン挿絵（本文中に小さな画像を配置）

```css
img.inline {
  page-break-before: avoid;
  page-break-after: avoid;
  width: 50%;           /* 本文幅の50% */
  height: auto;
  float: right;         /* 縦書きでは右寄せ */
  margin: 1em;
}
```

### 9.3 右寄せ / 左寄せ挿絵（縦書きの場合）

縦書き右綴じでは、「右」がノド側（綴じ側）、「左」が小口側（開き側）になります。

```css
/* 小口側（左）に寄せる: 本文の流れの外側 */
img.float-left {
  float: left;
  width: 40%;
  height: auto;
  margin: 1em;
}

/* ノド側（右）に寄せる */
img.float-right {
  float: right;
  width: 40%;
  height: auto;
  margin: 1em;
}
```

### 9.4 表紙画像

```css
img[src*="cover"] {
  page-break-before: avoid;
  page-break-after: always;
  width: 100%;
  height: 100%;
  object-fit: contain;
  margin: 0 auto;
}
```

### 9.5 object-fit のバリエーション

| 値 | 効果 |
|----|------|
| `contain` | 縦横比を保ちつつ枠内に収める（余白が出る）— **デフォルト推奨** |
| `cover` | 枠全体を埋める（はみ出し部分はトリミング） |
| `fill` | 枠に合わせて伸縮（縦横比が崩れるため非推奨） |
| `scale-down` | `contain` または画像原寸の小さい方 |

---

## 10. ノンブル（ページ番号）

### 10.1 基本設定

```css
:root {
  /* ページ番号のフォント */
  --vs-theme--page-top-left-content: counter(page) "　" env(doc-title);
  --vs-theme--page-top-right-content: counter(page);
}
```

### 10.2 カスタマイズ例

```css
:root {
  /* パターンA: 両ページにページ番号のみ */
  --vs-theme--page-top-left-content: counter(page);
  --vs-theme--page-top-right-content: counter(page);

  /* パターンB: 右ページに番号、左ページに章タイトル */
  --vs-theme--page-top-left-content: string(chapter);
  --vs-theme--page-top-right-content: counter(page);

  /* パターンC: 数字を全角漢数字に変換 */
  --vs-theme--page-top-left-content: counter(page, cjk-ideographic);
  --vs-theme--page-top-right-content: counter(page, cjk-ideographic);

  /* パターンD: ノンブル非表示 */
  --vs-theme--page-top-left-content: none;
  --vs-theme--page-top-right-content: none;

  /* パターンE: 「- 42 -」形式（英語風） */
  --vs-theme--page-top-left-content: "- " counter(page) " -";
  --vs-theme--page-top-right-content: "- " counter(page) " -";
}
```

`counter(page)` の代わりに `string(chapter)` を使うことで、柱（章タイトル）を表示できます。
`string(chapter)` に値をセットするには、見出し要素で `string-set: chapter content();` を指定してください（§7.2参照）。

### 10.3 ノンブルの位置調整

`--vs-theme--page-top-*` 変数では位置の微調整が難しい場合、CSSを直接上書きします。

```css
/* theme-bunko が生成するノンブル要素のクラス */
.vs-page-top-left,
.vs-page-top-right {
  font-size: 0.8em;
  font-family: "游明朝", serif;
  margin-top: 5mm;
  margin-right: 8mm;
}
```

---

## 11. EPUB向けの注意事項

### 11.1 電書協EPUB3制作ガイド準拠

`@vivliostyle/theme-epub3j` は電書協EPUB3制作ガイドに準拠しています。
`epub-custom.css` で補完する際は以下の要件を遵守してください：

- **縦書き**: `writing-mode: vertical-rl` + `-epub-writing-mode: vertical-rl`
- **ルビ**: `ruby` 要素 + `ruby-align: start`
- **画像**: インライン配置 + ページ区切り
- **脚注**: ポップアップまたは巻末配置
- **ページプログレッション**: rtl（右から左）

### 11.2 EPUB特有のCSSプロパティ

```css
/* EPUB用ベンダープレフィックス */
html {
  -epub-writing-mode: vertical-rl;
}

body {
  -epub-writing-mode: vertical-rl;
}

/* 縦中横 */
.tatechuyoko {
  -epub-text-combine: horizontal;
  text-combine-upright: all;
}
```

### 11.3 EPUBにおける改ページ

EPUBはリフロー型であるため、`page-break-*` は「ページ区切り」として解釈されます。
EPUBリーダーによって解釈が異なる可能性があるため、以下を推奨：

```css
/* 章区切りは必ず page-break-before を指定 */
h2 {
  page-break-before: always;
  -epub-page-break-before: always;
}

/* 挿絵は独立したセクションとして */
img[src*="image/"] {
  page-break-before: always;
  page-break-after: always;
  -epub-page-break-before: always;
  -epub-page-break-after: always;
}
```

### 11.4 フォント埋め込み

EPUBにフォントを埋め込む場合：

1. プロジェクトに `fonts/` ディレクトリを作成し、.otf ファイルを配置
2. CSS で `@font-face` を宣言（相対パスで参照）
3. `vivliostyle.config.js` の `includeAssets` でフォントファイルを指定

```js
// vivliostyle.config.js（EPUB用）
module.exports = {
  // ...
  theme: '@vivliostyle/theme-epub3j',
  style: 'epub-custom.css',
  includeAssets: [
    'fonts/NotoSerifCJKjp-Regular.otf',
    'fonts/NotoSerifCJKjp-Bold.otf',
  ],
};
```

**ライセンス注意**: Noto Serif CJK JP は SIL Open Font License 1.1 で提供されており、EPUBへの埋め込み・再配布が許可されています。

### 11.5 EPUBリーダー互換性

```css
/* 画像の最大幅制限（リーダーの画面サイズに収める） */
img {
  max-width: 100%;
  max-height: 100vh;
}

/* リンクは装飾なし・色は本文に従う */
a {
  text-decoration: none;
  color: inherit;
}

/* 目次（nav）のスタイル */
nav[epub|type="toc"] {
  page-break-before: always;
}

nav[epub|type="toc"] ol {
  list-style: none;
  padding: 0;
  margin: 0;
}

nav[epub|type="toc"] li {
  margin: 0.5em 0;
}
```

---

## 12. トラブルシューティング

### 12.1 フォントが反映されない

**症状**: 指定したフォント（游明朝など）が反映されず、ゴシック体や別のフォントで表示される

**原因と対策**:

1. **フォントがインストールされていない**
   ```bash
   # インストール済みフォントの確認
   fc-list | grep -i "yumin\|noto.*cjk\|hiragino"
   ```

2. **VivliostyleのChromiumがフォントを認識していない**
   ```bash
   # Chromiumのキャッシュクリア
   rm -rf ~/.vivliostyle
   vivliostyle build --config vivliostyle.config.js
   ```

3. **WSL環境でWindowsフォントが見えていない**
   ```bash
   # WSLからWindowsフォントを参照できるようにする
   # /etc/fonts/local.conf に以下を追加
   # <dir>/mnt/c/Windows/Fonts</dir>
   fc-cache -fv
   ```

4. **フォント指定のスペルミス・誤ったフォント名**
   ```css
   /* 正しいフォント名（環境依存）を fc-list で確認する */
   body {
     font-family: "游明朝", "YuMincho", serif;
   }
   ```

### 12.2 ルビが崩れる

**症状**: ルビ文字が親文字から大きくずれる、または改行位置が不自然になる

**原因と対策**:

1. **`ruby-align` が未指定**
   ```css
   ruby {
     ruby-align: start; /* 必須 */
   }
   ```

2. **ルビ文字が長すぎる（親文字数を超えている）**
   - ルビ文字数が親文字数を超える場合、はみ出しや重なりが発生します
   - 対策: ルビを分割するか、`ruby-align: space-between` を試す
   ```css
   ruby.long-ruby {
     ruby-align: space-between;
   }
   ```

3. **縦書き時のルビ位置がおかしい**
   ```css
   ruby {
     ruby-position: over; /* 縦書きでは right 相当 */
   }
   ```

4. **VFMルビ記法のシンタックスエラー**
   ```markdown
   <!-- 正しい記法 -->
   {漢字|よみ}

   <!-- よくあるミス -->
   {漢字|よみ}     ← バックスラッシュ1つ（正: 2つ）
   {漢字｜よみ}     ← 全角パイプ（正: 半角 | ）
   ```

### 12.3 改ページが効かない

**症状**: 章見出しや挿絵の前後で改ページされない

**原因と対策**:

1. **CSSの優先順位の問題**
   ```css
   /* page-break-before を !important で強化 */
   h2 {
     page-break-before: always !important;
   }
   ```

2. **theme-bunko のデフォルトスタイルに打ち消されている**
   - `bunko-custom.css` が `vivliostyle.config.js` の `style` で正しく読み込まれているか確認

3. **Vivliostyle CLI のバージョンが古い**
   ```bash
   vivliostyle --version
   # v11.0.0 以上推奨
   npm update -g @vivliostyle/cli
   ```

4. **水平線が改ページにならない**
   ```css
   hr {
     page-break-after: always;
     visibility: hidden; /* 表示を消すが改ページは有効 */
     margin: 0;
     padding: 0;
     border: none;
   }
   ```

### 12.4 画像が表示されない

**症状**: 挿絵が出力されない、または画像が欠落する

**原因と対策**:

1. **画像パスの指定ミス**
   - 原稿mdからの相対パスであることを確認: `![説明](image/ファイル名.webp)`
   - `vivliostyle.config.js` の workingDirectory 設定を確認

2. **WebPフォーマット未対応**
   - Vivliostyle v11.0.0 は WebP 対応済みですが、古いバージョンでは非対応
   - 代替として PNG/JPEG を使用

3. **画像が大きすぎる**
   - 推奨サイズ: A6文庫見開き = 1200x1756px 程度
   - 大きすぎる画像は縮小するか、`object-fit: contain` で対応

4. **画像ファイルが存在しない**
   ```bash
   ls -la novel/image/
   # 存在確認 + ファイル名の大文字小文字に注意（WSLの場合は特に）
   ```

### 12.5 PDFで文字化けする

**症状**: 特定の漢字や記号が□（豆腐）になる

**原因と対策**:

1. **フォントにグリフが存在しない**
   - 游明朝にない漢字を別フォントでフォールバック
   ```css
   body {
     font-family: "游明朝", "Noto Serif CJK JP", "IPAmj明朝", serif;
   }
   ```

2. **外字・異体字の扱い**
   - IPAmj明朝フォントの導入を検討（戸籍統一文字などに対応）

### 12.6 ビルドに時間がかかりすぎる

**対策**:
```bash
# タイムアウト値の引き上げ
vivliostyle build --timeout 300 --config vivliostyle.config.js

# Dockerモード（Chromiumがない環境）
vivliostyle build --render-mode docker --config vivliostyle.config.js
```

---

## 13. 実践例: A6文庫14行35字の完全CSS設定

以下は `templates/bunko-custom.css` の同内容をドキュメント化したものです。
本スキルのデフォルト設定であり、実際のプロジェクトにそのまま使用できます。

```css
/* ================================================================
   novel2epub-jp: A6文庫版カスタムCSS
   テーマ: @vivliostyle/theme-bunko の変数上書きにより
          日本語縦書き小説の文庫本組版を実現します。

   対象: PDF出力（印刷・閲覧用）
   仕様: A6判 (105mm x 148mm) / 14行 x 35字 / 縦書き右綴じ
   ================================================================ */

/* ----------------------------------------------------------------
   1. ページ基本設定
   ---------------------------------------------------------------- */

/* 用紙サイズ: A6判 (105mm x 148mm) */
@page {
  size: 105mm 148mm;
}

/* ビューポート: 縦書き・右綴じ */
@viewport {
  writing-mode: vertical-rl;
}

/* ----------------------------------------------------------------
   2. theme-bunko 変数上書き
   ---------------------------------------------------------------- */

:root {
  /* 行数・字数: A6文庫版標準 (14行 x 35字) */
  --vs-theme--num-of-line: 14;
  --vs-theme--num-of-character: 35;

  /* ノンブル（ページ番号）設定
     右ページ（小口側）上部にページ番号のみ表示
     左ページ（ノド側）上部に「ページ番号 + 作品タイトル」を表示 */
  --vs-theme--page-top-left-content: counter(page) "　" env(doc-title);
  --vs-theme--page-top-right-content: counter(page);
}

/* ----------------------------------------------------------------
   3. 段落スタイル
   ---------------------------------------------------------------- */

/* 段落: 文頭1字下げ（縦書き日本語組版の基本）
   上下マージンなし（行送りでリズムを保つ） */
p {
  text-indent: 1em;
  margin-top: 0;
  margin-bottom: 0;
}

/* ----------------------------------------------------------------
   4. 章見出し（h2）
   ---------------------------------------------------------------- */

/* 章見出し: 縦書き中央揃え、章の先頭で改ページ
   string-set で柱（ページ上部の章名表示）に章タイトルを設定 */
h2 {
  writing-mode: vertical-rl;
  text-align: center;
  page-break-before: always;
  string-set: chapter content();
}

/* ----------------------------------------------------------------
   5. 挿絵スタイル
   ---------------------------------------------------------------- */

/* 挿絵: novel/image/ 以下の画像を1ページ全面に表示
   前後改ページで独立したページとして扱う */
img[src*="image/"] {
  page-break-before: always;
  page-break-after: always;
  width: 100%;
  height: 100%;
  object-fit: contain;
  margin: 0 auto;
}

/* ----------------------------------------------------------------
   6. ルビ（ふりがな）調整
   ---------------------------------------------------------------- */

/* ルビ: 親文字の先頭に揃えて配置
   Webkit系レンダラでの縦書きルビ位置を適正化 */
ruby {
  ruby-align: start;
}

/* ルビ文字サイズ: 親文字の半分（縦書きで読みやすく） */
rt {
  font-size: 0.5em;
  font-weight: normal;
}

/* ----------------------------------------------------------------
   7. 脚注
   ---------------------------------------------------------------- */

/* 脚注: ページ下部に配置（VFMの [^1] 記法に対応）
   Vivliostyle の footnote ポリシーに従い自動配置 */
.footnote {
  font-size: 0.8em;
  line-height: 1.4;
}

/* ----------------------------------------------------------------
   8. その他の調整
   ---------------------------------------------------------------- */

/* 水平線（---）: 改ページとして扱う
   VFMでは scene break として使用 */
hr {
  page-break-after: always;
  visibility: hidden;
  margin: 0;
  padding: 0;
  border: none;
}

/* 表紙ページ（cover画像） */
img[src*="cover"] {
  page-break-before: avoid;
  page-break-after: always;
  width: 100%;
  height: 100%;
  object-fit: contain;
  margin: 0 auto;
}
```

### 検証済みの設定組み合わせ

| 設定 | 行数 | 字数 | 用途 | 検証状態 |
|------|------|------|------|----------|
| A6文庫標準 | 14 | 35 | 本スキルのデフォルト | ✓ 検証済み |
| A6文庫（大活字） | 13 | 33 | 読みやすさ重視 | 設定例 |
| A5文芸誌 | 15 | 39 | theme-bunko デフォルト | theme標準 |
| B6単行本 | 14 | 37 | 単行本・新書 | 設定例 |

---

## 参考リンク

- Vivliostyle CLI 公式: https://vivliostyle.org/ja/
- theme-bunko リポジトリ: https://github.com/vivliostyle/themes/tree/main/packages/%40vivliostyle/theme-bunko
- 電書協 EPUB3 制作ガイド: https://ebpaj.jp/counsel/guide
- W3C 日本語組版要件 (JLReq): https://www.w3.org/TR/jlreq/
- Noto Serif CJK JP: https://github.com/googlefonts/noto-cjk

---

*本ガイドは novel2epub-jp v1.0 の一部であり、`templates/bunko-custom.css` および `templates/epub-custom.css` と整合しています。*
*各セクションのコード例は、コピー＆ペーストでそのまま使用可能です。*
