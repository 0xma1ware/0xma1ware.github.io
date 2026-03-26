#!/usr/bin/env python3
"""
md2post.py — Build system for 0xma1ware's cybersecurity blog.

Usage:
    python3 md2post.py --build                         # rebuild EVERYTHING
    python3 md2post.py posts_md/my-writeup.md          # convert a single file
    python3 md2post.py posts_md/*.md                   # batch convert

The --build flag:
  1. Converts ALL .md files in posts_md/ to themed HTML in posts/
  2. Auto-generates index.html with category filters + pagination
  3. Auto-generates sitemap.xml with all URLs

Requirements: pip install markdown pyyaml Pygments
"""

import sys, os, re, glob, argparse, html as html_module
from datetime import datetime

try:
    import markdown
except ImportError:
    print("ERROR: pip install markdown"); sys.exit(1)
try:
    import yaml
except ImportError:
    print("ERROR: pip install pyyaml"); sys.exit(1)

# ── Config ──────────────────────────────────────────────────────────────────
SITE_URL       = "https://0xma1ware.github.io"
SITE_TITLE     = "0xma1ware \u2014 Cybersecurity Blog"
SITE_DESC      = "HTB writeups, CTF challenges, hardware hacking, and red teaming \u2014 by 0xma1ware."
TWITTER_HANDLE = "@0xma1ware"
GITHUB_URL     = "https://github.com/0xma1ware"
TWITTER_URL    = "https://x.com/0xma1ware"
AUTHOR_EMAIL   = "ma1ware@protonmail.com"
POSTS_MD_DIR   = "posts_md"
POSTS_OUT_DIR  = "posts"
POSTS_PER_PAGE = 6

# ── Logo HTML (shared between index and post pages) ─────────────────────────
LOGO_HTML = '<img src="{favicon}" alt="logo"><span class="prefix">0x</span>ma1ware<span class="cursor-blink"></span>'

# ── Utilities ───────────────────────────────────────────────────────────────

def parse_frontmatter(text):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
    return (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, text)

