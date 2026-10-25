"""Original, model-free import of SpeciesNet results into unverified review records."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path


CATEGORIES = {"0": "whole_image_classification", "1": "animal", "2": "human", "3": "vehicle"}
FORMAT_VERSION = "20261015"
LEGACY_KEYS = {"classifications", "prediction", "prediction_score", "prediction_source"}


def taxon(label):
    """Read SpeciesNet's seven-field label without inventing a species name."""
    if not isinstance(label, str) or not label.strip():
        raise ValueError("Classification labels must be nonempty strings")
    parts = label.split(";")
    result = {"raw_label": label, "rank": "unknown", "scientific_name": None}
    if len(parts) != 7:
        return result
    ident, class_name, order, family, genus, epithet, common = parts
    result.update({"taxon_id": ident, "common_name": common,
                   "taxonomy": dict(zip(("class", "order", "family", "genus", "species"), parts[1:6]))})
    if common.casefold() in {"blank", "animal", "vehicle", "no cv result"}:
        result["rank"] = "category"
    elif genus and epithet:
        result.update(rank="species", scientific_name=genus + " " + epithet)
    else:
        for rank, value in (("genus", genus), ("family", family), ("order", order), ("class", class_name)):
            if value:
                result.update(rank=rank, scientific_name=value)
                break
    return result


def _score(value):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not 0 <= value <= 1):
        raise ValueError("Scores must be finite numbers in [0, 1]")
    return value


def _raw_candidates(value):
    if value is None:
        return []
    if not isinstance(value, dict):
        raise ValueError("Raw classifications must be an object")
    classes, scores = value.get("classes"), value.get("scores")
    if not isinstance(classes, list) or not isinstance(scores, list) or len(classes) != len(scores):
        raise ValueError("Raw classification classes and scores must be matching lists")
    return [{"taxon": taxon(label), "classifier_score": _score(score)}
            for label, score in zip(classes, scores)]


