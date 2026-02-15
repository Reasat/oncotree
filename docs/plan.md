# Pipeline plan

From OncoTree source file to `mappings/oncotree.owl`, `mappings/oncotree.ttl`, `mappings/oncotree.sssom.tsv`

The sequence of actions, inputs/outputs, and how entity counts change.

**Conventions:** OncoTree class IRIs use `http://purl.obolibrary.org/obo/mondo/mappings/oncotree/<CODE>` (e.g. `.../oncotree/GNOS`).

---

## Get OncoTree data

Code is implemented in `oncotree2obo/main.py`.

OncoTree data has these two source formats

| What | Schema | Top-level type | Format |
|------|--------|----------------|---------|
| API | ApiResponse | array | Response is a list of terms: `[ term1, term2, ... ]` |
| File | FileFormat | object | File is a map from root code(s) to root term(s): `{ "TISSUE": { ... } }` |


### Through API (Preferred path)

We get a flat list of terms from the API call.  

```json
{
  "code": "GNOS",
  "color": "Gray",
  "name": "Glioma, NOS",
  "mainType": "Glioma",
  "externalReferences": {},
  "tissue": "CNS/Brain",
  "children": {},
  "parent": "DIFG",
  "history": [],
  "level": 3,
  "revocations": [
    "AOAST",
    "OAST"
  ],
  "precursors": []
}

{
  "code": "CLLSLL",
  "color": "LimeGreen",
  "name": "Chronic Lymphocytic Leukemia/Small Lymphocytic Lymphoma",
  "mainType": "Mature B-Cell Neoplasms",
  "externalReferences": {
    "UMLS": [
      "C0855095"
    ],
    "NCI": [
      "C7540"
    ]
  },
  "tissue": "Lymphoid",
  "children": {},
  "parent": "MBN",
  "history": [],
  "level": 5,
  "revocations": [],
  "precursors": [
    "CLL",
    "SLL"
  ]
}
```

### Through file

We get a nested dictionary that needs to be flattened for further processing.

```json
{
  "TISSUE": {
    "code": "TISSUE",
    "name": "Tissue",
    "externalReferences": { "UMLS": ["C0040300"], "NCI": ["C12801"] },
    "children": {
      "PANCREAS": {
        "code": "PANCREAS",
        "name": "Pancreas",
        "parent": "TISSUE",
        "externalReferences": { "UMLS": ["C0030274"], "NCI": ["C12699"] },
        "children": {}
      }
    }
  }
}
```

In both cases, this is saved in an in-memory JSON.

## JSON is converted to an in-memory graph

Code is implemented in `oncotree2obo/main.py`.

**Flattening** (handles both API and file shapes)
- **API:** tree is a list of terms. The parser walks the list and for each term sets `parent_code = term["parent"]` (e.g. `"parent": "PANCREAS"` → `parent_code: "PANCREAS"`).
- **File (nested):** tree is a dict (e.g. root with `children`). The parser walks recursively and sets `parent_code` from the parent's code.
- **Result:** each term keeps the same keys, plus `parent_code`. Fields like `color`, `children`, `history`, `revocations`, `precursors` are not used when building the graph.

**Terminology:** Active terms = items in the initial JSON. Obsolete terms = extra classes created from precursors/revocations. Total terms = active + obsolete.

Loop over the flat dictionary of terms (code → term) and add each to the RDF graph.

The selected fields stored are

| Input field | In OWL |
|-------------|--------|
| `code` | Class URI (e.g. `.../mappings/oncotree/PANET`) |
| `name` | `rdfs:label` |
| `parent` | `rdfs:subClassOf` to parent class |
| `mainType` | `rdfs:comment` "Main type: …" |
| `tissue` | `rdfs:comment` "Tissue: …" |
| `level` | `rdfs:comment` "Level: …" |
| `externalReferences.NCI` | `skos:exactMatch` to NCIT URIs |
| `externalReferences.UMLS` | `skos:exactMatch` to UMLS URIs |
| `revocations` | For each revoked code: create obsolete class with `owl:deprecated true`, label "obsolete [original name]", and `IAO:0100001` (term replaced by) → this active term. If multiple successors, use `oboInOwl:consider` instead. Obsolete terms are orphaned (no `rdfs:subClassOf`). |
| `precursors` | Inverse of revocations; used when populating `IAO:0100001` on obsolete terms. 1-to-1 → `IAO:0100001`; split (1 old → many new) → `oboInOwl:consider`; merge (many old → 1 new) → each old gets `IAO:0100001` to the replacement. |

**Not mapped** fields (present in JSON but not written to OWL):

| Input field | Notes |
|-------------|--------|
| `color` | UI color; not propagated |
| `children` | Used only during traversal and flattening in parser; not stored as RDF |
| `history` | Revision history; not propagated |

