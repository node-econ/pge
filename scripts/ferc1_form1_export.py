#!/usr/bin/env python3
"""FERC Form 1 financials from Zenodo raw XBRL — see module docstring after imports."""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

__doc__ = """\
FERC Form 1 (Income, Balance Sheet, Cash Flows) from Catalyst Zenodo raw XBRL:
https://zenodo.org/records/19947273

PUDL: https://github.com/catalyst-cooperative/pudl
Docs: https://docs.catalyst.coop/pudl/en/v2025.7.0/data_sources/ferc1.html

Outputs to data/utilities/ferc1_pge_viewer/:
  pge_form1_financials.json, pge_form1_financials.md, index.html

JSON groups each statement with one row per line and ``by_year`` amounts (raw
strings from XBRL). Display uses **USD millions** (value ÷ 1e6) with **two**
decimal places. Future calendar years may appear as empty placeholder columns.
"""

ZENODO = "19947273"

# Shown in outputs with empty amounts until XBRL is exported for that year.
PLACEHOLDER_DISPLAY_YEARS: tuple[int, ...] = (2026,)
ZENODO_FILE = f"https://zenodo.org/records/{ZENODO}/files/{{}}?download=1"
LINK_NS = "http://www.xbrl.org/2003/linkbase"
XLINK_NS = "http://www.w3.org/1999/xlink"
XBRLI_NS = "http://www.xbrl.org/2003/instance"
PARENT_CHILD = "http://www.xbrl.org/2003/arcrole/parent-child"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def zip_dir() -> Path:
    return repo_root() / "data" / "utilities" / "ferc1_raw_zips"


def tax_extract_dir() -> Path:
    return repo_root() / "data" / "utilities" / "ferc1_taxonomy_extracted"


def viewer_dir() -> Path:
    return repo_root() / "data" / "utilities" / "ferc1_pge_viewer"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "PGE-ferc1-export/1.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as out:
        out.write(r.read())


def ensure_zip(name: str) -> Path:
    p = zip_dir() / name
    if not p.is_file():
        zip_dir().mkdir(parents=True, exist_ok=True)
        print(f"Downloading {name}", file=sys.stderr)
        download(ZENODO_FILE.format(name), p)
    return p


def extract_form_taxonomy(tax_bundle: Path, form_ver: str) -> Path:
    out = tax_extract_dir() / f"form-1-{form_ver}"
    marker = out / ".extracted"
    if marker.is_file():
        return out
    inner = f"form-1-{form_ver}.zip"
    with zipfile.ZipFile(tax_bundle, "r") as z:
        if inner not in z.namelist():
            raise FileNotFoundError(f"{inner} not in {tax_bundle}")
        blob = z.read(inner)
    tmp = tax_extract_dir() / f"_{inner}"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(blob)
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(tmp, "r") as z2:
        z2.extractall(out)
    tmp.unlink(missing_ok=True)
    marker.write_text("ok", encoding="utf-8")
    return out


def ferc_ns_from_instance(root: ET.Element) -> str:
    for _p, uri in root.items():
        if isinstance(uri, str) and uri.startswith("http://ferc.gov/form/") and uri.endswith("/ferc"):
            return uri
    for child in root:
        if child.tag.endswith("schemaRef"):
            href = child.get(f"{{{XLINK_NS}}}href", "")
            m = re.search(r"/form-1_(\d{4}-\d{2}-\d{2})\.xsd", href)
            if m:
                return f"http://ferc.gov/form/{m.group(1)}/ferc"
    raise ValueError("Could not determine FERC namespace from XBRL instance.")


def form_version_from_ns(ns: str) -> str:
    m = re.search(r"http://ferc\.gov/form/(\d{4}-\d{2}-\d{2})/ferc", ns)
    if not m:
        raise ValueError(ns)
    return m.group(1)


def local_from_href(href: str) -> str:
    frag = href.split("#", 1)[-1]
    return frag[5:] if frag.startswith("ferc_") else frag


