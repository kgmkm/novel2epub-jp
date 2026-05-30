#!/usr/bin/env python3
"""
novel2epub-jp: build-pdf.py
Markdown原稿 → しっぽり明朝埋め込みPDF を一発生成

方式:
  1. VFM で全 .md を HTML に変換
  2. WOFF2 フォントを base64 埋め込み
  3. Puppeteer (CDP) で PDF 出力 (displayHeaderFooter: false)
  4. PyMuPDF でヘッダー/フッターをスタンプ (ページごとの表示制御対応)
  5. image-size=large の場合: 画像ページを別レンダーしてフルブリードで合成

前提:
  - Node.js + @vivliostyle/vfm (npx で自動取得)
  - puppeteer-core (npm install 済み)
  - Vivliostyle CLI 同梱の Chrome (自動検出)
  - WOFF2 フォント: fonts/ShipporiMincho-{Regular,Bold}.woff2
  - PyMuPDF (fitz): PDF後処理
  - fontTools: WOFF2→OTF変換

使用例:
  python scripts/build-pdf.py --project-dir /path/to/project
  python scripts/build-pdf.py --project-dir . --output dist/mybook.pdf
"""

import sys, os, argparse, subprocess, base64, glob, pathlib, json, re, io, urllib.parse

# ─── CLI ──────────────────────────────────────────────────────────

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PRESETS_FILE = SCRIPT_DIR / "presets.json"

def load_presets():
    """Load preset definitions from presets.json."""
    if PRESETS_FILE.is_file():
        with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def list_presets():
    """Print available presets and exit."""
    presets = load_presets()
    if not presets:
        print("No presets found. Create presets.json next to this script.")
        return
    print("Available presets:\n")
    for name, opts in presets.items():
        desc_parts = [
            f"image-size={opts.get('image_size', '?')}",
            f"caption={opts.get('image_caption', '?')}",
            f"header={opts.get('chapter_header_display', '?')}/{opts.get('chapter_header_position', '?')}",
            f"page-num={opts.get('page_number_display', '?')}/{opts.get('page_number_position', '?')}",
        ]
        print(f"  {name:<20s} {', '.join(desc_parts)}")
    print(f"\nUsage: python build-pdf.py --preset <name> --project-dir .")

# Early check for --list-presets
if "--list-presets" in sys.argv:
    list_presets()
    sys.exit(0)

parser = argparse.ArgumentParser(description="Build PDF with Shippori Mincho")
parser.add_argument("--preset", default=None,
                    help="Apply preset (showcase-small, showcase-medium, showcase-large, clean-*, minimal). Use --list-presets to see all.")
parser.add_argument("--project-dir", default=".", help="Project root")
parser.add_argument("--output", default=None, help="Output PDF path")
parser.add_argument("--novel-dir", default="novel", help="Novel dir name")
parser.add_argument("--title", default=None, help="Book title")
parser.add_argument("--subtitle", default="", help="Book subtitle (shown on title page)")
parser.add_argument("--author", default=None, help="Author name")
parser.add_argument("--size", default="105mm,148mm", help="Page size (w,h)")
parser.add_argument("--keep-html", action="store_true", help="Keep intermediate HTML")
parser.add_argument("--chapter-header-position", choices=['center','right','left'], default='right',
                    help="Chapter header position (default: right)")
parser.add_argument("--chapter-header-display", choices=['all','even','odd','none'], default='all',
                    help="Chapter header display mode (default: all)")
parser.add_argument("--chapter-header-content", choices=['book-title','chapter-name'], default='book-title',
                    help="Chapter header content: book-title or chapter-name (auto-detect from h2)")
parser.add_argument("--page-number-position", choices=['center','right','left','odd-right-even-left','odd-left-even-right'],
                    default='center', help="Page number position (default: center)")
parser.add_argument("--page-number-display", choices=['all','even','odd'], default='all',
                    help="Page number display mode (default: all)")
