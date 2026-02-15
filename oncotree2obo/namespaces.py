"""RDF Namespaces"""
from rdflib import Namespace, URIRef

# Standard namespaces
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
OBO = Namespace('http://purl.obolibrary.org/obo/')

# Ontology namespaces
BIOLINK = Namespace('https://w3id.org/biolink/vocab/')
NCIT = Namespace('http://purl.obolibrary.org/obo/NCIT_')
UMLS = Namespace('http://linkedlifedata.com/resource/umls/id/')
MONDO = Namespace('http://purl.obolibrary.org/obo/MONDO_')

# OncoTree namespace
# Note: this is a Mondo-hosted mappings IRI pattern, not the upstream OncoTree site.
ONCOTREE = Namespace('http://purl.obolibrary.org/obo/mondo/mappings/oncotree/')

# OBO deprecation properties (term replaced by, consider)
IAO_0100001 = URIRef('http://purl.obolibrary.org/obo/IAO_0100001')
OBOINOWL = Namespace('http://www.geneontology.org/formats/oboInOwl#')

# Ontology IRI
ONCOTREE_ONTOLOGY_IRI = 'http://purl.obolibrary.org/obo/mondo/oncotree.owl'
