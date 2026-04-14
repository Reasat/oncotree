#!/usr/bin/env python3
"""
OncoTree JSON → schema-conformant LinkML YAML (mondo_source_schema).

Input: tmp/oncotree_raw.json (from scripts/acquire.py) or any OncoTree JSON file.
Output: oncotree.linkml.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from oncotree_json import (  # noqa: E402
    flatten_tree,
    load_oncotree_json,
    resolve_version_metadata,
)

LOG = logging.getLogger(__name__)

ONC = "ONCOTREE:"

# API list responses omit some roots (e.g. TISSUE) while children still reference them as parent.
SYNTHETIC_ROOT_LABELS = {
    "TISSUE": "Tissue",
}


class QuotingDumper(yaml.SafeDumper):
    pass


def _represent_str(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    if any(c in data for c in ",:{}") or data.strip() != data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


QuotingDumper.add_representer(str, _represent_str)


def _obsolete_sets(flat_nodes: dict[str, dict[str, Any]]) -> tuple[set[str], dict[str, list[str]]]:
    obsolete_codes: set[str] = set()
    obsolete_to_replacements: dict[str, list[str]] = {}
    for code, node in flat_nodes.items():
        if not isinstance(node, dict) or "code" not in node:
            continue
        for obsolete_code in (node.get("revocations") or []) + (node.get("precursors") or []):
            if obsolete_code == code:
                continue
            obsolete_codes.add(obsolete_code)
            obsolete_to_replacements.setdefault(obsolete_code, []).append(code)
    return obsolete_codes, obsolete_to_replacements


def _validate_replacements(
    replacement_codes: list[str],
    obsolete_code: str,
    flat_nodes: dict[str, dict[str, Any]],
) -> None:
    for repl in replacement_codes:
        if repl not in flat_nodes:
            raise ValueError(
                f"Replacement code {repl!r} for obsolete {obsolete_code!r} not in node map."
            )


def extract_document(tree_data: Any, version_meta: dict[str, Any]) -> dict[str, Any]:
    flat_nodes = flatten_tree(tree_data)
    obsolete_codes, obsolete_to_replacements = _obsolete_sets(flat_nodes)
    terms: list[dict[str, Any]] = []

    for code, node in flat_nodes.items():
        if not isinstance(node, dict) or "code" not in node:
            continue
        if code in obsolete_codes:
            continue

        name = (node.get("name") or "").strip()
        parent_code = node.get("parent_code")
        main_type = node.get("mainType")
        tissue = node.get("tissue")
        level = node.get("level")
        external_refs = node.get("externalReferences") or {}

        term: dict[str, Any] = {"id": f"{ONC}{code}", "label": name}

        comments: list[str] = []
        if main_type:
            comments.append(f"Main type: {main_type}")
        if tissue:
            comments.append(f"Tissue: {tissue}")
        if level is not None:
            comments.append(f"Level: {level}")
        if comments:
            term["rdfs_comment"] = comments

        skos: list[str] = []
        for nci_id in external_refs.get("NCI", []):
            nci_id = str(nci_id).strip()
            if nci_id:
                skos.append(f"NCIT:{nci_id}")
        for umls_id in external_refs.get("UMLS", []):
            umls_id = str(umls_id).strip()
            if umls_id:
                skos.append(f"UMLS:{umls_id}")
        if skos:
            term["skos_exact_match"] = sorted(set(skos))

        if parent_code:
            term["parents"] = [f"{ONC}{parent_code}"]

        terms.append(term)

    # Parents may reference codes not present in the flat API list (see SYNTHETIC_ROOT_LABELS).
    emitted_codes = {str(t["id"]).removeprefix(ONC) for t in terms}
    missing_parent_codes: set[str] = set()
    for code, node in flat_nodes.items():
        if not isinstance(node, dict) or "code" not in node:
            continue
        if code in obsolete_codes:
            continue
        pc = node.get("parent_code")
        if pc and pc not in flat_nodes:
            missing_parent_codes.add(pc)
    for mpc in sorted(missing_parent_codes):
        if mpc in emitted_codes:
            continue
        label = SYNTHETIC_ROOT_LABELS.get(mpc, mpc.replace("_", " "))
        terms.append({"id": f"{ONC}{mpc}", "label": label})
        emitted_codes.add(mpc)

    for obsolete_code, replacement_codes in obsolete_to_replacements.items():
        _validate_replacements(replacement_codes, obsolete_code, flat_nodes)
        if obsolete_code in flat_nodes:
            obs_node = flat_nodes[obsolete_code]
            raw_name = (obs_node.get("name") or "").strip() or obsolete_code
        else:
            raw_name = obsolete_code
        term = {
            "id": f"{ONC}{obsolete_code}",
            "label": f"obsolete {raw_name}",
            "deprecated": True,
        }
        uniq = sorted(set(replacement_codes))
        if len(uniq) == 1:
            term["term_replaced_by"] = f"{ONC}{uniq[0]}"
        else:
            term["consider"] = [f"{ONC}{x}" for x in uniq]
        terms.append(term)

    terms.sort(key=lambda t: str(t["id"]))
    api_id = version_meta["api_identifier"]
    release_date = version_meta["release_date"]
    return {
        "title": "OncoTree",
        "version": f"{api_id} ({release_date})",
        "terms": terms,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="OncoTree JSON → LinkML YAML")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to OncoTree JSON (list or nested tree)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("oncotree.linkml.yaml"),
        help="Output YAML path (default: oncotree.linkml.yaml)",
    )
    parser.add_argument(
        "--version",
        "-v",
        type=str,
        default=None,
        help="api_identifier for /api/versions (optional; default latest stable)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)

    if not args.input.exists():
        print(f"FAIL: input not found: {args.input}", file=sys.stderr)
        return 1

    tree_data = load_oncotree_json(args.input)
    if args.version is None:
        version_meta = resolve_version_metadata(None)
    else:
        version_meta = resolve_version_metadata(args.version)

    doc = extract_document(tree_data, version_meta)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        yaml.dump(
            doc,
            fh,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            Dumper=QuotingDumper,
        )
    print(
        f"Wrote {args.output} ({len(doc['terms'])} terms)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
