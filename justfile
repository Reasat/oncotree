# OncoTree — Mondo source-ingest (non-OWL JSON → LinkML YAML → linkml-owl)
# Prerequisites: uv (https://docs.astral.sh/uv/)
# Optional (SSSOM): robot + sssom (e.g. in obolibrary/odkfull)
# Usage: just <recipe>

SCHEMA   := "linkml/mondo_source_schema.yaml"
YAML_OUT := "oncotree.linkml.yaml"
OWL_OUT  := "oncotree.linkml.owl"
RAW_JSON := "tmp/oncotree_raw.json"
PYTHON   := "uv run python"

# Install dependencies from pyproject.toml
install:
    uv sync

# Pin linkml-owl + main-branch linkml/linkml-runtime (mondo-source-ingest comma-in-synonym workaround).
dependencies:
    uv pip install linkml-owl==0.5.0 \
        "linkml @ git+https://github.com/linkml/linkml.git@main#subdirectory=packages/linkml" \
        "linkml-runtime @ git+https://github.com/linkml/linkml.git@main#subdirectory=packages/linkml_runtime"

# Fetch official tumourTypes JSON
acquire:
    {{ PYTHON }} scripts/acquire.py --output {{ RAW_JSON }}

# JSON → LinkML YAML
extract:
    {{ PYTHON }} scripts/extract.py --input {{ RAW_JSON }} --output {{ YAML_OUT }}

# linkml-validate
validate:
    uv run python -m linkml.validator.cli -s {{ SCHEMA }} -C OntologyDocument {{ YAML_OUT }}

# Phase 9 structural checks
verify:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -n "${EXPECTED_VERSION:-}" ]; then
      uv run python scripts/verify.py --yaml "{{ YAML_OUT }}" --expected-version "$EXPECTED_VERSION"
    else
      uv run python scripts/verify.py --yaml "{{ YAML_OUT }}"
    fi

check: validate verify

# YAML → OWL (linkml-owl; for OWL-native consumers)
data2owl:
    uv run python -m linkml_owl.dumpers.owl_dumper \
        --schema {{ SCHEMA }} \
        -o {{ OWL_OUT }} \
        {{ YAML_OUT }}

# Full pipeline: acquire → extract → validate → verify → data2owl
build: acquire extract validate verify data2owl
    @echo "Build complete: {{ YAML_OUT }}, {{ OWL_OUT }}"

# Re-run extract onward (skip API download)
iterate: extract validate verify data2owl
    @echo "Iteration complete"

# ROBOT metrics + top-level descendant counts (requires `robot`; needs {{ OWL_OUT }})
reports:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p reports
    robot measure -i "{{ OWL_OUT }}" -f json -m extended -o reports/metrics.json
    robot query -i "{{ OWL_OUT }}" -q sparql/count_classes_by_top_level.sparql reports/top-level-counts.tsv
    echo "Wrote reports/metrics.json, reports/top-level-counts.tsv"

# OBOGraphs JSON → SSSOM TSV (requires robot + sssom on PATH)
sssom:
    mkdir -p tmp
    robot convert -i {{ OWL_OUT }} --format json -o tmp/oncotree_obographs.json
    uv run sssom parse tmp/oncotree_obographs.json -I obographs-json -m data/metadata.sssom.yml -o oncotree.sssom.tsv
    rm -f tmp/oncotree_obographs.json

# Release artefacts: YAML, OWL, SSSOM, reports/
release: build reports sssom
    @echo "Release artefacts: {{ YAML_OUT }}, {{ OWL_OUT }}, oncotree.sssom.tsv, reports/"

clean:
    rm -f {{ YAML_OUT }} {{ OWL_OUT }} oncotree.sssom.tsv {{ RAW_JSON }}
    rm -rf tmp/
