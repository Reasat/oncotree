"""
Verify that OncoTree JSON conversion produced OWL/TTL with the correct entity counts.

Compares expected counts (from input JSON) to actual counts (from serialized RDF).
"""
from pathlib import Path
from typing import Dict, Any, Optional

from rdflib import Graph, RDF, OWL, SKOS

from oncotree2obo.namespaces import ONCOTREE, NCIT, UMLS
from oncotree2obo.parsers.oncotree_json_parser import (
    load_oncotree_json,
    flatten_tree,
    get_all_mappings,
)


def expected_from_json(tree_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Compute expected entity counts from OncoTree JSON (same logic as main.py).

    Returns dict with: classes, mappings_ncit, mappings_umls, mappings_total.
    """
    flat_nodes = flatten_tree(tree_data)
    classes = sum(
        1
        for node in flat_nodes.values()
        if isinstance(node, dict) and node.get("code")
    )

    # Count mappings with same normalization as main (strip IDs)
    mappings = get_all_mappings(tree_data)
    ncit = sum(1 for m in mappings if m.get("target_prefix") == "NCIT")
    umls = sum(1 for m in mappings if m.get("target_prefix") == "UMLS")

    return {
        "classes": classes,
        "mappings_ncit": ncit,
        "mappings_umls": umls,
        "mappings_total": len(mappings),
    }


def actual_from_rdf(rdf_path: Path) -> Dict[str, int]:
    """
    Count entities in a serialized OWL or TTL file.

    Returns dict with: classes, mappings_ncit, mappings_umls, mappings_total.
    """
    graph = Graph()
    suffix = rdf_path.suffix.lower()
    if suffix == ".owl":
        graph.parse(source=str(rdf_path), format="xml")
    elif suffix in (".ttl", ".turtle"):
        graph.parse(source=str(rdf_path), format="turtle")
    else:
        raise ValueError(f"Unsupported format: {rdf_path.suffix}")

    oncotree_uri_prefix = str(ONCOTREE)
    ncit_uri_prefix = str(NCIT)
    umls_uri_prefix = str(UMLS)

    # OncoTree classes: (s, RDF.type, OWL.Class) with s in ONCOTREE namespace
    classes = sum(
        1
        for s in graph.subjects(RDF.type, OWL.Class)
        if str(s).startswith(oncotree_uri_prefix)
    )

    # exactMatch triples by object namespace
    mappings_ncit = 0
    mappings_umls = 0
    for s, o in graph.subject_objects(SKOS.exactMatch):
        o_str = str(o)
        if o_str.startswith(ncit_uri_prefix):
            mappings_ncit += 1
        elif o_str.startswith(umls_uri_prefix):
            mappings_umls += 1

    return {
        "classes": classes,
        "mappings_ncit": mappings_ncit,
        "mappings_umls": mappings_umls,
        "mappings_total": mappings_ncit + mappings_umls,
    }


def verify(
    json_path: Optional[Path] = None,
    rdf_path: Optional[Path] = None,
    tree_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compare expected counts (from JSON) to actual counts (from OWL/TTL).

    Provide either (json_path + rdf_path) or (tree_data + rdf_path).
    Returns dict with keys: ok (bool), expected, actual, message.
    """
    if tree_data is None:
        if json_path is None or not json_path.exists():
            return {
                "ok": False,
                "expected": None,
                "actual": None,
                "message": "json_path required and must exist when tree_data not provided",
            }
        tree_data = load_oncotree_json(json_path)

    if rdf_path is None or not rdf_path.exists():
        return {
            "ok": False,
            "expected": None,
            "actual": None,
            "message": "rdf_path required and must exist",
        }

    expected = expected_from_json(tree_data)
    actual = actual_from_rdf(rdf_path)

    diffs = []
    for key in ("classes", "mappings_ncit", "mappings_umls", "mappings_total"):
        e, a = expected[key], actual[key]
        if e != a:
            diffs.append(f"{key}: expected {e}, got {a}")

    ok = len(diffs) == 0
    message = "OK" if ok else "; ".join(diffs)

    return {
        "ok": ok,
        "expected": expected,
        "actual": actual,
        "message": message,
    }


def verify_and_raise(
    json_path: Optional[Path] = None,
    rdf_path: Optional[Path] = None,
    tree_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Run verify(); if not ok, raise AssertionError with message.
    """
    result = verify(json_path=json_path, rdf_path=rdf_path, tree_data=tree_data)
    if not result["ok"]:
        raise AssertionError(result["message"])


def _main() -> int:
    """CLI: verify OWL/TTL entity counts match expected from same source (API or JSON file)."""
    import argparse
    from oncotree2obo.config import ROOT_DIR
    from oncotree2obo.parsers.oncotree_json_parser import download_oncotree_json

    parser = argparse.ArgumentParser(
        description="Verify OncoTree OWL/TTL has correct entity counts (expected from API or JSON).",
    )
    parser.add_argument(
        "--json", "-j", type=Path, default=None,
        help="OncoTree JSON file; if omitted, expected counts come from API (same as default build).",
    )
    parser.add_argument(
        "--version", "-v", type=str, default=None,
        help="OncoTree API version when not using --json (e.g. oncotree_2025_10_03).",
    )
    parser.add_argument(
        "--owl", "-o", type=Path, default=None,
        help="OWL or TTL file (default: oncotree.owl in repo root).",
    )
    args = parser.parse_args()

    rdf_path = args.owl or (ROOT_DIR / "oncotree.owl")
    if args.json is not None:
        result = verify(json_path=args.json, rdf_path=rdf_path)
    else:
        tree_data = download_oncotree_json(version=args.version)
        result = verify(tree_data=tree_data, rdf_path=rdf_path)
    if result["ok"]:
        print("OK:", result["message"])
        print("  expected/actual:", result["expected"])
        return 0
    print("VERIFY FAILED:", result["message"])
    print("  expected:", result["expected"])
    print("  actual:", result["actual"])
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
