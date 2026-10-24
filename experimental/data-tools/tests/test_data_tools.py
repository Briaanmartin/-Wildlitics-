"""Tests use generated images and videos, never wildlife research data."""
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

from PIL import Image

MODULE = Path(__file__).resolve().parents[1] / "data_tools.py"
SPEC = importlib.util.spec_from_file_location("wildlitics_data_tools", MODULE)
tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tools)


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def image(self, name="source.png", colour="red", size=(20, 10)):
        path = self.root / name
        Image.new("RGB", size, colour).save(path)
        return path

    def row(self, path, **extra):
        return {"image_path": str(path), "scientific_name": "Helarctos malayanus",
                "verified": "true", "verified_by": "Synthetic-fixture reviewer",
                "license": "generated fixture", "group_id": "site-A", "event_id": "",
                "bbox_x": ".25", "bbox_y": ".2", "bbox_w": ".5", "bbox_h": ".6",
                "is_background": "false", **extra}

    def manifest(self, rows):
        path = self.root / "annotations.csv"
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def export(self, rows, name="dataset"):
        return tools.export_dataset(self.manifest(rows), self.root / name,
                                    val_fraction=0, test_fraction=0)

    def test_all_three_formats_preserve_object_geometry(self):
        source = self.image()
        original = source.read_bytes()
        result = self.export([self.row(source)])
        self.assertEqual(source.read_bytes(), original)
        directory = self.root / "dataset"
        stem = result["images"][0]["source_sha256"]
        yolo = (directory / "labels/train" / (stem + ".txt")).read_text().split()
        self.assertEqual(int(yolo[0]), 0)
        self.assertEqual(list(map(float, yolo[1:])), [.5, .5, .5, .6])
        coco = json.loads((directory / "annotations/train.coco.json").read_text())
        self.assertEqual(coco["annotations"][0]["bbox"], [5., 2., 10., 6.])
        self.assertEqual(coco["annotations"][0]["category_id"], 1)
        xml = ET.parse(directory / "voc/train" / (stem + ".xml"))
        bounds = xml.find("object/bndbox")
        self.assertEqual([int(bounds.find(key).text) for key in ("xmin", "ymin", "xmax", "ymax")],
                         [6, 3, 15, 8])

    def test_multiple_species_in_one_frame_keep_their_own_boxes(self):
        image = self.image()
        rows = [self.row(image), self.row(image, scientific_name="Neofelis diardi",
                                          bbox_x="0", bbox_y="0", bbox_w=".2", bbox_h=".2")]
        self.export(rows)
        data = json.loads((self.root / "dataset/annotations/train.coco.json").read_text())
        self.assertEqual(len(data["images"]), 1)
        self.assertEqual(len(data["annotations"]), 2)
        self.assertEqual(len(data["categories"]), 2)

    def test_reviewed_backgrounds_have_empty_yolo_labels_and_no_objects(self):
        animal = self.image()
        empty = self.image("empty.png", "blue")
        result = self.export([self.row(animal),
                              self.row(empty, scientific_name="", bbox_x="", bbox_y="",
                                       bbox_w="", bbox_h="", is_background="true")])
        self.assertEqual(result["counts"]["train"]["background_images"], 1)
        background = next(item for item in result["images"] if item["background"])
        path = self.root / "dataset/labels/train" / (background["source_sha256"] + ".txt")
        self.assertEqual(path.read_text(), "")

    def test_unverified_labels_cannot_be_exported(self):
        with self.assertRaisesRegex(ValueError, "human verifier"):
            self.export([self.row(self.image(), verified="false")])
        self.assertFalse((self.root / "dataset").exists())

    def test_same_image_bytes_cannot_cross_groups(self):
        first = self.image()
        second = self.root / "copy.png"
        shutil.copyfile(first, second)
        with self.assertRaisesRegex(ValueError, "Identical image bytes"):
            self.export([self.row(first), self.row(second, group_id="site-B")])

    def test_same_encounter_cannot_cross_groups(self):
        with self.assertRaisesRegex(ValueError, "event_id"):
            self.export([self.row(self.image(), event_id="camera1/event1"),
                         self.row(self.image("other.png", "blue"), event_id="camera1/event1", group_id="site-B")])

    def test_duplicate_annotation_rows_do_not_inflate_counts(self):
        row = self.row(self.image())
        result = self.export([row, row])
        self.assertEqual(result["counts"]["train"]["images"], 1)
        self.assertEqual(result["counts"]["train"]["objects"]["Helarctos malayanus"], 1)

    def test_conflicting_species_for_identical_box_are_rejected(self):
        path = self.image()
        with self.assertRaisesRegex(ValueError, "conflicting species"):
            self.export([self.row(path), self.row(path, scientific_name="Neofelis diardi")])

    def test_invalid_boxes_do_not_create_partial_dataset(self):
        image = self.image()
        for extra in ({"bbox_x": "-.1"}, {"bbox_w": "2"}, {"bbox_h": "nan"}, {"bbox_h": ""}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.export([self.row(image, **extra)])
        self.assertFalse((self.root / "dataset").exists())

    def test_existing_output_is_preserved(self):
        destination = self.root / "dataset"
        destination.mkdir()
        marker = destination / "keep.txt"
        marker.write_text("keep this")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.export([self.row(self.image())])
        self.assertEqual(marker.read_text(), "keep this")

    def test_exif_orientation_is_materialised_and_original_preserved(self):
        path = self.root / "rotated.jpg"
        exif = Image.Exif()
        exif[274] = 6
        Image.new("RGB", (20, 10), "red").save(path, exif=exif)
        original = path.read_bytes()
        result = self.export([self.row(path)])
        record = result["images"][0]
        with Image.open(self.root / "dataset" / record["prepared_image"]) as prepared:
            self.assertEqual(prepared.size, (10, 20))
            self.assertNotIn(274, prepared.getexif())
        self.assertEqual(path.read_bytes(), original)

    def test_group_splits_are_reproducible_and_never_split_a_group(self):
        images = [{"group_id": "site-" + str(number // 3)} for number in range(30)]
        first = tools.assign_groups(images, seed=41)
        second = tools.assign_groups(list(reversed(images)), seed=41)
        self.assertEqual(first, second)
        self.assertEqual(set(first.values()), {"train", "val", "test"})
        self.assertEqual(len(first), 10)

    def test_insufficient_groups_are_not_silently_split_by_frame(self):
        with self.assertRaisesRegex(ValueError, "Not enough independent groups"):
            tools.assign_groups([{"group_id": "one-site"}])

    def test_invalid_split_fractions_are_rejected(self):
        for val, test in ((float("nan"), .2), (-.1, .2), (.5, .5)):
            with self.subTest(val=val, test=test), self.assertRaises(ValueError):
                tools.assign_groups([{"group_id": str(i)} for i in range(5)], val_fraction=val, test_fraction=test)

    def test_class_names_are_xml_escaped_and_yaml_quoted(self):
        label = 'Taxon & <example>: "name"'
        result = self.export([self.row(self.image(), scientific_name=label)])
        stem = result["images"][0]["source_sha256"]
        xml = ET.parse(self.root / "dataset/voc/train" / (stem + ".xml"))
        self.assertEqual(xml.find("object/name").text, label)
        data = json.loads((self.root / "dataset/class_map.json").read_text())
        self.assertIn(label, data)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg and ffprobe are required")
class VideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.video = cls.root / "test video ; name.mp4"
        subprocess.run([shutil.which("ffmpeg"), "-v", "error", "-nostdin", "-f", "lavfi", "-i",
                        "testsrc2=size=64x48:rate=5", "-t", "2", "-c:v", "mpeg4", "-q:v", "3",
                        "-threads", "1", str(cls.video)], check=True, capture_output=True, timeout=30)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.destination = self.root / self._testMethodName

    def test_real_frame_timestamps_and_completed_job_resume(self):
        original = tools.digest(self.video)
        result = tools.sample_video(self.video, self.destination, interval=.5)
        self.assertEqual(len(result["frames"]), 4)
        for frame, expected in zip(result["frames"], [0, .6, 1.2, 1.8]):
            self.assertAlmostEqual(frame["video_offset_seconds"], expected, places=5)
            self.assertFalse(frame["verified"])
            with Image.open(self.destination / frame["image_path"]) as image:
                self.assertEqual(image.size, (64, 48))
        cached = tools.sample_video(self.video, self.destination, interval=.5)
        self.assertTrue(cached["cache_reused"])
        self.assertEqual(tools.digest(self.video), original)

    def test_missing_cached_frame_is_not_silently_accepted(self):
        result = tools.sample_video(self.video, self.destination, interval=1)
        (self.destination / result["frames"][0]["image_path"]).unlink()
        with self.assertRaisesRegex(ValueError, "missing or has changed"):
            tools.sample_video(self.video, self.destination, interval=1)

    def test_changed_interval_requires_a_new_output(self):
        tools.sample_video(self.video, self.destination, interval=1)
        with self.assertRaisesRegex(ValueError, "different source or sampling interval"):
            tools.sample_video(self.video, self.destination, interval=.5)

    def test_existing_unrelated_directory_is_preserved(self):
        self.destination.mkdir()
        marker = self.destination / "keep.txt"
        marker.write_text("original")
        with self.assertRaises(ValueError):
            tools.sample_video(self.video, self.destination)
        self.assertEqual(marker.read_text(), "original")

    def test_invalid_interval_is_rejected(self):
        for interval in (0, -1, float("nan"), float("inf")):
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                tools.sample_video(self.video, self.destination, interval=interval)


if __name__ == "__main__":
    unittest.main()
