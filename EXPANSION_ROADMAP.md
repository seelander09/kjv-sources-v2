# Corpus Expansion Roadmap

## Scope

This roadmap defines a quality-gated expansion path beyond the Pentateuch.

## Phases

### Phase 1: Historical Books

- Target: Joshua to 2 Chronicles
- Entry criteria:
  - Parser supports chapter/verse extraction with canonical references
  - Source confidence scores generated for each verse
- Exit criteria:
  - >= 95% valid canonical references
  - >= 90% schema-valid records
  - Scholar review completed for a 5% sample

### Phase 2: Wisdom Literature

- Target: Job to Song of Songs
- Additional gate:
  - Poetry-aware segmentation quality check
  - Theme consistency metrics for sampled passages

### Phase 3: Prophetic Literature

- Target: Isaiah to Malachi
- Additional gate:
  - Editorial-layer heuristic validation against benchmark annotations

### Phase 4: New Testament Comparative Layer

- Target: Matthew to Revelation
- Additional gate:
  - Cross-corpus comparative metrics validated (Torah-to-NT similarity reproducibility)

## Model Evaluation Gates

- Version each model artifact with training metadata
- Require reproducible metrics on a fixed holdout set:
  - Macro F1
  - Per-source precision/recall
  - Calibration check for confidence bins

## Scholar-in-the-Loop Review

- Annotation schema: `schemas/source_annotation.schema.json`
- Require two-pass adjudication for disputed passages
- Track provenance:
  - reviewer id
  - timestamp
  - rationale
  - confidence
