# Wildlitics: open-method development plan

Updated 25 October 2026 after combining the experimental helpers and the 24 October research package. This is the unified implementation plan. The [development index](README.md) connects the code, evidence and status; the [research report](../research/2026-10-24/REPORT.md) remains a dated evidence snapshot.

## Scope and current status

The public Wildlitics repository documents the original Windows application using MegaDetector, SpeciesNet and BioCLIP 2. This development branch contains independent experimental helpers, the research library and a [new native desktop prototype](../../desktop/README.md). The original 2.3.3 source and trained private models remain absent; the new prototype is a separate implementation.

The standalone open-method prototype built in the development session is separate from this repository. It includes BioCLIP 2/FAISS retrieval, a DINOv2 encoder option, GBIF caching, and local GLM-OCR/Qwen adapters. Its last completed software test run passed 76 tests; real DINOv2 and GBIF online/offline checks completed. Real GLM-OCR/Qwen validation and the updated prototype package remain pending after execution-environment interruptions. Those results are not a field-accuracy benchmark, and the separate prototype code is not bundled in this PR.

### Implemented in this change

- An original CSV-to-YOLO/COCO/VOC exporter with per-object labels and multiple species per image.
- Whole-group train/validation/test allocation with reproducible seeds.
- Rejection of unverified labels, conflicting boxes, identical files crossing groups, and declared encounters crossing groups.
- Preservation of reviewed background images as negative examples.
- EXIF-oriented, metadata-stripped prepared images while source files remain unchanged.
- Local-video sampling through FFmpeg, with actual selected-frame timestamps and integrity-checked reuse of completed jobs.
- Tests using generated images and real synthetic-video decoding, plus a GitHub Actions workflow.
- A model-free SpeciesNet review importer supporting legacy image-level results and output format `20261015`, preserving per-box associations and raw decision evidence.
- A separate native desktop prototype with local multi-camera projects, a cancellable official SpeciesNet CLI worker, saved-job resume, per-object human review and descriptive PDF/HTML/CSV reports. Its standard upstream detector is MDv5a; the original application's MDV6/BioCLIP model policy has not been migrated.

See [experimental/data-tools](../../experimental/data-tools/README.md) for commands and the precise input contract. These helpers do not run inference, train models or accept species labels automatically.

## What each source contributes

