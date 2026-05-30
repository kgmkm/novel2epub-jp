/**
 * ============================================================
 * novel2epub-jp: Vivliostyle CLI 設定（A6文庫版テンプレート）
 * ============================================================
 *
 * このファイルをプロジェクトルートに配置し、以下の項目を編集してください。
 *   - title: 作品タイトル
 *   - author: 著者名
 *   - entry: 原稿ファイル一覧（novel/ 以下の .md を辞書順に列挙）
 *
 * 編集後、以下のコマンドで PDF + EPUB を同時生成します。
 *   vivliostyle build
 *
 * 個別出力やプレビューは以下を参照：
 *   vivliostyle build -o dist/output.pdf -f pdf
 *   vivliostyle preview
 */

module.exports = {
  /**
   * 作品タイトル（必須）
   * 出力ファイル名とEPUBメタデータに使用されます。
   * プレースホルダを作業対象のタイトルに置き換えてください。
   */
  title: '作品タイトル',

  /**
   * 著者名（必須）
   * EPUBメタデータ（dc:creator）に使用されます。
   */
  author: '著者名',

  /**
   * 言語（必須）
   * 日本語指定。EPUBのメタデータとハイフネーションに影響します。
   */
  language: 'ja',

  /**
   * 読み方向（必須）
   * 'rtl' = right-to-left。縦書き右綴じの日本語書籍で必須です。
   * EPUBの readingProgression にも反映されます。
   */
  readingProgression: 'rtl',

  /**
   * エントリファイル（必須）
   * 組版対象のMarkdown原稿一覧。
   * novel/ ディレクトリ以下の .md ファイルを辞書順で列挙してください。
   *
   * 注意：日本語ファイル名の辞書順はロケール依存です。
   * LC_ALL=ja_JP.UTF-8 環境で正しくソートされることを前提とします。
   * novel/image/ 以下の画像ディレクトリは entry に含めないでください。
   *
   * 例（「妖狐は、嗤う」4章構成の場合）：
   *   'novel/序章-01.md',
   *   'novel/第1章-01.md',
   *   'novel/第2章-01.md',
   *   'novel/第3章-01.md',
   */
  entry: [
    // TODO: novel/ 以下の .md ファイルを辞書順でここに列挙してください。
    // 例:
    // 'novel/序章-01.md',
    // 'novel/第1章-01.md',
  ],

  /**
   * 出力設定（必須）
   * PDF（A6文庫版）と EPUB（電子書籍）の両方を生成します。
   *
   * 出力先：dist/ ディレクトリ
   *   - PDF: dist/{タイトル}-bunko.pdf
   *   - EPUB: dist/{タイトル}.epub
   *
   * 単一形式のみ出力する場合は不要な方を削除してください。
   */
  output: [
    {
      // A6文庫版PDF出力（theme-bunko使用・縦書き右綴じ）
      path: 'dist/作品タイトル-bunko.pdf',
      format: 'pdf',
      theme: '@vivliostyle/theme-bunko',
      style: 'bunko-custom.css',
      size: '105mm,148mm',
    },
    {
      // EPUB出力（電子書籍配信用・theme-epub3j使用・縦書き右綴じ）
      path: 'dist/作品タイトル.epub',
      format: 'epub',
      theme: '@vivliostyle/theme-epub3j',
      style: 'epub-custom.css',
      readingProgression: 'rtl',
    },
  ],

  /**
   * 目次（toc）
   * true にすると見出し（h2）から目次を自動生成します。
   * 章見頭に h2 を使用している場合に有効です。
   */
  toc: true,

  /**
   * EPUBアセット制御（重要：画像埋め込み用）
   * novel/image/ 以下の挿絵をEPUBに正しく埋め込むため includes を指定。
   * 不要なディレクトリは excludes で除外してEPUB肥大化を防止。
   *
   * 画像埋め込みのため novel/image/** を明示的に含める。
   */
  copyAsset: {
    includes: ['novel/image/**'],
    excludes: ['.git/**', '.vivliostyle/**', 'node_modules/**', 'dist/**'],
  },

  /**
   * 表紙画像（オプション）
   * EPUBの表紙、またはPDFの先頭ページに使用する画像。
   * novel/image/cover.jpg などに配置し、パスを指定してください。
   */
  // cover: 'novel/image/cover.jpg',
};
