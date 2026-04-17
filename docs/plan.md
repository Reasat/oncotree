# Pipeline plan — OncoTree → Mondo source-ingest

## Phase 1 — Intake (mondo-source-ingest)

| # | Question | Answer |
|---|----------|--------|
| Q1 | **Source location** | Official publisher: MSKCC OncoTree API — `GET https://oncotree.mskcc.org/api/tumorTypes` (optional query `version=<api_identifier>`). Version list: `GET https://oncotree.mskcc.org/api/versions`. |
| Q2 | **Source format** | **JSON** — API returns a **flat list** of term objects; a **nested** tree object is also supported when loading from a local file. Raw snapshot: `tmp/oncotree_raw.json`. |
| Q3 | **Authentication** | **No** — public endpoints; no API keys. |
| Q4 | **Versioning** | **Yes** — `/api/versions` exposes `api_identifier` and `release_date` (e.g. `oncotree_latest_stable`, `oncotree_2025_10_03`). Default tumourTypes fetch matches latest stable; metadata in YAML uses the resolved row from `/api/versions`, not the pipeline run date. |

**Confirm before changes:** If upstream URLs, auth, or versioning behaviour change, update this table and the pipeline scripts.

**Intake confirmed:** Phase 1 table reviewed and accepted — 2026-04-14.

---

## Phases 2–9 — Status (mondo-source-ingest)

| Phase | Scope | Status |
|-------|--------|--------|
| **2 — Scaffold** | `justfile`, `linkml/`, `scripts/`, `src/oncotree/`, `pyproject.toml`, `uv.lock`, `.gitignore`, `tmp/`, `sparql/`, `reports/`, `.github/workflows/` | **Done** — non-OWL layout (no `odk.sh` / ROBOT mirror chain). |
| **3 — Schema & datamodel** | `linkml/mondo_source_schema.yaml` v0.4.0 + OncoTree slots; `gen-pydantic` → `src/oncotree/datamodel.py` | **Done** |
| **4 — Source analysis** | Labels → `rdfs:label`; no source definitions; **no** exact/related synonyms from OncoTree (skill: OncoTree has none); hierarchy via `parent` → `parents`; obsoletion via `revocations`/`precursors` + self-revocation ignored; xrefs → `skos_exact_match` (not `hasDbXref`); class IRIs `ONCOTREE:<code>` | **Recorded** — see **Field → schema slots** below |
| **5 — Scripts** | `scripts/acquire.py`, `scripts/extract.py`, `scripts/oncotree_json.py` | **Done** |
| **6 — Validate & iterate** | `just validate`, `just iterate` | **Done** |
| **7 — Derive OWL** | `just data2owl` → `oncotree.linkml.owl` | **Done** |
| **8 — CI & release** | PR: `.github/workflows/build.yml`. Release: `.github/workflows/release.yml` — `workflow_dispatch`, **weekly** cron `0 13 * * 3` (UTC), **push to `main`** on listed paths; assets include YAML, OWL, SSSOM, **`reports/metrics.json`**, **`reports/top-level-counts.tsv`** | **Done** — schedule kept for recurring upstream drops |
| **9 — Verify** | `scripts/verify.py --yaml oncotree.linkml.yaml`; results in `docs/release_notes.md` | **Done** — re-run `scripts/ci_inner.sh` in `obolibrary/odkfull:v1.6` on 2026-04-14: PASS |

---

Upstream is the **official** OncoTree API:

- `GET https://oncotree.mskcc.org/api/tumorTypes` — default = latest stable tumour types (flat JSON list).
- `GET https://oncotree.mskcc.org/api/versions` — `api_identifier` + `release_date` for ontology metadata.

No API keys.

## Artefacts

| Step | Output |
|------|--------|
| `scripts/acquire.py` | `tmp/oncotree_raw.json` |
| `scripts/extract.py` | `oncotree.linkml.yaml` (`OntologyDocument`) |
| `linkml-validate` | schema `linkml/mondo_source_schema.yaml` |
| `scripts/verify.py` | Phase 9 structural checks on YAML |
| `linkml-owl` | `oncotree.linkml.owl` |
| `robot` + `sssom` | `oncotree.sssom.tsv` |
| `robot measure` + SPARQL | `reports/metrics.json`, `reports/top-level-counts.tsv` (`just reports`) |

Primary contract for Mondo ingest: **`oncotree.linkml.yaml`**. OWL is derived for OWL-native consumers.

## JSON shapes

- **API:** array of term objects (`code`, `name`, `parent`, `mainType`, `tissue`, `level`, `externalReferences`, `revocations`, `precursors`, …).
- **File (nested):** object keyed by root codes; same fields per node; flattened in code with `parent_code`.

## Field → schema slots

| Source | Slot / predicate |
|--------|------------------|
| `code` | Class id `ONCOTREE:<code>` |
| `name` | `rdfs:label` |
| `parent` / `parent_code` | `parents` → `rdfs:subClassOf` (single parent) |
| `mainType`, `tissue`, `level` | `rdfs_comment` (multivalued strings: `Main type: …`, `Tissue: …`, `Level: …`) |
| `externalReferences.NCI` | `skos_exact_match` → `NCIT:<id>` |
| `externalReferences.UMLS` | `skos_exact_match` → `UMLS:<id>` |
| Obsolete / revoked | `owl:deprecated true`; label `obsolete <name>`; `term_replaced_by` (`IAO:0100001`) if one replacement; `consider` (`oboInOwl:consider`) if multiple |
| Self-revocation (code in own `revocations`) | Ignored when building obsolete edges |

**Obsolete terms** are not given `parents` (orphaned), per prior behaviour.

## Synthetic root `TISSUE`

The flat API list does **not** include a row for code `TISSUE`, but many nodes list `parent: TISSUE`. The extractor adds a **minimal term** `ONCOTREE:TISSUE` with label `Tissue` so all `parents` references resolve in-file (see `SYNTHETIC_ROOT_LABELS` in `scripts/extract.py`).

## Versioning

`title` = `OncoTree`. `version` in `OntologyDocument` = `{api_identifier} ({release_date})` from `/api/versions` (e.g. `oncotree_latest_stable (2025-10-03)`), not the pipeline run date.

## CI / release

- `scripts/ci_inner.sh` — full pipeline inside `obolibrary/odkfull` (robot + network).
- Local: `just build` / `just sssom` with `uv` and `robot` on PATH.

## SSSOM

- `robot convert -i oncotree.linkml.owl --format json` → OBOGraphs JSON.
- `sssom parse … -I obographs-json` → `oncotree.sssom.tsv` with `data/metadata.sssom.yml`.

## Reports (QC — mondo-source-ingest pattern)

There is a **single** release OWL (`oncotree.linkml.owl`), not mirror/transform/final triples. QC still uses ROBOT like other source repos:

| Output | Command |
|--------|---------|
| `reports/metrics.json` | `robot measure -i oncotree.linkml.owl -f json -m extended -o reports/metrics.json` |
| `reports/top-level-counts.tsv` | `robot query -i oncotree.linkml.owl -q sparql/count_classes_by_top_level.sparql reports/top-level-counts.tsv` |

`sparql/count_classes_by_top_level.sparql` currently counts descendants under **`ONCOTREE:TISSUE`** (extend `VALUES ?topLevel` if you add more grouping roots). Regenerate with **`just reports`** after **`just data2owl`** (or use **`just release`**, which runs `build` → `reports` → `sssom`).