def parse_presentation(pre_path: Path, abstract_local: str) -> list[tuple[str, int]]:
    tree = ET.parse(pre_path)
    r = tree.getroot()
    locs: dict[str, str] = {}
    for loc in r.findall(f".//{{{LINK_NS}}}loc"):
        lab = loc.get(f"{{{XLINK_NS}}}label")
        href = loc.get(f"{{{XLINK_NS}}}href")
        if lab and href:
            locs[lab] = local_from_href(href)
    root_lab = next(
        (lab for lab, name in locs.items() if name == abstract_local), None
    )
    if not root_lab:
        raise ValueError(f"Root {abstract_local} not found in {pre_path}")

    xlink_arcrole = f"{{{XLINK_NS}}}arcrole"
    xlink_from = f"{{{XLINK_NS}}}from"
    xlink_to = f"{{{XLINK_NS}}}to"
    children: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for arc in r.findall(f".//{{{LINK_NS}}}presentationArc"):
        if arc.get(xlink_arcrole) != PARENT_CHILD:
            continue
        fr = arc.get(xlink_from)
        to = arc.get(xlink_to)
        if fr and to:
            children[fr].append((to, float(arc.get("order", "0"))))
    for lst in children.values():
        lst.sort(key=lambda x: x[1])

    # Duplicate xlink:label values can point at the same concept; arcs may attach
    # to any of those labels (e.g. StatementOfIncomeLineItems vs …_1).
    by_concept: dict[str, list[str]] = defaultdict(list)
    for lab, name in locs.items():
        by_concept[name].append(lab)

    def out_edges(lab: str) -> list[tuple[str, float]]:
        name = locs.get(lab, "")
        acc: list[tuple[str, float]] = []
        for l in by_concept.get(name, [lab]):
            acc.extend(children.get(l, []))
        acc.sort(key=lambda x: x[1])
        seen: set[str] = set()
        dedup: list[tuple[str, float]] = []
        for to, ord_ in acc:
            if to not in seen:
                seen.add(to)
                dedup.append((to, ord_))
        return dedup

    out: list[tuple[str, int]] = []

    def dfs(lab: str, depth: int) -> None:
        nm = locs.get(lab, "")
        if nm:
            out.append((nm, depth))
        for ch, _ in out_edges(lab):
            dfs(ch, depth + 1)

    dfs(root_lab, 0)
    dedup: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for item in out:
        if item not in seen:
            seen.add(item)
            dedup.append(item)
    return dedup


XBRLDI_NS = "http://xbrl.org/2006/xbrldi"


def parse_context_index(root: ET.Element) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for ctx in root.findall(f".//{{{XBRLI_NS}}}context"):
        cid = ctx.get("id")
        if not cid:
            continue
        entity = ctx.find(f"{{{XBRLI_NS}}}entity")
        seg = (
            entity.find(f"{{{XBRLI_NS}}}segment") if entity is not None else None
        )
        typed = False
        explicit: list[tuple[str, str]] = []
        if seg is not None:
            for tm in seg.findall(f"{{{XBRLDI_NS}}}typedMember"):
                typed = True
                break
            for em in seg.findall(f"{{{XBRLDI_NS}}}explicitMember"):
                dim = em.get("dimension") or ""
                mem = (em.text or "").strip()
                explicit.append((dim, mem))
        electric = any(
            mem.endswith("ElectricUtilityMember") for _d, mem in explicit
        )
        period = ctx.find(f"{{{XBRLI_NS}}}period")
        instant = ds = de = None
        if period is not None:
            ins = period.find(f"{{{XBRLI_NS}}}instant")
            if ins is not None and ins.text:
                instant = ins.text.strip()
            sd = period.find(f"{{{XBRLI_NS}}}startDate")
            ed = period.find(f"{{{XBRLI_NS}}}endDate")
            if sd is not None and ed is not None and sd.text and ed.text:
                ds, de = sd.text.strip(), ed.text.strip()
        out[cid] = {
            "electric": electric,
            "typed": typed,
            "explicit": explicit,
            "instant": instant,
            "duration_start": ds,
            "duration_end": de,
        }
    return out


