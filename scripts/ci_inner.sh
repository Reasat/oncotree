#!/usr/bin/env bash
# Run full pipeline inside obolibrary/odkfull (or any env with python3, robot, network).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

pip3 install --break-system-packages uv
uv sync
uv pip install --break-system-packages linkml-owl==0.5.0 \
  "linkml @ git+https://github.com/linkml/linkml.git@main#subdirectory=packages/linkml" \
  "linkml-runtime @ git+https://github.com/linkml/linkml.git@main#subdirectory=packages/linkml_runtime"

uv run python scripts/acquire.py --output tmp/oncotree_raw.json
uv run python scripts/extract.py --input tmp/oncotree_raw.json --output oncotree.linkml.yaml
uv run python -m linkml.validator.cli -s linkml/mondo_source_schema.yaml -C OntologyDocument oncotree.linkml.yaml
uv run python scripts/verify.py --yaml oncotree.linkml.yaml
uv run python -m linkml_owl.dumpers.owl_dumper \
  --schema linkml/mondo_source_schema.yaml \
  -o oncotree.linkml.owl \
  oncotree.linkml.yaml

mkdir -p reports
robot measure -i oncotree.linkml.owl -f json -m extended -o reports/metrics.json
robot query -i oncotree.linkml.owl -q sparql/count_classes_by_top_level.sparql reports/top-level-counts.tsv

mkdir -p tmp
robot convert -i oncotree.linkml.owl --format json -o tmp/oncotree_obographs.json
uv run sssom parse tmp/oncotree_obographs.json -I obographs-json -m data/metadata.sssom.yml -o oncotree.sssom.tsv
rm -f tmp/oncotree_obographs.json

echo "OK: oncotree.linkml.yaml, oncotree.linkml.owl, oncotree.sssom.tsv, reports/metrics.json, reports/top-level-counts.tsv"
