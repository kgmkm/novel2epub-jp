# novel2epub-jp 要件定義書 v1.1

作成日: 2026-05-29
ステータス: 策定中
ベースプロジェクト: 妖狐は、嗤う（/mnt/y/novel/yoko-project/）

---

## 1. 概要

### 1.1 目的

novel2hermes-jp で執筆した日本語小説Markdown原稿を、Vivliostyle CLIを使用して日本語縦書き組版のPDF・EPUBに変換するHermes Agentスキル。

本スキルの実装ファイル群は、OpenCode等のオーケストレーションツールが参照・実行できる構成とする。ファイルは自己完結的であり、外部ツールが読んで手順を再現できるように記述する。

### 1.2 対象ユーザ

- novel2hermes-jp または spicy_novel-jp で小説原稿を管理している著者
- 日本語縦書き文庫形式の電子書籍・印刷用PDFを作成したい著者
- コマンドラインで完結する組版パイプラインを求めている著者

### 1.3 前提スキル

- **novel2hermes-jp**: 企画・執筆・推敲（上流）
- **novel2epub-jp**: 組版・出力（下流、本スキル）

両スキルは独立して読み込み可能だが、併用を前提に設計する。

### 1.4 ベースプロジェクト: 「妖狐は、嗤う」

要件定義・テンプレート・テストは以下の実プロジェクトを基準に行う。

```
/mnt/y/novel/yoko-project/
├── AGENTS.md                    ← 作品ガイド（文体規則・禁止事項）
├── proposal.md                  ← 企画書（タイトル・あらすじ・テーマ）
├── character/                   ← キャラ設定
│   ├── 01-01-灯_6歳.md
│   ├── 01-02-灯_16歳.md
│   ├── 01-親-灯.md
│   ├── 02-九十九.md
│   ├── 03-焔鋼.md
│   └── 04-焔緋色.md
├── plot/                        ← プロット
│   ├── 序章.md
│   ├── 第1章.md
│   ├── 第2章.md
│   └── 第3章.md
└── novel/                       ← 原稿（本スキルの入力）
    ├── 序章-01.md
    ├── 第1章-01.md
    ├── 第2章-01.md
    ├── 第3章-01.md
    └── image/                   ← 挿絵
        ├── 序章2.webp           ← 1200x1756px
        ├── 序章4.webp
        ├── 一章1.webp
        ├── 二章3.webp
        ├── 三章5.webp
        └── 三章6.webp
```

- タイトル: 妖狐は、嗤う
- 著者: カガミカミ水鏡
- 全4章（序章 + 第1〜3章）・約1.6万字
- 挿絵6枚: 全画面表示前提のWebP（1200x1756px）

---

## 2. 入力仕様

### 2.1 原稿形式

| 項目 | 仕様 |
|------|------|
| フォーマット | Markdown (.md)、VFM拡張記法対応 |
| 文字エンコーディング | UTF-8 |
| 改行コード | LF（CRLFも許容） |

### 2.2 原稿ディレクトリ構造

`novel/*.md` を入力とし、ファイル名の辞書順で章順を決定する。

```
novel/
├── 序章-01.md       ← 辞書順ソートで正しく章順になる
├── 第1章-01.md
├── 第2章-01.md
├── 第3章-01.md
└── image/           ← 挿絵ディレクトリ（下位ディレクトリはentryに含めない）
    ├── 序章2.webp
    └── ...
```

**注意**: 日本語ファイル名の辞書順はlocale依存。`LC_ALL=ja_JP.UTF-8` 環境で正しくソートされることを前提とする。

### 2.3 挿絵仕様

| 項目 | 仕様 |
|------|------|
| 配置 | `novel/image/` ディレクトリ |
| フォーマット | WebP（優先）、JPEG/PNGも許容 |
| 命名規則 | `{章名}{連番}.webp`（例: `序章2.webp`, `三章5.webp`） |
| 解像度 | 1200x1756px（A6文庫版見開き相当） |
| 組版方法 | 画面一面に貼る（全ページ占有）。前後改ページ |
| VFM埋込 | 原稿md内に `![挿絵](image/序章2.webp)` で挿入位置を明示 |

### 2.4 VFMルビ記法

Markdown内で以下の記法を使用する。執筆時から使用を推奨するが、後付けにも対応する（§4.2参照）。

