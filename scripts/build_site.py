# -*- coding: utf-8 -*-
"""
构建静态站点（GitHub Pages 用）：把 reports/（复盘报告）渲染为 HTML。

用法:
    python scripts/build_site.py [--out site]

产物:
    site/index.html           首页（报告列表）
    site/reports/<date>.html  每日复盘报告
    site/style.css            样式（纯手写，无外部依赖）
"""
import argparse
import html
import os
import re
import shutil
from datetime import datetime

try:
    import markdown
except ImportError:
    raise SystemExit("缺少依赖 markdown，请先 pip install markdown")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT, "reports")

CSS = """
:root { --bg:#f7f7f5; --card:#fff; --fg:#222; --muted:#888; --accent:#b5442e; --line:#e5e5e2; }
* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system,"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
       background:var(--bg); color:var(--fg); line-height:1.75; }
header.site { background:#1d1d1b; color:#fff; padding:28px 0; }
header.site h1 { margin:0 0 6px; font-size:22px; }
header.site .sub { color:#aaa; font-size:13px; }
.wrap { max-width:880px; margin:0 auto; padding:0 20px; }
nav.crumb { font-size:13px; margin:20px 0 -10px; }
nav.crumb a { color:var(--accent); text-decoration:none; }
main article { background:var(--card); border:1px solid var(--line); border-radius:8px;
               padding:28px 36px; margin:20px 0 40px; }
article h1 { font-size:22px; border-bottom:2px solid var(--line); padding-bottom:10px; }
article h2 { font-size:18px; margin-top:28px; border-left:4px solid var(--accent); padding-left:10px; }
article h3 { font-size:15px; }
article table { border-collapse:collapse; width:100%; font-size:13.5px; margin:14px 0; }
article th, article td { border:1px solid var(--line); padding:6px 10px; text-align:left; }
article th { background:#f4f1ee; }
article code { background:#f0eeea; padding:1px 5px; border-radius:4px; font-size:13px; }
article pre { background:#1d1d1b; color:#e8e6e1; padding:14px; border-radius:6px; overflow-x:auto; }
article pre code { background:none; color:inherit; }
article blockquote { border-left:3px solid var(--line); margin:12px 0; padding:2px 14px; color:#555; }
article img { max-width:100%; }
a { color:var(--accent); }
ul.links { list-style:none; padding:0; }
ul.links li { margin:10px 0; }
ul.links a { text-decoration:none; font-size:15px; }
ul.links .date { color:var(--muted); font-size:12px; margin-left:8px; }
ul.links .desc { color:var(--muted); font-size:12.5px; display:block; margin-top:2px; }
footer { color:var(--muted); font-size:12px; padding:20px 0 40px; text-align:center; }
@media (max-width:640px){ main article { padding:18px 16px; } }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{css}">
</head>
<body>
<header class="site"><div class="wrap">
  <h1>A 股市场分析多 Agent 系统</h1>
  <div class="sub">盘后复盘报告与短线交易方法论 · 纯分析建议模式</div>
</div></header>
<nav class="wrap crumb"><a href="index.html">首页</a>{crumb}</nav>
<main class="wrap">
{body}
</main>
<footer>自动构建于 {time} · GitHub Pages</footer>
</body>
</html>
"""


def render_md(text):
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )


def first_heading(text):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "未命名"


def first_paragraph(text):
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith(">") and not line.startswith("---"):
            return line[:120] + ("…" if len(line) > 120 else "")
    return ""


def report_date(fname):
    m = re.search(r"(\d{8})_review\.md", fname)
    if m:
        return m.group(1)
    return None


def build_report_pages(out_dir):
    links = []
    for fname in sorted(os.listdir(REPORTS_DIR), reverse=True):
        if not fname.endswith("_review.md"):
            continue
        text = open(os.path.join(REPORTS_DIR, fname), encoding="utf-8").read()
        body = render_md(text)
        date = report_date(fname)
        title = first_heading(text) or fname
        if date:
            title = f"{date[:4]}-{date[4:6]}-{date[6:]} 盘后复盘"
        out = os.path.join(out_dir, "reports")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, fname.replace(".md", ".html")), "w", encoding="utf-8") as f:
            f.write(TEMPLATE.format(
                title=title,
                css="../style.css",
                crumb=' · <a href="reports.html">复盘报告</a>',
                body=body,
                time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            ))
        links.append({
            "href": f"reports/{fname.replace('.md', '.html')}",
            "label": title,
            "desc": first_paragraph(text),
            "group": "报告" if date else "报告",
            "sort": date or fname,
        })
    return links


def build_index(out_dir, report_links):
    body = """<article>
<h2>每日复盘报告</h2>
<ul class="links">
"""
    for it in sorted(report_links, key=lambda x: x["sort"], reverse=True):
        body += (f'<li><a href="{it["href"]}">{html.escape(it["label"])}</a>'
                 f'<span class="date">{it["sort"]}</span>'
                 f'<span class="desc">{html.escape(it["desc"])}</span></li>\n')
    body += "</ul></article>"

    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            title="首页",
            css="style.css",
            crumb="",
            body=body,
            time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ))

    with open(os.path.join(out_dir, "reports.html"), "w", encoding="utf-8") as f:
        body = """<article>
<h2>全部复盘报告</h2>
<ul class="links">
"""
        for it in sorted(report_links, key=lambda x: x["sort"], reverse=True):
            body += (f'<li><a href="{it["href"]}">{html.escape(it["label"])}</a>'
                     f'<span class="desc">{html.escape(it["desc"])}</span></li>\n')
        body += "</ul></article>"
        f.write(TEMPLATE.format(
            title="复盘报告",
            css="style.css",
            crumb="",
            body=body,
            time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site")
    args = ap.parse_args()
    out_dir = args.out
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    report_links = build_report_pages(out_dir)
    build_index(out_dir, report_links)
    print(f"构建完成：{len(report_links)} 篇报告 -> {out_dir}")


if __name__ == "__main__":
    main()
