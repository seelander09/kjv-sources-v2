"""FastAPI application exposing visualization-friendly endpoints for the KJV sources project."""

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client.models import FieldCondition, Filter, MatchValue

from kjv_sources.qdrant_client import KJVQdrantClient, create_qdrant_client

DEFAULT_SOURCES = ["J", "E", "P", "R"]
BOOK_ORDER = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
BOOK_INDEX = {book: index for index, book in enumerate(BOOK_ORDER)}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GEO_RESULTS_PATTERN = "torah_geographical_results_*.json"

SOURCE_CENTROIDS = {
    "J": {"name": "Jahwist Heartland (Judah)", "lat": 31.7767, "lon": 35.2345},
    "E": {"name": "Elohist Heartland (Ephraim)", "lat": 32.179, "lon": 35.267},
    "P": {"name": "Priestly Center (Jerusalem)", "lat": 31.7767, "lon": 35.2345},
    "R": {"name": "Redactor Perspective", "lat": 31.9, "lon": 35.3},
}

DEFAULT_LOCATION = {
    "name": "Central Canaan",
    "lat": 31.5,
    "lon": 35.2,
    "region": "Levant",
    "approximate": True,
}

LOCATION_FEATURES: List[Tuple[Tuple[str, ...], Dict[str, Any]]] = [
    (("mount sinai", "horeb", "mount horeb"), {"name": "Mount Sinai / Horeb", "lat": 28.539, "lon": 33.975, "region": "Sinai Peninsula"}),
    (("jordan river", "jordan valley"), {"name": "Jordan River", "lat": 32.45, "lon": 35.57, "region": "Jordan Valley"}),
    (("promised land", "land of promise", "land of canaan", "canaan"), {"name": "Land of Canaan", "lat": 31.8, "lon": 35.1, "region": "Levant"}),
    (("red sea", "sea of reeds"), {"name": "Red Sea", "lat": 28.0, "lon": 34.0, "region": "Sinai Peninsula"}),
    (("wilderness", "desert", "wilderness journey", "negev"), {"name": "Negev Wilderness", "lat": 30.8, "lon": 34.8, "region": "Negev"}),
    (("egypt", "pharaoh"), {"name": "Egypt", "lat": 30.0444, "lon": 31.2357, "region": "Lower Egypt"}),
    (("babylon", "babylonia"), {"name": "Babylon", "lat": 32.536, "lon": 44.420, "region": "Mesopotamia"}),
    (("jerusalem", "temple mount", "zion"), {"name": "Jerusalem / Zion", "lat": 31.7767, "lon": 35.2345, "region": "Judea"}),
    (("galilee", "sea of galilee", "tiberias"), {"name": "Galilee", "lat": 32.82, "lon": 35.53, "region": "Galilee"}),
    (("samaria", "samarian hills"), {"name": "Samaria", "lat": 32.28, "lon": 35.2, "region": "Samaria"}),
    (("judea", "judean hills"), {"name": "Judean Hills", "lat": 31.68, "lon": 35.12, "region": "Judea"}),
    (("transjordan", "beyond jordan"), {"name": "Transjordan", "lat": 32.1, "lon": 35.8, "region": "Transjordan"}),
    (("gilead",), {"name": "Gilead", "lat": 32.2, "lon": 35.8, "region": "Transjordan"}),
    (("bashan",), {"name": "Bashan", "lat": 32.8, "lon": 35.9, "region": "Golan"}),
    (("ammon",), {"name": "Ammon", "lat": 31.95, "lon": 35.93, "region": "Transjordan"}),
    (("moab",), {"name": "Moab", "lat": 31.5, "lon": 35.75, "region": "Transjordan"}),
    (("edom", "mount seir"), {"name": "Edom / Mount Seir", "lat": 30.523, "lon": 35.59, "region": "Transjordan"}),
    (("mount paran",), {"name": "Mount Paran", "lat": 29.5, "lon": 34.5, "region": "Negev"}),
    (("mount hermon",), {"name": "Mount Hermon", "lat": 33.4167, "lon": 35.85, "region": "Golan"}),
    (("mount carmel",), {"name": "Mount Carmel", "lat": 32.7, "lon": 35.04, "region": "Galilee"}),
    (("mount tabor",), {"name": "Mount Tabor", "lat": 32.69, "lon": 35.36, "region": "Lower Galilee"}),
    (("mount gerizim",), {"name": "Mount Gerizim", "lat": 32.213, "lon": 35.273, "region": "Samaria"}),
    (("mount ebal",), {"name": "Mount Ebal", "lat": 32.213, "lon": 35.275, "region": "Samaria"}),
    (("valley of jezreel", "esdraelon"), {"name": "Valley of Jezreel", "lat": 32.6, "lon": 35.3, "region": "Galilee"}),
    (("jordan valley",), {"name": "Jordan Valley", "lat": 32.2, "lon": 35.6, "region": "Jordan Valley"}),
    (("dead sea", "salt sea", "sea of arabah"), {"name": "Dead Sea", "lat": 31.3, "lon": 35.5, "region": "Jordan Valley"}),
    (("mediterranean", "great sea", "coastal plain"), {"name": "Mediterranean Coast", "lat": 32.5, "lon": 34.3, "region": "Coastal Plain"}),
    (("arabah", "araba"), {"name": "Arabah", "lat": 30.5, "lon": 35.4, "region": "Arabah"}),
    (("shephelah",), {"name": "Shephelah", "lat": 31.7, "lon": 34.9, "region": "Shephelah"}),
    (("hazor",), {"name": "Hazor", "lat": 33.03, "lon": 35.57, "region": "Upper Galilee"}),
    (("megiddo",), {"name": "Megiddo", "lat": 32.58, "lon": 35.18, "region": "Jezreel"}),
    (("bethlehem",), {"name": "Bethlehem", "lat": 31.705, "lon": 35.202, "region": "Judea"}),
    (("hebron",), {"name": "Hebron", "lat": 31.5326, "lon": 35.0998, "region": "Judea"}),
    (("beersheba", "beersheba"), {"name": "Beersheba", "lat": 31.252, "lon": 34.791, "region": "Negev"}),
    (("dan",), {"name": "Dan", "lat": 33.249, "lon": 35.693, "region": "Upper Galilee"}),
    (("euphrates", "river euphrates"), {"name": "Euphrates Frontier", "lat": 36.5, "lon": 40.0, "region": "Mesopotamia"}),
    (("brook of egypt",), {"name": "Brook of Egypt", "lat": 31.13, "lon": 33.8, "region": "Sinai Frontier"}),
]