| 記法 | HTML出力 | 用途 |
|------|----------|------|
| `{漢字\|かんじ}` | `<ruby>漢字<rt>かんじ</rt></ruby>` | 単語ルビ |
| `{鋼\|はがね}` | `<ruby>鋼<rt>はがね</rt></ruby>` | 固有名詞 |
| `{焔 緋色\|ほむら ひいろ}` | 複数ルビ | フルネーム+ふりがな |
| `{九十九\|つくも}` | `<ruby>九十九<rt>つくも</rt></ruby>` | 固有名詞 |

「妖狐は、嗤う」での実例:
```markdown
{灯|あかり}は六つになったばかりだった。
{九十九|つくも}の{紅|くれない}の目が、灯を見下ろしていた。
{焔 緋色|ほむら ひいろ}が刀を構えた。
```

### 2.5 その他のVFM記法対応

| 記法 | 用途 | 備考 |
|------|------|------|
| `[^1]` / `[^1]: ...` | 脚注 | 電子書籍では底部に配置 |
| `---`（水平線） | 改ページ | scene breakとして扱う |
| `## 見出し` | 章見出し | h2推奨。h1は表題用 |
| `<!-- -->` メタデータ | VFMメタデータ | title/author定義可能 |

---

## 3. 出力仕様

### 3.1 出力形式

| 優先度 | 形式 | 拡張子 | 用途 | テーマ |
|--------|------|--------|------|--------|
| 1（主） | PDF | `.pdf` | 印刷・閲覧 | `@vivliostyle/theme-bunko` |
| 2 | EPUB | `.epub` | 電子書籍配信 | `@vivliostyle/theme-epub3j` |
| 3 | WebPub | - | ブラウザプレビュー | 開発用 |

テーマ・出力形式ともに設定変更可能。

### 3.2 PDF出力仕様

#### デフォルト: A6文庫版

| 項目 | デフォルト値 | CSS変数 | 備考 |
|------|-------------|---------|------|
| 用紙サイズ | `105mm × 148mm` (A6) | - | `size` 設定項目 |
| 書字方向 | 縦書き・右綴じ | `writing-mode: vertical-rl` | |
| 行数/ページ | 14行 | `--vs-theme--num-of-line` | |
| 字数/行 | 35字 | `--vs-theme--num-of-character` | |
| 段落字下げ | 1字下げ | `text-indent: 1em` | |
| ノンブル | ページ番号 | `--vs-theme--page-top-right-content` | |

#### 設定変更可能パラメータ

`vivliostyle.config.js` またはCSS変数で以下を変更可能：

- 用紙サイズ（A5, B5, B6, カスタムmm指定）
- 行数/ページ、字数/行
- 余白（上下左右・ノド・小口）
- フォントファミリー（游明朝、Noto Serif CJK JP等）
- フォントサイズ（自動計算 or 手動指定）
- ノンブル表示/非表示・位置
- 章見出しスタイル
- 表紙（cover）の有無・画像指定

### 3.3 EPUB出力仕様

| 項目 | 仕様 |
|------|------|
| テーマ | `@vivliostyle/theme-epub3j`（電書協EPUB3制作ガイド準拠） |
| 書字方向 | `readingProgression: rtl` |
| 言語 | `language: ja` |
| ルビ | HTML ruby要素として出力 |
| 画像 | 表紙画像・挿絵の埋め込み対応 |

### 3.4 出力ディレクトリ構造

```
{プロジェクトルート}/
└── dist/
    ├── 妖狐は、嗤う-bunko.pdf
    ├── 妖狐は、嗤う.epub
    └── preview/                ← WebPub（vivliostyle preview用）
```

タイトルは `vivliostyle.config.js` の `title` フィールドから取得。未設定時はプロジェクトディレクトリ名。

### 3.5 挿絵の組版ルール

挿絵は全画面表示（1ページ占有）とする:

```css
/* bunko-custom.css 内の挿絵スタイル */
.illustration {
  page-break-before: always;
  page-break-after: always;
  width: 100%;
  height: 100vw;  /* 縦書き時はvwが高さ方向 */
  object-fit: contain;
  margin: 0;
}
```

原稿md内での挿絵マークアップ:
```markdown
---

![序章の狐火の夜](image/序章2.webp)

---
```

