#!/usr/bin/env python3
"""Build the Torah Source Atlas dataset from the pipeline's per-book CSVs.

Reads output/<Book>/<Book>.csv (produced by kjv_pipeline.py) and writes:
  - viz/data.json                 the compact dataset
  - injects the same JSON into viz/index.html between the kjv-data script tags
  - injects viz/doublets.json (if present) between the kjv-doublets script tags

Run from the project root:  py -3 viz/build_data.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "viz"
BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
SOURCES = ["J", "E", "P", "D", "R"]


def parse_pct(raw: str) -> dict:
    """'J:39.4;E:0.0;P:57.0;R:2.1;UNKNOWN:0.0' -> {'J': 39.4, 'P': 57.0, 'R': 2.1}"""
    out = {}
    if not isinstance(raw, str):
        return out
    for part in raw.split(";"):
        if ":" not in part:
            continue
        key, val = part.split(":", 1)
        try:
            v = float(val)
        except ValueError:
            continue
        if v > 0:
            out[key.strip()] = round(v, 1)
    return out


def main() -> int:
    books_out = []
    total_verses = 0
    unknown_hits = 0

    for book in BOOKS:
        csv_path = ROOT / "output" / book / f"{book}.csv"
        if not csv_path.exists():
            print(f"ERROR: {csv_path} missing. Run kjv_pipeline.py first.")
            return 1
        df = pd.read_csv(csv_path)
        df = df.sort_values(["chapter", "verse"])
        total_verses += len(df)

        chapters = []
        book_share: dict = {s: 0.0 for s in SOURCES}
        for chap, cdf in df.groupby("chapter", sort=True):
            verses = []
            for _, row in cdf.iterrows():
                sig = str(row["sources"]) if isinstance(row["sources"], str) else "UNKNOWN"
                pct = parse_pct(row.get("source_percentages", ""))
                if not pct:
                    # Fall back to an even split across the listed sources.
                    codes = [c for c in sig.split(";") if c]
                    uniq = list(dict.fromkeys(codes)) or ["UNKNOWN"]
                    pct = {c: round(100.0 / len(uniq), 1) for c in uniq}
                if "UNKNOWN" in pct:
                    unknown_hits += 1
                for s, v in pct.items():
                    if s in book_share:
                        book_share[s] += v / 100.0

                entry = {
                    "v": int(row["verse"]),
                    "sig": sig,
                    "pct": pct,
                    "t": str(row["full_text"]),
                }
                # For multi-source verses keep each hand's words separately.
                codes = [c for c in sig.split(";") if c]
                uniq = list(dict.fromkeys(codes))
                if len(uniq) > 1:
                    parts = []
                    for code in uniq:
                        col = f"text_{code}"
                        txt = row.get(col)
                        if isinstance(txt, str) and txt.strip():
                            parts.append([code, txt.strip()])
                    if parts:
                        entry["parts"] = parts
                verses.append(entry)
            chapters.append({"c": int(chap), "verses": verses})

        n = len(df)
        share = {s: round(100.0 * v / n, 1) for s, v in book_share.items() if v > 0}
        books_out.append(
            {"name": book, "n": n, "share": share, "chapters": chapters}
        )
        print(f"{book}: {n} verses, {len(chapters)} chapters, share {share}")

    data = {
        "meta": {
            "verses": total_verses,
            "scope": "Pentateuch (Genesis-Deuteronomy), KJV",
            "provenance": "Wikiversity color-coded Documentary Hypothesis text, parsed by kjv-sources",
        },
        "books": books_out,
    }

    out_json = VIZ / "data.json"
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out_json.write_text(payload, encoding="utf-8")
    print(f"Wrote {out_json} ({len(payload) / 1024:.0f} KB), UNKNOWN verses: {unknown_hits}")

    index = VIZ / "index.html"
    if index.exists():
        html = index.read_text(encoding="utf-8")
        safe = payload.replace("</", "<\\/")
        new_html, count = re.subn(
            r'(<script id="kjv-data" type="application/json">).*?(</script>)',
            lambda m: m.group(1) + safe + m.group(2),
            html,
            flags=re.DOTALL,
        )
        if count == 1:
            print(f"Injected data into {index}")
        else:
            print("WARNING: kjv-data script tag not found in index.html; skipped injection")

        doublets_path = VIZ / "doublets.json"
        if doublets_path.exists():
            dd = json.loads(doublets_path.read_text(encoding="utf-8"))
            dpayload = json.dumps(dd, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
            new_html, dcount = re.subn(
                r'(<script id="kjv-doublets" type="application/json">).*?(</script>)',
                lambda m: m.group(1) + dpayload + m.group(2),
                new_html,
                flags=re.DOTALL,
            )
            if dcount == 1:
                print(f"Injected {len(dd.get('doublets', []))} doublets into {index}")
            else:
                print("WARNING: kjv-doublets script tag not found in index.html; skipped injection")
        index.write_text(new_html, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
