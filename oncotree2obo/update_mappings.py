"""Update mappings from OncoTree data"""
import logging
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd

from oncotree2obo.config import MAPPINGS_DIR
from oncotree2obo.parsers.oncotree_json_parser import (
    download_oncotree_json, load_oncotree_json, get_all_mappings
)

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler(sys.stdout))


def write_sssom_mapping(mappings: List[Dict], output_path: Path, 
                       source_prefix: str = 'ONCOTREE',
                       target_prefix: str = None):
    """
    Write mappings to SSSOM format TSV file.
    
    Args:
        mappings: List of mapping dictionaries
        output_path: Path to output file
        source_prefix: Source prefix (default: ONCOTREE)
        target_prefix: Target prefix to filter by (if None, includes all)
    """
    # Filter by target prefix if specified
    if target_prefix:
        filtered = [m for m in mappings if m.get('target_prefix') == target_prefix]
    else:
        filtered = mappings
    
    if not filtered:
        LOG.warning(f"No mappings found for {target_prefix or 'all prefixes'}")
        return
    
    # Convert to DataFrame
    rows = []
    for m in filtered:
        rows.append({
            'subject_id': m['source_id'],
            'object_id': m['target_id'],
            'predicate_id': m.get('mapping_type', 'skos:exactMatch'),
            'mapping_justification': 'semapv:ManualMappingCuration',
            'author_id': 'https://orcid.org/0000-0000-0000-0000',
        })
    
    df = pd.DataFrame(rows)
    
    # Write SSSOM header
    header_lines = [
        "# SSSOM mapping file",
        f"# Source: OncoTree",
        f"# Generated from OncoTree externalReferences",
        "",
    ]
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(header_lines))
        df.to_csv(f, sep='\t', index=False)
    
    LOG.info(f"Wrote {len(df)} mappings to {output_path}")


def update_mappings(json_file: Path = None, version: str = None):
    """
    Update all mapping files from OncoTree data.
    
    Args:
        json_file: Optional path to local JSON file
        version: Optional version string for API download
    """
    LOG.info("Starting mapping update")
    
    # Load or download OncoTree data
    if json_file and json_file.exists():
        tree_data = load_oncotree_json(json_file)
    else:
        tree_data = download_oncotree_json(version)
    
    # Extract all mappings
    all_mappings = get_all_mappings(tree_data)
    LOG.info(f"Extracted {len(all_mappings)} total mappings")
    
    # Ensure mappings directory exists
    MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write NCIT mappings
    ncit_path = MAPPINGS_DIR / 'oncotree-ncit.sssom.tsv'
    write_sssom_mapping(all_mappings, ncit_path, target_prefix='NCIT')
    
    # Write UMLS mappings
    umls_path = MAPPINGS_DIR / 'oncotree-umls.sssom.tsv'
    write_sssom_mapping(all_mappings, umls_path, target_prefix='UMLS')
    
    # Write combined mappings
    combined_path = MAPPINGS_DIR / 'oncotree-all.sssom.tsv'
    write_sssom_mapping(all_mappings, combined_path)
    
    LOG.info("Mapping update complete!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Update OncoTree mappings')
    parser.add_argument('--json-file', type=Path, help='Path to local OncoTree JSON file')
    parser.add_argument('--version', type=str, help='OncoTree version to download')
    
    args = parser.parse_args()
    
    update_mappings(json_file=args.json_file, version=args.version)
