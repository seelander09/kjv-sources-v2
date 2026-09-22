#!/usr/bin/env python3
"""Data quality checks for generated KJV source CSV artifacts."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

EXPECTED_BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
EXPECTED_TOTAL_VERSES = 5852
REQUIRED_COLUMNS = {
    "book",
    "chapter",
    "verse",
    "canonical_reference",
    "full_text",
    "sources",
    "source_count",
    "primary_source",
}
VALID_SOURCES = {"J", "E", "P", "D", "R", "UNKNOWN"}
REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9 ]+\s+\d+:\d+$")


def _validate_frame(df: pd.DataFrame, label: str) -> list[str]:
    issues: list[str] = []

    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        issues.append(f"{label}: missing required columns: {sorted(missing_cols)}")
        return issues

    if df.empty:
        issues.append(f"{label}: dataset is empty")
        return issues

    invalid_refs = df["canonical_reference"].astype(str).map(lambda value: not REFERENCE_PATTERN.match(value))
    if invalid_refs.any():
        issues.append(f"{label}: invalid canonical references: {int(invalid_refs.sum())}")

    source_series = df["sources"].fillna("").astype(str)
    invalid_source_rows = 0
    for value in source_series:
        parsed = [chunk.strip() for chunk in value.replace(",", ";").split(";") if chunk.strip()]
        if not parsed:
            invalid_source_rows += 1
            continue
        if any(source not in VALID_SOURCES for source in parsed):
            invalid_source_rows += 1
    if invalid_source_rows:
        issues.append(f"{label}: invalid source assignments: {invalid_source_rows}")

    source_count_mismatch = (
        source_series.map(lambda value: len([chunk for chunk in value.replace(",", ";").split(";") if chunk.strip()]))
        != df["source_count"].fillna(0).astype(int)
    )
    if source_count_mismatch.any():
        issues.append(f"{label}: source_count mismatch rows: {int(source_count_mismatch.sum())}")

    return issues


def main() -> int:
    root = Path(".")
    combined = root / "kjv_sources_combined.csv"
    if not combined.exists():
        print("[ERROR] Missing combined export: kjv_sources_combined.csv")
        return 1

    df = pd.read_csv(combined)
    issues = _validate_frame(df, "kjv_sources_combined.csv")

    books_present = sorted(df["book"].dropna().astype(str).unique().tolist())
    missing_books = [book for book in EXPECTED_BOOKS if book not in books_present]
    if missing_books:
        issues.append(f"Missing expected books: {missing_books}")

    total_verses = int(len(df))
    if total_verses != EXPECTED_TOTAL_VERSES:
        issues.append(f"Unexpected total verse count: {total_verses} (expected {EXPECTED_TOTAL_VERSES})")

    # Also validate per-book latest exports when available.
    for book in EXPECTED_BOOKS:
        candidate = root / "output" / book / f"{book}_latest.csv"
        if candidate.exists():
            book_df = pd.read_csv(candidate)
            issues.extend(_validate_frame(book_df, str(candidate)))

    if issues:
        print("[ERROR] Data quality checks failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("[OK] Data quality checks passed")
    print(f"  - total verses: {total_verses}")
    print(f"  - books: {', '.join(books_present)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
