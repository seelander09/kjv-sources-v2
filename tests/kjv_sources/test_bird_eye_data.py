from types import SimpleNamespace

from src.kjv_sources.api import build_doublet_heatmap_data, build_source_stratigraphy_data


class _ScrollClient:
    collection_name = "kjv_sources"

    def __init__(self):
        self.client = SimpleNamespace(scroll=self._scroll)

    @staticmethod
    def _scroll(collection_name, limit, with_payload):
        rows = [
            SimpleNamespace(
                payload={
                    "book": "Genesis",
                    "chapter": 1,
                    "verse": 1,
                    "sources": "P",
                    "primary_source": "P",
                    "is_doublet": True,
                    "doublet_categories": ["cosmogony"],
                    "doublet_names": ["Creation Stories"],
                }
            ),
            SimpleNamespace(
                payload={
                    "book": "Genesis",
                    "chapter": 2,
                    "verse": 4,
                    "sources": "J;R",
                    "primary_source": "J",
                    "is_doublet": False,
                }
            ),
        ]
        return (rows, None)

    @staticmethod
    def _parse_sources_field(sources, primary_source=None):
        if isinstance(sources, str):
            return [part.strip() for part in sources.split(";") if part.strip()]
        if sources:
            return list(sources)
        return [primary_source] if primary_source else []


def test_stratigraphy_applies_chapter_range():
    client = _ScrollClient()
    payload = build_source_stratigraphy_data(client, book="Genesis", chapter_range="1-1")
    assert payload["meta"]["chapter_range_applied"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["chapter"] == 1


def test_heatmap_contains_complexity_score():
    client = _ScrollClient()
    payload = build_doublet_heatmap_data(client)
    assert payload["heatmap"], "Expected at least one heatmap row"
    assert "complexity_score" in payload["heatmap"][0]
