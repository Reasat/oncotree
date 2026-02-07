# Pipeline plan: from API to artefacts

Each command, the sequence of actions, inputs/outputs, and how entity counts change.

---

## 1. Get OncoTree data (API or file)

**Command:** `python3 -m oncotree2obo` (no args) or `python3 -m oncotree2obo --json-file PATH` or `--version VERSION`

| Item | Detail |
|------|--------|
| **Action** | Fetch tumor types from OncoTree API, or load from local JSON file. |
| **Input** | Optional: `--json-file` path, or `--version` (e.g. `oncotree_2025_10_03`). If neither: download latest from API. |
| **Output** | In-memory **tree_data**: either a **list** of nodes (API) or a **dict** with one root key and nested nodes (file). |
| **Entities** | **Nodes** = N (tumor type codes). **Mappings** = from each node’s `externalReferences.NCI` and `externalReferences.UMLS`. M_ncit, M_umls, **M_total = M_ncit + M_umls**. (Example real run: N ≈ 897, M_total ≈ 1358.) |

---

## 2. Convert to RDF (oncotree2obo)

**Command:** same as above; this is the first step inside `oncotree2obo`.

| Item | Detail |
|------|--------|
| **Action** | Flatten tree → one OWL class per node; add `rdfs:subClassOf` for parent; add `skos:exactMatch` for each NCI/UMLS id (IDs stripped). Serialize graph to TTL and OWL. |
| **Input** | **tree_data** from step 1. |
| **Output** | **oncotree.ttl**, **oncotree.owl** (same content, different format). |
| **Entities** | **Classes** = N (unchanged). **subClassOf triples** = N − 1 (one per non-root node). **exactMatch triples** = M_total (M_ncit to NCIT, M_umls to UMLS). So in the RDF we expect: N classes, M_total mapping triples. |

**Count check:** For real data, after this step we expect e.g. classes ≈ 897, mappings_total ≈ 1358 (and by prefix: NCIT ≈ 666, UMLS ≈ 692).

---

## 3. Convert OWL to obographs JSON (robot)

**Command:** `robot convert -i oncotree.owl -o oncotree.json` (Makefile: `oncotree.json` target)

| Item | Detail |
|------|--------|
| **Action** | Convert RDF/XML OWL to obographs JSON (logical content unchanged). |
| **Input** | **oncotree.owl** |
| **Output** | **oncotree.json** |
| **Entities** | Same as step 2: **nodes** = N, **edges** include hierarchy and exactMatch. **Number of nodes and mapping edges does not change**; only format changes. |

---

## 4. Parse to SSSOM TSV (sssom)

**Command:** `sssom parse oncotree.json -I obographs-json -m data/metadata.sssom.yml -o oncotree.sssom.tsv` (Makefile: `oncotree.sssom.tsv` target)

| Item | Detail |
|------|--------|
| **Action** | Extract mappings from obographs JSON and write SSSOM TSV (one row per mapping). |
| **Input** | **oncotree.json**, **data/metadata.sssom.yml** |
| **Output** | **oncotree.sssom.tsv** |
| **Entities** | **Rows** = mapping rows only = **M_total**. Class count is not represented as rows; the file has M_total data rows (plus header/comments). So **entity count in this file** = M_total (e.g. ≈ 1358). |

**Count change:** We go from “N classes + M_total mappings in OWL” to “one file with M_total mapping rows”. Class count is not in the TSV.

---

## 5. Update mappings from upstream (update-mappings)

**Command:** `python3 -m oncotree2obo.update_mappings` (Makefile: `update-mappings` target)

| Item | Detail |
|------|--------|
| **Action** | Load OncoTree data again (API or file), extract all mappings, write SSSOM TSVs into **mappings/** by target prefix. |
| **Input** | Same as step 1: API (default) or `--json-file` / `--version`. No input from oncotree.owl. |
| **Output** | **mappings/oncotree-ncit.sssom.tsv**, **mappings/oncotree-umls.sssom.tsv**, **mappings/oncotree-all.sssom.tsv** |
| **Entities** | **oncotree-ncit.sssom.tsv** rows = M_ncit. **oncotree-umls.sssom.tsv** rows = M_umls. **oncotree-all.sssom.tsv** rows = M_total. Same totals as step 1; split into files by prefix. |

---

## 6. Verify (optional)

**Command:** `python3 -m oncotree2obo.verify` or `--json PATH` or `--version VERSION` (Makefile: `verify` target, depends on `oncotree.owl`)

| Item | Detail |
|------|--------|
| **Action** | Compute expected counts from same source as build (API or JSON); load oncotree.owl (or given file); compare class count and mapping counts. |
| **Input** | **Expected:** API (default) or `--json` file or `--version`. **Actual:** **oncotree.owl** (or `--owl` path). |
| **Output** | Exit 0 + “OK” and counts, or exit 1 + “VERIFY FAILED” and expected vs actual. |
| **Entities** | Compares: **classes** (expected N vs actual N), **mappings_ncit**, **mappings_umls**, **mappings_total**. Numbers should not change between “expected from JSON/API” and “actual from OWL”. |

---

## Summary: how numbers change

| Step | Output(s) | Classes (or nodes) | Mappings (total) | M_ncit | M_umls |
|------|-----------|---------------------|-------------------|--------|--------|
| 1. API/file | tree_data (in memory) | N | M_total | M_ncit | M_umls |
| 2. oncotree2obo | oncotree.ttl, oncotree.owl | N | M_total | M_ncit | M_umls |
| 3. robot convert | oncotree.json | N | M_total | — | — |
| 4. sssom parse | oncotree.sssom.tsv | (not in file) | M_total rows | — | — |
| 5. update-mappings | mappings/*.sssom.tsv | (not in file) | M_total (all) | M_ncit (ncit file) | M_umls (umls file) |

From step 1 through 2 and 3, **N and M_total (and M_ncit, M_umls) stay the same**. Step 4 and 5 only output mapping rows (M_total or split by prefix); they do not add or remove entities relative to the source data.

**Typical real-data example (API latest):** N ≈ 897, M_total ≈ 1358, M_ncit ≈ 666, M_umls ≈ 692.
