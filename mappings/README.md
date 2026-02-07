# OncoTree Mappings

This directory contains SSSOM format mapping files for OncoTree codes to other terminologies.

## Mapping Files

- **oncotree-ncit.sssom.tsv**: Mappings from OncoTree codes to NCIT (National Cancer Institute Thesaurus)
- **oncotree-umls.sssom.tsv**: Mappings from OncoTree codes to UMLS (Unified Medical Language System)

These mappings are extracted from the `externalReferences` fields in the OncoTree JSON data.

## Usage

Mappings can be updated by running:
```bash
make update-mappings
```

Or manually by running:
```bash
python3 -m oncotree2obo.update_mappings
```
