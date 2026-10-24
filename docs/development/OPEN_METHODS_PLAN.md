# Wildlitics: open-method development plan

Reviewed 24 October 2026. This document records the sources supplied by the developer, the decisions taken from them, and the boundary between implemented helpers and future application work.

## Scope and current status

The public Wildlitics repository documents a Windows application using MegaDetector, SpeciesNet and BioCLIP 2. It does not contain the application source or trained private models. This change adds independent experimental helpers; it does not claim to update the installed Wildlitics application.

The standalone open-method prototype built in the development session is separate from this repository. It includes BioCLIP 2/FAISS retrieval, a DINOv2 encoder option, GBIF caching, and local GLM-OCR/Qwen adapters. Its last completed software test run passed 76 tests; real DINOv2 and GBIF online/offline checks completed. Real GLM-OCR/Qwen validation and the updated prototype package remain pending after execution-environment interruptions. Those results are not a field-accuracy benchmark, and the separate prototype code is not bundled in this PR.

### Implemented in this change

- An original CSV-to-YOLO/COCO/VOC exporter with per-object labels and multiple species per image.
- Whole-group train/validation/test allocation with reproducible seeds.
- Rejection of unverified labels, conflicting boxes, identical files crossing groups, and declared encounters crossing groups.
- Preservation of reviewed background images as negative examples.
- EXIF-oriented, metadata-stripped prepared images while source files remain unchanged.
- Local-video sampling through FFmpeg, with actual selected-frame timestamps and integrity-checked reuse of completed jobs.
- Tests using generated images and real synthetic-video decoding, plus a GitHub Actions workflow.

See [experimental/data-tools](../../experimental/data-tools/README.md) for commands and the precise input contract. None of these helpers runs a detector, trains a model or assigns species automatically.

## What each source contributes