def pick_contexts(
    ctx_index: dict[str, dict[str, Any]], *, year: int, mode: str
) -> set[str]:
    y0, y1 = f"{year}-01-01", f"{year}-12-31"
    ok: set[str] = set()

    def duration_match(m: dict[str, Any]) -> bool:
        return m["duration_start"] == y0 and m["duration_end"] == y1

    def instant_match(m: dict[str, Any]) -> bool:
        return m["instant"] == y1

    def allow_segment(m: dict[str, Any]) -> bool:
        """Consolidated (no dims) or single UtilityTypeAxis = electric only."""
        if m["typed"]:
            return False
        exp = m["explicit"]
        if not exp:
            return True
        if len(exp) == 1:
            dim, mem = exp[0]
            if dim.endswith("UtilityTypeAxis") and mem.endswith(
                "ElectricUtilityMember"
            ):
                return True
        return False

    for cid, m in ctx_index.items():
        if mode == "duration_year":
            if not duration_match(m) or not allow_segment(m):
                continue
            ok.add(cid)
        elif mode == "instant_yearend":
            if not instant_match(m) or not allow_segment(m):
                continue
            ok.add(cid)
    return ok


def index_facts(root: ET.Element, ferc_ns: str) -> dict[str, list[dict[str, str]]]:
    idx: dict[str, list[dict[str, str]]] = defaultdict(list)
    for el in root.iter():
        if not el.tag.startswith(f"{{{ferc_ns}}}"):
            continue
        cref = el.get("contextRef")
        if not cref:
            continue
        local = el.tag.split("}", 1)[1]
        if local.endswith("TextBlock"):
            continue
        txt = (el.text or "").strip()
        if not txt:
            continue
        idx[local].append(
            {
                "contextRef": cref,
                "unitRef": el.get("unitRef") or "",
                "value": txt,
            }
        )
    return idx


def pick_fact(
    facts: list[dict[str, str]], allowed_ctx: set[str]
) -> dict[str, str] | None:
    for row in facts:
        if row["contextRef"] in allowed_ctx:
            return row
    return None


def fmt_label(name: str) -> str:
    if name == "NetIncomeLoss":
        return "Net Income (Loss)"
    s = re.sub(r"(Abstract|Table)$", "", name)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    return s.replace("_", " ").strip()


def fmt_millions_display(raw: str | None) -> str:
    """Format a raw numeric XBRL string as millions of USD with two decimals."""
    if raw is None or raw == "":
        return ""
    try:
        v = float(raw)
    except ValueError:
        return str(raw)
    return f"{v / 1e6:,.2f}"


STATEMENT_KEYS = (
    "income_statement",
    "balance_sheet_assets",
    "balance_sheet_liabilities",
    "cash_flows",
)


def merge_statement_rows(
    years_payload: list[dict[str, Any]],
    statement_key: str,
    display_years: list[int],
) -> list[dict[str, Any]]:
    """One table per statement: row order from newest *exported* year; fill by concept."""
    exported = sorted(yp["year"] for yp in years_payload)
    by_y = {yp["year"]: yp for yp in years_payload}
    newest = exported[-1]

    def concept_value(y: int, concept: str) -> str | None:
        if y not in by_y:
            return None
        cmap = {r["concept"]: r for r in by_y[y][statement_key]}
        row = cmap.get(concept)
        return row.get("value") if row else None

    def by_year_map(concept: str) -> dict[str, str | None]:
        return {str(y): concept_value(y, concept) for y in display_years}

    primary = by_y[newest][statement_key]
    primary_concepts = {r["concept"] for r in primary}
    merged: list[dict[str, Any]] = []
    for pr in primary:
        c = pr["concept"]
        merged.append(
            {
                "concept": c,
                "label": fmt_label(c),
                "depth": pr["depth"],
                "by_year": by_year_map(c),
            }
        )
    extras: dict[str, dict[str, Any]] = {}
    for y in exported[:-1]:
        for r in by_y[y][statement_key]:
            c = r["concept"]
            if c in primary_concepts or c in extras:
                continue
            extras[c] = {
                "concept": c,
                "label": fmt_label(c),
                "depth": r["depth"],
            }
    for c in sorted(extras, key=lambda k: (extras[k]["depth"], extras[k]["label"])):
        meta = extras[c]
        merged.append(
            {
                "concept": c,
                "label": fmt_label(c),
                "depth": meta["depth"],
                "by_year": by_year_map(c),
            }
        )
    return merged


