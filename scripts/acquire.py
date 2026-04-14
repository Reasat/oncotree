#!/usr/bin/env python3
"""Download OncoTree tumourTypes JSON to tmp/oncotree_raw.json."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from oncotree_json import download_oncotree_json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch OncoTree JSON from the official API")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=ROOT / "tmp" / "oncotree_raw.json",
        help="Output path (default: tmp/oncotree_raw.json)",
    )
    parser.add_argument(
        "--version",
        "-v",
        type=str,
        default=None,
        help="OncoTree api_identifier (e.g. oncotree_2025_10_03); default = latest stable",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
    data = download_oncotree_json(version=args.version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
