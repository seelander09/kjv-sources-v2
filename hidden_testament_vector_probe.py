#!/usr/bin/env python3
"""
Hidden/Lost Testament Vector Probe
=================================

Queries the third-column concepts ("Lost/Hidden Testament") across:
- scriptural_truth_complete
- kjv_genesis_verses
- kjv_exodus_verses
- kjv_leviticus_verses
- kjv_numbers_verses
- kjv_deuteronomy_verses

Returns the top 20 hits per concept with score >= 0.3 and saves a timestamped
JSON containing: score, reference/title, source attribution, and a short snippet.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
import json


console = Console()


CONCEPTS: List[str] = [
    "Of the Holy Spirit",
    "blood",
    "Jacob",
    "Elect",
    "John",
    "Elijah",
    "Hidden Manna in a golden jar",
    "Things that shall be 1,000 years (half a time)",
    "Caleb",
    "Face to face (clearly)",
]


COLLECTIONS: List[str] = [
    "scriptural_truth_complete",
    "kjv_genesis_verses",
    "kjv_exodus_verses",
    "kjv_leviticus_verses",
    "kjv_numbers_verses",
    "kjv_deuteronomy_verses",
]


def normalize_reference(payload: Dict[str, Any]) -> str:
    """Build a human-readable reference or title from mixed payload schemas."""
    title = payload.get("title") or payload.get("canonical_reference") or ""
    book = payload.get("book")
    chapter = payload.get("chapter")
    verse = payload.get("verse")

    if book and chapter is not None and verse is not None:
        return f"{book} {chapter}:{verse}"
    if title:
        return str(title)
    return ""


def get_text_field(payload: Dict[str, Any]) -> str:
    """Return a best-effort text field across payload variants."""
    return (
        payload.get("text")
        or payload.get("full_text")
        or payload.get("content")
        or ""
    )


def get_source_field(payload: Dict[str, Any]) -> str:
    """Return a best-effort source attribution field across payload variants."""
    return (
        payload.get("source")
        or payload.get("primary_source")
        or payload.get("content_type")
        or ""
    )


def main() -> None:
    console.print(
        "[bold blue]Hidden/Lost Testament Vector Probe[/bold blue]\n"
        "Querying concepts across Scriptural Truth + Torah collections\n"
    )

    client = QdrantClient(path="qdrant_data")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    results: Dict[str, List[Dict[str, Any]]] = {}
    total_steps = len(CONCEPTS) * len(COLLECTIONS)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Running vector probe...", total=total_steps)

        for concept in CONCEPTS:
            concept_hits: List[Dict[str, Any]] = []
            query_vec = model.encode([concept])[0].tolist()

            for coll in COLLECTIONS:
                try:
                    qr = client.query_points(
                        collection_name=coll,
                        query=query_vec,
                        limit=50,
                        score_threshold=0.3,
                        with_payload=True,
                    )

                    for point in qr.points:
                        payload = point.payload or {}
                        text = get_text_field(payload)
                        snippet = (
                            text[:160] + "..." if isinstance(text, str) and len(text) > 160 else text
                        )

                        concept_hits.append(
                            {
                                "concept": concept,
                                "collection": coll,
                                "score": float(point.score),
                                "reference": normalize_reference(payload),
                                "source_attribution": get_source_field(payload),
                                "snippet": snippet,
                            }
                        )
                finally:
                    # Use ASCII arrow to avoid Windows console unicode issues
                    progress.update(task, advance=1, description=f"{concept} -> {coll}")

            # Keep only top 20 by score for this concept
            concept_hits.sort(key=lambda x: x["score"], reverse=True)
            results[concept] = concept_hits[:20]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(f"hidden_testament_vector_probe_{ts}.json")
    payload = {
        "timestamp": ts,
        "query_model": "all-MiniLM-L6-v2",
        "score_threshold": 0.3,
        "top_k_per_concept": 20,
        "collections": COLLECTIONS,
        "results": results,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[bold green]✅ Saved results to {out_path}[/bold green]")


if __name__ == "__main__":
    main()


