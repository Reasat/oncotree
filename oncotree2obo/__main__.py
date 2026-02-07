"""Entry point for oncotree2obo module"""
import argparse
from pathlib import Path

from oncotree2obo.main import oncotree2obo

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert OncoTree JSON to OWL")
    parser.add_argument("--json-file", type=Path, default=None, help="Path to local OncoTree JSON file")
    parser.add_argument("--version", type=str, default=None, help="OncoTree version to download")
    parser.add_argument("--use-cache", action="store_true", help="Use cached data (not implemented)")
    args = parser.parse_args()
    oncotree2obo(json_file=args.json_file, version=args.version)
