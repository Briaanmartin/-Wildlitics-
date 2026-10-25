# Wildlitics combined development workspace

Combined 25 October 2026 on `codex/wildlitics-development-20261024`. [PR #1](https://github.com/Briaanmartin/-Wildlitics-/pull/1) is the combined review for the experimental helpers and the research package originally proposed in [PR #2](https://github.com/Briaanmartin/-Wildlitics-/pull/2). The original branch histories are preserved. Combining the branches does not install features in the desktop application.

## Start here

| Material | Location | Status |
|---|---|---|
| Original application documentation | [Repository README](../../README.md) | Documents prototype 2.3.3; that original desktop source and installer are absent |
| New native desktop prototype | [Desktop 0.1.0](../../desktop/README.md) | Independent implementation: multi-camera projects, official local SpeciesNet inference, review history and descriptive PDF/HTML/CSV reports; original 2.3.3 source remains absent |
| Experimental data tools | [Commands and input formats](../../experimental/data-tools/README.md) | Implemented: reviewed annotation exports, grouped splits, timestamped video sampling and SpeciesNet review import |
| Unified development plan | [OPEN_METHODS_PLAN.md](OPEN_METHODS_PLAN.md) | Current implementation priorities and acceptance criteria |
| Research package | [Research index](../research/2026-10-24/README.md) and [PDF review](../research/2026-10-24/Wildlitics-research-review.pdf) | Dated 24 October 2026; 200 unique journal articles, 100 entries per topic, 28 priority assessments |
| Evidence and caveats | [KEY_EVIDENCE.md](../research/2026-10-24/KEY_EVIDENCE.md) and [methodology](../research/2026-10-24/METHODOLOGY.md) | Findings are distinguished from proposals; metadata screening is distinguished from closer source assessment |
| SpeciesNet compatibility | [SPECIESNET.md](SPECIESNET.md) | Legacy image-level and `20261015` per-detection output handled without inventing object associations |

The research folder remains an unchanged snapshot with its original checksums. The unified plan is the current work queue; publication dates and historical implementation statements in the research report describe the 24 October review. The new desktop source is separate from the original application described by that snapshot.

## How the two work streams connect

| Existing helper | Research-supported next step | Boundary |
|---|---|---|
| Reviewed CSV to YOLO/COCO/VOC; whole-group splitting | Build an expert-labelled benchmark, check class coverage and prevent site/encounter leakage | Export validity does not establish label correctness or field accuracy |
| FFmpeg sampling with actual frame offsets and cache integrity | Integrate camera/deployment timing and measure sampling recall on brief appearances | Sparse sampling does not establish animal absence |
| SpeciesNet review import preserving raw/processed decisions and scope | Add confusion/rare-species audits, calibration and candidate review | The importer runs no inference and accepts no labels automatically |
| Source register and research bibliography | Compare local heads, SpeciesNet fine-tuning and ecological methods on matched field data | The bibliography is evidence for experiments, not a completed accuracy improvement |

## Work queue

1. **P0 — benchmark, review and survey quality:** obtain independent expert labels, retain model errors/failures, audit difficult classes and operating effort, and establish site/encounter holdouts.
2. **P1 — connect the helpers:** adapt the real application's database and job queue, retaining original media, timestamps, processing states and review history.
3. **P1 — model comparison and calibration:** evaluate the existing model policy, local BioCLIP/DINOv2 heads and optional SpeciesNet fine-tuning using matched splits and separate calibration data.
4. **P1/P2 — ecological analysis:** add validated Camtrap DP/camtrapR exports, activity sensitivity and uncertainty, coverage-based diversity, then occupancy models with diagnostics.
5. **P2 — document and taxonomy assistance:** finish real GLM-OCR/Qwen validation and packaging of the separate local prototype, and preserve evidence and human review in any application integration.
6. **P2/P3 — optimisation and new tasks:** test context, augmentation, deployment formats and optional individual-ID/audio/aerial use cases after an appropriate baseline is established.

Detailed inputs, evidence and acceptance gates are in the [unified plan](OPEN_METHODS_PLAN.md). The existing suite has 39 software tests using generated images, synthetic SpeciesNet results and actual FFmpeg decoding; those checks do not measure wildlife recognition.

## Local checks

```bash
python -m pip install -r experimental/data-tools/requirements.txt
python -m unittest discover -s experimental/data-tools/tests -v
```

FFmpeg and ffprobe must be on PATH for video checks. Research integrity can be checked against `docs/research/2026-10-24/CHECKSUMS.sha256`; the bibliography's recorded counts are in [validation.json](../research/2026-10-24/validation.json). No model download or field data is needed for these checks.