parser.add_argument("--image-size", choices=['small','medium','large'], default='small',
                    help="Image size: small(contain-fit), medium(body-width 70%%), large(cover-fill full-bleed)")
parser.add_argument("--image-caption", choices=['on','off'], default='on',
                    help="Show image caption. Applies to small/medium only; large always hides caption.")

# ── Preset application ───────────────────────────────────────────
# Strategy: if --preset is given, load preset values as parser defaults
# BEFORE parsing. This way individual CLI flags override preset values.
_preset_name = None
for i, arg in enumerate(sys.argv[1:], 1):
    if arg == "--preset" and i < len(sys.argv) - 1:
        _preset_name = sys.argv[i + 1]
        break
    elif arg.startswith("--preset="):
        _preset_name = arg.split("=", 1)[1]
        break

if _preset_name:
    _presets = load_presets()
    if _preset_name not in _presets:
        print(f"ERROR: Unknown preset '{_preset_name}'. Use --list-presets.", file=sys.stderr)
        sys.exit(1)
    _p = _presets[_preset_name]
    # Map preset JSON keys → argparse dest names
    _preset_defaults = {
        'image_size': _p.get('image_size', 'small'),
        'image_caption': _p.get('image_caption', 'on'),
        'chapter_header_position': _p.get('chapter_header_position', 'right'),
        'chapter_header_display': _p.get('chapter_header_display', 'all'),
        'chapter_header_content': _p.get('chapter_header_content', 'book-title'),
        'page_number_position': _p.get('page_number_position', 'center'),
        'page_number_display': _p.get('page_number_display', 'all'),
    }
    parser.set_defaults(**_preset_defaults)
    print(f"Preset applied: {_preset_name}")

args = parser.parse_args()

project = pathlib.Path(args.project_dir).resolve()
novel_dir = project / args.novel_dir
fonts_dir = project / "fonts"

if not novel_dir.is_dir():
    print(f"ERROR: novel dir not found: {novel_dir}", file=sys.stderr)
    sys.exit(1)

# ─── Chrome location ──────────────────────────────────────────────

chrome_candidates = [
    *sorted(glob.glob(os.path.expanduser(
        "~/.cache/vivliostyle/browsers/chrome/*/chrome-linux64/chrome"
    )), reverse=True),
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
]
chrome = None
for c in chrome_candidates:
    if os.path.isfile(c) and os.access(c, os.X_OK):
        chrome = c
        break
if not chrome:
    print("ERROR: Chrome not found. Install via: vivliostyle build (once)",
          file=sys.stderr)
    sys.exit(1)
print(f"Chrome: {chrome}")

# ─── Fonts (WOFF2 → base64 for CSS + OTF bytes for PyMuPDF) ─────

font_regular = fonts_dir / "ShipporiMincho-Regular.woff2"
font_bold = fonts_dir / "ShipporiMincho-Bold.woff2"

if not font_regular.is_file():
    print(f"ERROR: font not found: {font_regular}", file=sys.stderr)
    sys.exit(1)
if not font_bold.is_file():
    font_bold = font_regular  # fallback

woff2_regular_b64 = base64.b64encode(font_regular.read_bytes()).decode()
woff2_bold_b64 = base64.b64encode(font_bold.read_bytes()).decode()


def woff2_to_ttf_bytes(woff2_path):
    """Convert WOFF2 font to plain TTF bytes usable by PyMuPDF."""
    from fontTools.ttLib import TTFont
    font = TTFont(str(woff2_path))
    font.flavor = None  # Remove WOFF/WOFF2 flavor → plain OpenType
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


# Pre-convert font for PyMuPDF stamping (needs plain OTF/TTF, not WOFF2)
stamp_font_bytes = woff2_to_ttf_bytes(font_regular)
print("Font: WOFF2 → TTF converted for PyMuPDF stamping")

# ─── VFM: Markdown → HTML ────────────────────────────────────────

md_files = sorted(novel_dir.glob("*.md"))
if not md_files:
    print(f"ERROR: no .md files in {novel_dir}", file=sys.stderr)
    sys.exit(1)