def slugify(text):
    text = re.sub(r'<[^>]+>', '', text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

def format_date(d):
    if hasattr(d, 'strftime'): return d.strftime('%Y-%m-%d')
    m = re.match(r'(\d{4}-\d{2}-\d{2})', str(d))
    return m.group(1) if m else str(d)

def fix_image_paths(body):
    body = re.sub(r'!\[([^\]]*)\]\(\./imgs/', r'![\1](../imgs/', body)
    body = re.sub(r'!\[([^\]]*)\]\(imgs/', r'![\1](../imgs/', body)
    body = re.sub(r'!\[([^\]]*)\]\(/imgs/', r'![\1](../imgs/', body)
    return body

def add_heading_ids(html_content):
    seen = {}
    def repl(m):
        tag, attrs, content = m.group(1), m.group(2) or "", m.group(3)
        s = slugify(content)
        if s in seen: seen[s] += 1; s = f"{s}-{seen[s]}"
        else: seen[s] = 0
        return f'<{tag} id="{s}"{attrs}>{content}</{tag}>'
    return re.sub(r'<(h[1-6])(\s[^>]*)?>(.+?)</\1>', repl, html_content)

def generate_toc(html_content):
    headings = re.findall(r'<(h[1-4])\s*id="([^"]*)"[^>]*>(.*?)</\1>', html_content, re.DOTALL)
    if len(headings) < 3: return ""
    items = ''.join(
        f'<li class="toc-{t}"><a href="#{h}">{html_module.escape(re.sub(r"<[^>]+>","",x).strip())}</a></li>'
        for t, h, x in headings)
    return f'<div class="toc"><div class="toc-title">// Table of Contents</div><ul>{items}</ul></div>'

def convert_md_to_html(md_text):
    exts = ['markdown.extensions.fenced_code','markdown.extensions.codehilite',
            'markdown.extensions.tables','markdown.extensions.nl2br','markdown.extensions.sane_lists']
    cfg = {'markdown.extensions.codehilite': {
        'css_class':'highlight','guess_lang':False,'noclasses':True,'pygments_style':'monokai'}}
    try: return markdown.markdown(md_text, extensions=exts, extension_configs=cfg)
    except:
        exts.remove('markdown.extensions.codehilite')
        return markdown.markdown(md_text, extensions=exts)

def get_output_filename(meta, input_path):
    if meta.get('slug'): return meta['slug'].strip().rstrip('.html') + '.html'
    bn = os.path.splitext(os.path.basename(input_path))[0]
    bn = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', bn)
    return slugify(bn) + '.html'

def extract_excerpt(meta, body_html):
    if meta.get('excerpt'): return meta['excerpt']
    fp = re.search(r'<p>(.*?)</p>', body_html, re.DOTALL)
    if fp:
        t = re.sub(r'<[^>]+>', '', fp.group(1)).strip()
        return t[:217].rsplit(' ',1)[0]+'...' if len(t)>220 else t
    return ''

def get_category(meta):
    cats = meta.get('categories', [])
    return cats[0] if isinstance(cats, list) and cats else str(cats) if cats else ''

def get_tags(meta):
    tags = meta.get('tags', [])
    if isinstance(tags, str): tags = [t.strip() for t in tags.split(',')]
    return tags

# ── Header/Footer fragments ────────────────────────────────────────────────

def make_header(favicon_path):
    logo = LOGO_HTML.format(favicon=favicon_path)
    home = "../" if favicon_path.startswith("..") else "/"
    return f'''<header class="site-header">
    <a href="{home}" class="site-logo">{logo}</a>
    <button class="menu-toggle" aria-label="Menu" onclick="document.querySelector('.site-nav').classList.toggle('open')">
      <span></span><span></span><span></span>
    </button>
    <nav><ul class="site-nav">
      <li><a href="{home}">home</a></li>
      <li><a href="{GITHUB_URL}" target="_blank" rel="noopener">github</a></li>
      <li><a href="{TWITTER_URL}" target="_blank" rel="noopener">x.com</a></li>
    </ul></nav>
  </header>'''

FOOTER_HTML = f'''<footer class="site-footer">
    <div class="footer-links">
      <a href="{GITHUB_URL}" target="_blank" rel="noopener">GitHub</a>
      <a href="{TWITTER_URL}" target="_blank" rel="noopener">X / Twitter</a>
      <a href="mailto:{AUTHOR_EMAIL}">Email</a>
    </div>
    <p>&copy; 2025 0xma1ware. All rights reserved.</p>
  </footer>'''


# ── Post Page ───────────────────────────────────────────────────────────────

def build_post_page(meta, body_html, toc_html, filename):
    title = meta.get('title', 'Untitled Post')
    date = format_date(meta.get('date', ''))
    author = meta.get('author', '0xma1ware')
    category = get_category(meta)
    tags = get_tags(meta)
    difficulty = meta.get('difficulty', '')
    description = (meta.get('description','') or extract_excerpt(meta, body_html))[:200]

    e = html_module.escape
    cat_cls = 'hardware' if category.lower()=='hardware' else ''
    cat_html = f'<span class="category {cat_cls}">{e(category)}</span>' if category else ''
    diff_html = f'<span class="diff {difficulty.lower()}">{difficulty.lower()}</span>' if difficulty and difficulty.lower() in ('easy','medium','hard') else ''
    tags_html = ''.join(f'<span class="tag">{e(t)}</span>' for t in tags)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e(title)} \u2014 0xma1ware</title>
  <meta name="description" content="{e(description)}">
  <meta name="author" content="{e(author)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{SITE_URL}/posts/{e(filename)}">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}/posts/{e(filename)}">
  <meta property="og:image" content="{SITE_URL}/favicon.ico">
  <meta property="article:published_time" content="{e(date)}">
  <meta property="article:author" content="{e(author)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:site" content="{TWITTER_HANDLE}">
  <meta name="twitter:title" content="{e(title)}">
  <meta name="twitter:description" content="{e(description)}">
  <link rel="icon" href="../favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&family=Orbitron:wght@600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org", "@type": "BlogPosting",
    "headline": "{e(title)}", "description": "{e(description)}",
    "datePublished": "{e(date)}",
    "author": {{ "@type": "Person", "name": "{e(author)}", "url": "{GITHUB_URL}" }},
    "publisher": {{ "@type": "Person", "name": "{e(author)}" }},
    "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{SITE_URL}/posts/{e(filename)}" }}
  }}
  </script>
</head>
<body>
  {make_header("../favicon.ico")}

  <div class="post-header animate-in">
    <a href="../" class="back-link">&larr; back to all posts</a>
    <h1>{e(title)}</h1>
    <div class="post-meta">
      <span>{e(date)}</span>
      {cat_html}
      {diff_html}
      <span>by {e(author)}</span>
    </div>
    <div class="tags" style="margin-top:.75rem;">{tags_html}</div>
  </div>

  <article class="post-content animate-in">
    {toc_html}
    {body_html}
  </article>

  {FOOTER_HTML}
