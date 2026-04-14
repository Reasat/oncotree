# Release notes

Ontology statistics and Phase 9 verification. Update **Latest verification** when you cut a release.

**Skill traceability:** Intake (Phase 1) and phases 2–9 are summarized in [`docs/plan.md`](plan.md) (tables *Phase 1 — Intake* and *Phases 2–9 — Status*).

**Reports:** `reports/metrics.json` (`robot measure -m extended`) and `reports/top-level-counts.tsv` (SPARQL under `ONCOTREE:TISSUE`). Regenerate with `just reports` after `just data2owl`.

---

## Phase 9 checklist (Mondo source-ingest)

| Check | How |
|-------|-----|
| Title and version in YAML | `scripts/verify.py --yaml oncotree.linkml.yaml` |
| Duplicate IDs, labels, parent / replacement refs | `verify.py` |
| Optional version pin | `EXPECTED_VERSION='oncotree_latest_stable (2025-10-03)' just verify` |
| LinkML validation | `uv run python -m linkml.validator.cli -s linkml/mondo_source_schema.yaml -C OntologyDocument oncotree.linkml.yaml` |
| OWL from YAML | `just data2owl`; load in ROBOT / Protégé (manual) |

**Non-OWL path:** canonical file is **`oncotree.linkml.yaml`**; **`oncotree.linkml.owl`** is linkml-owl output.

---

## Latest verification

**When:** 2026-04-14 (local `just build` + `just sssom`; artefacts gitignored).

**Upstream:** `oncotree_latest_stable (2025-10-03)` from `/api/versions`.

| Metric | Value |
|--------|------:|
| Terms in YAML | 913 |
| Unique IDs | 913 |
| Broken parent / term_replaced_by / consider refs | 0 |
| `linkml-validate` | PASS |
| `scripts/verify.py` | PASS |

**Mappings (SSSOM):** rows derived from `skos:exactMatch` on active terms (NCIT + UMLS).

**Schema:** `mondo_source_schema` v0.4.0 + OncoTree slots (`term_replaced_by`, `consider`, `rdfs_comment`).