html_parts = []
for md in md_files:
    print(f"VFM: {md.name}")
    result = subprocess.run(
        ["npx", "--yes", "@vivliostyle/vfm", str(md),
         "--partial", "--language", "ja", "--hardLineBreaks"],
        capture_output=True, text=True, cwd=str(project), timeout=60
    )
    if result.returncode != 0:
        print(f"  WARNING: {result.stderr[:200]}", file=sys.stderr)
    html_parts.append(result.stdout)

# ─── Title ────────────────────────────────────────────────────────

title = args.title or project.name
author = args.author or ""
subtitle = args.subtitle

# Try to read from AGENTS.md or proposal.md
agents = project / "AGENTS.md"
if agents.exists() and not args.title:
    text = agents.read_text(encoding="utf-8")
    for line in text.split("\n"):
        if line.startswith("# ") and not line.startswith("##"):
            t = line.replace("# ", "").strip()
            if not t:
                continue
            # "作品ガイド — 『タイトル』" 形式からタイトルを抽出
            if "作品ガイド" in t and "—" in t:
                parts = t.split("—", 1)
                t = parts[1].strip().replace("『", "").replace("』", "")
            if t and "作品ガイド" not in t:
                title = t
                break

# ─── HTML Preprocessing ──────────────────────────────────────────

OPENING_BRACKETS = '「『（【＂｢'
DIGIT_FW_MAP = str.maketrans('0123456789', '０１２３４５６７８９')


def add_no_indent_class(html):
    """修正2: <p>タグの先頭文字が始め括弧類なら class='no-indent' を付与"""
    def check_and_replace(m):
        tag = m.group(0)
        after = m.string[m.end():]
        i = 0
        while i < len(after):
            if after[i] == '<':
                gt = after.find('>', i)
                if gt == -1:
                    break
                i = gt + 1
            elif after[i] in ' \n\t\r':
                i += 1
            else:
                if after[i] in OPENING_BRACKETS:
                    if 'class=' in tag:
                        return tag.replace('class="', 'class="no-indent ')
                    else:
                        return tag.replace('<p', '<p class="no-indent"')
                break
        return tag

    return re.sub(r'<p(?:\s[^>]*)?>', check_and_replace, html)


def convert_digits_in_text_nodes(html):
    """修正3: テキストノード内の半角数字を処理（1桁→全角、2桁以上→tcy）"""
    def process_text(text):
        result = []
        i = 0
        while i < len(text):
            if text[i] in '0123456789':
                j = i
                while j < len(text) and text[j] in '0123456789':
                    j += 1
                num = text[i:j]
                if len(num) == 1:
                    result.append(num.translate(DIGIT_FW_MAP))
                else:
                    result.append(f'<span class="tcy">{num}</span>')
                i = j
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)

    result = []
    i = 0
    while i < len(html):
        if html[i] == '<':
            tag_end = html.find('>', i)
            if tag_end == -1:
                result.append(html[i:])
                break
            result.append(html[i:tag_end + 1])
            i = tag_end + 1
        else:
            j = html.find('<', i)
            if j == -1:
                result.append(process_text(html[i:]))
                break
            result.append(process_text(html[i:j]))
            i = j
    return ''.join(result)


def preprocess_html(html):
    """全HTML前処理を適用"""
    html = add_no_indent_class(html)
    html = convert_digits_in_text_nodes(html)
    return html


# ─── Build body HTML ─────────────────────────────────────────────

body_html = ''.join(html_parts)
body_html = preprocess_html(body_html)

# Remove figcaption: always for large mode, and when --image-caption off
if args.image_size == 'large' or args.image_caption == 'off':
    body_html = re.sub(r'\s*<figcaption[^>]*>.*?</figcaption>', '', body_html, flags=re.DOTALL)

# ─── Extract h2 titles for chapter-name mode ─────────────────────

