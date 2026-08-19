# 每日复盘报告（GitHub Pages）

A 股市场分析多 Agent 系统（[ai-market-analysis-agent-system](https://github.com/baiyulong/ai-market-analysis-agent-system)）产出的每日盘后复盘报告。

- `reports/`：每日复盘报告 `<date>_review.md`
- `scripts/build_site.py`：把 `reports/` 渲染为静态站点（仅报告，不含方法论文档）
- `.github/workflows/pages.yml`：push 到 `main` 后自动构建并部署 GitHub Pages

## 发布流程

1. 从主仓库复制新报告：`cp ../ai-market-analysis-agent-system/reports/<date>_review.md reports/`
2. `git add -A && git commit -m "<date> 复盘" && git push`
3. Actions 自动构建部署，站点：`https://baiyulong.github.io/ai-daily-market-analysis/`