def build_view_payload(
    company: str, source: dict[str, str], years_out: list[dict[str, Any]]
) -> dict[str, Any]:
    exported_years = sorted(yp["year"] for yp in years_out)
    display_years = sorted(set(exported_years) | set(PLACEHOLDER_DISPLAY_YEARS))
    by_y = {yp["year"]: yp for yp in years_out}
    year_meta: list[dict[str, Any]] = []
    for y in display_years:
        if y in by_y:
            year_meta.append(
                {
                    "year": y,
                    "xbrl_member": by_y[y]["xbrl_member"],
                    "form_taxonomy_version": by_y[y]["form_taxonomy_version"],
                    "placeholder": False,
                }
            )
        else:
            year_meta.append(
                {
                    "year": y,
                    "xbrl_member": None,
                    "form_taxonomy_version": None,
                    "placeholder": True,
                }
            )
    payload: dict[str, Any] = {
        "company": company,
        "source": source,
        "years": display_years,
        "year_meta": year_meta,
        "amount_display": "usd_millions_two_decimals",
        "amount_display_note": (
            "Amounts in millions of USD (value ÷ 1e6, two decimal places). "
            "Placeholder years have no filing data yet."
        ),
    }
    for key in STATEMENT_KEYS:
        payload[key] = merge_statement_rows(years_out, key, display_years)
    return payload