h2_titles = re.findall(r'<h2[^>]*>(.*?)</h2>', body_html, re.DOTALL)
h2_titles = [re.sub(r'<[^>]+>', '', t).strip() for t in h2_titles]  # strip inner HTML
print(f"Chapter titles found: {len(h2_titles)} → {h2_titles[:3]}{'...' if len(h2_titles) > 3 else ''}")

# ─── Image handling ───────────────────────────────────────────────


def split_at_images(body_html):
    """Split body HTML at <figure>...</figure> blocks (VFM image output).
    Returns list of (type, content) tuples where type is 'text' or 'image'.
    For 'image', content is the img src attribute value.

    Removes both leading and trailing <hr> around <figure> to prevent
    blank pages from CSS 'page-break-after: always' on hr.
    """
    segments = []
    # VFM wraps images in: <hr>\n<figure>...<img src="...">...</figure>\n<hr>
    # Match optional <hr> BEFORE + <figure>...</figure> + optional <hr> AFTER
    pattern = r'(?:\s*<hr>\s*)?(<figure>\s*<img\b[^>]*>\s*(?:<figcaption[^>]*>.*?</figcaption>\s*)?</figure>)(?:\s*<hr>\s*)?'

    last_end = 0
    for m in re.finditer(pattern, body_html, re.DOTALL):
        # Text before this image (strip trailing whitespace/hr remnants)
        before = body_html[last_end:m.start()]
        # Remove trailing <hr> and whitespace to avoid blank pages
        before = re.sub(r'(?:\s*<hr>\s*)+$', '', before).strip()
        if before:
            segments.append(('text', before))

        # Extract img src from figure
        img_match = re.search(r'<img\b[^>]*src="([^"]+)"', m.group(0))
        if img_match:
            segments.append(('image', img_match.group(1)))

        last_end = m.end()

    # Remaining text after last image (strip trailing hr to avoid blank page)
    remaining = body_html[last_end:]
    remaining = re.sub(r'(?:\s*<hr>\s*)+$', '', remaining).strip()
    if remaining:
        segments.append(('text', remaining))

    return segments


# For image-size=large: split into segments
# For small/medium: wrap images with appropriate CSS
if args.image_size == 'large':
    body_segments = split_at_images(body_html)
    image_count = sum(1 for t, _ in body_segments if t == 'image')
    print(f"Image size: large (full-bleed, {image_count} images extracted)")
else:
    # Single segment with all content
    body_segments = [('text', body_html)]

    if args.image_size == 'small':
        pass  # default CSS handles it
    elif args.image_size == 'medium':
        pass  # CSS handles it
# ─── Title page HTML ─────────────────────────────────────────────

subtitle_elem = f'\n  <p class="sub-title">{subtitle}</p>' if subtitle else ""
title_page_html = f"""
<div class="title-page">
  <h1 class="main-title">{title}</h1>{subtitle_elem}
</div>
"""

# ─── Chapter header JS (chapter-name mode) ───────────────────────
# Note: This JS was for Puppeteer's displayHeaderFooter + document.title
# With PyMuPDF stamping, chapter-name is resolved post-render via text search.
# Keep the JS for potential future use but it's no longer critical.

chapter_header_js = ""
if args.chapter_header_content == 'chapter-name':
    chapter_header_js = """<script>
document.addEventListener('DOMContentLoaded',function(){
  var obs=new IntersectionObserver(function(e){e.forEach(function(x){if(x.isIntersecting && x.target.tagName==='H2') document.title=x.target.textContent})},{threshold:0.1});
  document.querySelectorAll('h2').forEach(function(h){obs.observe(h)});
});
</script>"""

# ─── CSS variables based on image-size ────────────────────────────

if args.image_size == 'small':
    img_css = """figure {
  display: block;
  page-break-before: always;
  page-break-after: always;
  text-align: center;
  margin: 0;
}
img {
  display: inline-block;
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
}
figcaption {
  display: block;
  font-size: 8pt;
  color: #555;
  margin-top: 1em;
  font-family: 'SM', serif;
}"""
    extra_css = ""
