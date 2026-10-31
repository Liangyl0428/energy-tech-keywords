# 基础数据统计（stats/）

统计对象：**能对应到具体技术词**的论文 / 专利 / 政策——即标题（论文、专利为标题+摘要，政策为正文）
至少命中本仓库 `subtopics/` 词典（33 个子方向、1,811 个词条）中任一词条的文档。
范围与 [docs/覆盖统计.md](../docs/覆盖统计.md) 的"命中文档"一致。

本次统计（2026-10-31）：**论文 1,496,283 篇、专利 343,618 件（2021–2025）、政策 5,519 条**命中词典。

- `data/`：统计结果 CSV（UTF-8 with BOM，Excel 可直接打开）
- `figures/`：可视化图表 PNG
- `build_stats.py`：可复算脚本（读取 OpenAlex `works` 表、`data/patent/*.csv`、`data/policy/政策全文.jsonl`）

## 一、论文（OpenAlex）

本次共 **1,496,283 篇**（2021–2026）；2026 年截至语料快照（约 2026 年中），趋势图末年为不完整年度。

| 文件 | 内容 |
|---|---|
| `data/papers_by_year.csv` | 逐年发文量、占比 |
| `data/papers_by_institution.csv` | Top 100 机构（`institutions` 字段按 `;` 拆分） |
| `data/papers_by_journal.csv` | Top 20 期刊/来源 |
| `data/papers_by_language.csv` | 语言分布 |
| `data/papers_by_type.csv` | 文献类型（article / preprint 等） |
| `data/papers_citations.csv` | 被引次数总体分布（总和/均值/中位数/P90/有引用占比） |
| `figures/papers_overview.png` | 发文趋势、Top 机构、语言、类型四联图 |
| `figures/papers_journals.png` | Top 20 期刊/来源 |

**关于"地域分布"**：`works` 表只保留了机构名称（`institutions`），没有国家/地区字段，
因此论文侧无法统计国家分布；机构与语言、期刊来源是可用的替代维度。若需要国家分布，
需回到 `data/article/*.csv` 的 `raw_authorships`（含机构 `country_code`）重新关联。

## 二、专利

本次共 **343,618 件**（2021–2025，按公开号去重）。2026 年专利仅 1–5 月完整、收录口径与往年不同，
**不纳入本目录的描述统计**；2026 的覆盖率仍见 [docs/覆盖统计.md](../docs/覆盖统计.md)。

| 文件 | 内容 |
|---|---|
| `data/patents_by_year.csv` | 逐年公开量、占比 |
| `data/patents_by_country.csv` | Top 80 公开国家/地区（`country_code`） |
| `data/patents_by_assignee.csv` | Top 100 申请人（`assignees` 按 `\\|` 拆分） |
| `data/patents_by_status.csv` | 法律状态分布（`status_normalized`） |
| `data/patents_by_ipc.csv` | 6 个能源 IPC 小类分布（H01F/H02B/H02G/H02H/H02J/H02M） |
| `data/patents_top_countries_by_year.csv` | Top 10 国家 × 年份（趋势用） |
| `figures/patents_overview.png` | 年度趋势、Top 国家、Top 申请人、法律状态四联图 |

口径提示：

- 按 `publication_number` 全局去重；聚合表（2021_2023、2024_2025）优先于 IPC 分表。
- 申请人按 `|` 拆分，份额分母是全部申请人署名（一件专利可有多个申请人）；法律状态份额分母为有状态记录数；IPC 份额分母为能归入 6 个能源小类的记录数。
- 本目录的专利统计不含 2026。
- 2026 专利（1–5 月完整）只进入 [docs/覆盖统计.md](../docs/覆盖统计.md) 的覆盖率，不进入本目录的分布统计。

## 三、政策

本次共 **5,519 条**（2000–2026）命中词典；2026 年数据截至 2026-09。

| 文件 | 内容 |
|---|---|
| `data/policies_by_year.csv` | 逐年政策量、占比（2000–2026；不含 56 条无日期） |
| `data/policies_by_publisher.csv` | Top 80 发布机构（`publisher`） |
| `data/policies_by_region.csv` | 适用区域（`applicable_region`） |
| `data/policies_by_level.csv` | 行政层级（`administrative_level`） |
| `data/policies_by_type.csv` | 政策类型（`policy_type`） |
| `data/policies_by_relevance.csv` | 相关性分级（`relevance_tier`） |
| `figures/policies_overview.png` | 年度趋势、Top 发布机构、区域、类型四联图 |

2026 年政策截至 2026-09；另有 56 条命中词典但无日期（语料共 61 条无日期），未计入 `policies_by_year.csv`，因此分年表合计 5,463 条。

## 四、复算

```bash
# 依赖：本机 OpenAlex works 库、data/patent、data/policy，以及 energy-topic-hotspots 的匹配实现
python stats/build_stats.py            # 生成 data/*.csv + figures/*.png
python stats/build_stats.py --no-fig   # 只出 CSV
```

匹配口径与 `energy-topic-hotspots/src/energy_hotspots/term_hotspots/extract_counts.py` 一致：
Aho-Corasick、文档级去重、父子词条最长匹配抑制、短缩略语大小写敏感。
