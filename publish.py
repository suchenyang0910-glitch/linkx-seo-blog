#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seo.linkx.club publisher.

Writes one SEO article, refreshes index.html (newest-5 list, preserving the
SEO <head>), then commits & pushes. Extracted from the daily cron so the agent
no longer has to reason about markup/git (root cause of context overflow) and
so index.html can never again be clobbered with dead links.

Usage:
  python publish.py --title "标题" --slug my-english-slug --body-file _draft.md
                   [--date YYYY-MM-DD] [--tags "东南亚出海,SEO"]
                   [--no-push] [--dry-run]
"""
import argparse, datetime, html, os, re, subprocess

REPO = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(REPO, 'content', 'posts')
INDEX = os.path.join(REPO, 'index.html')

FALLBACK_INDEX = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>LinkX 出海情报</title>
<meta name="description" content="LinkX 东南亚出海情报 · 实时高薪职位与风控雷达">
<meta name="keywords" content="东南亚求职,出海,柬埔寨工作,越南IT,新加坡HR">
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen">
<header class="border-b border-gray-800 p-6 text-center">
<h1 class="text-2xl font-bold">\U0001F4DB LinkX 出海情报</h1>
<p class="text-gray-500 text-sm mt-1">OSINT · AI清洗 · 风雷雷达</p>
<div class="mt-4"><a href="/content/posts/" class="text-indigo-400 hover:text-indigo-300 text-sm underline">浏览全部文章 \u2192</a></div>
</header>
<main class="max-w-4xl mx-auto p-6">
<h2 class="text-lg font-semibold mb-4">\U0001F4D1 近期深度分析</h2>
<div class="space-y-3">
{links}
</div>
</main>
<footer class="text-center text-gray-600 text-xs mt-8 p-4 border-t border-gray-800">
<p>数据由 LinkX AI 系统自动采集与清洗 · <a href="https://t.me/HelixOpsBot?start=seo_lead" class="text-indigo-400">Telegram Bot</a></p>
</footer>
</body>
</html>
"""

BAD_TITLES = ('slug', 'seo-friendly', 'seo友好', '（', '(')


def get_title(path):
    txt = open(path, encoding='utf-8').read()
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', txt, re.M)
    if m:
        t = m.group(1).strip().strip('"\'')
        if t and not any(b.lower() in t.lower() for b in BAD_TITLES):
            return t
    m = re.search(r'^#\s+(.+)$', txt, re.M)
    if m:
        return m.group(1).strip()
    return os.path.splitext(os.path.basename(path))[0]


def build_links(n=5):
    files = sorted([f for f in os.listdir(POSTS) if f.endswith('.md')], reverse=True)[:n]
    return "\n".join(
        '<a href="/content/posts/{0}" class="block bg-gray-900 p-4 rounded-lg border '
        'border-gray-800 hover:border-indigo-500 transition font-semibold">\U0001F4CE {1}</a>'.format(
            f, html.escape(get_title(os.path.join(POSTS, f))))
        for f in files)


def refresh_index():
    links = build_links(5)
    cur = open(INDEX, encoding='utf-8-sig').read() if os.path.exists(INDEX) else ''
    if '<div class="space-y-3">' in cur and '\n</div>' in cur:
        new = re.sub(r'(<div class="space-y-3">\n).*?(\n</div>)',
                     lambda m: m.group(1) + links + m.group(2), cur, flags=re.S)
    else:
        new = FALLBACK_INDEX.format(links=links)
    open(INDEX, 'w', encoding='utf-8', newline='\n').write(new)


def run(args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, encoding='utf-8')


def last_line(s):
    s = (s or '').strip()
    return s.splitlines()[-1] if s else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--title', required=True)
    ap.add_argument('--slug', required=True)
    ap.add_argument('--body-file', required=True)
    ap.add_argument('--date', default=None)
    ap.add_argument('--tags', default='东南亚出海,SEO')
    ap.add_argument('--no-push', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    date = a.date or datetime.datetime.now().strftime('%Y-%m-%d')
    slug = re.sub(r'[^A-Za-z0-9\-]+', '-', a.slug).strip('-').lower() or 'post'
    body = open(a.body_file, encoding='utf-8').read().strip()
    body = re.sub(r'^---.*?---\s*', '', body, flags=re.S)  # drop stray frontmatter
    tags = ", ".join("'%s'" % t.strip() for t in a.tags.split(',') if t.strip())

    fname = "%s-%s.md" % (date, slug)
    content = ('---\ntitle: "%s"\ndate: %s\ntags: [%s]\ndraft: false\n---\n\n# %s\n\n%s\n'
               % (a.title, date, tags, a.title, body))
    open(os.path.join(POSTS, fname), 'w', encoding='utf-8', newline='\n').write(content)
    print("wrote content/posts/%s" % fname)

    refresh_index()
    print("index.html refreshed (newest 5)")

    if a.dry_run:
        print("dry-run: skipped git")
        return

    run(['git', 'add', '-A'])
    c = run(['git', '-c', 'core.quotepath=false', 'commit', '-m', 'SEO: %s %s' % (date, a.title)])
    print("commit:", last_line(c.stdout) or last_line(c.stderr))
    if not a.no_push:
        p = run(['git', 'push', 'origin', 'master'])
        print("push:", last_line(p.stderr) or last_line(p.stdout) or 'ok')


if __name__ == '__main__':
    main()
