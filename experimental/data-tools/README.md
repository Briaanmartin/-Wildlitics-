# Experimental Wildlitics data tools

Original, independent helpers for preparing reviewed wildlife datasets and sampling local videos. These are experimental development tools, not the source or an update of the installed Wildlitics application.

## Included

- CSV annotations to YOLO detection labels, COCO detection JSON and Pascal VOC XML.
- Multiple labelled animals/species per image.
- Explicitly reviewed background images retained as negatives.
- Deterministic splits of whole declared groups, never random individual frames.
- Checks for unverified rows, duplicate/conflicting boxes, identical images crossing groups and declared encounters crossing groups.
- EXIF-oriented prepared image copies; source files remain unchanged.
- FFmpeg sampling with actual selected-frame PTS and integrity-checked reuse of completed jobs.

No detector, classifier, training job, account login or cloud upload is run by these helpers. No model weights or third-party application source are bundled.

## Install

Python 3.10+ and Pillow are required:

```bash
python -m pip install -r experimental/data-tools/requirements.txt
```

Video sampling also needs FFmpeg and ffprobe on PATH. The helper invokes the installed executable; it does not install or bundle FFmpeg. Its licence depends on the selected build: [official terms](https://ffmpeg.org/legal.html).

## Prepare reviewed annotations

Copy [annotations.template.csv](examples/annotations.template.csv). Replace the paths and labels, record your photo permissions and reviewer, and set verified=true only after review.

Required columns:

| Column | Meaning |
|---|---|
| image_path | Local source image; relative to the CSV or absolute |
| scientific_name | Human-reviewed class/taxon label; not automatically checked against a taxonomy |
| verified | true, yes or 1 after review |
| verified_by | Reviewer identifier |
| license | Actual photo permission/licence, e.g. user-owned |
| group_id | Meaningful site/camera holdout group |
| event_id | Optional globally unique encounter identifier |
| bbox_x, bbox_y, bbox_w, bbox_h | Animal box in normalised xywh, after EXIF orientation |
| is_background | true only for a reviewed background image with no animal boxes |

Use one row per animal box. A frame containing two different species gets two rows with separate boxes. For a reviewed background image, scientific_name and all bbox fields must be empty.

The template intentionally contains unverified rows. It is not ready-to-train data. A CSV declaration records human review; software cannot establish the scientific correctness of a label or the validity of a claimed photo licence.

## Export a dataset

```bash
python experimental/data-tools/data_tools.py export-dataset --manifest annotations.csv --output prepared-v1 --seed 123 --val-fraction 0.15 --test-fraction 0.15
```

At least three independent groups are required when all three splits are requested. The fractions approximate group proportions, not exact image or object proportions. Class coverage is not guaranteed; review missing-class warnings.

Outputs:

- images/train, images/val, images/test: oriented prepared copies.
- labels/<split>: zero-based class IDs and normalised YOLO cx/cy/w/h labels.
- annotations/<split>.coco.json: one-based category IDs and absolute-pixel xywh.
- voc/<split>: class names and one-based inclusive pixel bounds.
- class_map.json: the class-to-ID mapping.
- data.yaml: a dataset configuration using the absolute output path.
- dataset_manifest.json: source/prepared hashes, groups, split assignment, provenance, counts and warnings.

Original files are never moved or edited. JPEG inputs are re-encoded at quality 95; other supported image inputs are prepared as PNG. Metadata is stripped from the prepared copies. Existing output directories are refused. If you move the dataset, update the path in data.yaml.

### Holdout limits

All appearances of an identical source-file hash must use the same group_id, and a declared event_id cannot cross groups. This does not detect every near-duplicate or related encounter. Choose site/camera groups that prevent repeated backgrounds or adjacent camera-trap frames leaking between splits. Augmentation must occur only after assigning groups, and augmented descendants must retain their parent's split.

Reviewed background labels are preserved as negative examples; detector failures are not automatically converted into backgrounds.

## Sample local videos

```bash
python experimental/data-tools/data_tools.py sample-video --video recording.mp4 --output sampled-recording --interval 2 --timeout 600
```

The interval is a configurable minimum gap between selected decoded frames. For a 5 FPS source and a 0.5-second interval, selection can occur at 0.0, 0.6, 1.2 and 1.8 seconds. The manifest records those actual selected timestamps rather than inventing nominal 0.5-second offsets.

Outputs are frames/*.jpg and video_manifest.json. Timestamps are decoded frame PTS after FFmpeg -copyts -start_at_zero; they are not a camera's UTC capture timestamps. Link them to recording/deployment timing explicitly.

Running the same completed job with the same source hash and interval reuses it only after checking frame hashes. A different source/interval, missing frame or modified cached frame requires a new output directory. An interrupted extraction is restarted, not resumed midway through a video.

Sampling can miss brief appearances. No animal detector is run by this command, no source video is deleted, and an unselected frame is not evidence of ecological absence. Feed reviewed/extracted frames into the existing detector separately.

## Tests

```bash
python -m unittest discover -s experimental/data-tools/tests -v
```

Tests use generated images and an actual two-second synthetic video decoded with FFmpeg. They check all three coordinate formats, multiple species, background examples, group integrity, metadata/orientation handling, original-file preservation, frame timestamps and completed-job reuse. These are software tests, not wildlife accuracy or runtime benchmarks.

A GitHub Actions workflow runs the checks on Python 3.12/Linux. Windows and application-database/job-queue integration still need testing.

## Source decisions and future work

The [development plan](../../docs/development/OPEN_METHODS_PLAN.md) records all six sources supplied by the developer and the subsequent training, review, document and deployment work.

These helpers use generic format definitions and FFmpeg invocation, implemented independently. They do not copy code from Pustaka, Kunci or the unlicensed demonstration repositories. They do not select or change the licence of the existing Wildlitics application. Source photographs and external packages retain their own terms.
