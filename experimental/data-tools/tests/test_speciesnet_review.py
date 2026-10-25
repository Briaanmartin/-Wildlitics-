"""Synthetic schema fixtures, not SpeciesNet inference or wildlife validation."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "speciesnet_review.py"
SPEC = importlib.util.spec_from_file_location("speciesnet_review", MODULE)
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)

BEAR = "fixture-bear;mammalia;carnivora;ursidae;helarctos;malayanus;sun bear"
CAT = "fixture-cat;mammalia;carnivora;felidae;neofelis;diardi;sunda clouded leopard"
FAMILY = "fixture-family;mammalia;carnivora;felidae;;;cat family"
BLANK = "fixture-blank;;;;;;blank"


def detection(label=BEAR, category="1", box=None, source="classifier"):
    return {"category": category, "label": review.CATEGORIES[category], "conf": .92,
            "bbox": box or [.1, .2, .3, .4],
            "raw_classifications": {"classes": [label], "scores": [.87]},
            "processed_classification": {"class": label, "score": .87, "source": source}}


def modern(*detections, **extra):
    return {"info": {"format_version": "20261015"}, "predictions": [
        {"filepath": "fixture.jpg", "model_version": "4.0.3a", "detections": list(detections), **extra}]}


class SpeciesNetReviewTests(unittest.TestCase):
    def test_each_animal_keeps_its_own_box_and_species(self):
        source = modern(detection(), detection(CAT, box=[.5, .1, .2, .2]))
        before = deepcopy(source)
        result = review.normalise_results(source)
        records = result["images"][0]["detections"]
        self.assertEqual([d["suggestion"]["taxon"]["scientific_name"] for d in records],
                         ["helarctos malayanus", "neofelis diardi"])
        self.assertEqual(records[1]["bbox_normalised_xywh"], [.5, .1, .2, .2])
        self.assertTrue(all(d["review_required"] and not d["verified"] for d in records))
        self.assertEqual(result["summary"]["verified_observations"], 0)
        self.assertEqual(source, before)

    def test_legacy_image_prediction_is_not_copied_to_any_box(self):
        source = {"predictions": [{"filepath": "old.jpg", "model_version": "4.0.3a",
            "detections": [{"category": "1", "conf": .9, "bbox": [0, 0, .2, .2]},
                           {"category": "1", "conf": .8, "bbox": [.5, .5, .2, .2]}],
            "classifications": {"classes": [BEAR], "scores": [.91],
                                "target_classes": [CAT], "target_logits": [-1.2]},
            "prediction": BEAR, "prediction_score": .91, "prediction_source": "classifier"}]}
        image = review.normalise_results(source)["images"][0]
        self.assertTrue(all(d["suggestion"] is None and not d["raw_candidates"] for d in image["detections"]))
        self.assertEqual(image["image_classification"]["classification_scope"], "image_unassociated")
        self.assertEqual(image["raw_prediction"], source["predictions"][0])
        self.assertIn("no_per_object_association", image["image_classification"]["review_flags"])

    def test_geofence_rollup_retains_raw_species_and_final_family(self):
        box = detection(CAT)
        box["processed_classification"] = {"class": FAMILY, "score": .95,
                                           "source": "classifier+geofence+rollup_to_family"}
        item = review.normalise_results(modern(box))["images"][0]["detections"][0]
        self.assertEqual(item["suggestion"]["taxon"]["rank"], "family")
        self.assertEqual(item["suggestion"]["taxon"]["scientific_name"], "felidae")
        self.assertEqual(item["raw_candidates"][0]["taxon"]["raw_label"], CAT)
        self.assertEqual(set(item["review_flags"]), {"not_species_level", "geofencing_applied",
                         "taxonomic_rollup", "processed_differs_from_raw_top1"})

    def test_whole_image_placeholder_is_not_a_detector_confidence(self):
        box = detection(category="0", box=[0, 0, 1, 1])
        box["conf"] = 1
        item = review.normalise_results(modern(box))["images"][0]["detections"][0]
        self.assertEqual(item["classification_scope"], "whole_image")
        self.assertIsNone(item["detector_score"])
        self.assertEqual(item["whole_image_placeholder_score"], 1)

    def test_missing_empty_and_failed_detections_are_distinct(self):
        source = {"predictions": [{"filepath": "not-run.jpg"}, {"filepath": "empty.jpg", "detections": []},
                                  {"filepath": "failed.jpg", "failures": ["DETECTOR"]}]}
        states = [x["processing_status"] for x in review.normalise_results(source)["images"]]
        self.assertEqual(states, ["detections_not_provided", "no_detections_reported", "component_failure"])

    def test_detector_only_boxes_remain_unclassified(self):
        result = review.normalise_results(modern({"category": "1", "conf": .1, "bbox": [0, 0, 1, 1]}))
        item = result["images"][0]["detections"][0]
        self.assertIsNone(item["suggestion"])
        self.assertIn("no_processed_classification", item["review_flags"])

    def test_partial_failure_keeps_successful_results_with_failure_flag(self):
        image = review.normalise_results(modern(detection(), failures=["GEOLOCATION"]))["images"][0]
        self.assertEqual(image["processing_status"], "component_failure")
        self.assertIn("component_failure", image["detections"][0]["review_flags"])
        self.assertIsNotNone(image["detections"][0]["suggestion"])

    def test_blank_suggestion_remains_unverified_category(self):
        image = review.normalise_results(modern(detection(BLANK)))["images"][0]
        self.assertEqual(image["detections"][0]["suggestion"]["taxon"]["rank"], "category")
        self.assertFalse(image["verified"])

    def test_unknown_label_is_preserved_without_guessing_species(self):
        result = review.taxon("unexpected-taxonomy-label")
        self.assertEqual(result["rank"], "unknown")
        self.assertIsNone(result["scientific_name"])
        self.assertEqual(result["raw_label"], "unexpected-taxonomy-label")

    def test_mixed_schemas_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Mixed"):
            review.normalise_results(modern(detection(), prediction=BEAR))

    def test_unknown_format_and_unversioned_box_fields_are_rejected(self):
        for version in ("future-format", None):
            source = modern(detection())
            source["info"] = {} if version is None else {"format_version": version}
            with self.subTest(version=version), self.assertRaises(ValueError):
                review.normalise_results(source)

    def test_invalid_scores_are_rejected(self):
        for score in (float("nan"), float("inf"), -.1, 1.1, True, "0.9"):
            source = modern(detection())
            source["predictions"][0]["detections"][0]["raw_classifications"]["scores"] = [score]
            with self.subTest(score=score), self.assertRaisesRegex(ValueError, "Scores"):
                review.normalise_results(source)

    def test_invalid_boxes_are_rejected(self):
        for box in ([.9, 0, .2, 1], [0, 0, 0, 1], [0, 0, float("nan"), 1], [0, True, .2, .2], [0, 0, 1]):
            with self.subTest(box=box), self.assertRaises(ValueError):
                review.normalise_results(modern(detection(box=box)))

    def test_mismatched_candidate_lengths_are_rejected(self):
        source = modern(detection())
        source["predictions"][0]["detections"][0]["raw_classifications"]["scores"] = []
        with self.assertRaisesRegex(ValueError, "matching lists"):
            review.normalise_results(source)

    def test_category_conflict_and_unknown_category_are_rejected(self):
        for category in ("2", "99", 1):
            box = detection()
            box["category"] = category
            with self.subTest(category=category), self.assertRaises(ValueError):
                review.normalise_results(modern(box))

    def test_duplicate_filepaths_and_wrong_input_format_are_rejected(self):
        source = modern(detection())
        source["predictions"].append(deepcopy(source["predictions"][0]))
        for value in (source, {"images": []}, [], {"predictions": ["not an object"]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                review.normalise_results(value)

    def test_missing_decision_source_is_rejected(self):
        source = modern(detection())
        del source["predictions"][0]["detections"][0]["processed_classification"]["source"]
        with self.assertRaisesRegex(ValueError, "decision source"):
            review.normalise_results(source)

    def test_cli_preserves_source_hash_and_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "input.json", root / "review.json"
            content = json.dumps(modern(detection())).encode()
            source.write_bytes(content)
            command = [sys.executable, str(MODULE), "--input", str(source), "--output", str(output)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(first.stdout)["detections"], 1)
            self.assertEqual(json.loads(output.read_text())["source_file"]["sha256"], sha256(content).hexdigest())
            original_output = output.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(output.read_bytes(), original_output)
            self.assertEqual(source.read_bytes(), content)

    def test_json_nan_is_rejected_before_output_is_created(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "input.json", root / "output.json"
            source.write_text('{"predictions": [], "unexpected": NaN}')
            with self.assertRaisesRegex(ValueError, "Non-finite"):
                review.import_results(source, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