水平線 `---` で前後改ページを保証する。

---

## 4. 機能要件

### 4.1 ビルドパイプライン

```
novel/*.md  ──→  VFM変換  ──→  HTML中間生成  ──→  Vivliostyle組版  ──→  PDF/EPUB
     │               │                                │
     │               │                                └── CSS（theme + bunko-custom.css）
     │               └── ルビ・脚注・メタデータ処理
     └── vivliostyle.config.js（エントリ・出力設定）
              │
              └── novel/image/*.webp（挿絵・表紙）
```

### 4.2 ルビ自動付与（オプション）

既存原稿にルビが未付与の場合、以下の手段で後付け可能にする：

| 手段 | 説明 | 優先度 |
|------|------|--------|
| **A. キャラ設定からの辞書生成** | `character/*.md` の「ふりがな」フィールドから `{漢字\|よみ}` 辞書を自動生成し、原稿に一括適用 | メイン |
| B. 対話的ルビ付与 | ユーザ指定の語にルビを追加（セッション内でAIが提案） | 補助 |
| C. MeCab形態素解析 | 固有名詞の読み推定（要人間確認） | 補助 |

「妖狐は、嗤う」のキャラシート例（`01-01-灯_6歳.md`）:
```markdown
| 氏名（ふりがな） | 灯（あかり） |
```
↓ 辞書エントリ生成:
```json
{"灯": "あかり"}
```

AGENTS.mdの「ふりがなルール」:
```
登場人物の初出時は、可能な限りふりがなを添える。
特に漢字が色名・物体名と誤読されうる名前は、フルネーム＋ふりがんで導入する。
（例：鋼（はがね）、焔 緋色（ほむら ひいろ））
```

### 4.3 vivliostyle.config.js テンプレート

スキル実行時にプロジェクトルートに `vivliostyle.config.js` を生成する。「妖狐は、嗤う」の例:

```js
module.exports = {
  title: '妖狐は、嗤う',
  author: 'カガミカミ水鏡',
  language: 'ja',
  readingProgression: 'rtl',
  entry: [
    'novel/序章-01.md',
    'novel/第1章-01.md',
    'novel/第2章-01.md',
    'novel/第3章-01.md',
  ],
  output: [
    {
      path: 'dist/妖狐は、嗤う-bunko.pdf',
      format: 'pdf',
    },
    {
      path: 'dist/妖狐は、嗤う.epub',
      format: 'epub',
    },
  ],
  theme: '@vivliostyle/theme-bunko',
  size: '105mm,148mm',
  style: 'bunko-custom.css',
  vfm: { hardLineBreaks: true },
  cover: 'novel/image/cover.jpg',
  toc: true,
};
```

### 4.4 bunko-custom.css（A6文庫14行×35字）

```css
/* ================================================
   novel2epub-jp: A6文庫版カスタムCSS
   テーマ: @vivliostyle/theme-bunko 上書き
   ================================================ */

:root {
  /* 行数・字数（A6文庫版） */
  --vs-theme--num-of-line: 14;
  --vs-theme--num-of-character: 35;

  /* ノンブル: 右ページ右上にページ番号 */
  --vs-theme--page-top-left-content: counter(page) '　' env(doc-title);
  --vs-theme--page-top-right-content: counter(page);
}

/* 段落: 1字下げ */
p {
  text-indent: 1em;
  margin-top: 0;
  margin-bottom: 0;
}

/* 章見出し: 中央・改ページ */
h2 {
  writing-mode: vertical-rl;
  text-align: center;
  page-break-before: always;
  string-set: chapter content();
}

/* 挿絵: 1ページ占有・全画面表示 */
img[src*="image/"] {
  page-break-before: always;
  page-break-after: always;
  width: 100%;
  height: 100%;
  object-fit: contain;
  margin: 0 auto;
}

/* 縦書きルビのWebkit調整 */
ruby {
  ruby-align: start;
}
rt {
  font-size: 0.5em;
  font-weight: normal;
}
```

### 4.5 EPUBテンプレート（epub3j.config.js）

