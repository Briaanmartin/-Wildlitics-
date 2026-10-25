"""Original data-preparation helpers for Wildlitics. No model training is run here."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import random
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from PIL import Image, ImageOps


def digest(path):
    result = sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _box(row):
    fields = [row.get("bbox_" + key, "").strip() for key in ("x", "y", "w", "h")]
    if not all(fields):
        raise ValueError("Each animal requires all four normalised bbox_x/y/w/h values")
    x, y, w, h = map(float, fields)
    if (not all(math.isfinite(value) for value in (x, y, w, h))
            or not 0 <= x < 1 or not 0 <= y < 1 or w <= 0 or h <= 0
            or x + w > 1.000001 or y + h > 1.000001):
        raise ValueError("Invalid normalised animal box")
    return x, y, min(w, 1 - x), min(h, 1 - y)


def read_annotations(manifest):
    """One verified object per row; reviewed background images have no object."""
    manifest = Path(manifest).resolve()
    required = {"image_path", "scientific_name", "verified", "verified_by", "license", "group_id"}
    images, events, hashes = {}, {}, {}
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Missing annotation columns: " + ", ".join(sorted(required)))
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Duplicate CSV column names")
        for line, raw in enumerate(reader, 2):
            try:
                if None in raw:
                    raise ValueError("Too many CSV fields")
                row = {key: (value or "").strip() for key, value in raw.items()}
                if row["verified"].lower() not in {"true", "yes", "1"} or not row["verified_by"]:
                    raise ValueError("Every annotation requires a human verifier")
                if not row["license"] or not row["group_id"]:
                    raise ValueError("Photo permission/license and a holdout group_id are required")
                source = (manifest.parent / row["image_path"]).resolve()
                if not source.is_file():
                    raise ValueError("Image not found: " + str(source))
                key = str(source)
                if key not in hashes:
                    hashes[key] = digest(source)
                checksum = hashes[key]
                event = row.get("event_id", "")
                if event and event in events and events[event] != row["group_id"]:
                    raise ValueError("The same event_id cannot cross holdout groups")
                if event:
                    events[event] = row["group_id"]
                background = row.get("is_background", "").lower() in {"true", "yes", "1"}
                if background and (row["scientific_name"] or any(row.get("bbox_" + part, "") for part in ("x", "y", "w", "h"))):
                    raise ValueError("Reviewed background rows cannot contain species or animal boxes")
                if not background and not row["scientific_name"]:
                    raise ValueError("Animal rows need a scientific_name")
                with Image.open(source) as original:
                    oriented = ImageOps.exif_transpose(original)
                    width, height = oriented.size
                if checksum not in images:
                    images[checksum] = {
                        "source_path": key, "source_sha256": checksum, "group_id": row["group_id"],
                        "width": width, "height": height, "license": row["license"], "verified_by": row["verified_by"],
                        "event_ids": [], "background": background, "objects": [],
                    }
                item = images[checksum]
                if item["group_id"] != row["group_id"]:
                    raise ValueError("Identical image bytes cannot cross holdout groups")
                if item["background"] != background:
                    raise ValueError("The same image cannot be both background and animal-labelled")
                if event and event not in item["event_ids"]:
                    item["event_ids"].append(event)
                if not background:
                    box = _box(row)
                    for previous in item["objects"]:
                        if tuple(previous["bbox"]) == box and previous["scientific_name"] != row["scientific_name"]:
                            raise ValueError("The same box has conflicting species labels")
                    obj = {"scientific_name": row["scientific_name"], "bbox": list(box)}
                    if obj not in item["objects"]:
                        item["objects"].append(obj)
            except (ValueError, OSError) as exc:
                raise ValueError(f"Annotation line {line}: {exc}") from exc
    if not images:
        raise ValueError("Annotation manifest is empty")
    return sorted(images.values(), key=lambda item: item["source_sha256"])


def assign_groups(images, seed=123, val_fraction=.15, test_fraction=.15):
    """Split whole declared groups, never individual frames or animal crops."""
    if (not all(math.isfinite(value) for value in (val_fraction, test_fraction))
            or val_fraction < 0 or test_fraction < 0 or val_fraction + test_fraction >= 1):
        raise ValueError("Validation/test fractions must be finite, nonnegative and sum to less than 1")
    groups = sorted({item["group_id"] for item in images})
    active = 1 + int(val_fraction > 0) + int(test_fraction > 0)
    if len(groups) < active:
        raise ValueError("Not enough independent groups for the requested train/validation/test split")
    shuffled = list(groups)
    random.Random(seed).shuffle(shuffled)
    n_val = max(1, round(len(groups) * val_fraction)) if val_fraction else 0
    n_test = max(1, round(len(groups) * test_fraction)) if test_fraction else 0
    while n_val + n_test >= len(groups):
        if n_val >= n_test and n_val > 1:
            n_val -= 1
        elif n_test > 1:
            n_test -= 1
        else:
            raise ValueError("Cannot allocate independent groups to all requested splits")
    assignment = {group: "test" for group in shuffled[:n_test]}
    assignment.update({group: "val" for group in shuffled[n_test:n_test + n_val]})
    assignment.update({group: "train" for group in shuffled[n_test + n_val:]})
    return assignment


def _normalised_copy(source, destination):
    with Image.open(source) as original:
        oriented = ImageOps.exif_transpose(original).convert("RGB")
        clean = Image.new("RGB", oriented.size)
        clean.paste(oriented)
        if destination.suffix == ".jpg":
            clean.save(destination, quality=95, subsampling=0)
        else:
            clean.save(destination)
        clean.close()
        oriented.close()


def export_dataset(manifest, output, *, seed=123, val_fraction=.15, test_fraction=.15):
    """Write YOLO, COCO and VOC annotations from reviewed labels, preserving originals."""
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Dataset output already exists; choose a new directory")
    images = read_annotations(manifest)
    assignment = assign_groups(images, seed, val_fraction, test_fraction)
    names = sorted({obj["scientific_name"] for image in images for obj in image["objects"]})
    if not names:
        raise ValueError("At least one animal class is required")
    classes = {name: number for number, name in enumerate(names)}
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="." + output.name + "-", dir=output.parent))
    splits = ("train", "val", "test")
    coco = {split: {"images": [], "annotations": [],
                    "categories": [{"id": number + 1, "name": name} for name, number in classes.items()]}
            for split in splits}
    counts = {split: {"images": 0, "background_images": 0, "objects": {}} for split in splits}
    assignments = []
    try:
        for split in splits:
            for relative in ("images/" + split, "labels/" + split, "voc/" + split):
                (stage / relative).mkdir(parents=True)
        for image_id, item in enumerate(images, 1):
            split = assignment[item["group_id"]]
            extension = ".jpg" if Path(item["source_path"]).suffix.lower() in {".jpg", ".jpeg"} else ".png"
            stem = item["source_sha256"]
            image_name = stem + extension
            relative = "images/" + split + "/" + image_name
            _normalised_copy(item["source_path"], stage / relative)
            width, height = item["width"], item["height"]
            entry = {"id": image_id, "file_name": relative, "width": width, "height": height}
            coco[split]["images"].append(entry)
            xml = ET.Element("annotation")
            ET.SubElement(xml, "filename").text = image_name
            size = ET.SubElement(xml, "size")
            for key, value in (("width", width), ("height", height), ("depth", 3)):
                ET.SubElement(size, key).text = str(value)
            yolo = []
            for obj in item["objects"]:
                name, (x, y, w, h) = obj["scientific_name"], obj["bbox"]
                category = classes[name]
                yolo.append(f"{category} {x + w / 2:.10g} {y + h / 2:.10g} {w:.10g} {h:.10g}")
                left, top, pixel_w, pixel_h = x * width, y * height, w * width, h * height
                coco[split]["annotations"].append({
                    "id": len(coco[split]["annotations"]) + 1, "image_id": image_id,
                    "category_id": category + 1, "bbox": [left, top, pixel_w, pixel_h],
                    "area": pixel_w * pixel_h, "iscrowd": 0,
                })
                child = ET.SubElement(xml, "object")
                ET.SubElement(child, "name").text = name
                bounds = ET.SubElement(child, "bndbox")
                coords = (("xmin", math.floor(left) + 1), ("ymin", math.floor(top) + 1),
                          ("xmax", min(width, math.ceil(left + pixel_w))),
                          ("ymax", min(height, math.ceil(top + pixel_h))))
                for key, value in coords:
                    ET.SubElement(bounds, key).text = str(value)
                counts[split]["objects"][name] = counts[split]["objects"].get(name, 0) + 1
            (stage / "labels" / split / (stem + ".txt")).write_text(
                "\n".join(yolo) + ("\n" if yolo else ""), encoding="utf-8")
            ET.ElementTree(xml).write(stage / "voc" / split / (stem + ".xml"),
                                      encoding="utf-8", xml_declaration=True)
            counts[split]["images"] += 1
            counts[split]["background_images"] += int(item["background"])
            assignments.append({**item, "split": split, "prepared_image": relative,
                                "prepared_sha256": digest(stage / relative)})
        (stage / "annotations").mkdir()
        for split in splits:
            (stage / "annotations" / (split + ".coco.json")).write_text(
                json.dumps(coco[split], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (stage / "class_map.json").write_text(json.dumps(classes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        yaml = ["path: " + json.dumps(str(output)), "train: images/train", "val: images/val",
                "test: images/test", "names:"]
        yaml.extend(f"  {number}: " + json.dumps(name, ensure_ascii=False) for name, number in classes.items())
        (stage / "data.yaml").write_text("\n".join(yaml) + "\n", encoding="utf-8")
        warnings = []
        for split in splits:
            if counts[split]["images"]:
                missing = [name for name in names if not counts[split]["objects"].get(name)]
                if missing:
                    warnings.append({"split": split, "missing_classes": missing})
        result = {"schema_version": 1, "manifest_sha256": digest(manifest),
                  "seed": seed, "group_assignment": assignment, "counts": counts,
                  "warnings": warnings, "images": assignments,
                  "coordinate_conventions": {"input": "normalised xywh after EXIF orientation",
                                              "YOLO": "zero-based class; normalised cx cy w h",
                                              "COCO": "one-based category; absolute-pixel xywh",
                                              "VOC": "one-based inclusive pixel bounds"},
                  "note": "Declared groups prevent only declared leakage; review near-duplicates and site/event identifiers."}
        (stage / "dataset_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stage.rename(output)
        return result
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def sample_video(source, output, *, interval=2.0, timeout=600):
    """Sample actual decoded-frame PTS; reuse only complete, integrity-checked jobs."""
    if not math.isfinite(interval) or interval <= 0 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Interval and timeout must be positive finite numbers")
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file():
        raise ValueError("Video file not found")
    checksum = digest(source)
    if output.exists():
        manifest = output / "video_manifest.json"
        if not manifest.is_file():
            raise ValueError("Output exists without a completed video manifest")
        result = json.loads(manifest.read_text(encoding="utf-8"))
        if result.get("source_sha256") != checksum or result.get("interval_seconds") != interval:
            raise ValueError("Existing video job uses a different source or sampling interval")
        for frame in result.get("frames", []):
            path = (output / frame["image_path"]).resolve()
            if not path.is_relative_to(output) or not path.is_file() or digest(path) != frame["sha256"]:
                raise ValueError("A cached video frame is missing or has changed")
        if not result.get("frames"):
            raise ValueError("Cached job has no sampled frames")
        return {**result, "cache_reused": True}
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("Install FFmpeg and ffprobe and add both to PATH")
    probe = subprocess.run([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json",
                            str(source)], capture_output=True, text=True, timeout=60, check=True)
    metadata = json.loads(probe.stdout)
    if not any(stream.get("codec_type") == "video" for stream in metadata.get("streams", [])):
        raise ValueError("Input contains no video stream")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="." + output.name + "-", dir=output.parent))
    try:
        (stage / "frames").mkdir()
        filter_text = f"select='isnan(prev_selected_t)+gte(t-prev_selected_t,{interval})',showinfo"
        command = [ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-n", "-copyts", "-start_at_zero",
                   "-i", str(source), "-map", "0:v:0", "-an", "-sn", "-dn", "-vf", filter_text,
                   "-fps_mode", "vfr", "-q:v", "2", str(stage / "frames" / "frame_%06d.jpg")]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        if completed.returncode:
            raise RuntimeError("FFmpeg failed: " + completed.stderr[-1800:])
        times = {int(number): float(value) for number, value in
                 re.findall(r"\bn:\s*(\d+).*?\bpts_time:\s*([-+\deE.]+)", completed.stderr)}
        files = sorted((stage / "frames").glob("frame_*.jpg"))
        if not files or len(files) != len(times) or set(times) != set(range(len(files))):
            raise RuntimeError("Could not align extracted frames with their decoded timestamps")
        frames = [{"sample_index": number, "image_path": "frames/" + path.name,
                   "video_offset_seconds": times[number], "sha256": digest(path),
                   "verified": False} for number, path in enumerate(files)]
        version = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, timeout=10, check=True).stdout.splitlines()[0]
        result = {"schema_version": 1, "source_path": str(source), "source_sha256": checksum,
                  "interval_seconds": interval, "timestamp_basis": "decoded frame PTS after FFmpeg -copyts -start_at_zero",
                  "ffmpeg_version": version, "frames": frames, "cache_reused": False,
                  "review_required": True, "source_metadata": metadata,
                  "note": "Sampling can miss brief appearances. No detector was run and no animal absence is inferred."}
        (stage / "video_manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        stage.rename(output)
        return result
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export-dataset")
    export.add_argument("--manifest", required=True)
    export.add_argument("--output", required=True)
    export.add_argument("--seed", type=int, default=123)
    export.add_argument("--val-fraction", type=float, default=.15)
    export.add_argument("--test-fraction", type=float, default=.15)
    video = sub.add_parser("sample-video")
    video.add_argument("--video", required=True)
    video.add_argument("--output", required=True)
    video.add_argument("--interval", type=float, default=2)
    video.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args(argv)
    try:
        if args.command == "export-dataset":
            result = export_dataset(args.manifest, args.output, seed=args.seed,
                                    val_fraction=args.val_fraction, test_fraction=args.test_fraction)
            print(json.dumps({"counts": result["counts"], "warnings": result["warnings"]}, indent=2))
        else:
            result = sample_video(args.video, args.output, interval=args.interval, timeout=args.timeout)
            print(json.dumps({"sampled_frames": len(result["frames"]), "cache_reused": result["cache_reused"]}))
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print("Error: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
