# novel2epub-jp

日本語縦書き小説を、しっぽり明朝埋め込みのA6文庫PDFおよびEPUBに変換するHermes Agentスキル。

| EPUB（Thorium Reader） | PDF（Adobe Acrobat） |
|:---:|:---:|
| ![EPUB作例](image/preview_epub_thorium.webp) | ![PDF作例](image/preview_pdf_adobe_reader.webp) |
| 『妖狐は、嗤う』第1章 | 『妖狐は、嗤う』見開き表示 |

## 機能

- **PDF生成** (`build-pdf.py`)
  - Puppeteer + PyMuPDFによる高品質縦書きPDF
  - しっぽり明朝（Shippori Mincho）Regular/Bold埋め込み
  - 章ヘッダ / ページ番号（ノンブル）の位置・表示制御
  - 挿絵サイズ（小/中/大）+ キャプション表示切替
  - JLREQ準拠（始め括弧の字下げ禁止、半角数字→全角/縦中横）
  - VFMルビ記法 `{漢字|よみ}` 対応

- **EPUB生成**
  - Vivliostyle CLI + `@vivliostyle/theme-epub3j` を使用

## インストール

### 前提

```bash
# Node.js
npm install -g puppeteer-core @vivliostyle/vfm

# Python
pip install pymupdf fonttools
```

ChromeはVivliostyle CLI経由で自動インストールされます。

### フォント

プロジェクトルートに以下を配置：

```
fonts/
├── ShipporiMincho-Regular.woff2
└── ShipporiMincho-Bold.woff2
```

（Google FontsのShippori MinchoをWOFF2に変換して配置）

## 基本的な使い方

### プリセットで素早く生成（おすすめ）

```bash
# プリセット一覧を確認
python3 scripts/build-pdf.py --list-presets

# showcase-small: 挿絵小+キャプションあり（ショーケース用）
python3 scripts/build-pdf.py --preset showcase-small --project-dir . --output dist/book.pdf

# showcase-large: 挿絵大フルブリード（迫力重視）
python3 scripts/build-pdf.py --preset showcase-large --project-dir . --output dist/book.pdf

# clean-small: 挿絵小のみ（キャプションなし）
python3 scripts/build-pdf.py --preset clean-small --project-dir . --output dist/book.pdf
```

### 個別オプションで細かく制御

```bash
python3 /path/to/novel2epub-jp/scripts/build-pdf.py \
  --project-dir /path/to/your-novel \
  --output dist/book.pdf \
  --image-size large \
  --image-caption off
```

プリセットを指定した上で、個別オプションでオーバーライドも可能：

```bash
# showcase-small のベースに caption だけ off にする
python3 scripts/build-pdf.py --preset showcase-small --image-caption off --project-dir .
```

### プリセット一覧

| プリセット名 | 挿絵サイズ | キャプション | 章ヘッダ | ページ番号 | 用途 |
|-------------|-----------|-------------|---------|-----------|------|
| showcase-small | 小 | on | even/左 | all/交互 | ショーケース用（挿絵小＋説明） |
| showcase-medium | 中 | on | even/左 | all/交互 | ショーケース用（挿絵中＋説明） |
| showcase-large | 大 | off | even/左 | all/交互 | ショーケース用（挿絵フルブリード） |
| clean-small | 小 | off | even/左 | all/交互 | 配布用（挿絵小のみ） |
| clean-medium | 中 | off | even/左 | all/交互 | 配布用（挿絵中のみ） |
| clean-large | 大 | off | even/左 | all/交互 | 配布用（挿絵大のみ） |
| minimal | 小 | off | なし | all/中央 | シンプル（ヘッダなし） |

### 主なオプション

| オプション | 値 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `--image-size` | small / medium / large | small | 挿絵の表示サイズ |
| `--image-caption` | on / off | on | 挿絵下の説明文（figcaption）の表示 |
| `--chapter-header-display` | all / even / odd / none | all | 章ヘッダの表示ページ |
| `--page-number-display` | all / even / odd | all | ページ番号の表示ページ |

詳細は `scripts/build-pdf.py --help` を参照。

## novel2hermes_jp との連携

このスキルは `novel2hermes_jp` で執筆したMarkdown原稿を入力として想定していますが、以下の条件を満たせば単独でも使用可能です：

- `novel/*.md` に原稿が配置されている
- ルビはVFM記法 `{漢字|よみ}` で記述
- 挿絵は `novel/image/` 以下に配置し、Markdown内で `![alt](image/xxx.webp)` と参照

## ライセンス

- スキル本体: MIT
- 同梱フォント（しっぽり明朝）: SIL Open Font License 1.1

## 関連リポジトリ

- [novel2hermes_jp](https://github.com/kgmkm/novel2hermes_jp) — 執筆支援スキル（本スキルの上流）
- [novel2epub-jp_sample](https://github.com/kgmkm/novel2epub-jp_sample) — 生成サンプル（EPUB + PDF）
- [vfm-syntax](https://github.com/kgmkm/vfm-syntax) — VFM記法リファレンス
- [jlreq-skill](https://github.com/kgmkm/jlreq-skill) — W3C日本語組版ルール