```js
module.exports = {
  title: '妖狐は、嗤う',
  author: 'カガミカミ水鏡',
  language: 'ja',
  readingProgression: 'rtl',
  entry: [
    'novel/序章-01.md',
    'novel/第1章-01.md',
    'novel/第2章-01.md',
    'novel/第3章-01.md',
  ],
  output: [
    {
      path: 'dist/妖狐は、嗤う.epub',
      format: 'epub',
    },
  ],
  theme: '@vivliostyle/theme-epub3j',
  style: 'epub-custom.css',
  vfm: { hardLineBreaks: true },
  cover: 'novel/image/cover.jpg',
  toc: true,
};
```

### 4.6 プレビュー機能

`vivliostyle preview` によるブラウザプレビューをサポート。

```bash
# プレビュー起動
vivliostyle preview --config vivliostyle.config.js
```

### 4.7 ビルドコマンド

```bash
# PDF出力（デフォルト）
vivliostyle build --config vivliostyle.config.js

# EPUB出力
vivliostyle build --config vivliostyle.config.js -o dist/妖狐は、嗤う.epub -f epub

# PDF + EPUB 同時出力
vivliostyle build --config vivliostyle.config.js
```

---

## 5. オーケストレーション要件

### 5.1 前提

本スキルの実装ファイル群は、Hermes Agentが直接実行するだけでなく、OpenCode等の外部オーケストレーションツールが参照・実行できる構成とする。

### 5.2 ファイル構成（実装依頼対象）

各ファイルは自己完続的であり、外部ツールが読んで手順を再現できるように記述する。

```
/mnt/y/novel/skills/novel2epub-jp/
├── SKILL.md                       ← スキル本体（ロード時読込）
│                                     ・トリガー keywords
│                                     ・使用方法テーブル
│                                     ・参照ファイル一覧
│                                     ・注意点・確認リスト
├── references/
│   ├── vfm-syntax.md              ← VFM記法リファレンス（ルビ・脚注・圏点など）
│   ├── css-adjustment.md          ← CSS変数・縦書き組版微調整ガイド
│   └── publish-workflow.md        ← ビルド→確認→配信ワークフロー
│                                     ・初回セットアップ手順
│                                     ・ビルド手順
│                                     ・プレビュー確認手順
│                                     ・トラブルシューティング
├── templates/
│   ├── vivliostyle.config.js      ← A6文庫版テンプレート設定
│                                     ・entry/player/language/size既定値
│                                     ・PDF + EPUB output定義
│                                     ・コメントで各項目を解説
│   ├── bunko-custom.css           ← 14行35字カスタムCSS
│                                     ・theme-bunko変数上書き
│                                     ・縦書きルビ調整
│                                     ・挿絵全画面スタイル
│                                     ・段落・見出しスタイル
│   └── epub-custom.css            ← EPUB出力用カスタムCSS
│                                     ・電書協ガイド準拠
│                                     ・縦書き・ルビ・挿絵
└── scripts/
    └── ruby-dict.py               ← キャラ設定からのルビ辞書生成スクリプト
                                       ・character/*.md 読込
                                       ・ふりがなフィールド抽出
                                       ・{漢字|よみ} 形式の辞書生成
                                       ・原稿mdへの自動適用
```

### 5.3 OpenCode実行前提

OpenCodeが本スキルのファイル群を元にタスクを実行する場合、以下が利用可能である:

| ツール | 用途 | 備用 |
|------|------|------|
| `vivliostyle build` | PDF/EPUB生成 | v11.0.0インストール済み |
| `vivliostyle preview` | ブラウザプレビュー | |
| Node.js v22 | CLI実行環境 | v22.17.0インストール済み |
| Python 3 | ruby-dict.py実行 | |
| `@vivliostyle/theme-bunko` | PDF文庫テーマ | グローバルインストール済み |
| `@vivliostyle/theme-epub3j` | EPUB日本語テーマ | グローバルインストール済み |

---

## 6. 非機能要件

### 6.1 前提環境

| 項目 | 要件 | 現在 |
|------|------|------|
| Node.js | v18以上（v22推奨） | v22.17.0 ✓ |
| npm | v9以上 | v11.4.2 ✓ |
| Vivliostyle CLI | v11.0.0以上 | v11.0.0 ✓ |
| theme-bunko | 最新 | インストール済み ✓ |
| theme-epub3j | 最新 | インストール済み ✓ |
| OS | WSL2 / Linux / macOS | WSL2 ✓ |
| ブラウザ | Chrome系またはFirefox | プレビュー用 |

