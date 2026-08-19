# -*- coding: utf-8 -*-
"""
构建静态站点（GitHub Pages 用）：把 reports/（复盘报告）渲染为 HTML。

用法:
    python scripts/build_site.py [--out site]

产物:
    site/index.html           首页（报告卡片列表，含关键指标摘要）
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
:root {
  --bg:#f4f4f2; --card:#fff; --fg:#24292f; --muted:#8b949e;
  --accent:#b5442e; --accent-dark:#8f3320; --line:#e3e3df;
  --thead:#f0ede9; --ok:#1a7f37; --warn:#b5442e;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust:100%; }
body { margin:0; font-family:-apple-system,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
       background:var(--bg); color:var(--fg); line-height:1.8; }
header.site { background:linear-gradient(135deg,#1d1d1b 0%,#2c2c28 100%); color:#fff; padding:34px 0 30px;
              border-bottom:3px solid var(--accent); }
header.site h1 { margin:0 0 6px; font-size:24px; letter-spacing:1px; }
header.site .sub { color:#b9b9b3; font-size:13.5px; }
.wrap { max-width:900px; margin:0 auto; padding:0 20px; }
nav.crumb { font-size:13px; margin:22px 0 -6px; color:var(--muted); }
nav.crumb a { color:var(--accent); text-decoration:none; }
nav.crumb a:hover { text-decoration:underline; }

/* ===== 首页卡片 ===== */
.cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(390px,1fr)); gap:16px; margin:24px 0 48px; }
.card { display:block; background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:18px 20px; text-decoration:none; color:inherit;
        box-shadow:0 1px 3px rgba(0,0,0,.04); transition:transform .12s ease, box-shadow .12s ease; }
.card:hover { transform:translateY(-2px); box-shadow:0 6px 16px rgba(0,0,0,.08); }
.card-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.card-date { font-size:12.5px; color:var(--muted); font-variant-numeric:tabular-nums; }
.badge { font-size:12px; color:#fff; background:var(--accent); border-radius:20px; padding:2px 10px; }
.badge.soft { background:#e9e2de; color:var(--accent-dark); }
.card h3 { margin:0 0 8px; font-size:17px; }
.card .desc { font-size:13px; color:#57606a; margin:0 0 12px; display:-webkit-box;
              -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.chips { display:flex; flex-wrap:wrap; gap:6px; }
.chip { font-size:12px; background:#f4f0ed; border:1px solid var(--line); color:#4a4540;
        border-radius:6px; padding:2px 9px; }
.chip b { color:var(--accent-dark); font-weight:600; }
.page-title { font-size:20px; margin:26px 0 6px; }

/* ===== 文章排版 ===== */
main article { background:var(--card); border:1px solid var(--line); border-radius:10px;
               padding:30px 40px; margin:22px 0 40px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
article h1 { font-size:24px; border-bottom:2px solid var(--line); padding-bottom:12px; margin:0 0 22px; }
article h2 { font-size:19px; margin:34px 0 12px; border-left:4px solid var(--accent);
             padding-left:12px; line-height:1.4; }
article h3 { font-size:15.5px; margin:22px 0 8px; color:#333; }
article p { margin:10px 0; }
article ul, article ol { padding-left:26px; margin:12px 0; }
article li { margin:6px 0; }
article li::marker { color:var(--accent); }
article table { border-collapse:separate; border-spacing:0; width:100%; font-size:13.5px;
                margin:16px 0; border:1px solid var(--line); border-radius:8px; overflow:hidden; }
article th, article td { border:1px solid var(--line); padding:7px 12px; text-align:left;
                         vertical-align:top; }
article th { background:var(--thead); font-weight:600; white-space:nowrap; }
article tbody tr:nth-child(even) { background:#faf9f7; }
article tbody tr:hover { background:#f3efe9; }
article code { background:#f0eeea; padding:2px 6px; border-radius:4px; font-size:13px;
               font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace; }
article pre { background:#1d1d1b; color:#e8e6e1; padding:16px; border-radius:8px;
              overflow-x:auto; line-height:1.6; }
article pre code { background:none; color:inherit; padding:0; }
article blockquote { border-left:3px solid var(--accent); margin:14px 0; padding:4px 16px;
                     background:#faf7f4; color:#555; border-radius:0 6px 6px 0; }
article blockquote p { margin:6px 0; }
article img { max-width:100%; border-radius:6px; }
article a { color:var(--accent); }
article hr { border:none; border-top:1px solid var(--line); margin:24px 0; }
article strong { color:#1a1a1a; }

footer { color:var(--muted); font-size:12px; padding:10px 0 40px; text-align:center; }
@media (max-width:640px){
  main article { padding:18px 16px; }
  .cards { grid-template-columns:1fr; }
  header.site h1 { font-size:20px; }
  article th, article td { padding:6px 8px; }
}
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
  <div class="sub">每日盘后复盘报告 · 纯分析建议模式</div>
</div></header>
<nav class="wrap crumb"><a href="index.html">首页</a>{crumb}</nav>
<main class="wrap">
{body}
</main>
<footer>自动构建于 {time} · GitHub Pages</footer>
</body>
</html>
"""

