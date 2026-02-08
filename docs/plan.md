# Pipeline plan

From OncoTree source file to `oncotree.owl`, `oncotree.ttl`, `oncotree.sssom.tsv`

The sequence of actions, inputs/outputs, and how entity counts change.

---

## 1. Get OncoTree data 

Code is implemented in `oncotree2obo/main.py`.

### Through API

We get a flat list of nodes from the API call.  

```json
{
    "code": "PANET",
    "color": "Purple",
    "name": "Pancreatic Neuroendocrine Tumor",
    "mainType": "Pancreatic Cancer",
    "externalReferences": {
      "UMLS": [
        "C1337011"
      ],
      "NCI": [
        "C27720"
      ]
    },
    "tissue": "Pancreas",
    "children": {},
    "parent": "PANCREAS",
    "history": [],
    "level": 2,
    "revocations": [],
    "precursors": []
  },
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

In both cases, this is saved in an in-memory json.

## Json is converted to an in-memory graph

Code is implemented in `oncotree2obo/main.py`.

**Flattening** (handles both API and file shapes)
- **API:** tree is a list of nodes. The parser walks the list and for each node sets `parent_code = node["parent"]` (e.g. `"parent": "PANCREAS"` → `parent_code: "PANCREAS"`).
- **File (nested):** tree is a dict (e.g. root with `children`). The parser walks recursively and sets `parent_code` from the parent's code.
- **Result:** each node keeps the same keys, plus `parent_code`. Fields like `color`, `children`, `history`, `revocations`, `precursors` are not used when building the graph.

Loop over the flat dictionary of nodes (code → node) and add each to the RDF graph.

The selected fields stored are

| Input field | In OWL |
|-------------|--------|
| `code` | Class URI (e.g. `oncotree:PANET`) |
| `name` | `rdfs:label` |
| `parent` | `rdfs:subClassOf` to parent class |
| `mainType` | `rdfs:comment` "Main type: …" |
| `tissue` | `rdfs:comment` "Tissue: …" |
| `level` | `rdfs:comment` "Level: …" |
| `externalReferences.NCI` | `skos:exactMatch` to NCIT URIs |
| `externalReferences.UMLS` | `skos:exactMatch` to UMLS URIs |

**Not mapped** fields (present in JSON but not written to OWL):

| Input field | Notes |
|-------------|--------|
| `color` | UI color; not propagated |
| `children` | Used only during traversal and flattening in parser; not stored as RDF |
| `history` | Revision history; not propagated |
| `revocations` | Always empty in current data; Not propagated |
| `precursors` | Always empty in current data; not propagated |

After the graph creation, run verification to ensure the node numbers and total exactmatches are equal to json. Total exactmatched is calculated by summing `externalReferences.NCI` and `externalReferences.UMLS`.

## Run `graph.serialize()` to create `.owl` and `.ttl`

Code is implemented in `oncotree2obo/main.py`

```xml
<!-- OWL/RDF/XML example -->
  <rdf:Description rdf:about="http://purl.obolibrary.org/obo/mondo/mappings/unknown_prefix/ONCOTREE/PANET">
    <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
    <rdf:type rdf:resource="https://w3id.org/biolink/vocab/Disease"/>
    <rdfs:label>Pancreatic Neuroendocrine Tumor</rdfs:label>
    <rdfs:subClassOf rdf:resource="http://purl.obolibrary.org/obo/mondo/mappings/unknown_prefix/ONCOTREE/PANCREAS"/>
    <rdfs:comment>Main type: Pancreatic Cancer</rdfs:comment>
    <rdfs:comment>Tissue: Pancreas</rdfs:comment>
    <rdfs:comment>Level: 2</rdfs:comment>
    <skos:exactMatch rdf:resource="http://purl.obolibrary.org/obo/NCIT_C27720"/>
    <skos:exactMatch rdf:resource="http://linkedlifedata.com/resource/umls/id/C1337011"/>
  </rdf:Description>
```

```turtle
oncotree:PANET a owl:Class,
        biolink:Disease ;
    rdfs:label "Pancreatic Neuroendocrine Tumor" ;
    rdfs:comment "Level: 2",
        "Main type: Pancreatic Cancer",
        "Tissue: Pancreas" ;
    rdfs:subClassOf oncotree:PANCREAS ;
    skos:exactMatch umls:C1337011,
        ncit:C27720 .
```

## Convert OWL to obographs JSON using robot

`robot convert -i oncotree.owl -o oncotree.json`

## Parse to SSSOM TSV (sssom)

`sssom parse oncotree.json -I obographs-json -m data/metadata.sssom.yml -o oncotree.sssom.tsv` 

## Logs

During the execution of each step, print logs. In the log, note the Node counts and externalReferences counts from each of the sources.

**Typical real-data example (API, oncotree_2025_10_03):** Nodes ≈ 897, # externalReferences ≈ 1358, externalReferences.NCI =  666, externalReferences.UMLS = 692.
