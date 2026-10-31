# 基础数据统计（stats/）

本目录存放**能对应到具体技术词**的论文 / 专利 / 政策文档的覆盖统计，是
[docs/覆盖统计.md](../docs/覆盖统计.md) 的机器可读版本与分年明细。

## 口径

- **词表**：本仓库 `subtopics/` 下 33 个 CSV，共 1,811 个词条（中文官方名、英文官方名、别称/简称）。
- **匹配**：与 `energy-topic-hotspots` 的 `src/energy_hotspots/term_hotspots/extract_counts.py` 同一实现——
  词条级 Aho-Corasick、父子词条最长匹配抑制、短缩略语大小写敏感（CO ≠ Co）、英文复数与分隔符归一。
- **命中 / 覆盖**：文档的标题（论文为标题+摘要，专利为标题+摘要，政策为正文）中至少出现该词条任一变体；
  一篇文档对同一词条至多计 1 次。
- 覆盖率的分母是该年度该来源的**全部文档**，分子是其中**至少命中一个词条**的文档；词条级命中数见
  `term_hits_by_year.csv`（同一篇文档可命中多个词条，因此词条命中数之和 ≥ 文档数）。

## 文件

| 文件 | 内容 |
|---|---|
| `coverage_by_source.csv` | 三源汇总：窗口、文档总数、命中文档数、命中率、口径备注 |
| `coverage_by_year.csv` | 三源 × 2021–2026 分年：`total_docs` / `covered_docs` / `hit_rate` |
| `term_hits_by_year.csv` | 词条 × 来源 × 年份的命中数（`paper` / `patent` / `policy`） |

## 各来源口径与 2026 注意

- **论文**：`analyze/data/independent_corpus.duckdb` 的 `works` 表，`is_retracted=false`，
  窗口 2021-01-01 – 2026-12-31；按 `clean_title + clean_abstract` 匹配。
  分年合计 **1,754,330** 篇，与 `docs/覆盖统计.md` 的 1,754,329 相差 1 篇（数据库版本微调），
  覆盖率四舍五入后同为 85.3%。
  `term_hits_by_year.csv` 的论文命中按季度汇总：分析窗是 2021Q3–2026Q2，因此 2021 只有 Q3–Q4、
  2026 只有 Q1–Q2 的命中。
- **专利**：`data/patent/*.csv`（含 2021–2026），按 `publication_number` 全局去重；
  2021–2026 共 **538,066** 件，命中 **418,978** 件（77.9%）。
  2026 仅 1–5 月完整（6–8 月零星），且来自 `patent_v3` 全量快照，收录口径与
  2021–2025（按 IPC 小组 + OPS 导出）不同，**只用于覆盖统计，不用于跨年增速**。
- **政策**：`data/policy/政策全文.jsonl`，要求正文 `text` 非空；2000–2026 共 **6,621** 条，
  命中 **5,519** 条（83.4%）。2026 截至 2026-09；另有 61 条无日期记录（不计入分年表）。

## 复算

- 论文：`works` 表按年分批扫描 `clean_title + clean_abstract`，用上述词表做 Aho-Corasick 匹配，
  统计"至少命中一个词条"的文档数。
- 专利：逐 CSV 读取 `publication_number` / `publication_date` / `title` / `abstract`，按公开号去重后匹配。
- 政策：逐行读取 JSONL，正文非空才计入；按 `publication_date`（缺则 `issue_date`）取年份。
- 词条级命中明细来自 `energy-topic-hotspots` 的
  `outputs/terms/papers_by_quarter.csv`、`patents_by_year.csv`、`policies_by_year.csv`，
  `term_hits_by_year.csv` 是这三张表的合并版（论文按季度求和到年）。
