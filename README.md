# OncoTree Ingest

## About OncoTree & this repository

OncoTree is an open-source ontology developed at [Memorial Sloan Kettering Cancer Center](https://www.mskcc.org/) for standardizing cancer type diagnosis from a clinical perspective by assigning each diagnosis a unique OncoTree code.

The purpose of this repository is for data transformations for ingest into Mondo. Mainly, it is for generating an `oncotree.owl` and other release artefacts.

**Homepage:** https://oncotree.mskcc.org/

**Official Repository:** https://github.com/cBioPortal/oncotree

Disclaimer: This repository and its created data artefacts are unofficial. For official, up-to-date OncoTree data, please visit [oncotree.mskcc.org](https://oncotree.mskcc.org).

## Setup

### 1. Python dependencies

#### Python installation
- [RealPython blog install guide](https://realpython.com/installing-python/): Guide for installing on Windows or Mac
- [Python documentation for installing on Windows](https://docs.python.org/3/using/windows.html)
- [Python documentation for installing on Mac](https://docs.python.org/3/using/mac.html)

#### Setup virtual environment & installing packages
1. Run: `make install`
2. This will install all required Python dependencies

## Running & creating release

Run: `make all`

Running this will create new release artefacts in the root directory:
- `oncotree.owl`: OncoTree ontologized in OWL format
- `oncotree.sssom.tsv`: SSSOM mapping file
- `mappings/`: Folder containing SSSOM format mappings (e.g., OncoTree → NCIT, OncoTree → MONDO)

You can also run individual targets:
- `make oncotree.owl`: Downloads OncoTree JSON and generates OWL file
- `make oncotree.sssom.tsv`: Generates SSSOM mapping file from OWL
- `make update-mappings`: Updates mappings from upstream sources

## Mappings

The `mappings/` folder contains SSSOM format mappings that can be found between OncoTree codes and other terminologies:
- **NCIT mappings**: Extracted from OncoTree's `externalReferences.NCI` fields
- **UMLS mappings**: Extracted from OncoTree's `externalReferences.UMLS` fields
- **MONDO mappings**: Created through NCIT mappings (OncoTree → NCIT → MONDO via mondo.sssom.tsv)

## Release files

- `oncotree.owl`: OncoTree ontologized in OWL format
- `oncotree.sssom.tsv`: SSSOM mapping file
- `mappings/`: Directory containing additional SSSOM mapping files

Notice: These are generated based on the latest downloadable data files from the OncoTree API, updated regularly.

## Architecture

### Core Processing Flow

1. **Data Download**: Retrieves OncoTree JSON from the official API
2. **Parsing**: Transforms JSON tree structure into RDF graph
3. **Mapping Extraction**: Extracts external references (NCIT, UMLS) as mappings
4. **Output Generation**: Creates OWL files and SSSOM mapping files

### Key Modules

**`oncotree2obo/main.py`**: Core processing logic
- Entry point for all data transformation
- Converts OncoTree JSON tree structure to OWL ontology
- Extracts and manages mappings

**`oncotree2obo/parsers/`**: Parsers for OncoTree data formats
- `oncotree_json_parser.py`: Handles OncoTree JSON tree structure

## Documentation

- **[docs/oncotree_schema.json](docs/oncotree_schema.json)** – JSON Schema for OncoTree API response (flat list) and file format (nested tree). See [docs/README.md](docs/README.md).

## License

This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).