See `## Verifications` for verification timing and metrics.

## Implication of precursor and revocation:

### 1 to 1 replacement, Example: GMUCM -> URMM. Use obo:IAO_0100001
 
### Mergers (many → 1)
Example: CLL + SLL → CLLSLL, use obo:IAO_0100001
### Splits (1 → many)
Example: ALL → BLL and TLL
Both BLL and TLL list revocations: ["ALL"]. So ALL has two replacements, which is a split. The obsolete term ALL receives `oboInOwl:consider` pointing to each replacement (consider BLL, consider TLL).

## Run a second pass to get the term information for the precursors and revocations

For each precursor, revocations get the name and add them as obsolete terms. When building obsolete codes, ignore cases where a code revokes itself:

For each term code and its term, look at revocations and precursors and get their names, these are `obsolete_codes`.
For every `obsolete_code` in those lists, record the codes that are replacement for it, to create `replacement_codes` list. Figure out obo:IAO_0100001 or oboInOwl:consider based on this list.

The fields for **Obsolete term** `owl:deprecated true`, `rdfs:label` "obsolete {original name}", replacement link (IAO_0100001 or consider), no `rdfs:subClassOf` (orphaned term).

**Missing obsolete term names (implemented):** If an obsolete code is referenced by revocations/precursors but is not present in the source JSON (common with API outputs), still create the obsolete term anyway, using a minimal label derived from the code (e.g. `obsolete LEUK`). This may need revisiting if better name lookup is required.

Print how many obsolete terms were made, how many have direct replacements (obo:IAO_0100001) and how many have oboInOwl:consider 

## Run `graph.serialize()` to create `.owl` and `.ttl` in the `mappings` folder

Code is implemented in `oncotree2obo/main.py`

### owl format

```xml
<!-- OWL/RDF/XML example: Active term GNOS (revocations: AOAST, OAST) -->
  <rdf:Description rdf:about="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/GNOS">
    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
    <rdf:type rdf:resource="https://w3id.org/biolink/vocab/Disease"/>
    <rdfs:label>Glioma, NOS</rdfs:label>
    <rdfs:subClassOf rdf:resource="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/DIFG"/>
    <rdfs:comment>Main type: Glioma</rdfs:comment>
    <rdfs:comment>Tissue: CNS/Brain</rdfs:comment>
    <rdfs:comment>Level: 3</rdfs:comment>
  </rdf:Description>

  <!-- Obsolete terms (AOAST, OAST revoked and replaced by GNOS) -->
  <rdf:Description rdf:about="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/AOAST">
    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
    <rdfs:label>obsolete Anaplastic Oligoastrocytoma</rdfs:label>
    <owl:deprecated rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">true</owl:deprecated>
    <obo:IAO_0100001 rdf:resource="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/GNOS"/>
  </rdf:Description>
  <rdf:Description rdf:about="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/OAST">
    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
    <rdfs:label>obsolete Oligoastrocytoma</rdfs:label>
    <owl:deprecated rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">true</owl:deprecated>
    <obo:IAO_0100001 rdf:resource="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/GNOS"/>
  </rdf:Description>

  <!-- Active term CLLSLL (precursors: CLL, SLL merged into this term) -->
  <rdf:Description rdf:about="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/CLLSLL">
    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
    <rdf:type rdf:resource="https://w3id.org/biolink/vocab/Disease"/>
    <rdfs:label>Chronic Lymphocytic Leukemia/Small Lymphocytic Lymphoma</rdfs:label>
    <rdfs:subClassOf rdf:resource="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/MBN"/>
    <rdfs:comment>Main type: Mature B-Cell Neoplasms</rdfs:comment>
    <rdfs:comment>Tissue: Lymphoid</rdfs:comment>
    <rdfs:comment>Level: 5</rdfs:comment>
    <skos:exactMatch rdf:resource="http://purl.obolibrary.org/obo/NCIT_C7540"/>
    <skos:exactMatch rdf:resource="http://linkedlifedata.com/resource/umls/id/C0855095"/>
  </rdf:Description>

  <!-- Obsolete terms (CLL, SLL merged and replaced by CLLSLL) -->
  <rdf:Description rdf:about="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/CLL">
    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
    <rdfs:label>obsolete Chronic Lymphocytic Leukemia</rdfs:label>
    <owl:deprecated rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">true</owl:deprecated>
    <obo:IAO_0100001 rdf:resource="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/CLLSLL"/>
  </rdf:Description>
  <rdf:Description rdf:about="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/SLL">
    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
    <rdfs:label>obsolete Small Lymphocytic Lymphoma</rdfs:label>
    <owl:deprecated rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">true</owl:deprecated>
    <obo:IAO_0100001 rdf:resource="http://purl.obolibrary.org/obo/mondo/mappings/oncotree/CLLSLL"/>
  </rdf:Description>
```

