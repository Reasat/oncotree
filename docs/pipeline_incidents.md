# Pipeline incidents

## 2026-04-14 — ROBOT `reports/` (QC parity)

- Added **`reports/`** with `metrics.json` (extended `robot measure`) and **`top-level-counts.tsv`** (`sparql/count_classes_by_top_level.sparql` — counts under `TISSUE`), **`just reports`**, **`scripts/ci_inner.sh`** + release asset uploads. Single OWL input (no mirror/transform/final trio).

## 2026-04-14 — Skill continuation (post–Phase 1 confirmation)

- **Phase 1** intake table in `docs/plan.md` was confirmed accurate by the maintainer.
- **Phases 2–9** status matrix added to `docs/plan.md` so the mondo-source-ingest traceability is explicit (scaffold through verify/release).

## 2026-04-14 — Full alignment with mondo-source-ingest

- **Change:** Replaced rdflib-first `oncotree2obo` with **JSON → LinkML YAML → linkml-owl** (`oncotree.linkml.yaml`, `oncotree.linkml.owl`), **`justfile`**, **`uv`**, **`scripts/verify.py`** on YAML, and **`scripts/ci_inner.sh`** for ODK Docker parity with other Mondo source repos.
- **Synthetic `TISSUE`:** The flat tumourTypes list omits a node for `TISSUE` while children use `parent: TISSUE`. The extractor adds `ONCOTREE:TISSUE` with label `Tissue` so parent references resolve (`scripts/extract.py`).
- **linkml-runtime:** Pinned via `just dependencies` / `ci_inner.sh` (main-branch `linkml` + `linkml-runtime`, `linkml-owl==0.5.0`) for the inlined-list comma workaround per mondo-source-ingest.

## linkml-owl / large OWL

If linkml-owl fails on very large outputs, document here and release YAML-only; for current OncoTree size, `data2owl` completes successfully.
