"""RDF Namespaces"""
from rdflib import Namespace

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
ONCOTREE = Namespace('http://purl.obolibrary.org/obo/mondo/mappings/unknown_prefix/ONCOTREE/')

# Ontology IRI
ONCOTREE_ONTOLOGY_IRI = 'http://purl.obolibrary.org/obo/mondo/oncotree.owl'