elif args.image_size == 'medium':
    img_css = """figure {
  display: block;
  page-break-before: always;
  page-break-after: always;
  text-align: center;
  margin: 0;
}
img {
  display: inline-block;
  max-width: 78mm;
  max-height: 108mm;
  object-fit: contain;
}
figcaption {
  display: block;
  font-size: 8pt;
  color: #555;
  margin-top: 1em;
  font-family: 'SM', serif;
}"""
    extra_css = ""
else:  # large — images are extracted and rendered separately
    img_css = """/* Images extracted for separate full-bleed rendering */
figure { display: none; }
img { display: none; }  /* Hide any remaining inline images */"""
    extra_css = ""

# ─── Page size parsing ────────────────────────────────────────────

size_parts = args.size.replace("mm", "").replace("in", "").split(",")
w_str, h_str = size_parts[0].strip(), size_parts[1].strip()
unit = "mm" if "mm" in args.size else "in"
page_w_mm = float(w_str) if unit == "mm" else float(w_str) * 25.4
page_h_mm = float(h_str) if unit == "mm" else float(h_str) * 25.4

# ─── CSS template (shared between text renders) ──────────────────


def build_css_block():
    """Build the main CSS for text content pages."""
    return f"""<style>
@font-face {{
  font-family: 'SM';
  src: url(data:font/woff2;base64,{woff2_regular_b64}) format('woff2');
  font-weight: 400;
}}
@font-face {{
  font-family: 'SM';
  src: url(data:font/woff2;base64,{woff2_bold_b64}) format('woff2');
  font-weight: 700;
}}

@page {{
  size: {w_str}{unit} {h_str}{unit};
  margin: 20{unit} 15{unit} 20{unit} 12{unit};
}}

html, body {{
  font-family: 'SM', serif;
  font-weight: 400;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 10pt;
  line-height: 1.8;
  margin: 0;
  padding: 0;
}}

h1 {{
  font-weight: 700;
  font-size: 14pt;
  text-align: center;
  page-break-before: always;
  margin-top: 3em;
}}

h2 {{
  font-weight: 700;
  font-size: 11pt;
  text-align: center;
  page-break-before: always;
}}

p {{
  text-indent: 1em;
  margin: 0;
}}

.no-indent {{
  text-indent: 0;
}}

hr {{
  page-break-after: always;
  visibility: hidden;
  border: none;
  margin: 0;
}}

{img_css}

ruby {{ ruby-align: start; }}
rt {{ font-size: 0.5em; font-weight: normal; }}

span.tcy {{ text-combine-upright: all; }}

.title-page {{
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 90vh;
  writing-mode: vertical-rl;
  page-break-after: always;
}}
.main-title {{
  font-size: 18pt;
  font-weight: 700;
  margin-bottom: 2em;
  text-align: center;
}}
.sub-title {{
  font-size: 11pt;
  font-weight: 400;
  text-align: center;
}}

.footnote {{ font-size: 0.8em; }}
{extra_css}
</style>"""


# ─── Build full HTML for a text segment ──────────────────────────


def build_text_html(content, include_title_page=True):
    """Build complete HTML document for a text segment."""
    title_page = title_page_html if include_title_page else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{title}</title>
<base href="../novel/">
{build_css_block()}
{chapter_header_js}
</head>
<body>
{title_page}
{content}
</body>
</html>"""


def build_image_html(img_src):
    """Build minimal HTML for full-bleed image rendering."""
    # Resolve relative path to absolute file:// URL
    decoded_src = urllib.parse.unquote(img_src)
    abs_path = (novel_dir / decoded_src).resolve()
    file_url = 'file://' + str(abs_path)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
  size: {w_str}{unit} {h_str}{unit};
  margin: 0;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{
  width: {w_str}{unit};
  height: {h_str}{unit};
  overflow: hidden;
}}
img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
}}
</style>
</head>
<body><img src="{file_url}"></body>
</html>"""


# ─── Puppeteer rendering helper ──────────────────────────────────