def _suggestion(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("Processed classification must be an object")
    source = value.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("Processed classification requires its original decision source")
    return {"taxon": taxon(value.get("class")), "ensemble_score": _score(value.get("score")),
            "decision_source": source}


def _flags(raw, suggestion):
    flags = []
    if suggestion is None:
        flags.append("no_processed_classification")
    else:
        if suggestion["taxon"]["rank"] != "species":
            flags.append("not_species_level")
        source = suggestion["decision_source"].casefold()
        if "geofence" in source:
            flags.append("geofencing_applied")
        if "rollup" in source:
            flags.append("taxonomic_rollup")
        if raw and raw[0]["taxon"]["raw_label"] != suggestion["taxon"]["raw_label"]:
            flags.append("processed_differs_from_raw_top1")
    return flags


def normalise_results(payload):
    """Support legacy image-level JSON and the explicit 20261015 box-level schema.

    No label is accepted, no threshold is imposed, and no image-level prediction
    is attributed to an individual detection. Raw source records remain intact.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("predictions"), list):
        raise ValueError("Expected SpeciesNet run_model JSON with a predictions list (not MegaDetector JSON)")
    info = payload.get("info", {})
    if not isinstance(info, dict):
        raise ValueError("Source info must be an object")
    version = info.get("format_version")
    if version is not None and version != FORMAT_VERSION:
        raise ValueError(f"Unsupported SpeciesNet format_version: {version!r}")
    images, paths = [], set()
    for number, original in enumerate(payload["predictions"]):
        if not isinstance(original, dict):
            raise ValueError(f"Prediction {number} must be an object")
        item = deepcopy(original)
        path = item.get("filepath")
        if not isinstance(path, str) or not path.strip() or path in paths:
            raise ValueError(f"Prediction {number} requires a unique, nonempty filepath")
        paths.add(path)
        failures = item.get("failures", [])
        if not isinstance(failures, list) or not all(isinstance(x, str) for x in failures):
            raise ValueError(f"Invalid component failures for {path}")
        has_detections = "detections" in item
        detections = item.get("detections", [])
        if not isinstance(detections, list) or not all(isinstance(x, dict) for x in detections):
            raise ValueError(f"Invalid detections for {path}")
        per_box = any("raw_classifications" in d or "processed_classification" in d for d in detections)
        legacy = bool(LEGACY_KEYS.intersection(item))
        if legacy and (per_box or version == FORMAT_VERSION):
            raise ValueError(f"Mixed image-level and box-level classification schemas for {path}")
        if per_box and version != FORMAT_VERSION:
            raise ValueError("Box-level SpeciesNet output requires info.format_version=20261015")
        schema = "per_detection" if version == FORMAT_VERSION else "legacy_image"
        image = {"filepath": path, "model_version": item.get("model_version"),
                 "source_schema": schema, "failures": failures,
                 "processing_status": "component_failure" if failures else "results_available",
                 "verified": False, "review_required": True, "raw_prediction": item,
                 "detections": [], "image_classification": None}
        for index, det in enumerate(detections):
            category = det.get("category")
            if not isinstance(category, str) or category not in CATEGORIES:
                raise ValueError(f"Unknown detection category for {path}: {category!r}")
            if category == "0" and schema != "per_detection":
                raise ValueError("Whole-image pseudo-detections require the box-level schema")
            if "label" in det and det["label"] != CATEGORIES[category]:
                raise ValueError(f"Detection label/category conflict for {path}")
            box = det.get("bbox")
            if (not isinstance(box, list) or len(box) != 4
                    or any(isinstance(v, bool) or not isinstance(v, (int, float))
                           or not math.isfinite(v) for v in box)):
                raise ValueError(f"Invalid normalised xywh box for {path}")
            x, y, w, h = box
            if not (0 <= x < 1 and 0 <= y < 1 and w > 0 and h > 0
                    and x + w <= 1.000001 and y + h <= 1.000001):
                raise ValueError(f"Out-of-bounds normalised xywh box for {path}")
            raw = _raw_candidates(det.get("raw_classifications"))
            suggestion = _suggestion(det.get("processed_classification"))
            flags = _flags(raw, suggestion)
            if failures:
                flags.append("component_failure")
            if category == "0":
                flags.append("whole_image_scope")
            image["detections"].append({
                "detection_index": index, "category": category, "label": CATEGORIES[category],
                "classification_scope": "whole_image" if category == "0" else "detection",
                "bbox_normalised_xywh": box, "detector_score": None if category == "0" else _score(det.get("conf")),
                "whole_image_placeholder_score": _score(det.get("conf")) if category == "0" else None,
                "raw_candidates": raw, "suggestion": suggestion, "review_flags": flags,
                "verified": False, "review_required": True})
        if legacy:
            raw = _raw_candidates(item.get("classifications"))
            suggestion = None
            if "prediction" in item:
                suggestion = _suggestion({"class": item["prediction"], "score": item.get("prediction_score"),
                                          "source": item.get("prediction_source")})
            elif {"prediction_score", "prediction_source"}.intersection(item):
                raise ValueError(f"Prediction metadata without a prediction for {path}")
            image["image_classification"] = {"classification_scope": "image_unassociated",
                "raw_candidates": raw, "suggestion": suggestion,
                "review_flags": _flags(raw, suggestion) + ["no_per_object_association"],
                "verified": False, "review_required": True}
        if not detections:
            image["processing_status"] = ("component_failure" if failures else
                "no_detections_reported" if has_detections else "detections_not_provided")
        images.append(image)
    return {"schema_version": "wildlitics.speciesnet-review.v1", "source_info": deepcopy(info),
            "score_meaning": "Model scores are not measured field accuracy; ensemble scores may originate from detector heuristics or taxonomic rollup.",
            "images": images,
            "summary": {"images": len(images), "detections": sum(len(x["detections"]) for x in images),
                        "processing_status_counts": dict(Counter(x["processing_status"] for x in images)),
                        "verified_observations": 0}}


def import_results(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    content = source.read_bytes()
    def invalid_constant(value):
        raise ValueError(f"Non-finite JSON constant: {value}")
    result = normalise_results(json.loads(content, parse_constant=invalid_constant))
    result["source_file"] = {"path": str(source), "sha256": sha256(content).hexdigest()}
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write(encoded)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="SpeciesNet run_model JSON")
    parser.add_argument("--output", type=Path, required=True, help="New local review JSON file")
    args = parser.parse_args()
    try:
        result = import_results(args.input, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Import failed: {exc}\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
