"""Configuration"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
MAPPINGS_DIR = ROOT_DIR / 'mappings'
OUTPUT_DIR = ROOT_DIR

# Output paths
ONCOTREE_OWL_PATH = OUTPUT_DIR / 'oncotree.owl'
ONCOTREE_TTL_PATH = OUTPUT_DIR / 'oncotree.ttl'

# Data paths
METADATA_SSSOM_PATH = DATA_DIR / 'metadata.sssom.yml'
