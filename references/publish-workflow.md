# ビルド → 確認 → 配信ワークフロー

novel2epub-jp スキルを使用して、Markdown 原稿から印刷用PDF・電子書籍EPUBを生成し、
配信するまでの実践的な手順書です。

## 目次

- [ワークフローマップ](#ワークフローマップ)
- [1. 初回セットアップ](#1-初回セットアップ)
- [2. プロジェクト初期化](#2-プロジェクト初期化)
- [3. ルビ付与（オプション）](#3-ルビ付与オプション)
- [4. ビルド手順](#4-ビルド手順)
- [5. プレビュー](#5-プレビュー)
- [6. 出力確認](#6-出力確認)
- [7. 配信](#7-配信)
- [8. トラブルシューティング](#8-トラブルシューティング)
- [付録：コマンド早見表](#付録コマンド早見表)

---

## ワークフローマップ

```
[原稿準備] → [ルビ付与] → [config設定] → [プレビュー] → [ビルド] → [確認] → [配信]
 novel/*.md   ruby-dict.py  vivliostyle    vivliostyle   vivliostyle   dist/     note / 印刷所
 執筆済み      辞書生成      .config.js     preview       build         PDF/EPUB   入稿
```

| 段階 | 作業内容 | 所要時間目安 |
|------|---------|-------------|
| 原稿準備 | `novel/*.md` の執筆完了、挿絵配置 | 作品による |
| ルビ付与 | `ruby-dict.py` で固有名詞にふりがな一括付与 | 1分以内 |
| config設定 | `vivliostyle.config.js` の title/author/entry 編集 | 5分 |
| プレビュー | `vivliostyle preview` でブラウザ確認 | 起動10秒 + 確認 |
| ビルド | PDF / EPUB 生成 | 1〜2分 |
| 確認 | 出力ファイルの目視チェック | 5〜10分 |
| 配信 | note公開 or 印刷所入稿 | 5〜10分 |

---

## 1. 初回セットアップ

### 1.1 前提環境

| 項目 | 要件 | 確認コマンド |
|------|------|-------------|
| Node.js | v18 以上（v22 推奨） | `node --version` |
| npm | v9 以上 | `npm --version` |
| Python 3 | 3.8 以上（ruby-dict.py 用） | `python3 --version` |

### 1.2 Vivliostyle CLI のインストール

Vivliostyle CLI と日本語組版用テーマパッケージをグローバルインストールします。

```bash
npm install -g @vivliostyle/cli @vivliostyle/theme-bunko @vivliostyle/theme-epub3j
```

パッケージの内容：

| パッケージ | 用途 |
|-----------|------|
| `@vivliostyle/cli` | 組版エンジン CLI。PDF/EPUB 生成、プレビュー起動 |
| `@vivliostyle/theme-bunko` | A6文庫版テーマ。縦書き右綴じ、A6判（105mm×148mm） |
| `@vivliostyle/theme-epub3j` | 電書協EPUB3制作ガイド準拠の日本語EPUBテーマ |

### 1.3 動作確認

```bash
vivliostyle --version
# 出力例: @vivliostyle/cli v11.0.0

npm ls -g @vivliostyle/theme-bunko @vivliostyle/theme-epub3j
# theme-bunko と theme-epub3j が表示されればOK
```

> **Note**: Vivliostyle CLI は内部で Chromium を使用してPDFをレンダリングします。
> 初回実行時に Chromium が自動ダウンロードされるため、初回ビルドのみ時間がかかります。

---

## 2. プロジェクト初期化

### 2.1 プロジェクト構造の確認

本スキルが前提とするプロジェクト構造：

```
{プロジェクトルート}/
├── novel/                    ← 原稿（必須）
│   ├── 序章-01.md
│   ├── 第1章-01.md
│   ├── 第2章-01.md
│   ├── 第3章-01.md
│   └── image/                ← 挿絵（任意）
│       ├── 序章2.webp
│       └── ...
├── character/                ← キャラ設定（任意、ルビ辞書生成に使用）
│   ├── 01-灯_6歳.md
│   └── ...
└── vivliostyle.config.js     ← 設定ファイル（スキル実行時に配置）
```

### 2.2 テンプレートのコピー

スキルのテンプレートをプロジェクトルートにコピーします。

```bash
# vivliostyle.config.js をプロジェクトルートにコピー
cp /mnt/y/novel/skills/novel2epub-jp/templates/vivliostyle.config.js ./

# カスタムCSS も必要に応じてコピー
cp /mnt/y/novel/skills/novel2epub-jp/templates/bunko-custom.css ./
cp /mnt/y/novel/skills/novel2epub-jp/templates/epub-custom.css ./
```

### 2.3 entry 一覧の設定方法

`vivliostyle.config.js` の `entry` 配列に、組版対象の全 Markdown ファイルを
**ファイル名の辞書順**で列挙します。

```js
entry: [
  'novel/序章-01.md',
  'novel/第1章-01.md',
  'novel/第2章-01.md',
  'novel/第3章-01.md',
],
```

重要なポイント：

- `novel/` 直下の `.md` ファイルのみを列挙する（`novel/image/` 以下の画像は含めない）
- 日本語ファイル名の辞書順はロケール依存。`LC_ALL=ja_JP.UTF-8` 環境で正しくソートされることを前提とする
- ファイル名の命名規則によって章順が決まる（例：`序章-01.md` → `第1章-01.md` → `第2章-01.md`）

entry 一覧を手軽に生成するには：

```bash
# novel/ 以下の .md ファイルを辞書順に列挙
ls novel/*.md | sort | sed "s/^/  '/; s/$/',/"
```

### 2.4 title / author の設定

`vivliostyle.config.js` の以下の項目を作品に合わせて編集します。

```js
module.exports = {
  title: '妖狐は、嗤う',          // ← 作品タイトルに変更
  author: 'カガミカミ水鏡',       // ← 著者名に変更
  language: 'ja',                 // 日本語固定
  readingProgression: 'rtl',      // 縦書き右綴じ固定
  // ...
  output: [
    {
      path: 'dist/妖狐は、嗤う-bunko.pdf',  // ← タイトルに合わせて変更
      format: 'pdf',
    },
    {
      path: 'dist/妖狐は、嗤う.epub',       // ← タイトルに合わせて変更
      format: 'epub',
    },
  ],
};
```

`title` は出力ファイル名とEPUBメタデータの両方に使用されます。`author` はEPUBの `dc:creator` に反映されます。

### 2.5 設定項目のカスタマイズ（任意）

必要に応じて以下の項目を有効化・編集します。

```js
// カスタムCSS（行数・字数・余白の調整）
style: 'bunko-custom.css',

// 用紙サイズ変更（デフォルト: A6判 105mm×148mm）
size: '148mm,210mm',  // A5判に変更する例

// 表紙画像
cover: 'novel/image/cover.jpg',

// 目次自動生成
toc: true,

// VFM オプション（段落内改行を <br> に変換）
vfm: { hardLineBreaks: true },
```

---

## 3. ルビ付与（オプション）

`scripts/ruby-dict.py` を使用して、`character/*.md` のキャラクター設定から
ルビ辞書を自動生成し、原稿に `{漢字|よみ}` 形式のふりがなを一括付与します。

### 3.1 辞書の生成元

`character/*.md` の「氏名（ふりがな）」行から抽出します。

```markdown
| 氏名（ふりがな） | 灯（あかり） |
| 氏名（ふりがな） | 九十九（つくも） |
| 氏名（ふりがな） | 焔 緋色（ほむら ひいろ） |
```

↓ 以下の辞書エントリが生成される

```
「灯」 → 「あかり」
「九十九」 → 「つくも」
「焔 緋色」 → 「ほむら ひいろ」
```

### 3.2 ドライラン（変更内容の確認）

```bash
python3 /mnt/y/novel/skills/novel2epub-jp/scripts/ruby-dict.py \
  --project-dir /mnt/y/novel/yoko-project/ \
  --dry-run
```

ドライランでは、変更される行とその差分が表示されます。ファイルは一切変更されません。
変更内容を確認してから次のステップに進んでください。

### 3.3 ルビの適用（ファイル上書き）

```bash
python3 /mnt/y/novel/skills/novel2epub-jp/scripts/ruby-dict.py \
  --project-dir /mnt/y/novel/yoko-project/ \
  --in-place
```

スクリプトの保護機能：

- 既存の `{漢字|よみ}` ルビを保護（二重付与しない）
- 既存の `漢字（よみ）` 表記も保護
- 最長一致で辞書キーを置換（複合名「焔 緋色」が「焔」単体より優先される）

> **推奨**: ルビ付与後、原稿を `--dry-run` の差分で確認し、問題がなければコミットしてください。
> 手動でのルビ調整が必要な場合は、原稿内で直接 `{漢字|よみ}` を編集します。

---

## 4. ビルド手順

`vivliostyle build` コマンドで PDF と EPUB を生成します。
プロジェクトルート（`vivliostyle.config.js` があるディレクトリ）で実行してください。

### 4.1 PDF 出力（A6文庫版）

```bash
# vivliostyle.config.js に定義された output に従いビルド
vivliostyle build --config vivliostyle.config.js
```

出力先：`dist/{タイトル}-bunko.pdf`

### 4.2 EPUB 出力（電書協EPUB3準拠）

```bash
# EPUB 単体で出力（theme-epub3j を使用）
vivliostyle build \
  --config vivliostyle.config.js \
  -f epub \
  -o dist/妖狐は、嗤う.epub
```

出力先：`dist/{タイトル}.epub`

### 4.3 ビルドオプション

```bash
# カスタムCSS を指定してビルド
vivliostyle build --config vivliostyle.config.js --style bunko-custom.css

# 印刷用PDF（press-ready、トンボ付き）
vivliostyle build --config vivliostyle.config.js --press-ready

# カスタムCSS + 印刷用、同時指定
vivliostyle build --config vivliostyle.config.js \
  --style bunko-custom.css \
  --press-ready

# タイムアウト延長（画像が多い場合）
vivliostyle build --config vivliostyle.config.js --timeout 600
```

| オプション | 効果 |
|-----------|------|
| `--style <file>` | カスタムCSSを適用（theme のスタイルを上書き） |
| `--press-ready` | 印刷用PDF（トンボ付き）を出力 |
| `--timeout <秒>` | ビルドタイムアウトを延長（デフォルト: 120秒） |
| `--render-mode docker` | Dockerコンテナ上でChromiumを実行 |
| `-f <format>` | 出力形式を明示（pdf, epub, webpub） |
| `-o <path>` | 出力先パスを指定 |

---

## 5. プレビュー

### 5.1 プレビューの起動

```bash
vivliostyle preview --config vivliostyle.config.js
```

起動後、ブラウザで以下のURLを開きます。

```
http://localhost:13000
```

ファイル変更を監視して自動リロードされるため、原稿やCSSの編集 → 即座に確認
というサイクルで作業できます。

### 5.2 確認ポイント

プレビュー画面で以下を重点的に確認してください。

| 確認項目 | チェック内容 |
|---------|-------------|
| **ページ送り** | 縦書き右綴じで正しくページが進むか |
| **ルビ** | ふりがなが正しい文字に付与されているか。親文字の先頭に揃っているか |
| **脚注** | `[^1]` 記法の脚注がページ下部に正しく表示されているか |
| **挿絵位置** | 意図した位置に全画面表示されているか。前後改ページされているか |
| **ノンブル** | ページ番号が右上（小口側）に表示されているか |
| **章見出し** | h2 見出しが中央揃えで改ページされているか |
| **字下げ** | 段落の先頭が1字下げされているか |
| **フォント** | 日本語フォント（游明朝 / Noto Serif CJK JP）で表示されているか |

### 5.3 プレビューの停止

ターミナルで `Ctrl+C` を押してプレビューサーバーを停止します。

---

## 6. 出力確認

ビルド後、`dist/` ディレクトリに生成されたファイルを開いて最終確認します。

```
dist/
├── 妖狐は、嗤う-bunko.pdf   ← A6文庫版PDF
└── 妖狐は、嗤う.epub        ← EPUB電子書籍
```

### 6.1 PDF の確認項目

- [ ] 全ページが正しい順序で生成されているか
- [ ] 文字化け・豆腐（□）がないか
- [ ] 挿絵が正しい位置に表示されているか
- [ ] ルビが潰れずに読めるか
- [ ] ノンブル（ページ番号）が正しいか
- [ ] 印刷時の仕上がりサイズが適切か（A6: 105mm×148mm）
- [ ] プリンターで1ページ試し刷りして余白・文字サイズを確認（推奨）

### 6.2 EPUB の確認項目

- [ ] EPUBリーダー（iBooks, Kindle, 紀伊國屋Kinoppy等）で開けるか
- [ ] 縦書き右綴じで表示されるか
- [ ] 目次（toc）が機能するか
- [ ] ルビが正しく表示されるか
- [ ] 表紙画像が表示されるか（cover 設定時）
- [ ] EPUB Validation を通るか（[EPUB-Checker](https://www.pagina.gmbh/produkte/epub-checker/) 等で確認）

---

## 7. 配信

### 7.1 note 公開（PDF埋め込み）

note クリエイターページでPDFを埋め込み公開する手順：

1. note にログインし、新規記事を作成
2. 本文に概要・あらすじを記述
3. PDF埋め込みボタンから `dist/{タイトル}-bunko.pdf` をアップロード
4. プレビューで表示を確認し、公開

> **Note**: note のPDF埋め込みは横書き表示が前提です。縦書きPDFは埋め込み時に
> 見開き表示にならない場合があります。閲覧者には「ダウンロードして縦書き表示して
> お読みください」と案内することを推奨します。

### 7.2 同人誌印刷（オフセット / オンデマンド）

印刷所に入稿する場合の手順：

```bash
# 印刷用PDF（press-ready モード）でビルド
vivliostyle build --config vivliostyle.config.js \
  --style bunko-custom.css \
  --press-ready \
  -o dist/妖狐は、嗤う-印刷用.pdf
```

`--press-ready` オプションにより以下が適用されます：

- トンボ（トリムマーク）の追加
- ドブ（塗り足し）領域の確保
- 印刷用カラープロファイル（CMYK変換は別途必要）

印刷所入稿時のチェックリスト：

- [ ] トンボ付きPDFが生成されているか
- [ ] ページ数が印刷所の規定（通常4の倍数）を満たしているか
- [ ] ノド（綴じ側）の余白が十分か（右ページ左側 / 左ページ右側）
- [ ] フォントが埋め込まれているか（PDFプロパティで確認）
- [ ] 印刷所の入稿規定（ファイル形式・サイズ・カラーモード）に準拠しているか

### 7.3 電子書籍ストア配信

EPUB を各ストアに配信する場合：

| ストア | 補足 |
|--------|------|
| Amazon Kindle | EPUB → Kindle Previewer で .mobi/.kfx に変換 |
| 紀伊國屋 Kinoppy | EPUB をそのまま入稿可能 |
| BOOK☆WALKER | EPUB をそのまま入稿可能 |
| 楽天Kobo | EPUB をそのまま入稿可能（Kobo Writing Life） |
| BOOTH（pixiv） | EPUB をそのまま販売可能 |

> **Note**: 各ストアの入稿規定（ファイルサイズ制限・DRM要否・ISBN要否）を事前に確認してください。

---

## 8. トラブルシューティング

### 8.1 Chromium が起動しない

```
Error: Failed to launch the browser process!
```

**原因**: WSL2 / Docker / サーバー環境で Chromium が直接実行できない。

**解決策**: Docker 経由で Chromium を実行する。

```bash
vivliostyle build --config vivliostyle.config.js --render-mode docker
```

事前に Docker がインストールされ、デーモンが起動していることを確認してください。

```bash
docker --version
docker ps  # デーモン起動確認
```

### 8.2 ビルドがタイムアウトする

```
Error: Timeout. Exporting pages has been timed out.
```

**原因**: ページ数が多い、画像が多い、マシンの処理性能不足。

**解決策**: タイムアウト値を延長する。

```bash
vivliostyle build --config vivliostyle.config.js --timeout 600
```

デフォルトのタイムアウトは 120 秒です。600（10分）程度まで延長して様子を見てください。

### 8.3 画像が表示されない

**原因**: 画像ファイルのパスが解決できていない。
Vivliostyle は `entry` ファイルからの相対パスで画像を探します。

**解決策①**: `copyAsset` 設定を有効にする（Vivliostyle v11+）。

```js
// vivliostyle.config.js
module.exports = {
  // ...
  copyAsset: true,  // 画像アセットをビルドディレクトリにコピー
};
```

**解決策②**: 画像パスを確認する。

```markdown
<!-- 原稿が novel/序章-01.md の場合 -->
<!-- 正しい（原稿からの相対パス） -->
![挿絵](image/序章2.webp)

<!-- 誤り（絶対パスは解決されない） -->
![挿絵](/mnt/y/novel/yoko-project/novel/image/序章2.webp)
```

**解決策③**: 画像ファイルの存在確認。

```bash
ls -la novel/image/
```

### 8.4 フォントが中華フォントになる

**原因**: CSS で日本語フォントが明示指定されておらず、
Chromium が中国語フォントをフォールバックに選択している。

**解決策**: `bunko-custom.css` に日本語フォントを明示指定する。

```css
:root {
  /* 游明朝 → Noto Serif CJK JP → 明朝系フォールバック */
  --vs-theme--font-family: "游明朝", "YuMincho", "Noto Serif CJK JP",
    "Hiragino Mincho Pro", "MS 明朝", serif;
}
```

Noto Serif CJK JP をインストールしていない場合：

```bash
# WSL2 / Ubuntu
sudo apt install fonts-noto-cjk
```

### 8.5 EPUB が Invalid（バリデーションエラー）

**原因**: EPUB の構造が電書協EPUB3ガイドに準拠していない。

**解決策**:

1. `theme-epub3j` を使用しているか確認する

```bash
npm ls -g @vivliostyle/theme-epub3j
```

2. EPUB 出力時に `theme-epub3j` を明示指定する

```bash
vivliostyle build \
  --config vivliostyle.config.js \
  --theme @vivliostyle/theme-epub3j \
  -f epub \
  -o dist/output.epub
```

3. EPUB-Checker で検証する

```bash
# EPUB-Checker（Java製）をダウンロードして実行
java -jar epubcheck.jar dist/output.epub
```

### 8.6 ルビが二重に付与される

**原因**: 原稿に既存の `{漢字|よみ}` があり、さらに `ruby-dict.py --in-place` を実行した。

**解決策**: `ruby-dict.py` は既存ルビを保護する機能を持っていますが、
何らかの理由で保護が効かない場合は `--dry-run` で差分を確認し、
問題のある行を手動で修正してください。

```bash
# 必ず --dry-run で事前確認する
python3 scripts/ruby-dict.py --project-dir ./ --dry-run
```

### 8.7 vivliostyle.config.js が見つからない

```
Error: Config file "vivliostyle.config.js" does not exist.
```

**解決策**: プロジェクトルートに設定ファイルをコピーする。

```bash
cp /mnt/y/novel/skills/novel2epub-jp/templates/vivliostyle.config.js ./
# title / author / entry を編集
```

または `--config` で明示的にパスを指定する。

```bash
vivliostyle build --config /path/to/vivliostyle.config.js
```

---

## 付録：コマンド早見表

```bash
# === 初回セットアップ ===
npm install -g @vivliostyle/cli @vivliostyle/theme-bunko @vivliostyle/theme-epub3j
vivliostyle --version

# === プロジェクト初期化 ===
cp /mnt/y/novel/skills/novel2epub-jp/templates/vivliostyle.config.js ./
cp /mnt/y/novel/skills/novel2epub-jp/templates/bunko-custom.css ./
cp /mnt/y/novel/skills/novel2epub-jp/templates/epub-custom.css ./

# === ルビ付与 ===
# ドライラン
python3 /mnt/y/novel/skills/novel2epub-jp/scripts/ruby-dict.py \
  --project-dir /path/to/project --dry-run
# 適用
python3 /mnt/y/novel/skills/novel2epub-jp/scripts/ruby-dict.py \
  --project-dir /path/to/project --in-place

# === プレビュー ===
vivliostyle preview --config vivliostyle.config.js
# → http://localhost:13000

# === ビルド ===
# PDF + EPUB（vivliostyle.config.js の output 定義に従う）
vivliostyle build --config vivliostyle.config.js

# PDF のみ（カスタムCSS + 印刷用）
vivliostyle build --config vivliostyle.config.js \
  --style bunko-custom.css --press-ready

# EPUB のみ
vivliostyle build --config vivliostyle.config.js \
  -f epub -o dist/title.epub

# === トラブルシューティング ===
# Docker 経由でビルド
vivliostyle build --config vivliostyle.config.js --render-mode docker

# タイムアウト延長
vivliostyle build --config vivliostyle.config.js --timeout 600
```

---

*このドキュメントは novel2epub-jp v1.0 の一部です。*
*最新の情報は `/mnt/y/novel/skills/novel2epub-jp/SKILL.md` を参照してください。*
