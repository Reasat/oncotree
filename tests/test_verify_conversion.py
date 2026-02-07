"""
Tests that conversion from OncoTree JSON to OWL/TTL produces correct entity counts.
"""
import json
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, RDF, OWL, RDFS, SKOS, Literal

from oncotree2obo.verify import (
    expected_from_json,
    actual_from_rdf,
    verify,
    verify_and_raise,
)
from oncotree2obo.namespaces import ONCOTREE, NCIT, UMLS
from oncotree2obo.config import ONCOTREE_OWL_PATH, ROOT_DIR


# Minimal tree: 2 nodes (TISSUE, OVARY), 2 NCIT + 2 UMLS mappings
MINIMAL_TREE = {
    "TISSUE": {
        "code": "TISSUE",
        "name": "Tissue",
        "externalReferences": {"UMLS": ["C0040300"], "NCI": ["C12801"]},
        "children": {
            "OVARY": {
                "code": "OVARY",
                "name": "Ovary",
                "externalReferences": {"UMLS": ["C0029939"], "NCI": ["C12404"]},
                "children": {},
            }
        },
    }
}


class TestExpectedFromJson(unittest.TestCase):
    def test_expected_counts_minimal(self):
        exp = expected_from_json(MINIMAL_TREE)
        self.assertEqual(exp["classes"], 2)
        self.assertEqual(exp["mappings_ncit"], 2)
        self.assertEqual(exp["mappings_umls"], 2)
        self.assertEqual(exp["mappings_total"], 4)


class TestActualFromRdf(unittest.TestCase):
    def test_actual_counts_from_minimal_owl(self):
        graph = Graph()
        graph.bind("oncotree", ONCOTREE)
        graph.bind("ncit", NCIT)
        graph.bind("umls", UMLS)
        c1 = ONCOTREE["TISSUE"]
        c2 = ONCOTREE["OVARY"]
        graph.add((c1, RDF.type, OWL.Class))
        graph.add((c1, RDFS.label, Literal("Tissue")))
        graph.add((c2, RDF.type, OWL.Class))
        graph.add((c2, RDFS.label, Literal("Ovary")))
        graph.add((c2, RDFS.subClassOf, c1))
        graph.add((c1, SKOS.exactMatch, NCIT["C12801"]))
        graph.add((c1, SKOS.exactMatch, UMLS["C0040300"]))
        graph.add((c2, SKOS.exactMatch, NCIT["C12404"]))
        graph.add((c2, SKOS.exactMatch, UMLS["C0029939"]))

        with tempfile.NamedTemporaryFile(suffix=".owl", delete=False) as f:
            path = Path(f.name)
        try:
            graph.serialize(destination=str(path), format="xml")
            actual = actual_from_rdf(path)
            self.assertEqual(actual["classes"], 2)
            self.assertEqual(actual["mappings_ncit"], 2)
            self.assertEqual(actual["mappings_umls"], 2)
            self.assertEqual(actual["mappings_total"], 4)
        finally:
            path.unlink(missing_ok=True)


class TestVerify(unittest.TestCase):
    def test_verify_pass(self):
        graph = Graph()
        graph.bind("oncotree", ONCOTREE)
        graph.bind("ncit", NCIT)
        graph.bind("umls", UMLS)
        c1, c2 = ONCOTREE["TISSUE"], ONCOTREE["OVARY"]
        for c in (c1, c2):
            graph.add((c, RDF.type, OWL.Class))
        graph.add((c1, SKOS.exactMatch, NCIT["C12801"]))
        graph.add((c1, SKOS.exactMatch, UMLS["C0040300"]))
        graph.add((c2, SKOS.exactMatch, NCIT["C12404"]))
        graph.add((c2, SKOS.exactMatch, UMLS["C0029939"]))

        with tempfile.NamedTemporaryFile(suffix=".owl", delete=False) as f:
            rdf_path = Path(f.name)
        try:
            graph.serialize(destination=str(rdf_path), format="xml")
            result = verify(tree_data=MINIMAL_TREE, rdf_path=rdf_path)
            self.assertTrue(result["ok"], result["message"])
            self.assertEqual(result["expected"], result["actual"])
        finally:
            rdf_path.unlink(missing_ok=True)

    def test_verify_fail(self):
        graph = Graph()
        graph.add((ONCOTREE["TISSUE"], RDF.type, OWL.Class))
        # Only one class, but we expect two
        with tempfile.NamedTemporaryFile(suffix=".owl", delete=False) as f:
            rdf_path = Path(f.name)
        try:
            graph.serialize(destination=str(rdf_path), format="xml")
            result = verify(tree_data=MINIMAL_TREE, rdf_path=rdf_path)
            self.assertFalse(result["ok"])
            self.assertIn("classes", result["message"])
        finally:
            rdf_path.unlink(missing_ok=True)

    def test_verify_and_raise(self):
        # Valid OWL but wrong count (1 class instead of 2) so verify fails
        graph = Graph()
        graph.add((ONCOTREE["TISSUE"], RDF.type, OWL.Class))
        with tempfile.NamedTemporaryFile(suffix=".owl", delete=False) as f:
            rdf_path = Path(f.name)
        try:
            graph.serialize(destination=str(rdf_path), format="xml")
            with self.assertRaises(AssertionError):
                verify_and_raise(tree_data=MINIMAL_TREE, rdf_path=rdf_path)
        finally:
            rdf_path.unlink(missing_ok=True)


class TestVerifyIntegration(unittest.TestCase):
    """Integration: run conversion then verify (writes MINIMAL_TREE to temp JSON, builds OWL, verifies)."""

    def test_verify_after_conversion(self):
        from oncotree2obo.main import oncotree2obo

        fd, path = tempfile.mkstemp(suffix=".json")
        json_path = Path(path)
        try:
            with open(fd, "w") as f:
                json.dump(MINIMAL_TREE, f, indent=2)
            oncotree2obo(json_file=json_path)
            owl_path = ROOT_DIR / "oncotree.owl"
            self.assertTrue(owl_path.exists(), "oncotree.owl not produced")
            result = verify(json_path=json_path, rdf_path=owl_path)
            self.assertTrue(result["ok"], result["message"])
        finally:
            json_path.unlink(missing_ok=True)