app = FastAPI(
    title="KJV Documentary Lens API",
    version="0.1.0",
    description=(
        "Lightweight visualization API providing doublet flow data, documentary lens timelines, "
        "and geography-aware payloads for the KJV sources project."
    ),
)


ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@lru_cache(maxsize=1)
def _cached_client() -> KJVQdrantClient:
    """Create the shared Qdrant client (cached across requests)."""

    return create_qdrant_client(use_local=True)


def get_qdrant_client() -> KJVQdrantClient:
    """Return a cached Qdrant client instance or raise an HTTP error if unavailable."""

    try:
        return _cached_client()
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=503, detail=f"Qdrant client unavailable: {exc}") from exc


def _prepare_source_codes(stats: Dict[str, Any]) -> List[str]:
    """Merge default source ordering with any additional codes found in statistics."""

    base_order = list(DEFAULT_SOURCES)
    discovered = list(stats.get("source_codes", []))
    distribution_keys = list(stats.get("source_doublet_distribution", {}).keys())

    ordered: List[str] = []
    for code in base_order + discovered + distribution_keys:
        if code and code not in ordered:
            ordered.append(code)

    return ordered or list(DEFAULT_SOURCES)


def _build_transition_matrix(source_codes: List[str], links: List[Dict[str, Any]]) -> List[List[int]]:
    """Construct a square matrix representing directional counts between sources."""

    index_map = {code: idx for idx, code in enumerate(source_codes)}
    matrix = [[0 for _ in source_codes] for _ in source_codes]

    for link in links:
        src = link.get("source")
        dst = link.get("target")
        value = int(link.get("value", 0))
        if src in index_map and dst in index_map:
            matrix[index_map[src]][index_map[dst]] += value

    return matrix


def _build_chord_matrix(source_codes: List[str], links: List[Dict[str, Any]]) -> List[List[int]]:
    """Create a symmetric matrix for chord diagrams from pairwise source counts."""

    index_map = {code: idx for idx, code in enumerate(source_codes)}
    matrix = [[0 for _ in source_codes] for _ in source_codes]

    for link in links:
        src = link.get("source")
        dst = link.get("target")
        value = int(link.get("value", 0))
        if src in index_map and dst in index_map:
            i = index_map[src]
            j = index_map[dst]
            matrix[i][j] += value
            if i != j:
                matrix[j][i] += value

    return matrix


