"""OncoTree ingest to generate RDF .ttl and .owl

Resources
- https://oncotree.mskcc.org/
- https://github.com/cBioPortal/oncotree

Steps
- Downloads OncoTree JSON from API or loads from file
- Parses hierarchical tree structure
- Converts to RDF graph with OWL classes
- Adds parent-child relationships (rdfs:subClassOf)
- Adds external references as mappings (NCIT, UMLS)
- Serializes to TTL and OWL formats
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rdflib import Graph, RDF, OWL, RDFS, Literal, URIRef, SKOS
from rdflib.namespace import DC

from oncotree2obo.config import ONCOTREE_OWL_PATH, ONCOTREE_TTL_PATH, ROOT_DIR
from oncotree2obo.namespaces import (
    ONCOTREE, BIOLINK, NCIT, UMLS, ONCOTREE_ONTOLOGY_IRI, OBO,
    IAO_0100001, OBOINOWL,
)
from oncotree2obo.parsers.oncotree_json_parser import (
    download_oncotree_json, load_oncotree_json, flatten_tree, extract_mappings
)
from oncotree2obo.verify import expected_from_json, actual_from_graph

# Logging
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler(sys.stdout))


def create_ontology_metadata(graph: Graph):
    """Add ontology metadata to the graph."""
    ontology_iri = URIRef(ONCOTREE_ONTOLOGY_IRI)
    
    # Create ontology declaration
    graph.add((ontology_iri, RDF.type, OWL.Ontology))
    graph.add((ontology_iri, RDFS.label, Literal("OncoTree Ontology")))
    graph.add((ontology_iri, DC.description, Literal(
        "OncoTree ontology converted from OncoTree JSON. "
        "OncoTree is an open-source ontology for standardizing cancer type diagnosis."
    )))
    graph.add((ontology_iri, DC.creator, Literal("OncoTree Team at MSKCC")))
    graph.add((ontology_iri, DC.source, Literal("https://oncotree.mskcc.org/")))
    
    # Version IRI
    version_date = datetime.now().strftime("%Y-%m-%d")
    version_iri = URIRef(f"http://purl.obolibrary.org/obo/mondo/releases/{version_date}/oncotree.owl")
    graph.add((ontology_iri, OWL.versionIRI, version_iri))


def add_oncotree_class(graph: Graph, code: str, name: str, 
                       parent_code: Optional[str] = None,
                       main_type: Optional[str] = None,
                       tissue: Optional[str] = None,
                       level: Optional[int] = None):
    """
    Add an OncoTree class to the graph.
    
    Args:
        graph: RDF graph
        code: OncoTree code (e.g., "HGSOC")
        name: Display name
        parent_code: Parent OncoTree code (if any)
        main_type: Main cancer type
        tissue: Tissue type
        level: Hierarchy level
    """
    class_uri = ONCOTREE[code]
    
    # Class declaration
    graph.add((class_uri, RDF.type, OWL.Class))
    graph.add((class_uri, RDF.type, BIOLINK.Disease))
    graph.add((class_uri, RDFS.label, Literal(name)))
    
    # Add parent relationship
    if parent_code:
        parent_uri = ONCOTREE[parent_code]
        graph.add((class_uri, RDFS.subClassOf, parent_uri))
    
    # Add annotations
    if main_type:
        graph.add((class_uri, RDFS.comment, Literal(f"Main type: {main_type}")))
    
    if tissue:
        graph.add((class_uri, RDFS.comment, Literal(f"Tissue: {tissue}")))
    
    if level is not None:
        graph.add((class_uri, RDFS.comment, Literal(f"Level: {level}")))


def add_obsolete_class(
    graph: Graph,
    code: str,
    name: str,
    replacement_codes: list[str],
    flat_nodes: dict,
):
    """
    Add an obsolete OncoTree class to the graph.

    Args:
        graph: RDF graph
        code: Obsolete OncoTree code
        name: Original display name (prefixed with "obsolete ")
        replacement_codes: List of active codes that replace this term
        flat_nodes: Full node map for validation (replacement codes must exist)

    Raises:
        ValueError: If any replacement code is not in flat_nodes
    """
    for repl in replacement_codes:
        if repl not in flat_nodes:
            raise ValueError(
                f"Replacement code '{repl}' for obsolete '{code}' not found in node map. "
                "Ensure the input tree includes all active replacement terms."
            )

    class_uri = ONCOTREE[code]
    graph.add((class_uri, RDF.type, OWL.Class))
    graph.add((class_uri, RDFS.label, Literal(f"obsolete {name}")))
    graph.add((class_uri, OWL.deprecated, Literal(True)))

    if len(replacement_codes) == 1:
        graph.add((class_uri, IAO_0100001, ONCOTREE[replacement_codes[0]]))
    else:
        for repl in replacement_codes:
            graph.add((class_uri, OBOINOWL.consider, ONCOTREE[repl]))


def add_mappings(graph: Graph, code: str, external_refs: dict):
    """
    Add external reference mappings to the graph.
    
    Args:
        graph: RDF graph
        code: OncoTree code
        external_refs: Dictionary with 'NCI' and 'UMLS' keys containing lists of IDs
    """
    class_uri = ONCOTREE[code]
    
    # Add NCIT mappings
    nci_ids = external_refs.get('NCI', [])
    for nci_id in nci_ids:
        nci_id = nci_id.strip() # remove whitespace
        ncit_uri = NCIT[nci_id]
        graph.add((class_uri, SKOS.exactMatch, ncit_uri))
    
    # Add UMLS mappings
    umls_ids = external_refs.get('UMLS', [])
    for umls_id in umls_ids:
        umls_id = umls_id.strip() # remove whitespace
        umls_uri = UMLS[umls_id]
        graph.add((class_uri, SKOS.exactMatch, umls_uri))


def oncotree2obo(
    json_file: Optional[Path] = None,
    version: Optional[str] = None,
):
    """
    Convert OncoTree JSON to OWL ontology.

    Args:
        json_file: Optional path to local JSON file. If None, downloads from API.
        version: Optional version string for API download.
    """
    LOG.info("Starting OncoTree to OBO conversion")

    # Load or download OncoTree data
    if json_file and json_file.exists():
        tree_data = load_oncotree_json(json_file)
    else:
        tree_data = download_oncotree_json(version)

    # Create RDF graph
    graph = Graph()
    
    # Bind namespaces
    graph.bind("oncotree", ONCOTREE)
    graph.bind("biolink", BIOLINK)
    graph.bind("ncit", NCIT)
    graph.bind("umls", UMLS)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("skos", SKOS)
    graph.bind("obo", OBO)
    graph.bind("oboInOwl", OBOINOWL)
    
    # Add ontology metadata
    create_ontology_metadata(graph)
    
    # Flatten tree structure
    flat_nodes = flatten_tree(tree_data)
    LOG.info(f"Processing {len(flat_nodes)} OncoTree terms")

    # Collect obsolete codes (from revocations + precursors)
    obsolete_codes: set[str] = set()
    obsolete_to_replacements: dict[str, list[str]] = {}
    for code, node in flat_nodes.items():
        if not isinstance(node, dict) or 'code' not in node:
            continue
        for obsolete_code in (node.get('revocations') or []) + (node.get('precursors') or []):
            # Ignore self-revocation / self-precursor (code appears in its own revocations list)
            if obsolete_code == code:
                continue
            obsolete_codes.add(obsolete_code)
            obsolete_to_replacements.setdefault(obsolete_code, []).append(code)

    # Process each active node (skip obsolete codes)
    for code, node in flat_nodes.items():
        if not isinstance(node, dict) or 'code' not in node:
            continue
        if code in obsolete_codes:
            continue

        name = node.get('name', '')
        parent_code = node.get('parent_code')
        main_type = node.get('mainType')
        tissue = node.get('tissue')
        level = node.get('level')
        external_refs = node.get('externalReferences', {})
        
        # Add class
        add_oncotree_class(
            graph, code, name, parent_code, main_type, tissue, level
        )
        
        # Add mappings
        if external_refs:
            add_mappings(graph, code, external_refs)

    # Add obsolete classes
    for obsolete_code, replacement_codes in obsolete_to_replacements.items():
        if obsolete_code in flat_nodes:
            obsolete_node = flat_nodes[obsolete_code]
            name = obsolete_node.get('name') or obsolete_code
        else:
            # API may omit revoked terms; fall back to using the code as a label.
            name = obsolete_code
        add_obsolete_class(
            graph, obsolete_code, name, replacement_codes, flat_nodes
        )

    # Verify in-memory: class/mapping counts must match expected from the same JSON source
    expected = expected_from_json(tree_data)
    actual = actual_from_graph(graph)
    if (
        expected["classes"] != actual["classes"]
        or expected["classes_active"] != actual["classes_active"]
        or expected["classes_obsolete"] != actual["classes_obsolete"]
        or expected["mappings_total"] != actual["mappings_total"]
        or expected["terms_with_ncit"] != actual["terms_with_ncit"]
        or expected["terms_with_umls"] != actual["terms_with_umls"]
    ):
        LOG.error(
            "Verification failed: expected %s, got %s",
            expected,
            actual,
        )
        raise SystemExit(1)
    LOG.info(
        "Verification passed: %s",
        actual,
    )

    # Serialize to TTL
    ONCOTREE_TTL_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG.info(f"Writing TTL to {ONCOTREE_TTL_PATH}")
    graph.serialize(destination=str(ONCOTREE_TTL_PATH), format='turtle')
    
    # Serialize to OWL
    ONCOTREE_OWL_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG.info(f"Writing OWL to {ONCOTREE_OWL_PATH}")
    graph.serialize(destination=str(ONCOTREE_OWL_PATH), format='xml')
    
    LOG.info("Conversion complete!")
    LOG.info(f"Created {ONCOTREE_TTL_PATH}")
    LOG.info(f"Created {ONCOTREE_OWL_PATH}")