</body>
</html>'''


# ── Index Page ──────────────────────────────────────────────────────────────

def build_index_page(posts_data):
    e = html_module.escape

    # Collect unique categories for filter buttons
    categories = []
    seen_cats = set()
    for p in posts_data:
        c = p['category'].lower()
        if c and c not in seen_cats:
            seen_cats.add(c)
            categories.append(p['category'])

    filter_buttons = '<button class="filter-btn active" data-cat="all">All</button>\n      '
    filter_buttons += '\n      '.join(
        f'<button class="filter-btn" data-cat="{e(c.lower())}">{e(c)}</button>'
        for c in sorted(categories)
    )

    # Build post cards with data-category attribute
    cards = []
    for p in posts_data:
        cat_cls = 'hardware' if p['category'].lower()=='hardware' else ''
        cat_html = f'<span class="category {cat_cls}">{e(p["category"])}</span>' if p['category'] else ''
        diff_html = ''
        if p['difficulty']:
            d = p['difficulty'].lower()
            if d in ('easy','medium','hard'):
                diff_html = f'\n        <span class="diff {d}">{d}</span>'
        tags_html = '\n        '.join(f'<span class="tag">{e(t)}</span>' for t in p['tags'])
        cards.append(f'''
    <a href="posts/{e(p['filename'])}" class="post-card animate-in" data-category="{e(p['category'].lower())}">
      <div class="meta">
        <span class="date">{e(p['date'])}</span>
        {cat_html}{diff_html}
      </div>
      <h2>{e(p['title'])}</h2>
      <p class="excerpt">{e(p['excerpt'])}</p>
      <div class="tags">
        {tags_html}
      </div>
    </a>''')

    # Pagination + filter JS
    pagination_js = '''
<script>
(function() {
  const PER_PAGE = ''' + str(POSTS_PER_PAGE) + ''';
  const cards = Array.from(document.querySelectorAll('.post-card'));
  const filterBtns = document.querySelectorAll('.filter-btn');
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');
  const pageInfo = document.getElementById('page-info');
  let currentFilter = 'all';
  let currentPage = 1;

  function getFiltered() {
    return cards.filter(c =>
      currentFilter === 'all' || c.dataset.category === currentFilter
    );
  }

  function render() {
    const filtered = getFiltered();
    const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
    if (currentPage > totalPages) currentPage = totalPages;
    const start = (currentPage - 1) * PER_PAGE;
    const end = start + PER_PAGE;

    cards.forEach(c => c.classList.add('hidden'));
    filtered.forEach((c, i) => {
      if (i >= start && i < end) {
        c.classList.remove('hidden');
        c.style.animation = 'none';
        c.offsetHeight; // reflow
        c.style.animation = '';
        c.style.animationDelay = ((i - start) * 0.05) + 's';
      }
    });

    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    pageInfo.textContent = filtered.length > 0
      ? 'page ' + currentPage + ' / ' + totalPages
      : 'no posts found';

    // Show/hide pagination if only 1 page
    document.querySelector('.pagination').style.display =
      totalPages <= 1 ? 'none' : 'flex';
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.cat;
      currentPage = 1;
      render();
    });
  });

  prevBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; render(); } });
  nextBtn.addEventListener('click', () => { currentPage++; render(); });

  render();
})();
</script>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e(SITE_TITLE)}</title>
  <meta name="description" content="{e(SITE_DESC)}">
  <meta name="author" content="0xma1ware">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{SITE_URL}/">
  <meta property="og:title" content="{e(SITE_TITLE)}">
  <meta property="og:description" content="{e(SITE_DESC)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/">
  <meta property="og:image" content="{SITE_URL}/favicon.ico">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:site" content="{TWITTER_HANDLE}">
  <meta name="twitter:title" content="{e(SITE_TITLE)}">
  <meta name="twitter:description" content="{e(SITE_DESC)}">
  <link rel="icon" href="favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&family=Orbitron:wght@600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org", "@type": "Blog",
    "name": "{e(SITE_TITLE)}", "description": "{e(SITE_DESC)}",
    "url": "{SITE_URL}/",
    "author": {{ "@type": "Person", "name": "0xma1ware", "url": "{GITHUB_URL}" }}
  }}
  </script>
</head>
<body>
  {make_header("favicon.ico")}

  <section class="hero animate-in">
    <h1>Cyber<span class="accent">Security</span> Blog</h1>
    <p class="tagline">My descent into cybersecurity madness \u2014 HTB writeups, hardware hacking, red teaming &amp; more.</p>
  </section>

  <main class="posts-section">
    <div class="section-label">writeups &amp; posts</div>

    <div class="category-filter">
      {filter_buttons}
    </div>
{"".join(cards)}

    <div class="pagination">
      <button id="prev-page">&larr; prev</button>
      <span class="page-info" id="page-info"></span>
      <button id="next-page">next &rarr;</button>
    </div>
  </main>

  {FOOTER_HTML}