def _normalize_links(links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure link dictionaries only contain primitive JSON-friendly values."""

    normalized = []
    for link in links:
        normalized.append(
            {
                "source": link.get("source"),
                "target": link.get("target"),
                "value": int(link.get("value", 0)),
            }
        )
    return normalized


def build_doublet_flow_payload(stats: Dict[str, Any], client: KJVQdrantClient) -> Dict[str, Any]:
    """Transform raw doublet statistics into Sankey and chord friendly structures."""

    source_codes = _prepare_source_codes(stats)
    source_index = {code: idx for idx, code in enumerate(source_codes)}
    source_counts = stats.get("source_doublet_distribution", {})
    source_entities = getattr(client, "entity_relations", {}).get("source_entities", {})

    nodes: List[Dict[str, Any]] = []
    for code in source_codes:
        entity = source_entities.get(code, {})
        nodes.append(
            {
                "id": code,
                "label": entity.get("name", code),
                "description": entity.get("description", ""),
                "color": entity.get("color", ""),
                "value": int(source_counts.get(code, 0)),
            }
        )

    transitions = _normalize_links(stats.get("source_transitions", []) or [])
    chord_links = _normalize_links(stats.get("inter_source_doublets", []) or [])

    layered_transitions = []
    for layer in stats.get("source_transition_by_category", []) or []:
        layered_transitions.append(
            {
                "category": layer.get("category"),
                "links": _normalize_links(layer.get("links", []) or []),
            }
        )

    layered_chords = []
    for layer in stats.get("inter_source_doublets_by_category", []) or []:
        layered_chords.append(
            {
                "category": layer.get("category"),
                "pairs": _normalize_links(layer.get("pairs", []) or []),
            }
        )

    transition_matrix = _build_transition_matrix(source_codes, transitions)
    chord_matrix = _build_chord_matrix(source_codes, chord_links)

    categories_summary = [
        {"category": name, "value": int(count)}
        for name, count in sorted(
            (stats.get("doublet_categories", {}) or {}).items(),
            key=lambda item: (-item[1], item[0])
        )
    ]

    book_summary = [
        {"book": name, "value": int(count)}
        for name, count in sorted(
            (stats.get("doublets_by_book", {}) or {}).items(),
            key=lambda item: BOOK_INDEX.get(item[0], len(BOOK_INDEX))
        )
    ]

    return {
        "nodes": nodes,
        "sankey": {
            "links": transitions,
            "layered": layered_transitions,
            "matrix": transition_matrix,
        },
        "chord": {
            "links": chord_links,
            "layered": layered_chords,
            "matrix": chord_matrix,
        },
        "categories": categories_summary,
        "source_totals": [
            {"source": code, "value": int(source_counts.get(code, 0))}
            for code in source_codes
        ],
        "book_totals": book_summary,
        "meta": {
            "total_verses": int(stats.get("total_verses", 0)),
            "doublet_verses": int(stats.get("doublet_verses", 0)),
            "non_doublet_verses": int(stats.get("non_doublet_verses", 0)),
            "unique_doublets": int(stats.get("unique_doublet_count", 0)),
        },
        "sources": source_codes,
        "source_index": source_index,
    }


def _ensure_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _summarize_area_tags(result: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract thematic tags from a search result, normalizing to lists."""

    doublet_themes = _ensure_list(result.get("doublet_themes"))
    theological_differences = _ensure_list(result.get("theological_differences"))
    pov_themes = _ensure_list(result.get("pov_themes"))

    area_tags = sorted(set(doublet_themes) | set(theological_differences))

    return {
        "doublet_themes": doublet_themes,
        "theological_differences": theological_differences,
        "pov_themes": pov_themes,
        "area_tags": area_tags,
    }


def build_documentary_lens(results: List[Dict[str, Any]], client: KJVQdrantClient) -> Dict[str, Any]:
    """Convert hybrid doublet search results into a timeline-ready payload."""

    if not results:
        return {
            "points": [],
            "themes": [],
            "theme_series": [],
            "theme_summary": {},
            "sources": list(DEFAULT_SOURCES),
            "source_series": [],
            "source_summary": {},
            "book_distribution": [],
            "order_range": [0, 0],
        }

    points: List[Dict[str, Any]] = []
    theme_set: Set[str] = set()
    source_set: Set[str] = set()
    book_counter: defaultdict[str, int] = defaultdict(int)

    for item in results:
        book = item.get("book", "")
        chapter = int(item.get("chapter", 0) or 0)
        verse = int(item.get("verse", 0) or 0)
        score = float(item.get("score", 0.0) or 0.0)
        order = BOOK_INDEX.get(book, len(BOOK_INDEX)) * 10000 + chapter * 100 + verse

        sources = client._parse_sources_field(item.get("sources"), item.get("primary_source"))
        primary_source = item.get("primary_source") or (sources[0] if sources else "")
        source_set.update(sources)
        book_counter[book] += 1

        tags = _summarize_area_tags(item)
        theme_set.update(tags["area_tags"])

        text_value = item.get("text") or item.get("full_text", "")
        snippet = text_value[:240] + "..." if len(text_value) > 240 else text_value

        points.append(
            {
                "reference": item.get("reference") or item.get("canonical_reference") or f"{book} {chapter}:{verse}",
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "score": score,
                "order": order,
                "primary_source": primary_source,
                "sources": sources,
                "theological_differences": tags["theological_differences"],
                "doublet_themes": tags["doublet_themes"],
                "pov_themes": tags["pov_themes"],
                "area_tags": tags["area_tags"],
                "text": text_value,
                "snippet": snippet,
            }
        )

    points.sort(key=lambda entry: (entry["order"], -entry["score"]))
    for sequence, point in enumerate(points, start=1):
        point["sequence"] = sequence

    themes = sorted(theme_set)
    source_codes = _prepare_source_codes({"source_codes": list(source_set)})

    theme_counts = {theme: 0 for theme in themes}
    theme_series_map = {theme: [] for theme in themes}
    source_counts = {code: 0 for code in source_codes}
    source_series_map = {code: [] for code in source_codes}

    for point in points:
        order_value = point["order"]
        tags = set(point["area_tags"])
        point_sources = set(point["sources"])
        if point["primary_source"]:
            point_sources.add(point["primary_source"])

        for theme in themes:
            if theme in tags:
                theme_counts[theme] += 1
            theme_series_map[theme].append({"order": order_value, "value": theme_counts[theme]})

        for code in source_codes:
            if code in point_sources:
                source_counts[code] += 1
            source_series_map[code].append({"order": order_value, "value": source_counts[code]})

    theme_series = [
        {"name": theme, "values": theme_series_map[theme]}
        for theme in themes
    ]
    source_series = [
        {"name": code, "values": source_series_map[code]}
        for code in source_codes
    ]

    book_distribution = [
        {"book": book, "value": count}
        for book, count in sorted(
            book_counter.items(),
            key=lambda item: BOOK_INDEX.get(item[0], len(BOOK_INDEX))
        )
        if book
    ]

    order_range = [points[0]["order"], points[-1]["order"]] if points else [0, 0]

    return {
        "points": points,
        "themes": themes,
        "theme_series": theme_series,
        "theme_summary": theme_counts,
        "sources": source_codes,
        "source_series": source_series,
        "source_summary": source_counts,
        "book_distribution": book_distribution,
        "order_range": order_range,
    }


def load_geographical_results(limit: Optional[int] = None, filename: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[Path]]:
    """Load geographical search results from the latest JSON export (or a specified file)."""

    target_path: Optional[Path] = None
    if filename:
        candidate = PROJECT_ROOT / filename
        if candidate.exists():
            target_path = candidate
    else:
        files = sorted(
            PROJECT_ROOT.glob(GEO_RESULTS_PATTERN),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if files:
            target_path = files[0]

    if not target_path or not target_path.exists():
        return [], None

    with target_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        results = data
    elif isinstance(data, dict):
        if isinstance(data.get("results"), list):
            results = data["results"]
        elif isinstance(data.get("data"), list):
            results = data["data"]
        else:
            results = []
    else:
        results = []

    if limit is not None and limit > 0:
        results = results[:limit]

    return results, target_path


def fetch_verse_payload(client: KJVQdrantClient, reference: str) -> Optional[Dict[str, Any]]:
    """Fetch verse payload from Qdrant by canonical reference."""

    if not reference:
        return None

    try:
        records, _ = client.client.scroll(
            collection_name=client.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="canonical_reference", match=MatchValue(value=reference))]
            ),
            limit=1,
            with_payload=True,
        )
    except Exception:
        return None

    if not records:
        return None

    point = records[0]
    return getattr(point, "payload", None) or None


