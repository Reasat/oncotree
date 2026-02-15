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


def _obsolete_codes_from_tree(tree_data: Dict[str, Any]) -> set[str]:
    """Compute set of obsolete codes (from revocations + precursors)."""
    flat_nodes = flatten_tree(tree_data)
    obsolete = set()
    for node in flat_nodes.values():
        if isinstance(node, dict):
            code = node.get("code")
            for c in (node.get("revocations") or []) + (node.get("precursors") or []):
                # Ignore self-revocation / self-precursor
                if code and c == code:
                    continue
                obsolete.add(c)
    return obsolete


def expected_from_json(tree_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Compute expected entity counts from OncoTree JSON (same logic as main.py).

    Returns dict with:
      - classes, classes_active, classes_obsolete
      - mappings_ncit, mappings_umls, mappings_total
      - terms_with_ncit, terms_with_umls (coverage on active terms)

    Obsolete terms contribute to class count but not to mappings (obsolete terms
    do not get skos:exactMatch in the output).
    """
    flat_nodes = flatten_tree(tree_data)
    obsolete_codes = _obsolete_codes_from_tree(tree_data)

    # Total classes = all codes present in the main tree + any extra obsolete codes referenced
    # by revocations/precursors that are not present in the tree (common when using API).
    codes_in_tree = {
        node.get("code")
        for node in flat_nodes.values()
        if isinstance(node, dict) and node.get("code")
    }
    extra_obsolete = {c for c in obsolete_codes if c not in codes_in_tree}
    classes_active = len({c for c in codes_in_tree if c not in obsolete_codes})
    classes_obsolete = len(obsolete_codes)
    classes = classes_active + classes_obsolete

    # Mappings only from active nodes (obsolete terms get no skos:exactMatch)
    mappings = get_all_mappings(tree_data)
    active_mappings = [m for m in mappings if m.get("source_id", "").replace("ONCOTREE:", "") not in obsolete_codes]
    ncit = sum(1 for m in active_mappings if m.get("target_prefix") == "NCIT")
    umls = sum(1 for m in active_mappings if m.get("target_prefix") == "UMLS")

    # Coverage on active terms (unique term count, not mapping triple count)
    terms_with_ncit = 0
    terms_with_umls = 0
    for code, node in flat_nodes.items():
        if not isinstance(node, dict) or not node.get("code"):
            continue
        if code in obsolete_codes:
            continue
        ext = node.get("externalReferences") or {}
        if ext.get("NCI"):
            terms_with_ncit += 1
        if ext.get("UMLS"):
            terms_with_umls += 1

    return {
        "classes": classes,
        "classes_active": classes_active,
        "classes_obsolete": classes_obsolete,
        "mappings_ncit": ncit,
        "mappings_umls": umls,
        "mappings_total": len(active_mappings),
        "terms_with_ncit": terms_with_ncit,
        "terms_with_umls": terms_with_umls,
    }


def actual_from_graph(graph: Graph) -> Dict[str, int]:
    """
    Count entities in an in-memory RDF graph.

    Returns dict with:
      - classes, classes_active, classes_obsolete
      - mappings_ncit, mappings_umls, mappings_total
      - terms_with_ncit, terms_with_umls (coverage)
    """
    oncotree_uri_prefix = str(ONCOTREE)
    ncit_uri_prefix = str(NCIT)
    umls_uri_prefix = str(UMLS)

    classes = sum(
        1
        for s in graph.subjects(RDF.type, OWL.Class)
        if str(s).startswith(oncotree_uri_prefix)
    )
    classes_obsolete = sum(
        1
        for s in graph.subjects(RDF.type, OWL.Class)
        if str(s).startswith(oncotree_uri_prefix) and (s, OWL.deprecated, None) in graph
    )
    classes_active = classes - classes_obsolete
    mappings_ncit = 0
    mappings_umls = 0
    terms_with_ncit_set: set[str] = set()
    terms_with_umls_set: set[str] = set()
    for s, o in graph.subject_objects(SKOS.exactMatch):
        o_str = str(o)
        if o_str.startswith(ncit_uri_prefix):
            mappings_ncit += 1
            terms_with_ncit_set.add(str(s))
        elif o_str.startswith(umls_uri_prefix):
            mappings_umls += 1
            terms_with_umls_set.add(str(s))

    return {
        "classes": classes,
        "classes_active": classes_active,
        "classes_obsolete": classes_obsolete,
        "mappings_ncit": mappings_ncit,
        "mappings_umls": mappings_umls,
        "mappings_total": mappings_ncit + mappings_umls,
        "terms_with_ncit": len(terms_with_ncit_set),
        "terms_with_umls": len(terms_with_umls_set),
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
    graph = Graph()
    suffix = rdf_path.suffix.lower()
    if suffix == ".owl":
        graph.parse(source=str(rdf_path), format="xml")
    elif suffix in (".ttl", ".turtle"):
        graph.parse(source=str(rdf_path), format="turtle")
    else:
        raise ValueError(f"Unsupported format: {rdf_path.suffix}")
    actual = actual_from_graph(graph)

    diffs = []
    for key in (
        "classes",
        "classes_active",
        "classes_obsolete",
        "mappings_ncit",
        "mappings_umls",
        "mappings_total",
        "terms_with_ncit",
        "terms_with_umls",
    ):
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
    from oncotree2obo.config import ONCOTREE_OWL_PATH
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
        help="OWL or TTL file (default: mappings/oncotree.owl).",
    )
    args = parser.parse_args()

    rdf_path = args.owl or ONCOTREE_OWL_PATH
    expected_source = "API"
    if args.json is not None:
        expected_source = f"JSON file: {args.json}"
    elif args.version is not None:
        expected_source = f"API (version={args.version})"

    print("Verify inputs:")
    print(f"  expected_from: {expected_source}")
    print(f"  actual_from:   OWL/TTL file: {rdf_path}")
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