script_path = pathlib.Path(__file__).parent / 'print-pdf.cjs'


def render_pdf(html_path, pdf_path, strip_blank_final=False):
    """Render HTML to PDF via Puppeteer (no header/footer).
    If strip_blank_final=True, remove blank pages from the end using PyMuPDF."""
    puppeteer_opts = {
        'chrome': chrome,
        'displayHeaderFooter': False,
        'margin': {'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
    }

    result = subprocess.run([
        'node', str(script_path),
        str(html_path), str(pdf_path),
        json.dumps(puppeteer_opts)
    ], capture_output=True, text=True, timeout=300, cwd=str(project))

    if result.returncode != 0 or not pathlib.Path(pdf_path).exists():
        print(f"ERROR: Puppeteer PDF generation failed", file=sys.stderr)
        print(result.stderr[:1000], file=sys.stderr)
        sys.exit(1)

    # Print any Puppeteer output for debugging
    if result.stdout.strip():
        for line in result.stdout.strip().split('\n'):
            if not line.startswith('OK '):
                print(f"  Puppeteer: {line}")

    # Strip trailing blank pages (no text, no images)
    if strip_blank_final:
        import fitz as _fitz
        doc = _fitz.open(str(pdf_path))
        original_len = len(doc)
        while len(doc) > 1:
            last_pg = doc[-1]
            text = last_pg.get_text().strip()
            imgs = last_pg.get_images()
            if not text and not imgs:
                doc.delete_page(len(doc) - 1)
            else:
                break
        if len(doc) < original_len:
            tmp_out = str(pdf_path) + '.tmp'
            doc.save(tmp_out, garbage=4, deflate=True)
            doc.close()
            os.replace(tmp_out, str(pdf_path))
        else:
            doc.close()


# ─── Rendering ────────────────────────────────────────────────────

dist_dir = project / "dist"
dist_dir.mkdir(exist_ok=True)

# Write stamp font to temp file for PyMuPDF insert_textbox
temp_font_path = dist_dir / "_font_stamp.ttf"
temp_font_path.write_bytes(stamp_font_bytes)

# Determine output path
if args.output:
    pdf_path = pathlib.Path(args.output)
    if not pdf_path.is_absolute():
        pdf_path = project / pdf_path
else:
    safe_title = title.replace("/", "-").replace(" ", "")
    pdf_path = dist_dir / f"{safe_title}.pdf"

# Track which pages are image pages (1-indexed)
image_pages = set()

if args.image_size == 'large' and any(t == 'image' for t, _ in body_segments):
    # ─── Split-and-merge rendering for full-bleed images ─────────
    print("Rendering: split-and-merge mode (text + full-bleed images)")

    segment_pdfs = []  # list of (pdf_path, type)
    text_seg_idx = 0
    img_seg_idx = 0

    for seg_type, seg_content in body_segments:
        if seg_type == 'text':
            # Build text HTML (title page only in first text segment)
            include_title = (text_seg_idx == 0)
            html_str = build_text_html(seg_content, include_title_page=include_title)

            html_file = dist_dir / f"_seg_text_{text_seg_idx}.html"
            pdf_file = dist_dir / f"_seg_text_{text_seg_idx}.pdf"
            html_file.write_text(html_str, encoding="utf-8")

            print(f"  Rendering text segment {text_seg_idx} {'(with title page)' if include_title else ''}...")
            render_pdf(html_file, pdf_file, strip_blank_final=True)
            segment_pdfs.append((pdf_file, 'text'))
            text_seg_idx += 1

        elif seg_type == 'image':
            # Build image HTML
            html_str = build_image_html(seg_content)

            html_file = dist_dir / f"_seg_img_{img_seg_idx}.html"
            pdf_file = dist_dir / f"_seg_img_{img_seg_idx}.pdf"
            html_file.write_text(html_str, encoding="utf-8")

            print(f"  Rendering image segment {img_seg_idx} ({seg_content})...")
            render_pdf(html_file, pdf_file)
            segment_pdfs.append((pdf_file, 'image'))
            img_seg_idx += 1

    # ─── Merge all segment PDFs ──────────────────────────────────
    print("Merging PDF segments...")
    import fitz

    merged = fitz.open()
    page_offset = 0

    for seg_pdf_path, seg_type in segment_pdfs:
        seg_doc = fitz.open(str(seg_pdf_path))
        num_pages = len(seg_doc)

        if seg_type == 'image':
            # Record which pages are image pages
            for p in range(num_pages):
                image_pages.add(page_offset + p + 1)  # 1-indexed

        merged.insert_pdf(seg_doc)
        page_offset += num_pages
        seg_doc.close()

    # Save merged PDF temporarily
    temp_pdf = dist_dir / "_merged.pdf"
    merged.save(str(temp_pdf))
    merged.close()

    print(f"  Merged: {page_offset} pages (image pages: {sorted(image_pages)})")

    # Clean up segment files
    for seg_pdf_path, _ in segment_pdfs:
        seg_pdf_path.unlink(missing_ok=True)
    for f in dist_dir.glob("_seg_text_*.html"):
        f.unlink(missing_ok=True)
    for f in dist_dir.glob("_seg_img_*.html"):
        f.unlink(missing_ok=True)

else:
    # ─── Single-pass rendering (no image extraction) ─────────────
    print("Rendering: single-pass mode")

    full_html = build_text_html(body_html, include_title_page=True)

    html_path = dist_dir / "build.html"
    html_path.write_text(full_html, encoding="utf-8")
    html_mb = len(full_html) / 1024 / 1024
    print(f"HTML: {html_path} ({html_mb:.1f}MB)")

    render_pdf(html_path, pdf_path, strip_blank_final=True)

    if not args.keep_html:
        html_path.unlink(missing_ok=True)

    temp_pdf = pdf_path  # already in place

# ─── PyMuPDF Post-Processing: Stamp headers and footers ──────────

import fitz

print("Post-processing: stamping headers and footers...")

# Open the PDF (either merged or single-pass)
doc = fitz.open(str(temp_pdf))
total_pages = len(doc)

# Points per mm
mm = 72.0 / 25.4

# Page dimensions in points
pw = page_w_mm * mm
ph = page_h_mm * mm

# Margins (matching CSS @page margins: top=20mm, right=15mm, bottom=20mm, left=12mm)
margin_top = 20.0 * mm
margin_bottom = 20.0 * mm
margin_left = 12.0 * mm
margin_right = 15.0 * mm

# Content area
content_x0 = margin_left
content_x1 = pw - margin_right
content_width = content_x1 - content_x0


def should_show_header(page_num):
    """Determine if header should show on this page."""
    display = args.chapter_header_display
    if display == 'none':
        return False
    if page_num == 1:  # Never show header on title page
        return False
    if page_num in image_pages:  # Never show on image pages
        return False
    if display == 'all':
        return True
    if display == 'even':
        return page_num % 2 == 0
    if display == 'odd':
        return page_num % 2 == 1
    return False


def should_show_page_number(page_num):
    """Determine if page number should show on this page."""
    display = args.page_number_display
    if page_num in image_pages:  # Never show on image pages
        return False
    if display == 'all':
        return True
    if display == 'even':
        return page_num % 2 == 0
    if display == 'odd':
        return page_num % 2 == 1
    return False


def get_header_position():
    """Get alignment for header text."""
    pos = args.chapter_header_position
    align_map = {'left': fitz.TEXT_ALIGN_LEFT, 'center': fitz.TEXT_ALIGN_CENTER, 'right': fitz.TEXT_ALIGN_RIGHT}
    return align_map.get(pos, fitz.TEXT_ALIGN_RIGHT)


def get_footer_position(page_num):
    """Get alignment for page number, considering odd/even variants."""
    pos = args.page_number_position
    if pos == 'odd-right-even-left':
        return fitz.TEXT_ALIGN_RIGHT if page_num % 2 == 1 else fitz.TEXT_ALIGN_LEFT
    elif pos == 'odd-left-even-right':
        return fitz.TEXT_ALIGN_LEFT if page_num % 2 == 1 else fitz.TEXT_ALIGN_RIGHT
    else:
        align_map = {'center': fitz.TEXT_ALIGN_CENTER, 'right': fitz.TEXT_ALIGN_RIGHT, 'left': fitz.TEXT_ALIGN_LEFT}
        return align_map.get(pos, fitz.TEXT_ALIGN_CENTER)


def find_chapter_for_page(page_num, doc):
    """Find which chapter title applies to a given page by searching for h2 text."""
    # Search backwards from current page for the most recent chapter title
    for p in range(page_num - 1, -1, -1):
        page_obj = doc[p]
        text = page_obj.get_text()
        for ch_title in h2_titles:
            # Clean title for comparison
            clean_title = ch_title.strip()
            if clean_title and clean_title in text:
                return clean_title
    return None


# Determine header text source
header_text_fixed = title if args.chapter_header_content == 'book-title' else None

# Stamp each page
for i in range(total_pages):
    page = doc[i]
    page_num = i + 1

    # ─── Stamp Chapter Header ──────────────────────────────────
    if should_show_header(page_num):
        if args.chapter_header_content == 'book-title':
            header_text = header_text_fixed
        else:  # chapter-name
            header_text = find_chapter_for_page(page_num, doc)

        if header_text:
            # Header rect: in the top margin area
            header_rect = fitz.Rect(
                content_x0,           # x0: left margin
                margin_top * 0.15,    # y0: near top of page (some padding)
                content_x1,           # x1: right margin
                margin_top * 0.85     # y1: just above content area
            )

            rc = page.insert_textbox(
                header_rect,
                header_text,
                fontsize=7,
                fontname="shippori",
                fontfile=str(temp_font_path),
                align=get_header_position(),
                color=(0.4, 0.4, 0.4),  # Subtle gray
            )
            if rc < 0:
                print(f"  Warning: header text overflow on page {page_num}")

    # ─── Stamp Page Number ──────────────────────────────────────
    if should_show_page_number(page_num):
        # Footer rect: in the bottom margin area
        footer_rect = fitz.Rect(
            content_x0,               # x0: left margin
            ph - margin_bottom * 0.85,  # y0: just below content area
            content_x1,               # x1: right margin
            ph - margin_bottom * 0.15   # y1: near bottom of page
        )

        page_num_text = str(page_num)

        rc = page.insert_textbox(
            footer_rect,
            page_num_text,
            fontsize=8,
            fontname="shippori",
            fontfile=str(temp_font_path),
            align=get_footer_position(page_num),
            color=(0.3, 0.3, 0.3),  # Subtle gray
        )
        if rc < 0:
            print(f"  Warning: page number overflow on page {page_num}")

# ─── Save final PDF ──────────────────────────────────────────────

if str(temp_pdf) == str(pdf_path):
    # Single-pass: file already exists on disk, must use incremental save
    doc.save(str(pdf_path), incremental=True, encryption=0)
else:
    # Merge mode: temp_pdf != pdf_path, save to new file
    doc.save(str(pdf_path), garbage=4, deflate=True)
doc.close()

# Clean up temp file if it's different from output
if str(temp_pdf) != str(pdf_path) and temp_pdf.exists():
    temp_pdf.unlink(missing_ok=True)

# Clean up temp font
if temp_font_path.exists():
    temp_font_path.unlink(missing_ok=True)

pdf_mb = pdf_path.stat().st_size / 1024 / 1024
print(f"PDF:  {pdf_path} ({pdf_mb:.1f}MB)")
print(f"  Pages: {total_pages} | Image pages: {sorted(image_pages) if image_pages else 'none'}")
print(f"  Header: {args.chapter_header_content} ({args.chapter_header_display}, {args.chapter_header_position})")
print(f"  Footer: page-number ({args.page_number_display}, {args.page_number_position})")
print("Done!")