{pagination_js}
</body>
</html>'''


# ── Sitemap ─────────────────────────────────────────────────────────────────

def build_sitemap(posts_data):
    latest = posts_data[0]['date'] if posts_data else datetime.now().strftime('%Y-%m-%d')
    urls = [f'  <url>\n    <loc>{SITE_URL}/</loc>\n    <lastmod>{latest}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>']
    for p in posts_data:
        urls.append(f'  <url>\n    <loc>{SITE_URL}/posts/{html_module.escape(p["filename"])}</loc>\n    <lastmod>{html_module.escape(p["date"])}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>\n'


# ── Core ────────────────────────────────────────────────────────────────────

def process_file(input_path, output_path=None):
    with open(input_path, 'r', encoding='utf-8') as f:
        raw = f.read()
    meta, body = parse_frontmatter(raw)
    body = fix_image_paths(body)
    body_html = convert_md_to_html(body)
    body_html = add_heading_ids(body_html)
    toc_html = generate_toc(body_html)
    filename = get_output_filename(meta, input_path)
    if not output_path:
        output_path = os.path.join(POSTS_OUT_DIR, filename)
    else:
        filename = os.path.basename(output_path)
    page_html = build_post_page(meta, body_html, toc_html, filename)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(page_html)
    print(f"  \u2713 {os.path.basename(input_path)} \u2192 {output_path}")
    return output_path, meta, body_html

def collect_post_data(meta, body_html, filename):
    return {
        'title': meta.get('title', 'Untitled'),
        'date': format_date(meta.get('date', '')),
        'category': get_category(meta),
        'difficulty': meta.get('difficulty', ''),
        'tags': get_tags(meta),
        'excerpt': extract_excerpt(meta, body_html),
        'filename': filename,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build system for 0xma1ware's cybersecurity blog.",
        epilog='Workflow: python3 md2post.py --build && git push')
    parser.add_argument('files', nargs='*', help='Markdown file(s) to convert')
    parser.add_argument('-o', '--output', help='Output path (single file only)')
    parser.add_argument('--build', action='store_true', help='Full rebuild: posts + index + sitemap')
    args = parser.parse_args()

    if args.build:
        md_files = sorted(glob.glob(os.path.join(POSTS_MD_DIR, '*.md')))
        if not md_files:
            print(f"\n  No .md files found in {POSTS_MD_DIR}/\n"); sys.exit(1)

        print(f"\n  \u2554{'='*44}\u2557")
        print(f"  \u2551  md2post.py \u2014 full site rebuild            \u2551")
        print(f"  \u255a{'='*44}\u255d\n")

        print(f"  [1/3] Converting {len(md_files)} post(s)...\n")
        all_posts = []
        for md_path in md_files:
            out_path, meta, body_html = process_file(md_path)
            all_posts.append(collect_post_data(meta, body_html, os.path.basename(out_path)))
        all_posts.sort(key=lambda p: p['date'], reverse=True)

        print(f"\n  [2/3] Generating index.html...")
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(build_index_page(all_posts))
        cats = set(p['category'].lower() for p in all_posts if p['category'])
        print(f"  \u2713 index.html ({len(all_posts)} posts, {len(cats)} categories, {POSTS_PER_PAGE}/page)")

        print(f"\n  [3/3] Generating sitemap.xml...")
        with open('sitemap.xml', 'w', encoding='utf-8') as f:
            f.write(build_sitemap(all_posts))
        print(f"  \u2713 sitemap.xml ({len(all_posts)+1} URLs)")

        print(f"\n  {'='*44}")
        print(f"  Build complete! Ready to commit and push.")
        print(f"  {'='*44}\n")
        return

    if not args.files:
        parser.print_help(); print("\n  Tip: use --build for the full workflow.\n"); sys.exit(1)
    if args.output and len(args.files) > 1:
        print("ERROR: -o only works with a single file."); sys.exit(1)

    print(f"\n  md2post.py \u2014 converting {len(args.files)} file(s)...\n")
    count = 0
    for fp in args.files:
        if not os.path.isfile(fp): print(f"  \u2717 Not found: {fp}"); continue
        process_file(fp, args.output); count += 1
    print(f"\n  Done! {count} page(s). Run --build to update index & sitemap.\n")

if __name__ == '__main__':
    main()
