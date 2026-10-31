#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对“能对应到具体技术词”的论文 / 专利 / 政策做基础描述统计，并出图。

范围：与 docs/覆盖统计.md 相同——文档标题（论文/专利为标题+摘要，政策为正文）
至少命中词典（subtopics/ 下 1,811 词条）中的一个词条。

依赖：
  - 论文：<workspace>/analyze/data/independent_corpus.duckdb 的 works 表
  - 专利：<workspace>/data/patent/*.csv
  - 政策：<workspace>/data/policy/政策全文.jsonl
  - 匹配实现：<workspace>/energy-topic-hotspots/src/...

用法：
  python stats/build_stats.py            # 生成 data/*.csv 与 figures/*.png
  python stats/build_stats.py --no-fig   # 只出 CSV
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import json
import math
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
HOTSPOTS_SRC = WORKSPACE / "energy-topic-hotspots" / "src"
sys.path.insert(0, str(HOTSPOTS_SRC))

import duckdb  # noqa: E402
import pandas as pd  # noqa: E402
from energy_hotspots.term_hotspots.extract_counts import (  # noqa: E402
    load_terms, _build_globals, _init_matcher, _match_pids,
)

DB = WORKSPACE / "analyze" / "data" / "independent_corpus.duckdb"
PATENT_DIR = WORKSPACE / "data" / "patent"
POLICY_JSONL = WORKSPACE / "data" / "policy" / "政策全文.jsonl"
OUT = ROOT / "stats" / "data"
FIG = ROOT / "stats" / "figures"
YEARS = [str(y) for y in range(2021, 2027)]
# 专利统计只取 2021–2025：2026 仅 1–5 月完整且收录口径与往年不同
PATENT_STAT_YEARS = [str(y) for y in range(2021, 2026)]
PATENT_PREFIXES = ("H01F", "H02B", "H02G", "H02H", "H02J", "H02M")
UNKNOWN = "(未标注)"


def clean(x):
    """把 pandas 的 NaN / None / 'nan' 统一成空串。"""
    if x is None:
        return ""
    s = str(x).strip()
    return "" if s.lower() in ("nan", "none", "null") else s

_TERMS = load_terms()
_build_globals(_TERMS)
_init_matcher()


# ----------------------------------------------------------------- 论文
def scan_paper_batch(rows):
    inst = collections.Counter()
    journal = collections.Counter()
    lang = collections.Counter()
    typ = collections.Counter()
    cites = []
    n = 0
    for wid, year, title, abstract, institutions, jr, lg, tp, cb in rows:
        text = ((title or "") + " \n " + (abstract or "")).strip()
        if not text or not _match_pids(text):
            continue
        n += 1
        if institutions:
            for name in str(institutions).split(";"):
                name = name.strip()
                if name:
                    inst[name] += 1
        else:
            inst[UNKNOWN] += 1
        journal[str(jr).strip() if jr else UNKNOWN] += 1
        lang[str(lg).strip() if lg else UNKNOWN] += 1
        typ[str(tp).strip() if tp else UNKNOWN] += 1
        try:
            cites.append(int(float(cb)))
        except Exception:
            cites.append(0)
    return {
        "n": n, "inst": inst, "journal": journal,
        "lang": lang, "typ": typ, "cites": cites,
    }


def scan_papers(workers=32, batch=20000):
    con = duckdb.connect(str(DB), read_only=True)
    totals = collections.Counter()
    inst = collections.Counter()
    journal = collections.Counter()
    lang = collections.Counter()
    typ = collections.Counter()
    cites = []
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    with ctx.Pool(workers) as pool:
        for year in range(2021, 2027):
            q = f"""
                select work_id, publication_year, clean_title, clean_abstract,
                       institutions, journal, language, type, cited_by_count
                from works
                where is_retracted = false
                  and publication_date >= DATE '{year}-01-01'
                  and publication_date <= DATE '{year}-12-31'
            """
            cur = con.execute(q)
            while True:
                rows = cur.fetchmany(batch)
                if not rows:
                    break
                chunks = [rows[i:i + 5000] for i in range(0, len(rows), 5000)]
                for res in pool.map(scan_paper_batch, chunks):
                    totals[str(year)] += res["n"]
                    inst.update(res["inst"])
                    journal.update(res["journal"])
                    lang.update(res["lang"])
                    typ.update(res["typ"])
                    cites.extend(res["cites"])
            print(f"papers {year}: covered={totals[str(year)]}", file=sys.stderr, flush=True)
    con.close()
    return {
        "by_year": totals, "institutions": inst, "journals": journal,
        "languages": lang, "types": typ, "citations": cites,
    }


# ----------------------------------------------------------------- 专利
PATENT_COLS = ["publication_number", "publication_date", "country_code", "title",
               "abstract", "assignees", "status_normalized", "ipc_prefix", "ipcs"]


def scan_patent_chunk(df):
    out = []
    cols = set(df.columns)
    has_assignees = "assignees" in cols
    has_status = "status_normalized" in cols
    for _, r in df.iterrows():
        title = r.get("title") or ""
        abstract = (r.get("abstract") or "") if "abstract" in cols else ""
        text = (str(title) + " \n " + str(abstract)).strip()
        if not text or not _match_pids(text):
            continue
        pub = str(r.get("publication_number") or "")
        if not pub:
            continue
        year = str(r.get("publication_date") or "")[:4]
        if year not in PATENT_STAT_YEARS:
            continue
        ipc = str(r.get("ipc_prefix") or "") if "ipc_prefix" in cols else ""
        if not ipc and "ipcs" in cols:
            raw = str(r.get("ipcs") or "")
            for token in raw.replace(";", "|").replace(",", "|").split("|"):
                token = token.strip().upper()
                if token[:4] in PATENT_PREFIXES:
                    ipc = token[:4]
                    break
        out.append({
            "pub": pub, "year": year,
            "country": clean(r.get("country_code")),
            "assignees": clean(r.get("assignees")),
            "status": clean(r.get("status_normalized")),
            "ipc": ipc,
            "has_assignees": has_assignees,
            "has_status": has_status,
        })
    return out


def scan_patents(workers=32):
    files = sorted(glob.glob(str(PATENT_DIR / "*.csv")))
    by_year = collections.Counter()
    by_country = collections.Counter()
    by_assignee = collections.Counter()
    by_status = collections.Counter()
    by_ipc = collections.Counter()
    country_year = collections.Counter()
    seen = set()
    covered = set()
    ipc_map = {}
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    with ctx.Pool(workers) as pool:
        for path in files:
            usecols = None
            try:
                head = pd.read_csv(path, nrows=0)
                usecols = [c for c in PATENT_COLS if c in head.columns]
            except Exception:
                continue
            for chunk in pd.read_csv(path, usecols=usecols, dtype=str,
                                     chunksize=40000, on_bad_lines="skip"):
                for rows in pool.map(scan_patent_chunk, [chunk]):
                    for r in rows:
                        pub = r["pub"]
                        if pub in seen:
                            continue
                        seen.add(pub)
                        covered.add(pub)
                        by_year[r["year"]] += 1
                        if r["country"]:
                            by_country[r["country"]] += 1
                            country_year[(r["year"], r["country"])] += 1
                        if r["has_assignees"]:
                            if r["assignees"]:
                                for a in r["assignees"].split("|"):
                                    a = a.strip()
                                    if a:
                                        by_assignee[a] += 1
                            else:
                                by_assignee[UNKNOWN] += 1
                        if r["has_status"]:
                            by_status[r["status"] or UNKNOWN] += 1
                        if r["ipc"]:
                            by_ipc[r["ipc"]] += 1
                            ipc_map[pub] = r["ipc"]
            print(f"patents {Path(path).name}: total covered={len(seen)}", file=sys.stderr, flush=True)
    # 2026.csv 没有 assignees/status，2026 的份额会落到 (未标注)
    return {
        "by_year": by_year, "by_country": by_country, "by_assignee": by_assignee,
        "by_status": by_status, "by_ipc": by_ipc, "country_year": country_year,
        "covered": len(covered),
    }


# ----------------------------------------------------------------- 政策
def scan_policies():
    by_year = collections.Counter()
    by_publisher = collections.Counter()
    by_region = collections.Counter()
    by_level = collections.Counter()
    by_type = collections.Counter()
    by_relevance = collections.Counter()
    n = 0
    with POLICY_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            j = json.loads(line)
            text = (j.get("text") or "").strip()
            if not text:
                continue
            if not _match_pids(text):
                continue
            n += 1
            y = (j.get("publication_date") or j.get("issue_date") or "")[:4]
            if not y.isdigit():
                y = "unknown"
            by_year[y] += 1
            by_publisher[(j.get("publisher") or UNKNOWN).strip()] += 1
            by_region[(j.get("applicable_region") or UNKNOWN).strip()] += 1
            by_level[(j.get("administrative_level") or UNKNOWN).strip()] += 1
            by_type[(j.get("policy_type") or UNKNOWN).strip()] += 1
            by_relevance[(j.get("relevance_tier") or UNKNOWN).strip()] += 1
    return {
        "n": n, "by_year": by_year, "publishers": by_publisher,
        "regions": by_region, "levels": by_level, "types": by_type,
        "relevance": by_relevance,
    }


# ----------------------------------------------------------------- CSV
def write_csv(name, header, rows):
    path = OUT / name
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def top_rows(counter, n=100, label=None):
    total = sum(counter.values()) or 1
    rows = []
    for i, (k, v) in enumerate(counter.most_common(n), 1):
        rows.append([i, k, v, f"{v / total:.4f}"])
    return rows


def dump_papers(p):
    total = sum(p["by_year"].values())
    rows = []
    for y in YEARS:
        rows.append([y, p["by_year"].get(y, 0),
                     f"{p['by_year'].get(y, 0) / total:.4f}" if total else "0"])
    # 引用统计按年
    # 注：citations 列表与年份的对应关系未保留，这里只给整体引用分布
    import numpy as np
    c = np.array(p["citations"]) if p["citations"] else np.array([0])
    write_csv("papers_by_year.csv",
              ["year", "papers", "share"], rows)
    write_csv("papers_by_institution.csv",
              ["rank", "institution", "papers", "share"], top_rows(p["institutions"]))
    write_csv("papers_by_journal.csv",
              ["rank", "journal", "papers", "share"], top_rows(p["journals"]))
    write_csv("papers_by_language.csv",
              ["language", "papers", "share"],
              [[k, v, f"{v / total:.4f}"] for k, v in p["languages"].most_common()])
    write_csv("papers_by_type.csv",
              ["type", "papers", "share"],
              [[k, v, f"{v / total:.4f}"] for k, v in p["types"].most_common()])
    write_csv("papers_citations.csv",
              ["papers", "citation_sum", "citation_mean", "citation_median",
               "citation_p90", "share_cited"],
              [[total, int(c.sum()), f"{c.mean():.2f}", f"{float(np.median(c)):.1f}",
                f"{float(np.percentile(c, 90)):.1f}", f"{(c > 0).mean():.4f}"]])


def dump_patents(p):
    total = sum(p["by_year"].values())
    write_csv("patents_by_year.csv",
              ["year", "patents", "share"],
              [[y, p["by_year"].get(y, 0),
                f"{p['by_year'].get(y, 0) / total:.4f}" if total else "0"] for y in PATENT_STAT_YEARS])
    write_csv("patents_by_country.csv",
              ["rank", "country_code", "patents", "share"],
              top_rows(p["by_country"], 80))
    write_csv("patents_by_assignee.csv",
              ["rank", "assignee", "patents", "share"],
              top_rows(p["by_assignee"], 100))
    st_total = sum(p["by_status"].values()) or 1
    write_csv("patents_by_status.csv",
              ["status", "patents", "share"],
              [[k, v, f"{v / st_total:.4f}"] for k, v in p["by_status"].most_common()])
    ipc_total = sum(p["by_ipc"].values()) or 1
    write_csv("patents_by_ipc.csv",
              ["ipc_prefix", "patents", "share"],
              [[k, v, f"{v / ipc_total:.4f}"] for k, v in p["by_ipc"].most_common()])
    # 前 10 国家 × 年份
    top_countries = [c for c, _ in p["by_country"].most_common(10)]
    rows = []
    for y in PATENT_STAT_YEARS:
        for c in top_countries:
            rows.append([y, c, p["country_year"].get((y, c), 0)])
    write_csv("patents_top_countries_by_year.csv",
              ["year", "country_code", "patents"], rows)


def dump_policies(p):
    years = sorted(k for k in p["by_year"] if k.isdigit())
    total = sum(p["by_year"].values())
    write_csv("policies_by_year.csv",
              ["year", "policies", "share"],
              [[y, p["by_year"][y], f"{p['by_year'][y] / total:.4f}"] for y in years])
    write_csv("policies_by_publisher.csv",
              ["rank", "publisher", "policies", "share"], top_rows(p["publishers"], 80))
    for name, key in (("policies_by_region.csv", "regions"),
                      ("policies_by_level.csv", "levels"),
                      ("policies_by_type.csv", "types"),
                      ("policies_by_relevance.csv", "relevance")):
        write_csv(name, [name.split("_")[-1].replace(".csv", ""), "policies", "share"],
                  [[k, v, f"{v / total:.4f}"] for k, v in p[key].most_common()])


# ----------------------------------------------------------------- 图
def read_stat(name):
    with (OUT / name).open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def make_figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    names = {f.name for f in font_manager.fontManager.ttflist}
    for cand in ("Noto Sans CJK SC", "Noto Serif CJK SC", "WenQuanYi Zen Hei"):
        if cand in names:
            plt.rcParams["font.sans-serif"] = [cand]
            break
    plt.rcParams["axes.unicode_minus"] = False
    FIG.mkdir(parents=True, exist_ok=True)

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(FIG / name, dpi=160)
        plt.close(fig)

    def iv(v):
        try:
            return int(float(v))
        except Exception:
            return 0

    def known(rows, key, n=15):
        out = [r for r in rows if r[key] not in ("", "(未标注)", "nan", "None")]
        return out[:n]

    # 论文
    py = read_stat("papers_by_year.csv")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    ys = [r["year"] for r in py]
    vals = [iv(r["papers"]) for r in py]
    axes[0, 0].bar(ys, vals, color="#3b7dd8")
    axes[0, 0].set_title("论文：逐年发文量（命中词典）")
    axes[0, 0].set_ylabel("篇")
    if ys:
        axes[0, 0].annotate("2026 仅到 6 月", xy=(ys[-1], vals[-1]), ha="center",
                           xytext=(0, 6), textcoords="offset points", fontsize=8)
    inst = known(read_stat("papers_by_institution.csv"), "institution", 15)
    axes[0, 1].barh([r["institution"] for r in inst][::-1],
                    [iv(r["papers"]) for r in inst][::-1], color="#4c9f70")
    axes[0, 1].set_title("论文：Top 15 机构（不含未标注）")
    axes[0, 1].set_xlabel("篇")
    langs = [r for r in read_stat("papers_by_language.csv") if r["language"] != "(未标注)"][:8]
    axes[1, 0].bar([r["language"] for r in langs], [iv(r["papers"]) for r in langs],
                   color="#d98b3a")
    axes[1, 0].set_title("论文：语言分布（Top 8，不含未标注）")
    axes[1, 0].tick_params(axis="x", rotation=30)
    types = read_stat("papers_by_type.csv")
    axes[1, 1].pie([iv(r["papers"]) for r in types], labels=[r["type"] for r in types],
                   autopct="%1.1f%%")
    axes[1, 1].set_title("论文：文献类型")
    save(fig, "papers_overview.png")

    fig, ax = plt.subplots(figsize=(7, 8))
    jour = read_stat("papers_by_journal.csv")[:20]
    ax.barh([r["journal"] for r in jour][::-1], [iv(r["papers"]) for r in jour][::-1],
            color="#7a6bc9")
    ax.set_title("论文：Top 20 期刊/来源")
    ax.set_xlabel("篇")
    save(fig, "papers_journals.png")

    # 专利
    pat = read_stat("patents_by_year.csv")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    ys = [r["year"] for r in pat]
    vals = [iv(r["patents"]) for r in pat]
    axes[0, 0].bar(ys, vals, color="#c0504d")
    axes[0, 0].set_title("专利：逐年公开量（命中词典）")
    axes[0, 0].set_ylabel("件")
    if ys:
        axes[0, 0].annotate("2021–2025（2026 已排除）", xy=(0.02, 0.95),
                           xycoords="axes fraction", fontsize=8)
    ctry = read_stat("patents_by_country.csv")[:15]
    axes[0, 1].barh([r["country_code"] for r in ctry][::-1],
                    [iv(r["patents"]) for r in ctry][::-1], color="#3b7dd8")
    axes[0, 1].set_title("专利：Top 15 公开国家/地区")
    axes[0, 1].set_xlabel("件")
    asg = known(read_stat("patents_by_assignee.csv"), "assignee", 15)
    axes[1, 0].barh([r["assignee"] for r in asg][::-1],
                    [iv(r["patents"]) for r in asg][::-1], color="#4c9f70")
    axes[1, 0].set_title("专利：Top 15 申请人（不含未标注）")
    axes[1, 0].set_xlabel("件")
    st = read_stat("patents_by_status.csv")
    axes[1, 1].pie([iv(r["patents"]) for r in st], labels=[r["status"] for r in st],
                   autopct="%1.1f%%")
    axes[1, 1].set_title("专利：法律状态（2021–2025）")
    save(fig, "patents_overview.png")

    # 政策
    pol = read_stat("policies_by_year.csv")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    ys = [r["year"] for r in pol]
    axes[0, 0].bar(ys, [iv(r["policies"]) for r in pol], color="#8c6d31")
    axes[0, 0].set_title("政策：逐年发文量（命中词典）")
    axes[0, 0].tick_params(axis="x", rotation=60, labelsize=7)
    pub = known(read_stat("policies_by_publisher.csv"), "publisher", 15)
    axes[0, 1].barh([r["publisher"] for r in pub][::-1],
                    [iv(r["policies"]) for r in pub][::-1], color="#3b7dd8")
    axes[0, 1].set_title("政策：Top 15 发布机构（不含未标注）")
    axes[0, 1].set_xlabel("条")
    reg = known(read_stat("policies_by_region.csv"), "region", 10)
    axes[1, 0].barh([r["region"] for r in reg][::-1],
                    [iv(r["policies"]) for r in reg][::-1], color="#4c9f70")
    axes[1, 0].set_title("政策：Top 10 适用区域（不含未标注）")
    typ = read_stat("policies_by_type.csv")[:8]
    axes[1, 1].pie([iv(r["policies"]) for r in typ], labels=[r["type"] for r in typ],
                   autopct="%1.1f%%")
    axes[1, 1].set_title("政策：政策类型")
    save(fig, "policies_overview.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fig", action="store_true")
    ap.add_argument("--fig-only", action="store_true")
    ap.add_argument("--patents-only", action="store_true")
    ap.add_argument("--workers", type=int, default=32)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.fig_only:
        make_figures()
        print("figures rebuilt from CSV")
        return
    if args.patents_only:
        patents = scan_patents(args.workers)
        dump_patents(patents)
        if not args.no_fig:
            make_figures()
        print(json.dumps({"patents": patents["covered"]}, ensure_ascii=False))
        return
    papers = scan_papers(args.workers)
    patents = scan_patents(args.workers)
    policies = scan_policies()
    dump_papers(papers)
    dump_patents(patents)
    dump_policies(policies)
    if not args.no_fig:
        make_figures()
    print(json.dumps({"papers": sum(papers["by_year"].values()),
                      "patents": patents["covered"],
                      "policies": policies["n"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
