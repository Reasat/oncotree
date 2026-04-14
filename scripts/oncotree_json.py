"""OncoTree JSON loading, flattening, and upstream /api/versions resolution."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlopen

LOG = logging.getLogger(__name__)

ONCOTREE_API_BASE = "https://oncotree.mskcc.org/api"
ONCOTREE_API_TREE = f"{ONCOTREE_API_BASE}/tumorTypes"


def fetch_versions_list() -> List[Dict[str, Any]]:
    """GET /api/versions — official api_identifier and release_date for each release."""
    url = f"{ONCOTREE_API_BASE}/versions"
    LOG.info("Fetching OncoTree versions from %s", url)
    with urlopen(url) as response:
        return json.load(response)


def resolve_version_metadata(version: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve metadata for the tumourTypes payload.

    Args:
        version: Optional api_identifier. If None, use oncotree_latest_stable.

    Raises:
        ValueError: If identifier is not found.
    """
    versions = fetch_versions_list()
    want = version if version is not None else "oncotree_latest_stable"
    for v in versions:
        if v.get("api_identifier") == want:
            return v
    raise ValueError(f"Unknown OncoTree api_identifier: {want!r}")


def download_oncotree_json(version: Optional[str] = None) -> Dict[str, Any]:
    """GET tumourTypes JSON (list or nested tree)."""
    if version:
        url = f"{ONCOTREE_API_TREE}?version={version}"
    else:
        url = ONCOTREE_API_TREE
    LOG.info("Downloading OncoTree from %s", url)
    with urlopen(url) as response:
        data = json.load(response)
    n = len(data) if hasattr(data, "__len__") else "n/a"
    LOG.info("Downloaded OncoTree (top-level len=%s)", n)
    return data


def load_oncotree_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON from a local file."""
    LOG.info("Loading OncoTree from %s", file_path)
    with open(file_path, encoding="utf-8") as fh:
        return json.load(fh)


def flatten_tree(
    tree_data: Any,
    parent_code: Optional[str] = None,
    all_nodes: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Flatten API list or nested file tree into code → node dict with parent_code."""
    if all_nodes is None:
        all_nodes = {}

    if isinstance(tree_data, list):
        for node in tree_data:
            if isinstance(node, dict) and node.get("code"):
                node_data = node.copy()
                node_data["parent_code"] = node.get("parent")
                all_nodes[node["code"]] = node_data
        return all_nodes

    if isinstance(tree_data, dict):
        if "code" in tree_data:
            code = tree_data.get("code")
            if code:
                node_data = tree_data.copy()
                if parent_code:
                    node_data["parent_code"] = parent_code
                all_nodes[code] = node_data
                children = tree_data.get("children", {})
                if isinstance(children, dict):
                    for _k, child_node in children.items():
                        if isinstance(child_node, dict):
                            flatten_tree(child_node, parent_code=code, all_nodes=all_nodes)
        else:
            for _key, node in tree_data.items():
                if isinstance(node, dict):
                    flatten_tree(node, parent_code=parent_code, all_nodes=all_nodes)

    return all_nodes
