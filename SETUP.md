# Setup Guide for OncoTree-Mondo Repository

This guide explains how to set up and use the OncoTree-Mondo repository, which converts OncoTree JSON data into OWL format for ingestion into Mondo.

## Repository Structure

```
oncotree-mondo/
├── .github/
│   └── workflows/
│       └── build_and_release.yml    # Automated build and release workflow
├── data/
│   └── metadata.sssom.yml           # SSSOM metadata configuration
├── mappings/                         # Generated mapping files (SSSOM format)
│   └── README.md
├── oncotree2obo/                     # Main Python package
│   ├── __init__.py
│   ├── __main__.py                   # Entry point
│   ├── config.py                     # Configuration paths
│   ├── main.py                       # Core conversion logic
│   ├── namespaces.py                 # RDF namespace definitions
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── oncotree_json_parser.py   # OncoTree JSON parser
├── .gitignore
├── LICENSE.md
├── makefile                          # Build automation
├── README.md                         # Main documentation
└── requirements-unlocked.txt       # Python dependencies
```

## Quick Start

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Build OncoTree OWL file:**
   ```bash
   make all
   ```
   This will:
   - Download OncoTree JSON from the API
   - Convert it to `mappings/oncotree.owl`
   - Generate `mappings/oncotree.sssom.tsv`

## Key Features

### 1. Dynamic OncoTree Download
The repository can download OncoTree data directly from the API:
- Latest version: `python3 -m oncotree2obo`
- Specific version: `python3 -m oncotree2obo --version oncotree_2025_10_03`
- Local file: `python3 -m oncotree2obo --json-file path/to/oncotree.json`

### 2. OWL Generation
Converts OncoTree JSON to OWL ontology with:
- OWL classes for each OncoTree code
- `rdfs:subClassOf` relationships for parent-child hierarchy
- `skos:exactMatch` mappings to NCIT and UMLS
- Proper ontology metadata

### 3. Mapping Extraction
Extracts mappings from OncoTree's `externalReferences` into the release artefacts.

## Integration with Mondo

This repository follows the same pattern as the OMIM ingest repository:

1. **Input**: OncoTree JSON (from API or file)
2. **Processing**: Convert to OWL format
3. **Output**: 
   - `mappings/oncotree.owl` - OWL ontology file
   - `mappings/oncotree.sssom.tsv` - SSSOM mapping file

The `mappings/oncotree.owl` file can be ingested by `mondo-ingest` along with the mapping files to create MONDO mappings.

## Next Steps

1. **Test the conversion:**
   ```bash
   make all
   ```

2. **Review generated files:**
   - Check `mappings/oncotree.owl` for proper OWL structure
   - Verify `mappings/oncotree.sssom.tsv` contains expected mappings
   - Review `mappings/` directory for extracted mappings

3. **Create GitHub repository:**
   - Initialize git: `git init`
   - Create repo on GitHub in your namespace
   - Push code: `git push origin main`

4. **Share with Monarch:**
   - Once working, share the repo with Nico Matentzoglu
   - They can review and potentially transfer to `monarch-initiative/oncotree`

## Notes

- The OncoTree API is available at: https://oncotree.mskcc.org/api
- OncoTree codes map to NCIT via `externalReferences.NCI`
- NCIT codes can then be mapped to MONDO via `mondo.sssom.tsv` (in mondo-ingest)
- This creates the chain: OncoTree → NCIT → MONDO
