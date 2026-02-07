"""Parser for OncoTree JSON format"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlopen

LOG = logging.getLogger(__name__)

# OncoTree API endpoint
ONCOTREE_API_BASE = "https://oncotree.mskcc.org/api"
ONCOTREE_API_TREE = f"{ONCOTREE_API_BASE}/tumorTypes"


def download_oncotree_json(version: Optional[str] = None) -> Dict:
    """
    Download OncoTree JSON from the API.
    
    Args:
        version: Optional version string (e.g., "oncotree_2025_10_03").
                 If None, downloads the latest version.
    
    Returns:
        Dictionary containing the OncoTree tree structure
    """
    if version:
        url = f"{ONCOTREE_API_TREE}?version={version}"
    else:
        url = f"{ONCOTREE_API_TREE}"
    
    LOG.info(f"Downloading OncoTree from {url}")
    with urlopen(url) as response:
        data = json.load(response)
    LOG.info(f"Downloaded OncoTree with {len(data)} top-level nodes")
    return data


def load_oncotree_json(file_path: Path) -> Dict:
    """
    Load OncoTree JSON from a local file.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        Dictionary containing the OncoTree tree structure
    """
    LOG.info(f"Loading OncoTree from {file_path}")
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def flatten_tree(tree_data: Dict, parent_code: Optional[str] = None, 
                 all_nodes: Optional[Dict[str, Dict]] = None) -> Dict[str, Dict]:
    """
    Flatten the hierarchical OncoTree structure into a flat dictionary.
    
    Args:
        tree_data: Tree node or entire tree structure
        parent_code: Code of the parent node (None for root)
        all_nodes: Dictionary to accumulate all nodes (created if None)
    
    Returns:
        Dictionary mapping codes to node data
    """
    if all_nodes is None:
        all_nodes = {}
    
    # API returns a flat list of nodes (each with 'code', 'parent', etc.)
    if isinstance(tree_data, list):
        for node in tree_data:
            if isinstance(node, dict) and node.get("code"):
                node_data = node.copy()
                node_data["parent_code"] = node.get("parent")
                all_nodes[node["code"]] = node_data
        return all_nodes

    # Handle dict: single node or tree of nodes
    if isinstance(tree_data, dict):
        # Check if this is a single node or a tree structure
        if 'code' in tree_data:
            # Single node
            code = tree_data.get('code')
            if code:
                # Store node with parent information
                node_data = tree_data.copy()
                if parent_code:
                    node_data['parent_code'] = parent_code
                all_nodes[code] = node_data
                
                # Recursively process children
                children = tree_data.get('children', {})
                if isinstance(children, dict):
                    for child_code, child_node in children.items():
                        flatten_tree(child_node, parent_code=code, all_nodes=all_nodes)
        else:
            # Tree structure - iterate over top-level nodes
            for key, node in tree_data.items():
                if isinstance(node, dict):
                    flatten_tree(node, parent_code=parent_code, all_nodes=all_nodes)
    
    return all_nodes


def extract_mappings(node: Dict) -> List[Dict]:
    """
    Extract mappings from an OncoTree node.
    
    Args:
        node: OncoTree node dictionary
    
    Returns:
        List of mapping dictionaries with keys: source_id, target_id, target_prefix
    """
    mappings = []
    code = node.get('code')
    if not code:
        return mappings
    
    external_refs = node.get('externalReferences', {})
    
    # Extract NCIT mappings
    nci_ids = external_refs.get('NCI', [])
    for nci_id in nci_ids:
        mappings.append({
            'source_id': f'ONCOTREE:{code}',
            'target_id': f'NCIT:{nci_id}',
            'target_prefix': 'NCIT',
            'mapping_type': 'skos:exactMatch'
        })
    
    # Extract UMLS mappings
    umls_ids = external_refs.get('UMLS', [])
    for umls_id in umls_ids:
        mappings.append({
            'source_id': f'ONCOTREE:{code}',
            'target_id': f'UMLS:{umls_id}',
            'target_prefix': 'UMLS',
            'mapping_type': 'skos:exactMatch'
        })
    
    return mappings


def get_all_mappings(tree_data: Dict) -> List[Dict]:
    """
    Extract all mappings from the OncoTree structure.
    
    Args:
        tree_data: OncoTree tree structure (can be hierarchical dict or flat dict)
    
    Returns:
        List of all mappings
    """
    all_mappings = []
    
    # Flatten the tree structure
    flat_nodes = flatten_tree(tree_data)
    
    # Extract mappings from each node
    for code, node in flat_nodes.items():
        if isinstance(node, dict) and 'code' in node:
            mappings = extract_mappings(node)
            all_mappings.extend(mappings)
    
    return all_mappings


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Load OncoTree JSON from a file or a specific API version; print node/mapping counts.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file", "-f",
        type=Path,
        metavar="PATH",
        help="Path to OncoTree JSON file",
    )
    group.add_argument(
        "--version", "-v",
        type=str,
        metavar="VERSION",
        help="OncoTree version to download from API (e.g. oncotree_2025_10_03)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )

    if args.file is not None:
        data = load_oncotree_json(args.file)
    else:
        data = download_oncotree_json(version=args.version)

    flat = flatten_tree(data)
    mappings = get_all_mappings(data)
    by_prefix = {}
    for m in mappings:
        p = m["target_prefix"]
        by_prefix[p] = by_prefix.get(p, 0) + 1

    print(f"Nodes: {len(flat)}")
    print(f"Mappings: {len(mappings)} {by_prefix}")
    if mappings:
        print("Sample:", mappings[0])
