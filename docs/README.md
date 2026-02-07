# Documentation

## OncoTree data schema

**[oncotree_schema.json](oncotree_schema.json)** – JSON Schema for OncoTree data:

| What | Schema | Top-level type | Meaning |
|------|--------|----------------|---------|
| API | ApiResponse | array | Response is a list of nodes: `[ node1, node2, ... ]` |
| File | FileFormat | object | File is a map from root code(s) to root node(s): `{ "TISSUE": { ... } }` |

- **API response** (`ApiResponse`): `GET https://oncotree.mskcc.org/api/tumorTypes` returns a **flat list** of nodes. Each node has `code`, `parent` (code or null), `externalReferences` (e.g. `UMLS`, `NCI`), and optional `children`.
- **File format** (`FileFormat`): OncoTree JSON files (e.g. from the repo export) are a **nested tree**: one root key (e.g. `"TISSUE"`) whose value is the root node; `children` is a map of code → node, recursive.

The parser in `oncotree2obo.parsers.oncotree_json_parser` handles both shapes and flattens to a single `code → node` dict for OWL and mapping generation.
