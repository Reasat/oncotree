#!/usr/bin/env python3
"""Structural checks on produced OncoTree LinkML YAML (Phase 9)."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml


def load_doc(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify OncoTree LinkML YAML structure")
    parser.add_argument("--yaml", type=Path, required=True, help="Path to produced YAML")
    parser.add_argument(
        "--expected-version",
        type=str,
        default=None,
        help="If set, document version must equal this string",
    )
    args = parser.parse_args()

    if not args.yaml.exists():
        print(f"FAIL: file not found: {args.yaml}", file=sys.stderr)
        return 1

    doc = load_doc(args.yaml)
    title = doc.get("title")
    version = doc.get("version")
    terms = doc.get("terms") or []

    errors: list[str] = []
    if not title or not str(title).strip():
        errors.append("missing or empty title")
    if not version or not str(version).strip():
        errors.append("missing or empty version")
    if args.expected_version is not None and str(version) != args.expected_version:
        errors.append(
            f"version mismatch: expected {args.expected_version!r}, got {version!r}"
        )

    ids = [t.get("id") for t in terms]
    id_counts = Counter(ids)
    dupes = [i for i, c in id_counts.items() if c > 1 and i is not None]
    if dupes:
        errors.append(f"duplicate term IDs (sample): {dupes[:10]}")

    known = {i for i in ids if i}
    broken_refs: list[tuple[str, str, str]] = []
    missing_labels: list[str] = []

    for t in terms:
        tid = t.get("id")
        if tid is None or not str(tid).strip():
            errors.append("term with missing id")
            continue
        lab = t.get("label")
        if lab is None or not str(lab).strip():
            missing_labels.append(str(tid))
        for p in t.get("parents") or []:
            if p not in known:
                broken_refs.append((str(tid), "parent", str(p)))
        trb = t.get("term_replaced_by")
        if trb is not None and str(trb).strip():
            if trb not in known:
                broken_refs.append((str(tid), "term_replaced_by", str(trb)))
        for c in t.get("consider") or []:
            if c not in known:
                broken_refs.append((str(tid), "consider", str(c)))

    if missing_labels:
        errors.append(f"terms missing non-empty label (sample): {missing_labels[:10]}")
    if broken_refs:
        errors.append(
            f"broken refs (first 10): {broken_refs[:10]} (total {len(broken_refs)})"
        )

    term_count = len(terms)
    unique_ids = len(known)

    if errors:
        print("FAIL", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            f"Summary: terms={term_count}, unique_ids={unique_ids}",
            file=sys.stderr,
        )
        return 1

    print(
        f"PASS: terms={term_count}, unique_ids={unique_ids}, broken_refs=0",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