| Source | Useful method or product idea | Decision for Wildlitics |
|---|---|---|
| [Pustaka Biodiversitas](https://pustaka.biodiversitas.id/en/) | Local projects; integrated taxa, media, references and occurrences; name checks; data-quality reports; publications from one source; local AI/OCR | Adopt provenance, recoverable edits, reference-backed documents and offline-first data management. Keep taxonomic suggestions separate from accepted observation labels. |
| [Kunci Biodiversitas](https://kunci.biodiversitas.id/en/) | User-labelled photo datasets; backbone comparison; train/validation/test tracking; confidence calibration; confusion reports; model deployment; expert review | Build a reproducible training/evaluation module. Adapt to camera-trap species tasks rather than assuming its genus-first orchid workflow transfers unchanged. |
| [From Images to YOLO](https://github.com/DavidBolduc/From_images_to_YOLO_pipeline) | MegaDetector-assisted annotations; SAM2 masks; manual correction gates; annotation export; training orchestration | Implement the generic workflow independently. Preserve individual object labels and split by site/encounter rather than adopting single-class-per-image or image-randomisation assumptions. |
| [WILDLABS .NET/FFmpeg/MegaDetector discussion](https://wildlabs.net/en/discussion/automating-wildlife-monitoring-net-ffmpeg-and-megadetector) | Sample video frames, detect animals, retain timestamps, background jobs and recovery | Add a local-video intake module first. Sampling intervals and detector thresholds are configurable and require recall testing. The article's reported speedup is not a Wildlitics benchmark. |
| [USFWS AI-for-Species](https://github.com/USFWS/AI-for-Species) | Annotation conversions; contextual crops; detector/classifier separation; training/evaluation; deployment formats; sliced inference | Use compatible data formats, comparative crop tests, per-class metrics and optional deployment optimisation. Treat project-specific scripts and local model paths as references, not a ready-made Borneo model. |
| [Wild Animals Species Detection demo](https://github.com/Konda-coder/Wild-Animals-Species-Detection-Using-AI-Techniques-) | Simple upload/capture flow, prediction display and CSV history | Use interface ideas only. Do not replace specialist identification with an unvalidated generic ImageNet classifier, filter top-k into a false absence claim, or call model scores measured accuracy. |

The source register provides machine-readable links and licence observations: [source-registry.json](source-registry.json).

## Target application workflow

1. Import local photos and videos with camera/deployment identifiers and original timestamps.
2. Sample videos if requested; link each extracted frame to its source video and decoded timestamp.
3. Run the existing detector, retaining each animal box separately.
4. Produce species suggestions using the current model policy; optionally compare BioCLIP 2, DINOv2 and verified-reference retrieval.
5. Present the original crop, source frame, reference evidence, model/version and each score type to a reviewer.
6. Store human corrections as an audit trail without replacing the raw predictions.
7. Export reviewed observations and grouped training datasets.
8. Train and validate optional local models on appropriate holdout data.
9. Generate reproducible analyses and reports from reviewed records and explicit survey metadata.

Detector confidence, classifier probability and cosine similarity remain separate fields. A locally restricted species list must not force an identity. Missing detections, failed processing, unresolved species and reviewed absence are distinct states.

## Development order and acceptance criteria

### 1. Finish the standalone prototype package

- Reproduce the software checks against its current source.
- Complete a real local GLM-OCR transcription and Qwen evidence-table/report smoke test.
- Record model digests, runtime versions and whether the run was local/offline.
- Update setup instructions, source notices and the source ZIP together.
- Keep synthetic smoke tests clearly separated from wildlife performance.

Completion requires a working package and reproducible commands; adapters passing mocked service tests alone are insufficient for a claim of real-model validation.

### 2. Integrate dataset preparation and video intake

The helpers in this change are the starting implementation.

- Verify every export box against its oriented image.
- Include multiple species/objects from a frame and explicitly reviewed background frames.
- Keep all crops and augmented descendants of a parent encounter in the same split.
- Require meaningful site/camera holdout groups; exact-byte checking does not detect every visual duplicate.
- Review missing-class warnings before training.
- Preserve original files and refuse overwriting an existing dataset output.
- Carry exact selected-frame PTS into the observation record. File modification time is not capture time.
- Retain source videos. Sparse sampling is not evidence that an animal was absent.
- Cache completed extraction jobs by source hash and settings; changed/missing cached frames must invalidate reuse.

Application integration requires the real Wildlitics source and a tested adapter for its database and job queue.

### 3. Add training and model comparison

Start with a frozen BioCLIP 2 or DINOv2 encoder plus a small trainable classifier head. Compare backbones on the same labelled crops. Full fine-tuning is optional after the smaller baseline is evaluated.

- Partition by site/deployment/encounter before augmentation.
- Use training data for fitting; validation data for hyperparameters, calibration and review thresholds; reserve the test set for the final comparison.
- Include day/night imagery, partial animals, difficult taxa, backgrounds and species outside the reference catalogue.
- Measure per-class precision/recall/F1, macro metrics, confusion matrices, unresolved rates and retrieval recall where relevant.
- Report uncertainty and sample/group counts.
- Evaluate unknown-species rejection as its own task; a similarity cutoff is not automatically a validated unknown detector.
- Benchmark elapsed time, throughput, peak memory and review time on the actual target Windows hardware.
- Keep a model version inactive until an explicit activation step and reproducible evaluation.

Kunci's [training guide](https://kunci.biodiversitas.id/panduan/en/latih-ai.html) and the [orchid research paper](https://arxiv.org/abs/2609.24064) describe related methods, not evidence of Borneo camera-trap accuracy.

### 4. Complete species-data and document assistance

- GBIF: cache original responses, retrieval dates, accepted-name/synonym suggestions and stale/offline status. Never overwrite reviewed labels automatically. A name-match score is not identification confidence, and GBIF matching does not replace the chosen IUCN reference.
- GLM-OCR: prefer readable PDF text layers, otherwise transcribe rendered pages locally. Preserve source file hash, page number, extracted text and failed-page status.
- Qwen table extraction: require a source quote for every populated value; retain unsupported proposals as review issues, and leave absent fields empty.
- Qwen report drafting: calculate numerical summaries in application code. AI prose is an editable draft tied to those facts, with no invented population/absence/trend conclusions.
- Keep extracted literature records separate from verified camera-trap observations until a reviewer accepts them.

### 5. Improve review and data quality

- Show model version, crop association, candidate names and reference-photo credits.
- Provide filters for unresolved/conflicting predictions and missing metadata.
- Preserve raw predictions when users correct labels.
- Record reviewer, timestamp and reason for a change.
- Check names, duplicate media, missing coordinates/dates and incomplete photo credits.
- Export model suggestions and human-confirmed observations as distinct statuses.
- Count reviewed encounters according to documented rules; prediction counts are not individual animals.

### 6. Optimise only after a baseline is measured

- Load a model once per worker and reuse existing BioCLIP embeddings where preprocessing and weights match.
- Cache features by image/crop hash, model revision and preprocessing identity.
- Run expensive reference searches or alternate models on cases needing review rather than blindly running every model on every frame.
- Evaluate larger-context crops and optional SAHI slicing for small animals against the same holdout data.
- Compare PyTorch, ONNX Runtime and optional GPU deployment with matched preprocessing and output-equivalence checks.
- Validate FP16/quantisation effects on difficult classes, not just speed.
- Package model weights, class mapping, preprocessing, calibration, provenance, metrics and licence notices together.

## Shared records

| Record | Essential fields |
|---|---|
| Media | Stable ID, SHA-256, source path, camera/deployment/site, capture timestamp/timezone, video source and frame offset, dimensions/orientation |
| Detection | Media ID, box coordinates and convention, detector/version, detector score, processing status |
| Observation | Detection ID, original taxon label/rank, model suggestions, human label, verification state, reviewer and change history |
| Reference feature | Source/crop hash, reviewed label, photo licence/credit, backbone revision, preprocessing identity, vector/index version |
| Literature value | Source hash, page/chunk, extracted text, field value, source quote, issues and review state |
| Taxonomy suggestion | Original name, requested source, raw response, matched/accepted names, retrieval time, cache state and review state |
| Model run | Data/split fingerprints, seed, configuration, hardware/software, weights, metrics, calibration and activation state |
| Job | Input/configuration hash, stage, progress, completion/error state, outputs and resumability information |

Local source paths, thumbnails and locations can be sensitive. No research datasets, coordinates or trained private models belong in this public documentation repository by default.

## Attribution and reuse decisions

The additions in this change are original implementations of common annotation formats, grouping rules and FFmpeg invocation. No commercial-app code or code from repositories without a clear licence has been copied.

- Pustaka/Kunci are product/workflow references; their application code, player, assets and sample orchid data are not included.
- The DavidBolduc and Konda-coder repositories had no explicit licence in the inspected snapshots; do not assume permission to copy their code.
- USFWS declares CC0 for its repository, but acknowledges third-party sources. Dependencies and individual borrowed components retain their own terms.
- DINOv2 is Apache-2.0; BioCLIP 2 and FAISS are MIT; GLM-OCR weights are MIT; Qwen2.5-14B-Instruct is Apache-2.0. Confirm the selected versions and preserve upstream notices when distributing.
- The original SAM2 implementation is an optional annotation aid; no SAM2 code/model is bundled here.
- Ultralytics has AGPL/Enterprise licensing options. It is not a mandatory dependency of these helpers and is not automatically introduced into Wildlitics.
- FFmpeg is called as an external executable and not bundled. Its build-specific LGPL/GPL terms still matter if it is redistributed: [official licence page](https://ffmpeg.org/legal.html).

This plan does not select or change the licence of the existing Wildlitics application.

## Release boundary

This change can establish tested data-preparation helpers and a durable development plan. It cannot establish improved wildlife identification, replace the current application, or finish integration without application source and representative labelled field data. Do not merge experimental features into the production application solely because software tests pass.