# 首页卡片要展示的关键指标（按此顺序，从报告表格首两列提取）
KEY_METRICS = ["涨停", "跌停", "炸板", "最高连板", "最高高度", "成交额"]
STAGE_KEYWORDS = ["繁荣", "复苏", "退潮", "分歧", "冰点"]


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
        if line and not line.startswith("#") and not line.startswith(">") \
                and not line.startswith("---") and not line.startswith("|"):
            clean = line.replace("**", "").lstrip("- ").lstrip("* ").strip()
            if clean:
                return clean[:140] + ("…" if len(clean) > 140 else "")
    return ""


def report_date(fname):
    m = re.search(r"(\d{8})_review\.md", fname)
    return m.group(1) if m else None


def extract_metrics(text):
    """从报告表格行提取关键指标：`| 涨停 | 37家 | ...` -> {涨停: "37家"}"""
    metrics = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if not m:
            continue
        label, value = m.group(1).strip(), m.group(2).strip()
        for key in KEY_METRICS:
            if label == key and value and len(value) < 20:
                metrics[key] = value
                break
    return metrics


def extract_stage(text):
    """从"周期阶段："标题行提取周期阶段（仅作卡片徽标，不做精确判断）"""
    for line in text.splitlines():
        line = line.strip()
        if "周期阶段" in line and "：" in line:
            seg = line.split("：", 1)[1]
            for kw in STAGE_KEYWORDS:
                if kw in seg:
                    return kw
    return None


def badge_class(stage):
    if stage in ("繁荣", "复苏"):
        return "badge"
    return "badge soft"


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
            "sort": date or fname,
            "metrics": extract_metrics(text),
            "stage": extract_stage(text),
        })
    return links


def card_html(it):
    stage = it.get("stage")
    badge = (f'<span class="{badge_class(stage)}">{html.escape(stage)}</span>' if stage else "")
    chips = "".join(
        f'<span class="chip"><b>{html.escape(k)}</b> {html.escape(v)}</span>'
        for k, v in it["metrics"].items()
    )
    return (
        f'<a class="card" href="{it["href"]}">'
        f'<div class="card-head"><span class="card-date">{it["sort"]}</span>{badge}</div>'
        f'<h3>{html.escape(it["label"])}</h3>'
        f'<p class="desc">{html.escape(it["desc"])}</p>'
        f'<div class="chips">{chips}</div>'
        f'</a>'
    )


def build_index(out_dir, report_links):
    cards = "\n".join(card_html(it) for it in sorted(report_links, key=lambda x: x["sort"], reverse=True))
    body = f'<h2 class="page-title">每日复盘报告</h2>\n<div class="cards">\n{cards}\n</div>'

    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            title="首页",
            css="style.css",
            crumb="",
            body=body,
            time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ))

    with open(os.path.join(out_dir, "reports.html"), "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            title="复盘报告",
            css="style.css",
            crumb="",
            body=f'<h2 class="page-title">全部复盘报告</h2>\n<div class="cards">\n{cards}\n</div>',
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