def statement_rows(
    ordered: list[tuple[str, int]],
    fact_idx: dict[str, list[dict[str, str]]],
    ctx_ok: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    skip_suffix = ("Axis", "Domain", "Table")
    for name, depth in ordered:
        if any(name.endswith(s) for s in skip_suffix) or name == "UtilityTypeDomain":
            continue
        frows = fact_idx.get(name)
        if not frows:
            rows.append(
                {
                    "concept": name,
                    "label": fmt_label(name),
                    "depth": depth,
                    "value": None,
                    "unit": None,
                }
            )
            continue
        hit = pick_fact(frows, ctx_ok)
        rows.append(
            {
                "concept": name,
                "label": fmt_label(name),
                "depth": depth,
                "value": hit["value"] if hit else None,
                "unit": hit["unitRef"] if hit else None,
            }
        )
    return rows


def find_member(zpath: Path, needle: str) -> str:
    key = needle.lower().replace(" ", "_").replace(".", "")
    with zipfile.ZipFile(zpath, "r") as z:
        for n in z.namelist():
            if not n.lower().endswith(".xbrl"):
                continue
            stem = n.split("/")[-1].lower()
            if key in stem.replace(" ", "_"):
                return n
    raise FileNotFoundError(f"No .xbrl for {needle!r} in {zpath}")


def read_instance(zpath: Path, member: str) -> tuple[ET.Element, str]:
    with zipfile.ZipFile(zpath, "r") as z:
        root = ET.fromstring(z.read(member))
    return root, ferc_ns_from_instance(root)


def export_year(year: int, company: str, tax_bundle: Path) -> dict[str, Any]:
    zpath = ensure_zip(f"ferc1-xbrl-{year}.zip")
    member = find_member(zpath, company)
    root, ferc_ns = read_instance(zpath, member)
    form_ver = form_version_from_ns(ferc_ns)
    tax_root = extract_form_taxonomy(tax_bundle, form_ver)
    base = tax_root / "taxonomy" / "form1" / form_ver / "schedules"
    inc_pre = base / "ScheduleStatementOfIncome" / f"sched-114_{form_ver}_pre.xml"
    cf_pre = base / "ScheduleStatementOfCashFlows" / f"sched-120_{form_ver}_pre.xml"
    bs_a_pre = (
        base
        / "ScheduleComparativeBalanceSheetAssetsAndOtherDebits"
        / f"sched-4_{form_ver}_pre.xml"
    )
    bs_l_pre = (
        base
        / "ScheduleComparativeBalanceSheetLiabilitiesOtherCredits"
        / f"sched-4_{form_ver}_pre.xml"
    )
    ctx_i = parse_context_index(root)
    dur_ok = pick_contexts(ctx_i, year=year, mode="duration_year")
    ins_ok = pick_contexts(ctx_i, year=year, mode="instant_yearend")
    facts = index_facts(root, ferc_ns)
    inc_order = parse_presentation(inc_pre, "ScheduleStatementOfIncomeAbstract")
    cf_order = parse_presentation(cf_pre, "ScheduleStatementOfCashFlowsAbstract")
    bsa_order = parse_presentation(
        bs_a_pre, "ScheduleComparativeBalanceSheetAssetsAndOtherDebitsAbstract"
    )
    bsl_order = parse_presentation(
        bs_l_pre, "ScheduleComparativeBalanceSheetLiabilitiesOtherCreditsAbstract"
    )
    return {
        "year": year,
        "xbrl_member": member,
        "form_taxonomy_version": form_ver,
        "income_statement": statement_rows(inc_order, facts, dur_ok),
        "balance_sheet_assets": statement_rows(bsa_order, facts, ins_ok),
        "balance_sheet_liabilities": statement_rows(bsl_order, facts, ins_ok),
        "cash_flows": statement_rows(cf_order, facts, dur_ok),
    }


def md_table_consolidated(
    years: list[int], rows: list[dict[str, Any]], max_rows: int = 500
) -> str:
    hdr = "| Line | " + " | ".join(f"{y} (US$ M)" for y in years) + " |"
    sep = "| --- | " + " | ".join(["---:"] * len(years)) + " |"
    lines = [hdr, sep]
    for i, r in enumerate(rows):
        if i >= max_rows:
            trunc = " | ".join(["*(truncated)*"] * len(years))
            lines.append(f"| … | {trunc} |")
            break
        pad = "&nbsp;" * (int(r["depth"]) * 2)
        lab = (pad + r["label"]).replace("|", "\\|")
        cells: list[str] = []
        by_y = r.get("by_year") or {}
        for y in years:
            raw = by_y.get(str(y))
            cells.append(fmt_millions_display(raw) if raw is not None else "")
        lines.append("| " + lab + " | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    years = payload["years"]
    lines = [
        f"# FERC Form 1 — {payload['company']}",
        "",
        "Source: [Zenodo record " + ZENODO + "](https://zenodo.org/records/" + ZENODO + ") "
        "(Catalyst **PUDL raw** FERC Form 1 XBRL). Presentation order follows the **newest** "
        "year’s taxonomy; prior-year cells match by XBRL concept. "
        + (payload.get("amount_display_note") or ""),
        "",
        "| Year | XBRL file | Taxonomy |",
        "| --- | --- | --- |",
    ]
    for m in payload["year_meta"]:
        xf = m.get("xbrl_member")
        tax = m.get("form_taxonomy_version")
        xf_cell = f"`{xf}`" if xf else "*(pending)*"
        tax_cell = f"`{tax}`" if tax else "—"
        lines.append(f"| {m['year']} | {xf_cell} | {tax_cell} |")
    lines += [
        "",
        "## Statement of operations (income)",
        "",
        md_table_consolidated(years, payload["income_statement"]),
        "",
        "## Balance sheet — assets",
        "",
        md_table_consolidated(years, payload["balance_sheet_assets"]),
        "",
        "## Balance sheet — liabilities",
        "",
        md_table_consolidated(years, payload["balance_sheet_liabilities"]),
        "",
        "## Statement of cash flows",
        "",
        md_table_consolidated(years, payload["cash_flows"]),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path) -> None:
    path.write_text(
        textwrap.dedent(
            r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>FERC Form 1 viewer</title>
<style>
:root { font-family: system-ui, sans-serif; color: #0f172a; background: #f8fafc; }
body { margin: 0; display: flex; flex-direction: column; min-height: 100vh; }
header { background: #0f172a; color: #f8fafc; padding: 0.75rem 1rem; }
header h1 { font-size: 1.1rem; margin: 0; }
header .sub { font-size: 0.78rem; opacity: 0.9; margin: 0.35rem 0 0; font-weight: normal; }
nav { display: flex; flex-wrap: wrap; gap: 0.35rem; padding: 0.5rem 1rem; background: #e2e8f0; }
nav button { border: 0; border-radius: 6px; padding: 0.35rem 0.75rem; cursor: pointer;
  background: #fff; font-size: 0.88rem; }
nav button.active { background: #2563eb; color: #fff; }
main { flex: 1; padding: 1rem; overflow: auto; }
table { border-collapse: collapse; width: 100%; background: #fff; font-size: 0.82rem; }
th, td { border: 1px solid #e2e8f0; padding: 0.35rem 0.45rem; vertical-align: top; }
th { background: #f1f5f9; text-align: left; }
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; }
.muted { color: #64748b; font-size: 0.78rem; margin: 0 0 0.5rem; }
.hidden { display: none; }
.d1{padding-left:0.6rem}.d2{padding-left:1.2rem}.d3{padding-left:1.8rem}
.d4{padding-left:2.4rem}.d5{padding-left:3rem}.d6{padding-left:3.6rem}
</style>
</head>
<body>
<header>
  <h1 id="title">FERC Form 1</h1>
  <p id="sub" class="sub"></p>
</header>
<nav id="tabs"></nav>
<main id="main"></main>
<script>
async function load() {
  const data = await (await fetch('./pge_form1_financials.json')).json();
  document.getElementById('title').textContent = 'FERC Form 1 — ' + data.company;
  document.getElementById('sub').textContent = (data.amount_display_note || '') + ' '
    + (data.year_meta || []).map(m => m.year + ': ' + (m.placeholder ? '(pending)' : m.xbrl_member)).join(' · ');
  const years = data.years;
  const tabs = document.getElementById('tabs');
  const main = document.getElementById('main');
  const panels = [
    ['income_statement', 'Statement of operations (income)'],
    ['balance_sheet_assets', 'Balance sheet — assets'],
    ['balance_sheet_liabilities', 'Balance sheet — liabilities'],
    ['cash_flows', 'Statement of cash flows']];
  let first = true;
  for (const [key, title] of panels) {
    const id = 'p_' + key;
    const b = document.createElement('button');
    b.textContent = title;
    b.dataset.panel = id;
    if (first) { b.className = 'active'; first = false; }
    tabs.appendChild(b);
    const sec = document.createElement('section');
    sec.id = id;
    sec.className = 'panel' + (b.className ? '' : ' hidden');
    if (!b.className) sec.classList.add('hidden');
    let thead = '<tr><th>Line</th>';
    for (const y of years) thead += '<th class="num">' + y + ' (US$ M)</th>';
    thead += '</tr>';
    sec.innerHTML = '<table><thead>' + thead + '</thead><tbody></tbody></table>';
    main.appendChild(sec);
    const tb = sec.querySelector('tbody');
    for (const row of data[key]) {
      const tr = document.createElement('tr');
      const d = Math.min(row.depth || 0, 6);
      const c0 = document.createElement('td');
      c0.className = 'd' + d;
      c0.textContent = row.label;
      tr.appendChild(c0);
      for (const y of years) {
        const raw = (row.by_year || {})[String(y)];
        const c = document.createElement('td');
        c.className = 'num';
        c.textContent = raw == null ? '' : fmtM(raw);
        tr.appendChild(c);
      }
      tb.appendChild(tr);
    }
  }
  tabs.addEventListener('click', e => {
    if (e.target.tagName !== 'BUTTON') return;
    tabs.querySelectorAll('button').forEach(x => x.classList.remove('active'));
    e.target.classList.add('active');
    const id = e.target.dataset.panel;
    main.querySelectorAll('.panel').forEach(p => p.classList.toggle('hidden', p.id !== id));
  });
  tabs.querySelector('button')?.click();
}
function fmtM(s) {
  const v = parseFloat(s);
  if (isNaN(v)) return String(s);
  const x = v / 1e6;
  return x.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
load().catch(e => { document.getElementById('main').innerHTML = '<p>' + e + '</p>'; });
</script>
</body>
</html>
'''
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--company", default="Portland General Electric")
    ap.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()
    out = args.out_dir or viewer_dir()
    out.mkdir(parents=True, exist_ok=True)
    tax_bundle = ensure_zip("ferc1-xbrl-taxonomies.zip")
    years_out = [export_year(y, args.company, tax_bundle) for y in sorted(set(args.years))]
    source = {
        "zenodo": f"https://zenodo.org/records/{ZENODO}",
        "pudl": "https://github.com/catalyst-cooperative/pudl",
    }
    payload = build_view_payload(args.company, source, years_out)
    (out / "pge_form1_financials.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    write_markdown(payload, out / "pge_form1_financials.md")
    write_html(out / "index.html")
    print(f"Done -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
