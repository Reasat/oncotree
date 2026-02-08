# Pipeline plan: from API to artefacts

The sequence of actions, inputs/outputs, and how entity counts change.

---

## 1. Get OncoTree data (API or file)

We get list of nodes from the API call. This is saved in an in-memory json. Code is implemented in `oncotree2obo/main.py`.

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

## Json is converted to a in-memory graph

Code is implemented in `oncotree2obo/main.py`. 


Flattening (for nested dict)
API: tree is a list of nodes. The parser walks the list and for each node sets parent_code = node["parent"] (so "parent": "PANCREAS" → parent_code = "PANCREAS").
File (nested): tree is a dict (e.g. root with children). The parser walks recursively and sets parent_code from the parent’s code.
Result for this node: same keys, plus parent_code: "PANCREAS". Fields like color, children, history, revocations, precursors are not used when building the graph.

Loop over flat list of nodes add to a RDF graph object.

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

After the graph creation, run verification makes sure the node numbers and total exactmatches are equal to json. Total exactmatched is calculated by summing `externalReferences.NCI` and `externalReferences.UMLS`.

## Run `graph.serialize()` to create `.owl` and `.ttl`


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

Code is implemented in `oncotree2obo/main.py`

## Convert OWL to obographs JSON using robot

`robot convert -i oncotree.owl -o oncotree.json`

## Parse to SSSOM TSV (sssom)

`sssom parse oncotree.json -I obographs-json -m data/metadata.sssom.yml -o oncotree.sssom.tsv` 

**Typical real-data example (API latest):** Nodes ≈ 897, # externalReferences ≈ 1358, externalReferences.NCI =  666, externalReferences.UMLS = 692.