def identify_location(entry: Dict[str, Any], verse_payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Match a geographical result to a known location feature."""

    pattern = (entry.get("pattern") or "").lower()
    verse_text = ""
    if verse_payload:
        verse_text = str(verse_payload.get("full_text") or verse_payload.get("text") or "").lower()

    haystacks = [pattern, verse_text]

    for keywords, info in LOCATION_FEATURES:
        for keyword in keywords:
            if keyword and any(keyword in hay for hay in haystacks if hay):
                location = dict(info)
                location["matched_keyword"] = keyword
                location["approximate"] = info.get("approximate", False)
                return location

    fallback = dict(DEFAULT_LOCATION)
    fallback["matched_keyword"] = None
    return fallback


def build_geography_payload(
    entries: List[Dict[str, Any]], client: KJVQdrantClient, max_items: int
) -> Dict[str, Any]:
    """Merge geographical JSON exports with live Qdrant metadata for mapping."""

    if not entries:
        return {
            "locations": [],
            "arcs": [],
            "choropleth": [],
            "meta": {
                "total_entries": 0,
                "mapped_entries": 0,
                "unmapped_entries": 0,
                "source_totals": {},
                "theme_totals": {},
            },
        }

    source_entities = getattr(client, "entity_relations", {}).get("source_entities", {})
    location_groups: Dict[str, Dict[str, Any]] = {}
    arcs: List[Dict[str, Any]] = []

    for entry in entries[:max_items]:
        reference = entry.get("reference") or entry.get("verse_reference")
        verse_payload = fetch_verse_payload(client, reference)
        location = identify_location(entry, verse_payload)

        if "lat" not in location or "lon" not in location:
            continue

        key = location["name"]
        group = location_groups.setdefault(
            key,
            {
                "id": key.lower().replace(" ", "-"),
                "coordinates": {"lat": location["lat"], "lon": location["lon"]},
                "region": location.get("region"),
                "verses": [],
                "source_counts": {},
                "theme_counts": {},
                "score_total": 0.0,
                "score_max": 0.0,
                "approximate": location.get("approximate", False),
            },
        )

        score = float(entry.get("score") or entry.get("similarity_score") or 0.0)
        verse_sources = []
        if verse_payload:
            verse_sources = client._parse_sources_field(
                verse_payload.get("sources"),
                verse_payload.get("primary_source"),
            )
        if not verse_sources and entry.get("source"):
            verse_sources = [entry.get("source")] if entry.get("source") else []

        verse_data = {
            "reference": reference,
            "score": score,
            "pattern": entry.get("pattern"),
            "source": verse_payload.get("primary_source") if verse_payload else entry.get("source"),
            "sources": verse_sources,
            "themes": _ensure_list(verse_payload.get("doublet_themes")) if verse_payload else [],
            "theological_tags": _ensure_list(verse_payload.get("theological_differences")) if verse_payload else [],
            "pov_themes": _ensure_list(verse_payload.get("pov_themes")) if verse_payload else [],
            "text": (verse_payload.get("full_text") if verse_payload else entry.get("full_text")),
            "matched_keyword": location.get("matched_keyword"),
        }

        group["verses"].append(verse_data)
        group["score_total"] += score
        group["score_max"] = max(group["score_max"], score)

        contributing_sources = verse_sources or ([verse_data["source"]] if verse_data.get("source") else [])
        for source in contributing_sources:
            if not source:
                continue
            group["source_counts"][source] = group["source_counts"].get(source, 0) + 1

        for tag in verse_data["themes"] + verse_data["theological_tags"]:
            if not tag:
                continue
            group["theme_counts"][tag] = group["theme_counts"].get(tag, 0) + 1

        for source in contributing_sources:
            centroid = SOURCE_CENTROIDS.get(source)
            if not centroid:
                continue
            entity = source_entities.get(source, {})
            arcs.append(
                {
                    "source": source,
                    "from": {
                        "lat": centroid["lat"],
                        "lon": centroid["lon"],
                        "name": centroid["name"],
                    },
                    "to": {
                        "lat": location["lat"],
                        "lon": location["lon"],
                        "name": location["name"],
                    },
                    "weight": score,
                    "reference": reference,
                    "pattern": entry.get("pattern"),
                    "color": entity.get("color", ""),
                }
            )

    if not location_groups:
        return {
            "locations": [],
            "arcs": arcs,
            "choropleth": [],
            "meta": {
                "total_entries": len(entries),
                "mapped_entries": 0,
                "unmapped_entries": len(entries),
                "source_totals": {},
                "theme_totals": {},
            },
        }

    locations_output = []
    aggregate_source_totals: Dict[str, int] = defaultdict(int)
    aggregate_theme_totals: Dict[str, int] = defaultdict(int)

    for location_name, data in location_groups.items():
        verse_count = len(data["verses"])
        avg_score = data["score_total"] / verse_count if verse_count else 0.0
        theme_counts = [
            {"name": theme, "value": count}
            for theme, count in sorted(data["theme_counts"].items(), key=lambda item: (-item[1], item[0]))
        ]
        source_counts = [
            {"source": source, "value": count}
            for source, count in sorted(data["source_counts"].items(), key=lambda item: (-item[1], item[0]))
        ]

        for source_item in source_counts:
            aggregate_source_totals[source_item["source"]] += source_item["value"]
        for theme_item in theme_counts:
            aggregate_theme_totals[theme_item["name"]] += theme_item["value"]

        locations_output.append(
            {
                "id": data["id"],
                "name": location_name,
                "coordinates": data["coordinates"],
                "region": data["region"],
                "verses": data["verses"],
                "verse_count": verse_count,
                "score": {
                    "sum": data["score_total"],
                    "max": data["score_max"],
                    "average": avg_score,
                },
                "source_counts": source_counts,
                "theme_counts": theme_counts,
                "approximate": data.get("approximate", False),
            }
        )

    locations_output.sort(key=lambda loc: (-loc["verse_count"], -loc["score"]["average"]))

    choropleth = [
        {
            "name": loc["name"],
            "value": loc["verse_count"],
            "coordinates": loc["coordinates"],
        }
        for loc in locations_output
    ]

    mapped_entries = sum(loc["verse_count"] for loc in locations_output)
    meta = {
        "total_entries": len(entries),
        "mapped_entries": mapped_entries,
        "unique_locations": len(locations_output),
        "unmapped_entries": len(entries) - mapped_entries,
        "source_totals": dict(sorted(aggregate_source_totals.items(), key=lambda item: (-item[1], item[0]))),
        "theme_totals": dict(sorted(aggregate_theme_totals.items(), key=lambda item: (-item[1], item[0]))),
    }

    return {
        "locations": locations_output,
        "arcs": arcs,
        "choropleth": choropleth,
        "meta": meta,
    }


@app.get("/doublets/flow", tags=["doublets"])
def doublet_flow() -> Dict[str, Any]:
    """Return Sankey and chord inputs derived from doublet statistics."""

    client = get_qdrant_client()
    stats = client.get_doublet_statistics()
    if not stats:
        raise HTTPException(status_code=404, detail="Doublet statistics unavailable")

    return build_doublet_flow_payload(stats, client)


@app.get("/timeline/documentary-lens", tags=["timeline"])
def documentary_lens(
    query: str = Query(..., min_length=1, description="Query phrase to seed the hybrid doublet search"),
    category: Optional[str] = Query(None, description="Optional doublet category filter"),
    limit: int = Query(200, ge=1, le=500, description="Maximum number of matches to include in the timeline"),
) -> Dict[str, Any]:
    """Produce a timeline payload that couples verse order, sources, and theological tags."""

    client = get_qdrant_client()
    results = client.search_hybrid_doublet(query=query, category=category, limit=limit)

    payload = build_documentary_lens(results, client)
    payload.update(
        {
            "query": query,
            "category": category,
            "limit": limit,
            "total_results": len(results),
        }
    )
    return payload


@app.get("/geography/pov", tags=["geography"])
def geography_pov(
    limit: int = Query(200, ge=1, le=1000, description="Maximum number of geographical hits to merge"),
    file: Optional[str] = Query(None, description="Optional specific JSON filename under project root"),
) -> Dict[str, Any]:
    """Return merged geographical map payload combining exports and live Qdrant metadata."""

    client = get_qdrant_client()
    entries, data_path = load_geographical_results(limit=None, filename=file)
    if not entries:
        raise HTTPException(status_code=404, detail="No geographical results available")

    clipped_entries = entries[:limit] if limit else entries
    payload = build_geography_payload(clipped_entries, client, max_items=limit or len(entries))
    payload.setdefault("meta", {})
    payload["meta"]["data_file"] = data_path.name if data_path else None
    payload["meta"]["limit"] = limit
    payload["meta"]["requested_file"] = file

    return payload


def build_source_stratigraphy_data(
    client: KJVQdrantClient, book: Optional[str] = None, chapter_range: Optional[str] = None
) -> Dict[str, Any]:
    """Build source stratigraphy data for visualization."""
    try:
        all_results = client.client.scroll(
            collection_name=client.collection_name,
            limit=10000,
            with_payload=True
        )[0]
        
        # Organize by book -> chapter -> verse
        book_chapter_data: Dict[str, Dict[int, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        
        for result in all_results:
            payload = result.payload
            verse_book = payload.get("book", "")
            chapter = payload.get("chapter", 0)
            
            if book and verse_book != book:
                continue
            
            sources_list = client._parse_sources_field(
                payload.get("sources"),
                payload.get("primary_source")
            )
            
            # Calculate source percentages for this verse
            verse_text = payload.get("text", "")
            source_percentages = {}
            total_chars = len(verse_text)
            
            for source in DEFAULT_SOURCES:
                source_text_key = f"text_{source}"
                source_text = payload.get(source_text_key, "")
                if source_text and total_chars > 0:
                    source_percentages[source] = round((len(source_text) / total_chars) * 100, 2)
                else:
                    source_percentages[source] = 0.0
            
            book_chapter_data[verse_book][chapter].append({
                "verse": payload.get("verse", 0),
                "sources": sources_list,
                "source_percentages": source_percentages,
                "reference": payload.get("reference", f"{verse_book} {chapter}:{payload.get('verse', 0)}")
            })
        
        # Aggregate by chapter
        stratigraphy_data = []
        for verse_book in sorted(book_chapter_data.keys(), key=lambda x: BOOK_INDEX.get(x, 999)):
            if book and verse_book != book:
                continue
            for chapter_num in sorted(book_chapter_data[verse_book].keys()):
                verses = book_chapter_data[verse_book][chapter_num]
                # Aggregate source percentages for chapter
                chapter_source_percentages = {source: 0.0 for source in DEFAULT_SOURCES}
                total_verses = len(verses)
                
                for verse in verses:
                    for source in DEFAULT_SOURCES:
                        chapter_source_percentages[source] += verse["source_percentages"].get(source, 0.0)
                
                # Average percentages
                for source in DEFAULT_SOURCES:
                    chapter_source_percentages[source] = round(
                        chapter_source_percentages[source] / total_verses if total_verses > 0 else 0, 2
                    )
                
                stratigraphy_data.append({
                    "book": verse_book,
                    "chapter": chapter_num,
                    "source_percentages": chapter_source_percentages,
                    "verse_count": total_verses
                })
        
        return {
            "data": stratigraphy_data,
            "books": sorted(book_chapter_data.keys(), key=lambda x: BOOK_INDEX.get(x, 999)),
            "sources": DEFAULT_SOURCES,
            "meta": {
                "total_chapters": len(stratigraphy_data),
                "filter_book": book,
                "filter_chapter_range": chapter_range
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building stratigraphy data: {str(e)}")


def build_source_dominance_matrix(client: KJVQdrantClient) -> Dict[str, Any]:
    """Build source dominance matrix comparing sources across books."""
    try:
        all_results = client.client.scroll(
            collection_name=client.collection_name,
            limit=10000,
            with_payload=True
        )[0]
        
        # Aggregate by book and source
        book_source_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        book_total_verses: Dict[str, int] = defaultdict(int)
        
        for result in all_results:
            payload = result.payload
            verse_book = payload.get("book", "")
            sources_list = client._parse_sources_field(
                payload.get("sources"),
                payload.get("primary_source")
            )
            
            book_total_verses[verse_book] += 1
            for source in sources_list:
                book_source_counts[verse_book][source] += 1
        
        # Build matrix
        matrix_data = []
        for book in BOOK_ORDER:
            if book not in book_total_verses:
                continue
            total = book_total_verses[book]
            row = {"book": book}
            for source in DEFAULT_SOURCES:
                count = book_source_counts[book].get(source, 0)
                percentage = round((count / total * 100) if total > 0 else 0, 2)
                row[source] = percentage
                row[f"{source}_count"] = count
            row["total_verses"] = total
            matrix_data.append(row)
        
        return {
            "matrix": matrix_data,
            "books": BOOK_ORDER,
            "sources": DEFAULT_SOURCES,
            "meta": {
                "total_books": len(matrix_data),
                "total_verses": sum(book_total_verses.values())
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building dominance matrix: {str(e)}")


def build_doublet_heatmap_data(client: KJVQdrantClient, category: Optional[str] = None) -> Dict[str, Any]:
    """Build doublet distribution heatmap data."""
    try:
        all_results = client.client.scroll(
            collection_name=client.collection_name,
            limit=10000,
            with_payload=True
        )[0]
        
        # Organize by book -> chapter
        heatmap_data: Dict[str, Dict[int, Dict[str, Any]]] = defaultdict(lambda: defaultdict(lambda: {
            "doublet_count": 0,
            "doublets": [],
            "source_composition": defaultdict(int)
        }))
        
        for result in all_results:
            payload = result.payload
            if not payload.get("is_doublet", False):
                continue
            
            verse_book = payload.get("book", "")
            chapter = payload.get("chapter", 0)
            
            # Check category filter
            if category:
                doublet_categories = payload.get("doublet_categories", [])
                if isinstance(doublet_categories, str):
                    doublet_categories = [doublet_categories]
                if category not in doublet_categories:
                    continue
            
            sources_list = client._parse_sources_field(
                payload.get("sources"),
                payload.get("primary_source")
            )
            
            heatmap_data[verse_book][chapter]["doublet_count"] += 1
            heatmap_data[verse_book][chapter]["doublets"].append({
                "verse": payload.get("verse", 0),
                "sources": sources_list,
                "categories": payload.get("doublet_categories", []),
                "name": payload.get("doublet_names", [])
            })
            
            for source in sources_list:
                heatmap_data[verse_book][chapter]["source_composition"][source] += 1
        
        # Convert to array format
        heatmap_array = []
        for book in BOOK_ORDER:
            if book not in heatmap_data:
                continue
            for chapter_num in sorted(heatmap_data[book].keys()):
                chapter_data = heatmap_data[book][chapter_num]
                heatmap_array.append({
                    "book": book,
                    "chapter": chapter_num,
                    "doublet_count": chapter_data["doublet_count"],
                    "source_composition": dict(chapter_data["source_composition"]),
                    "doublets": chapter_data["doublets"]
                })
        
        return {
            "heatmap": heatmap_array,
            "books": BOOK_ORDER,
            "category_filter": category,
            "meta": {
                "total_chapters_with_doublets": len(heatmap_array),
                "total_doublets": sum(d["doublet_count"] for d in heatmap_array)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building doublet heatmap: {str(e)}")


@app.get("/api/v1/bird-eye/source-stratigraphy", tags=["bird-eye"])
async def get_source_stratigraphy(
    book: Optional[str] = Query(None, description="Filter by specific book"),
    chapter_range: Optional[str] = Query(None, description="Chapter range filter (e.g., '1-5')")
) -> Dict[str, Any]:
    """Get source stratigraphy data for visualization."""
    client = get_qdrant_client()
    return build_source_stratigraphy_data(client, book, chapter_range)


@app.get("/api/v1/bird-eye/source-flow-network", tags=["bird-eye"])
async def get_source_flow_network() -> Dict[str, Any]:
    """Get source flow network data (reuses doublet flow data)."""
    client = get_qdrant_client()
    stats = client.get_doublet_statistics()
    if not stats:
        raise HTTPException(status_code=404, detail="Statistics unavailable")
    return build_doublet_flow_payload(stats, client)


@app.get("/api/v1/bird-eye/doublet-heatmap", tags=["bird-eye"])
async def get_doublet_heatmap(
    category: Optional[str] = Query(None, description="Filter by doublet category")
) -> Dict[str, Any]:
    """Get doublet distribution heatmap data."""
    client = get_qdrant_client()
    return build_doublet_heatmap_data(client, category)


@app.get("/api/v1/bird-eye/source-dominance-matrix", tags=["bird-eye"])
async def get_source_dominance_matrix() -> Dict[str, Any]:
    """Get source dominance matrix comparing sources across books."""
    client = get_qdrant_client()
    return build_source_dominance_matrix(client)


@app.get("/api/v1/bird-eye/timeline", tags=["bird-eye"])
async def get_source_timeline(
    start_date: Optional[int] = Query(None, description="Start date filter (approximate BCE)"),
    end_date: Optional[int] = Query(None, description="End date filter (approximate BCE)")
) -> Dict[str, Any]:
    """Get source timeline data for evolution visualization."""
    # Note: This is a simplified version - full timeline would require historical dating
    client = get_qdrant_client()
    stratigraphy_data = build_source_stratigraphy_data(client)
    
    # Convert to timeline format (simplified - would need actual dating)
    timeline_data = []
    for item in stratigraphy_data["data"]:
        timeline_data.append({
            "book": item["book"],
            "chapter": item["chapter"],
            "source_percentages": item["source_percentages"],
            "approximate_date": None,  # Would need historical dating data
            "period": "Torah Period"  # Placeholder
        })
    
    return {
        "timeline": timeline_data,
        "sources": DEFAULT_SOURCES,
        "meta": {
            "total_entries": len(timeline_data),
            "date_range": {"start": start_date, "end": end_date}
        }
    }


@app.get("/", tags=["meta"])
def root() -> Dict[str, Any]:
    """Lightweight status endpoint for health checks."""

    try:
        client = get_qdrant_client()
        stats = client.get_collection_stats()
        collection_status = {
            "collection_name": stats.get("collection_name"),
            "total_points": stats.get("total_points"),
            "status": stats.get("status"),
        }
    except HTTPException as err:  # Fallback when Qdrant is not reachable
        collection_status = {"error": err.detail}

    return {
        "service": "kjv-documentary-lens",
        "endpoints": [
            {"path": "/doublets/flow", "description": "Layered Sankey + chord data"},
            {"path": "/timeline/documentary-lens", "description": "Documentary lens stacked timeline"},
            {"path": "/geography/pov", "description": "Geographic POV payload"},
            {"path": "/api/v1/bird-eye/source-stratigraphy", "description": "Source stratigraphy map"},
            {"path": "/api/v1/bird-eye/source-flow-network", "description": "Source flow network"},
            {"path": "/api/v1/bird-eye/doublet-heatmap", "description": "Doublet distribution heatmap"},
            {"path": "/api/v1/bird-eye/source-dominance-matrix", "description": "Source dominance matrix"},
            {"path": "/api/v1/bird-eye/timeline", "description": "Source evolution timeline"},
        ],
        "collection": collection_status,
    }