### 6.2 初回セットアップ手順

SKILL.mdに以下を記載し、初回起動時に確認:

```bash
# 1. 確認
vivliostyle --version   # → 11.0.0

# 2. 未インストールの場合
npm install -g @vivliostyle/cli @vivliostyle/theme-bunko @vivliostyle/theme-epub3j
```

### 6.3 パフォーマンス目安

- 1章（約8,000字）のPDF生成: 30秒以内
- 4章（約16,000字）一括PDF生成: 2分以内
- プレビュー起動: 10秒以内

### 6.4 エラーハンドリング

| エラー | 対応 |
|--------|------|
| entryファイル不在 | `novel/` ディレクトリに.mdファイルがありません |
| VFMパースエラー | 該当ファイル名と行番号を表示 |
| Vivliostyle未インストール | インストール手順を提示 |
| Chromium起動失敗 | Docker代替モード（`--render-mode docker`）を案内 |
| タイムアウト | `--timeout` 値の増加を提案 |
| 画像ファイル不在 | 警告を出しつつビルド継続（画像なしで出力） |

---

## 7. novel2hermes-jp との連携

### 7.1 データフロー

```
novel2hermes-jp                novel2epub-jp
─────────────                ─────────────
企画・執筆・推敲  →  novel/*.md  →  組版・出力
                      character/*.md → ルビ辞書生成
                      AGENTS.md      → タイトル・文体規則
                      proposal.md    → タイトル・著者名
   (上流)                        (下流)
```

### 7.2 連携ポイント

| 連携項目 | 内容 |
|----------|------|
| 原稿場所 | `novel/*.md` を共用 |
| 挿絵 | `novel/image/*.webp` を共用 |
| ふりがな | 執筆時から `{漢字\|よみ}` 記法を使用（推奨） |
| キャラ設定 | `character/*.md` からルビ辞書を自動生成可能 |
| AGENTS.md | タイトル・著者名・文体規則を参照 |
| proposal.md | タイトル・あらすじを参照 |

### 7.3 非連携時の動作

novel2hermes-jpを使用せず、任意のMarkdownファイルからでも組版可能。その場合は `entry` を手動指定する。

---

## 8. 制限事項

| 項目 | 制限 | 将来対応 |
|------|------|----------|
| 圏点（傍点） | VFM未対応. HTML直書き `<em style="text-emphasis: filled circle">` で対応 | VFM更新待ち |
| 割注 | ルビ記法とCSS併用で代替可能 | 専用記法追加検討 |
| 縦中横 | CSS対応. VFM記法なし. HTML直書き必要 | VFM更新待ち |
| WebP画像 | Vivliostyle CLI で対応済み | 問題なし |
| 目次 | `toc: true` で自動生成 | カスタムTOC対応検討 |
| 表紙画像 | 手動指定（cover フィールド） | テンプレート生成対応 |
| Web小説投稿 | なろう/カクヨムは別スキル対象 | pixiv-novel-archive連携 |

---

## 9. 用語定義

| 用語 | 定義 |
|------|------|
| VFM | Vivliostyle Flavored Markdown. ルビ・脚注等の出版向け拡張を持つMarkdown方言 |
| theme-bunko | Vivliostyle公式の文庫用テーマパッケージ. 縦書き・右綴じ既定値 |
| theme-epub3j | 電書協EPUB3制作ガイド準拠の日本語EPUBテーマ |
| ノド | 綴じる側の余白（縦書き右綴じ: 右側余白を広く） |
| 小口 | 綴じない側の余白（縦書き右綴じ: 左側余白） |
| ノンブル | ページ番号 |
| 全画面挿絵 | 1ページを占有する挿絵レイアウト |

---

## 10. 今後の拡張予定

1. 校正モード: 赤字・修正指示の可視化PDF出力
2. なろう/カクヨム投稿形式変換（別スキル or 拡張）
3. シリーズ作品の巻管理
4. Docker環境でのビルド対応（CI/CD用）
5. 表紙画像のテンプレート生成

---

*この要件定義書は novel2epub-jp v1.0 開発の基準文書です。*
*実装は OpenCode オーケストレーションを前提に、各ファイルが自己完続的であること。*