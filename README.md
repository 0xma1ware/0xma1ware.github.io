# 0xma1ware.github.io

A cybersecurity blog — HTB writeups, CTF challenges, hardware hacking, and red teaming.

## Quick Start — Writing a New Post

**Your entire workflow is 3 steps:**

```bash
# 1. Write your post in markdown
vim posts_md/2025-04-01-BoxName.md

# 2. Rebuild the site (generates all HTML, index, and sitemap)
python3 md2post.py --build

# 3. Push
git add . && git commit -m "Add BoxName writeup" && git push
```

That's it. No manual editing of index.html or sitemap.xml — `--build` handles everything.

## Markdown Frontmatter

Every post needs YAML frontmatter at the top:

```markdown
---
title: "HTB - BoxName"
date: 2025-04-01 12:00:00 +0300
categories: [htb]
tags: [AD, kerberos, winrm]
author: ma1ware
difficulty: medium
---

# Introduction

Your writeup content here...
```

| Field        | Required | Notes                                                   |
|-------------|----------|---------------------------------------------------------|
| `title`     | Yes      | Post title                                              |
| `date`      | Yes      | Publish date (`YYYY-MM-DD HH:MM:SS +TZ`)               |
| `categories`| Yes      | Category array — `[htb]` or `[hardware]`                |
| `tags`      | Yes      | Tag array                                               |
| `author`    | Yes      | Author name                                             |
| `difficulty`| No       | `easy` / `medium` / `hard` — adds a colored badge       |
| `excerpt`   | No       | Custom card text (auto-extracted from first paragraph)   |
| `slug`      | No       | Custom filename — e.g. `slug: cpap-hack` → `posts/cpap-hack.html` |

## md2post.py Usage

```bash
# Full rebuild (the main workflow)
python3 md2post.py --build

# Convert a single file (doesn't update index/sitemap)
python3 md2post.py posts_md/my-post.md

# Custom output path
python3 md2post.py posts_md/my-post.md -o posts/custom-name.html
```

**Requirements:** `pip install markdown pyyaml Pygments`

## Images

Place screenshots in `imgs/assets-boxname/` and reference in markdown as:

```markdown
![Alt text](./imgs/assets-boxname/screenshot.png)
```

The converter adjusts paths automatically for the `posts/` subdirectory.

## Project Structure

```
.
├── md2post.py          # Build script — the only tool you need
├── index.html          # Auto-generated home page
├── sitemap.xml         # Auto-generated sitemap
├── 404.html            # Custom 404 page
├── robots.txt          # Crawler directives
├── favicon.ico         # Site icon
├── .nojekyll           # Tells GitHub Pages: no Jekyll, serve as-is
├── css/
│   └── style.css       # All site styles
├── posts/              # Auto-generated HTML pages
├── posts_md/           # Your markdown source files (write here)
└── imgs/               # Screenshots organized by post
```

## SEO / Google Search Console

The site is designed for reliable indexing:
- **sitemap.xml** auto-generated with all URLs and dates
- **robots.txt** allows full crawling with sitemap reference
- **.nojekyll** prevents Jekyll build interference (the likely cause of your old site's indexing issues)
- Every page has canonical URLs, Open Graph tags, Twitter cards, and JSON-LD structured data

Submit `https://0xma1ware.github.io/sitemap.xml` in Google Search Console after deploying.

## License

MIT