### ttl format

```turtle
# Active term GNOS (revocations: AOAST, OAST)
oncotree:GNOS a owl:Class,
        biolink:Disease ;
    rdfs:label "Glioma, NOS" ;
    rdfs:comment "Level: 3",
        "Main type: Glioma",
        "Tissue: CNS/Brain" ;
    rdfs:subClassOf oncotree:DIFG .

# Obsolete terms revoked and replaced by GNOS
oncotree:AOAST a owl:Class ;
    rdfs:label "obsolete Anaplastic Oligoastrocytoma" ;
    owl:deprecated true ;
    obo:IAO_0100001 oncotree:GNOS .

oncotree:OAST a owl:Class ;
    rdfs:label "obsolete Oligoastrocytoma" ;
    owl:deprecated true ;
    obo:IAO_0100001 oncotree:GNOS .

# Active term CLLSLL (precursors: CLL, SLL merged into this)
oncotree:CLLSLL a owl:Class,
        biolink:Disease ;
    rdfs:label "Chronic Lymphocytic Leukemia/Small Lymphocytic Lymphoma" ;
    rdfs:comment "Level: 5",
        "Main type: Mature B-Cell Neoplasms",
        "Tissue: Lymphoid" ;
    rdfs:subClassOf oncotree:MBN ;
    skos:exactMatch umls:C0855095,
        ncit:C7540 .

# Obsolete terms merged and replaced by CLLSLL
oncotree:CLL a owl:Class ;
    rdfs:label "obsolete Chronic Lymphocytic Leukemia" ;
    owl:deprecated true ;
    obo:IAO_0100001 oncotree:CLLSLL .

oncotree:SLL a owl:Class ;
    rdfs:label "obsolete Small Lymphocytic Lymphoma" ;
    owl:deprecated true ;
    obo:IAO_0100001 oncotree:CLLSLL .
```

## Convert OWL to OBOGraphs JSON (`obographs-json`) using ROBOT

OBOGraphs JSON is required by `sssom parse -I obographs-json`.

Note on naming: ROBOT uses `--format json` for OBOGraphs JSON, while SSSOM uses `-I obographs-json` for the same schema.

`robot convert -i mappings/oncotree.owl --format json -o mappings/oncotree.json`

## Parse to SSSOM TSV (sssom)

`sssom parse mappings/oncotree.json -I obographs-json -m data/metadata.sssom.yml -o mappings/oncotree.sssom.tsv`

## Verifications

Verification is done at *major transforms* (especially where information can be lost: JSON → RDF, OWL → OBOGraphs JSON, OBOGraphs JSON → SSSOM).

### Verify after flattening (source JSON → flat terms)
- **Purpose:** Catch upstream shape changes early (API/file) before RDF creation.
- **Checks (minimal):**
  - Active term count (number of terms with a `code`)
  - External reference totals from JSON: total NCI IDs + total UMLS IDs (active terms only)

### Verify after RDF graph creation (flat terms → in-memory RDF graph)
- **Purpose:** Main correctness check for class creation + mapping + obsoletion logic.
- **Expected:** Counts from the same JSON used as input (API response or local JSON file).
- **Actual:** Counts from the in-memory RDF graph.
- **Checks:**
  - **Classes:** report `classes_active`, `classes_obsolete`, and `classes = classes_active + classes_obsolete`
  - **Mappings totals (B):** total `skos:exactMatch` triples to NCIT + UMLS
  - **Coverage (A):** number of **unique active terms** with ≥1 NCIT mapping; number of **unique active terms** with ≥1 UMLS mapping (each term counts once, regardless of how many IDs it has)

This verification runs during `python3 -m oncotree2obo` immediately after building the in-memory RDF graph (in `oncotree2obo/main.py`).

### Verify the serialized OWL/TTL (optional round-trip)
- **Purpose:** Ensure serialization did not change entity counts.
- **Expected:** counts from the in-memory RDF graph (same as above).
- **Actual:** parse `mappings/oncotree.owl` (or `mappings/oncotree.ttl`) and recount classes + mappings.

### Verify OBOGraphs JSON + SSSOM outputs (format + row-count sanity)
- **OBOGraphs JSON:** confirm the produced `mappings/oncotree.json` is in OBOGraphs JSON schema (not JSON-LD).
- **SSSOM TSV:** row count should match `mappings_total` (total exact matches) from the RDF graph **unless** cleaning/dedup/filtering occurs; if it does not match, log a breakdown.
- **Logging when counts don’t match:** `sssom parse` may remove mappings during cleaning (e.g. unknown prefixes). If the SSSOM row count is lower than expected, print/log a breakdown of what changed, e.g.:
  - expected `mappings_total` vs produced TSV row count
  - number dropped due to unknown prefixes / prefix cleaning
  - number dropped due to duplicate rows (if any dedup occurs)
  - number filtered by predicate (if a predicate filter is used)

