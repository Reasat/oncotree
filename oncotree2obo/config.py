"""Configuration"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
MAPPINGS_DIR = ROOT_DIR / 'mappings'

# Output paths
ONCOTREE_OWL_PATH = MAPPINGS_DIR / 'oncotree.owl'
ONCOTREE_TTL_PATH = MAPPINGS_DIR / 'oncotree.ttl'

# Data paths
METADATA_SSSOM_PATH = DATA_DIR / 'metadata.sssom.yml'