| Source | Useful method or product idea | Decision for Wildlitics |
|---|---|---|
| [Pustaka Biodiversitas](https://pustaka.biodiversitas.id/en/) | Local projects; integrated taxa, media, references and occurrences; name checks; data-quality reports; publications from one source; local AI/OCR | Adopt provenance, recoverable edits, reference-backed documents and offline-first data management. Keep taxonomic suggestions separate from accepted observation labels. |
| [Kunci Biodiversitas](https://kunci.biodiversitas.id/en/) | User-labelled photo datasets; backbone comparison; train/validation/test tracking; confidence calibration; confusion reports; model deployment; expert review | Build a reproducible training/evaluation module. Adapt to camera-trap species tasks rather than assuming its genus-first orchid workflow transfers unchanged. |
| [From Images to YOLO](https://github.com/DavidBolduc/From_images_to_YOLO_pipeline) | MegaDetector-assisted annotations; SAM2 masks; manual correction gates; annotation export; training orchestration | Implement the generic workflow independently. Preserve individual object labels and split by site/encounter rather than adopting single-class-per-image or image-randomisation assumptions. |
| [WILDLABS .NET/FFmpeg/MegaDetector discussion](https://wildlabs.net/en/discussion/automating-wildlife-monitoring-net-ffmpeg-and-megadetector) | Sample video frames, detect animals, retain timestamps, background jobs and recovery | Add a local-video intake module first. Sampling intervals and detector thresholds are configurable and require recall testing. The article's reported speedup is not a Wildlitics benchmark. |
| [USFWS AI-for-Species](https://github.com/USFWS/AI-for-Species) | Annotation conversions; contextual crops; detector/classifier separation; training/evaluation; deployment formats; sliced inference | Use compatible data formats, comparative crop tests, per-class metrics and optional deployment optimisation. Treat project-specific scripts and local model paths as references, not a ready-made Borneo model. |
| [Wild Animals Species Detection demo](https://github.com/Konda-coder/Wild-Animals-Species-Detection-Using-AI-Techniques-) | Simple upload/capture flow, prediction display and CSV history | Use interface ideas only. Do not replace specialist identification with an unvalidated generic ImageNet classifier, filter top-k into a false absence claim, or call model scores measured accuracy. |
| [Google SpeciesNet](https://github.com/google/cameratrapai), [2024 paper](https://doi.org/10.1049/cvi2.12318), [official announcement](https://blog.google/outreach-initiatives/entrepreneurs/ai-nature-climate-accelerator-nonprofits-speciesnet/) | Detector/crop classification; per-object results; geographic filtering; taxonomic rollup; recoverable runs | Extend the existing integration with explicit schema handling, raw/processed decision provenance and crop-level review. Do not assign legacy image predictions to individual animals. See [SpeciesNet assessment](SPECIESNET.md). |

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

SpeciesNet package 5.0.6 uses per-detection output format `20261015`, while the documented Wildlitics package 5.0.5 has image-level predictions. The experimental importer supports both without inventing object associations. Package/model upgrades and direct database integration still require validation with the real application source.

## Development order and acceptance criteria

### 1. P0: establish the benchmark, review process and survey quality

- Obtain independent expert-labelled animals and reviewed backgrounds, with stable media/object IDs and documented class definitions.
- Hold out sites/deployments and encounters before augmentation. Include day/night, partial or small animals, similar taxa and species outside the local catalogue.
- Use the grouped exporter as preparation support, then audit group meaning and near-duplicates; byte hashes alone cannot establish independence.
- Record raw predictions, failures, reviewer corrections and model versions. Add per-species confusion, day/night results, unresolved rates and random as well as targeted audits.
- Measure detector box precision/recall, species classification on valid crops, and end-to-end species recall including missed animals. Record uncertainty using appropriate independent groups.
- Audit operating intervals, downtime, clock/timezone corrections and processing coverage before ecological analysis.
- Preserve raw and corrected timestamps and record who made each correction.

Acceptance requires a versioned benchmark and auditable survey inputs. Software test success and published study accuracy are separate from Wildlitics field performance. The [training-quality study](https://doi.org/10.1002/rse2.70052), [classification-bias study](https://doi.org/10.1111/2041-210x.70132) and [quality-control protocol](https://doi.org/10.1111/1365-2664.70010) motivate this priority; their limits are recorded in [KEY_EVIDENCE.md](../research/2026-10-24/KEY_EVIDENCE.md).

### 2. P1: integrate the existing dataset, video and review helpers

The helpers and new desktop source are the starting implementation. The new desktop connects camera intake, an official SpeciesNet subprocess and reviewed records in SQLite; integration into the original 2.3.3 application still requires its real source and database/job-queue adapters.

- Verify every export box against its oriented image.
- Include multiple species/objects from a frame and explicitly reviewed background frames.
- Keep all crops and augmented descendants of a parent encounter in the same split.
- Require meaningful site/camera holdout groups; exact-byte checking does not detect every visual duplicate.
- Review missing-class warnings before training.
- Preserve original files and refuse overwriting an existing dataset output.
- Carry exact selected-frame PTS into the observation record. File modification time is not capture time.
- Retain source videos. Sparse sampling is not evidence that an animal was absent.
- Cache completed extraction jobs by source hash and settings; changed/missing cached frames must invalidate reuse.
- Preserve SpeciesNet raw candidates, processed suggestions, decision sources and taxonomic ranks. Legacy image-level suggestions and whole-image classifications must retain their original scope.
- Show candidate/reference evidence, missing metadata and review status, and record reviewer, time and reason for corrections without replacing raw predictions.
- Test recovery, cancellation and dependency installation on the target Windows environment.

Acceptance requires preserved input hashes, correct per-object geometry, recoverable jobs and explicit observation states on representative projects. AI suggestions remain separate from human-confirmed observations.

### 3. P1: compare local adaptation and calibrate review decisions

Compare the existing model policy, frozen BioCLIP 2/DINOv2 local heads and optional SpeciesNet fine-tuning on the same labelled crops and holdouts. The [2026 SpeciesNet fine-tuning study](https://doi.org/10.1016/j.scitotenv.2026.181926) supports a local experiment; its balanced 15-species Australian evaluation does not establish Borneo accuracy or universal data requirements.

- Partition by site/deployment/encounter before augmentation.
- Use training data for fitting, validation data for model choices, and a separate calibration subset for score calibration and review-policy development. Reserve the test set for the final comparison.
- Include day/night imagery, partial animals, difficult taxa, backgrounds and species outside the reference catalogue.
- Measure per-class precision/recall/F1, macro metrics, confusion matrices, unresolved rates and retrieval recall where relevant.
- Report uncertainty and sample/group counts.
- Evaluate unknown-species rejection as its own task; a similarity cutoff is not automatically a validated unknown detector.
- Benchmark elapsed time, throughput, peak memory and review time on the actual target Windows hardware.
- Keep a model version inactive until an explicit activation step and reproducible evaluation.
- Save full classifier logits where available and evaluate reliability, Brier score/log loss and risk/coverage. Do not derive a full-distribution temperature-scaling calculation from top-k-only output or interpret raw FAISS cosine scores as calibrated probabilities.
- Compare expert-review time, corrections and false rare-species positives in addition to average classification metrics.

Acceptance requires a paired comparison with reproducible inputs, class/group counts, calibration provenance and results for priority taxa. The [camera-trap calibration study](https://doi.org/10.1002/rse2.412) informs the experiment. Kunci's [training guide](https://kunci.biodiversitas.id/panduan/en/latih-ai.html) and [orchid research](https://arxiv.org/abs/2609.24064) remain related-task references.

### 4. P1/P2: connect reviewed observations to validated ecological methods

- Export linked deployment, media and observation records against a pinned [Camtrap DP](https://doi.org/10.1002/rse2.374) schema, and provide camtrapR-compatible record tables and camera-operation matrices.
- Distinguish observed presence maps from formal occupancy inference. Build repeated-occasion histories using qualifying detections, operational nondetections and unsampled/inactive or insufficiently processed occasions as distinct states.
- Keep encounter separation, occupancy occasion width and activity sampling units in separate settings and record them with every result.
- Preserve raw activity records and offer justified filter sensitivity comparisons. [Peral et al.](https://doi.org/10.1002/ece3.9408) and [Smith](https://doi.org/10.1007/s00265-024-03544-6) provide conflicting evidence about independence filters; neither a fixed 30-minute nor a fixed 60-minute rule is accepted as universal.
- Add circular overlap and uncertainty, plus incidence-based diversity/sample-coverage comparisons, checking numerical agreement with pinned reference implementations.
- Retain descriptive activity charts and label any additional activity-level estimator with its own assumptions.
- Evaluate a local R adapter or compatible exports using the [camtrapR version 3 workflow](https://doi.org/10.1111/2041-210x.70409), published online on 21 October 2026.
- Introduce single-species occupancy before community models; require fit/autocorrelation checks and, where applicable, convergence and posterior predictive diagnostics.
- Compare AI- and expert-derived ecological outputs, especially rare species and low-precision classes. Promising agreement in [Thornton et al.](https://doi.org/10.1111/1365-2664.70370) is evidence for testing, not automatic permission to skip local validation.
- Defer density/individual-ID outputs until their survey design, movement/geometry or identity inputs and validation are available.

Acceptance requires reproducible exports, documented effort and assumptions, numerical comparison with reference workflows, and an ecological agreement assessment. The [research report](../research/2026-10-24/REPORT.md) and [priority evidence notes](../research/2026-10-24/KEY_EVIDENCE.md) provide the supporting methods and limitations.

### 5. P2: finish the separate prototype and document/taxonomy assistance

- Reproduce the separate prototype's software checks against its current source.
- Complete a real local GLM-OCR transcription and Qwen evidence-table/report smoke test.
- Record model digests, runtime versions and whether the run was local/offline.
- Update setup instructions, source notices and the source ZIP together, retaining the distinction between synthetic checks and wildlife performance.

- GBIF: cache original responses, retrieval dates, accepted-name/synonym suggestions and stale/offline status. Never overwrite reviewed labels automatically. A name-match score is not identification confidence, and GBIF matching does not replace the chosen IUCN reference.
- GLM-OCR: prefer readable PDF text layers, otherwise transcribe rendered pages locally. Preserve source file hash, page number, extracted text and failed-page status.
- Qwen table extraction: require a source quote for every populated value; retain unsupported proposals as review issues, and leave absent fields empty.
- Qwen report drafting: calculate numerical summaries in application code. AI prose is an editable draft tied to those facts, with no invented population/absence/trend conclusions.
- Keep extracted literature records separate from verified camera-trap observations until a reviewer accepts them.

Acceptance requires a working package, actual local-model validation and reproducible commands. Adapters passing fixture-service tests alone do not establish real-model validation. This work can proceed alongside the benchmark when it does not depend on field data.

### 6. P2/P3: optimise after measuring a baseline, then assess new tasks

- Load a model once per worker and reuse existing BioCLIP embeddings where preprocessing and weights match.
- Cache features by image/crop hash, model revision and preprocessing identity.
- Run expensive reference searches or alternate models on cases needing review rather than blindly running every model on every frame.
- Evaluate larger-context crops and optional SAHI slicing for small animals against the same holdout data.
- Compare PyTorch, ONNX Runtime and optional GPU deployment with matched preprocessing and output-equivalence checks.
- Validate FP16/quantisation effects on difficult classes, not just speed.
- Package model weights, class mapping, preprocessing, calibration, provenance, metrics and licence notices together.
- Test copy-paste augmentation or learned sequence/crop context with separate ablations and real mixed-species cases; preserve individual objects and split provenance.
- Evaluate assisted annotation, including optional SAM2, with a human correction gate and checked component terms.
- Treat individual-ID, density, aerial images and audio as separately validated use cases. The [community watch](../research/2026-10-24/COMMUNITY_UPDATES.md) is a source of candidates rather than verified Wildlitics improvements.

Acceptance requires a measured quality/runtime/reviewer-effort tradeoff on the target hardware and a reproducible activation/rollback path.

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
- Google's SpeciesNet repository declares Apache-2.0 for its code. Preserve team attribution and check selected weights/dependencies separately; the new review importer contains no upstream implementation or model weights.
- DINOv2 is Apache-2.0; BioCLIP 2 and FAISS are MIT; GLM-OCR weights are MIT; Qwen2.5-14B-Instruct is Apache-2.0. Confirm the selected versions and preserve upstream notices when distributing.
- The original SAM2 implementation is an optional annotation aid; no SAM2 code/model is bundled here.
- Ultralytics has AGPL/Enterprise licensing options. It is not a mandatory dependency of these helpers and is not automatically introduced into Wildlitics.
- FFmpeg is called as an external executable and not bundled. Its build-specific LGPL/GPL terms still matter if it is redistributed: [official licence page](https://ffmpeg.org/legal.html).

This plan does not select or change the licence of the existing Wildlitics application.

## Release boundary

This change can establish tested data-preparation helpers and a durable development plan. It cannot establish improved wildlife identification, replace the current application, or finish integration without application source and representative labelled field data. Do not merge experimental features into the production application solely because software tests pass.