If SSSOM does not emit these details by default, add a small post-step summary script (TBD) that compares expected mapping tuples from `mappings/oncotree.json` to the produced `mappings/oncotree.sssom.tsv` and prints a diff summary.

### Standalone verification command (`make verify`)
`python3 -m oncotree2obo.verify` compares:
- **Expected:** counts from API (or from `-j/--json` if a JSON file is provided)
- **Actual:** counts parsed from an on-disk OWL/TTL file (`mappings/oncotree.owl` by default, or `-o/--owl`)


## Automate the actions in a Makefile

```makefile
.PHONY: all help install verify cleanup

# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: mappings/oncotree.owl mappings/oncotree.sssom.tsv

# build: Create new mappings/oncotree.owl
# - OncoTree JSON is downloaded by the script at runtime
mappings/oncotree.owl:
	python3 -m oncotree2obo
	make cleanup

# Create mapping artefact(s)
mappings/oncotree.json: mappings/oncotree.owl
	robot convert -i $< --format json -o $@

# Create SSSOM mapping file from OWL
mappings/oncotree.sssom.tsv: mappings/oncotree.json
	sssom parse $< -I obographs-json -m data/metadata.sssom.yml -o $@
	make cleanup

cleanup:
	@rm -f mappings/oncotree.json

# SETUP / INSTALLATION -------------------------------------------------------------------------------------------------
install:
	pip install -r requirements-unlocked.txt --user --break-system-packages

# Verify mappings/oncotree.owl entity counts match API (or use: oncotree2obo.verify -j FILE)
verify: mappings/oncotree.owl
	python3 -m oncotree2obo.verify

# HELP -----------------------------------------------------------------------------------------------------------------
help:
	@echo "----------------------------------------"
	@echo "	Command reference: OncoTree"
	@echo "----------------------------------------"
	@echo "all"
	@echo "Creates all release artefacts.\n"
	@echo "mappings/oncotree.owl"
	@echo "Creates main release artefact: mappings/oncotree.owl\n"
	@echo "mappings/oncotree.sssom.tsv"
	@echo "Creates an SSSOM TSV of OncoTree terms.\n"
	@echo "install"
	@echo "Install's Python requirements.\n"
	@echo "verify"
	@echo "Verifies mappings/oncotree.owl entity counts match API (or use -j FILE for JSON).\n"
```

## Logs

During the execution of each step, print logs. In the log, note the term counts and externalReferences counts from each of the sources.

**Typical real-data example (API, oncotree_2025_10_03):** Active terms ≈ 897, # externalReferences ≈ 1358, externalReferences.NCI = 666, externalReferences.UMLS = 692.

## Edge cases (TBD)

Behavior to be defined for:
- Missing or null `parent`
- Obsolete code not in JSON and no name available (implemented as minimal-label fallback; may need revisiting if better name lookup is required).
- Self-revocation (ignore when building obsolete terms)
- Duplicate IDs in external reference arrays
- Cycles in parent hierarchy

## Data related observations
### Strange self-revocation (oncotree_2025_10_03)
```json
{
  "code": "PTCL",
  "color": "LimeGreen",
  "name": "Peripheral T-Cell lymphoma, NOS",
  "mainType": "Mature T and NK Neoplasms",
  "externalReferences": {
    "UMLS": [
      "C0079774"
    ],
    "NCI": [
      "C4340"
    ]
  },
  "tissue": "Lymphoid",
  "children": {},
  "parent": "MTNN",
  "history": [
    "PTCLNOS"
  ],
  "level": 5,
  "revocations": [
    "PTCL"
  ],
  "precursors": []
}
```
### Google AI explanation
Self-revocation is when a code appears in its own revocations list (e.g. PTCL revokes PTCL). It indicates a change in definition or hierarchy while the code string stays the same.
Why it happens 
The old PTCL was broader; the new PTCL is narrower.
The code is reused, but the old meaning is marked revoked.
The history field (e.g. PTCLNOS) reflects the previous identifier.
What it’s for
The OncoTree Mapping Tool uses it to mark ambiguous mappings.
Legacy PTCL samples are flagged so users can decide whether they map to the current PTCL or another Mature T/NK neoplasm.
How to represent it in OWL
Do not use IAO_0100001. When building obsolete codes, ignore cases where a code revokes itself

### No self-precursor found (oncotree_2025_10_03)