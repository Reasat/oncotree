# OncoTree

OncoTree JSON (MSKCC) preprocessed into **LinkML `OntologyDocument` YAML** and **linkml-owl** OWL for Mondo ingest.

**Upstream:** https://oncotree.mskcc.org/ — API `https://oncotree.mskcc.org/api/tumorTypes`

## Setup

1. Install [uv](https://docs.astral.sh/uv/).
2. `uv sync`
3. Align LinkML pins (mondo-source-ingest workaround for inlined lists): `just dependencies`

## Run

```bash
just build    # acquire → extract → validate → verify → data2owl
just reports  # robot measure + top-level SPARQL (needs `robot`; needs oncotree.linkml.owl)
just sssom    # OBOGraphs JSON → SSSOM TSV (needs `robot` + `sssom` on PATH)
```

Full release-style run: `just release` (= `build` + `reports` + `sssom`).

Tight loop after `tmp/oncotree_raw.json` exists: `just iterate`

Inside **ODK Docker** (robot + network), same as CI:

```bash
docker run --rm -v "$PWD:/work" -w /work obolibrary/odkfull:v1.6 bash scripts/ci_inner.sh
```

## Outputs

| File | Description |
|------|-------------|
| `oncotree.linkml.yaml` | Primary artefact for Mondo ingest |
| `oncotree.linkml.owl` | OWL from linkml-owl (OWL consumers) |
| `oncotree.sssom.tsv` | SSSOM (OncoTree ↔ NCIT/UMLS via `skos:exactMatch`) |
| `reports/metrics.json` | ROBOT extended metrics on `oncotree.linkml.owl` |
| `reports/top-level-counts.tsv` | Descendant counts under grouping root(s) (see `sparql/`) |

## Docs

| Doc | Contents |
|-----|----------|
| [`docs/plan.md`](docs/plan.md) | Field mappings, ID scheme, versioning |
| [`docs/release_notes.md`](docs/release_notes.md) | Stats and Phase 9 verification |
| [`docs/pipeline_incidents.md`](docs/pipeline_incidents.md) | Incidents and resolutions |

## License

[Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).
