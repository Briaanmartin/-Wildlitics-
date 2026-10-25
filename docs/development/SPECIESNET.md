# SpeciesNet: decisions for Wildlitics

Reviewed 24 October 2026 against Google's repository commit `b9aa454d2f31ee74d71c3b162f4ba6c834e93322`, its published package metadata, the 2024 paper and Google's announcement.

## What is already present

Wildlitics' main README already documents SpeciesNet classifier **4.0.3a** with Python package **5.0.5**, alongside MegaDetector MDV6-yolov10-c and BioCLIP 2. The classifier-model version and Python-package version are different identifiers. This research does not constitute a new SpeciesNet installation or a production-app upgrade.

The [official repository](https://github.com/google/cameratrapai) describes an EfficientNetV2-M species classifier and detector/classifier cascade. MegaDetector locates objects; SpeciesNet provides taxonomic suggestions. Keep those roles and scores distinct.

## Findings that change development

1. **Handle the output migration explicitly.** [PyPI package 5.0.6](https://pypi.org/project/speciesnet/5.0.6/) was published 16 October 2026. The inspected current repository documents output format `20261015`: each classified detection carries `raw_classifications` and `processed_classification`. The published 5.0.5 wheel documents one image-level `classifications`/`prediction` record plus separate detections. Do not assume an image prediction identifies every animal in a multi-animal frame, or infer an association from list order.
2. **Retain raw and processed results.** Raw candidates precede geographic filtering. The processed class may result from detector decisions, geographic filtering or taxonomic rollup. Preserve its decision source and actual rank. A family/genus result remains unresolved at species level, even if a local checklist contains only one plausible species.
3. **Keep whole-image classifications separate.** In format `20261015`, category `0` is a whole-image pseudo-detection; its confidence of 1.0 is a placeholder, not evidence of perfect object detection. Its species suggestion cannot be assigned to every actual MegaDetector box.
4. **Reuse the existing detector.** Google's [advanced documentation](https://github.com/google/cameratrapai/blob/b9aa454d2f31ee74d71c3b162f4ba6c834e93322/advanced_topics.md#running-each-component-separately) describes classifier-only and ensemble-only stages using saved detections. Test that route against Wildlitics' chosen MDV6 output before introducing a second detector. Record detector identity, coordinate convention, image orientation and crop preprocessing together.
5. **Make geography auditable.** Use the actual project country, such as `IDN` for Indonesia or `MYS` for Malaysia. Do not treat Borneo as one country or assume all local administrative divisions have filtering rules. Preserve supplied/resolved location and raw candidates; offer a comparison with geographic filtering disabled when reviewing unexpected records. The new importer preserves geography but does not apply or reconstruct filtering rules.
6. **Pin the complete run.** Keep package version, model identifier/revision, preprocessing, detector settings, classification limits, geographic configuration and source-media hashes. Newer taxonomy/geofencing or a new package release is not evidence of improved local recognition.

## What the paper establishes

Gadot, Istrate, Kim, Morris, Beery, Birch and Ahumada, [*To crop or not to crop: Comparing whole-image and cropped classification on a large dataset of camera trap images*](https://doi.org/10.1049/cvi2.12318), IET Computer Vision 18(8), 1193–1208 (2024), compares detector-based cropping with whole-image classification across three datasets. Cropping improved macro-F1 in those experiments; the authors did not evaluate multi-species images or establish benefits for every animal size or ecosystem.

For Wildlitics, compare its current crop pipeline against alternatives on the same independently labelled site/encounter holdout. Measure per-class performance, missed animals, unresolved outcomes and runtime. Do not transfer the paper's improvement percentage to Wildlitics, or assume adding whole-image inference to every frame improves the crop baseline.

Google's [3 March 2025 announcement](https://blog.google/outreach-initiatives/entrepreneurs/ai-nature-climate-accelerator-nonprofits-speciesnet/) establishes the open-source release and Wildlife Insights context; it is not a Wildlitics benchmark. Credit Google's Camera Traps AI team, the paper's authors, Wildlife Insights collaborators and the relevant detector developers. The supplied quotation's claim about one person's share of code is not independently verified and does not alter the team attribution.

## Implemented now: a model-free review importer

[speciesnet_review.py](../../experimental/data-tools/speciesnet_review.py) reads legacy image-level output and explicitly versioned `20261015` output:

- Keeps individual boxes, model version, raw candidates, final class, decision source and original records.
- Retains older image-level results in a separate unassociated field, with no fabricated per-object labels.
- Marks geographic filtering, rollup, non-species labels and changed top candidates for review.
- Separates missing detections, reported empty detections and component failures.
- Keeps all suggestions unverified and records the input JSON's SHA-256.
- Rejects unknown/mixed formats, invalid scores/boxes and overwriting an existing output.

This is an original schema adapter; it does not copy Google's implementation, run SpeciesNet, read source photos, train models, measure wildlife accuracy or integrate with Wildlitics' database. Tests use synthetic schema fixtures and exercise the real CLI. Upstream model execution and Windows integration remain to be validated.

## Reuse and distribution

The inspected Google repository declares Apache-2.0 for its code. Selected model weights and every dependency require their own version-specific review; the repository licence does not automatically cover the detector stack or all external data. This change bundles no upstream implementation or model weights and does not change Wildlitics' application licence.
