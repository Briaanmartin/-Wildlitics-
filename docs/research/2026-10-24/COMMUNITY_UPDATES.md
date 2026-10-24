# WILDLABS and technical discussion watch

Checked 24 October 2026. These are community/vendor/project reports, distinct from peer-reviewed evidence. No posts or messages were sent. Dates refer to the named post rather than proof of the last software release.

## 2026-10-20 — Introducing Kaleidoscope BirdNET

Source: WILDLABS / Wildlife Acoustics. [Read post](https://wildlabs.net/en/article/introducing-kaleidoscoper-birdnet).

**Evidence type:** Vendor announcement.

**Reported:** An integrated acoustic identification and review workflow.

**Wildlitics proposal:** A useful future audio-review pattern: retain recording, alternatives and reviewer decisions. Check component licences and local species performance before an optional audio module.

**Priority:** Later; outside current photo scope.

## 2026-10-15 — WILDLABS AWARDS 2026: AudioMoth Edge

Source: WILDLABS / Open Acoustic Devices. [Read post](https://wildlabs.net/en/article/wildlabs-awards-2026-audiomoth-edge).

**Evidence type:** Project-development announcement.

**Reported:** A project developing hardware and software for on-device sound recognition.

**Wildlitics proposal:** Track constrained-device requirements, but do not treat planned hardware as a completed camera-trap identification upgrade.

**Priority:** Watch.

## 2026-10-14 — Introducing DroneMegaDetector

Source: WILDLABS / model author. [Read post](https://wildlabs.net/en/article/introducing-dronemegadetector).

**Evidence type:** Preprint and author announcement; under review as stated in post.

**Reported:** A drone-image detector with tiled inference, code and weights; a preprint is linked.

**Wildlitics proposal:** Consider only for future aerial imagery. Benchmark camera-trap and aerial domains separately; do not substitute it for the terrestrial baseline.

**Priority:** Watch; adjacent domain.

## 2026-10-08 — TwigaTools: an open intelligence hub

Source: WILDLABS / Giraffe Conservation Foundation. [Read post](https://wildlabs.net/en/article/twigatools-open-intelligence-hub-giraffe-conservation-and-other-wildlife).

**Evidence type:** Project announcement.

**Reported:** No-code summaries and connectors layered over existing monitoring platforms, with connectivity and permissions considered.

**Wildlitics proposal:** Use modular imports/exports and reproducible summaries; retain platform permissions and offline caches if connectors are added.

**Priority:** Useful architecture reference.

## 2026-10-07 — Speeding-up AI training

Source: WILDLABS / David Bolduc. [Read post](https://wildlabs.net/en/article/speeding-ai-training).

**Evidence type:** Author workflow report.

**Reported:** Timelapse, MegaDetector and SAM2 help prepare YOLO training data. A comment dated 12 October points to Annotator-Pro.

**Wildlitics proposal:** Extend assisted annotation after checking licences, preserve per-object labels and keep manual review and site grouping. The single-class-per-image assumption needs explicit rejection for mixed scenes.

**Priority:** Near-term annotation workflow.

## 2026-09-25 — Automating wildlife monitoring with .NET, FFmpeg and MegaDetector

Source: WILDLABS / workflow author. [Read post](https://wildlabs.net/en/discussion/automating-wildlife-monitoring-net-ffmpeg-and-megadetector).

**Evidence type:** Community workflow report.

**Reported:** A live-camera intake and frame-sampling workflow with author-reported runtime improvements.

**Wildlitics proposal:** Use timestamped local video intake, recoverable jobs and sampling-recall evaluation. No local speed claim can be transferred from this post.

**Priority:** Near-term video intake.

## 2026-08-28 — Wildlens

Source: WILDLABS / project author. [Read post](https://wildlabs.net/en/article/wildlens).

**Evidence type:** Personal-project report without independently assessed benchmark.

**Reported:** The author reports a livestream species detector trained with iNaturalist imagery.

**Wildlitics proposal:** Use as an example of an intake/demo flow; verify training-image domain, split design, class coverage and code availability before considering the model.

**Priority:** Low; evidence incomplete.

## 2026-04-23 — SpeciesNet Studio: self-hosted review UI

Source: Microsoft Biodiversity GitHub discussion. [Read post](https://github.com/microsoft/Biodiversity/discussions/631).

**Evidence type:** Author software announcement.

**Reported:** A contributor presents a self-hosted SpeciesNet review interface.

**Wildlitics proposal:** Inspect review organisation and alternative-candidate presentation as product references; check code licence before reuse.

**Priority:** Review-interface reference.

## 2026-01-28 — Machine Learning for Camera Trap Footage

Source: WILDLABS discussion / practitioners. [Read post](https://wildlabs.net/en/discussion/machine-learning-camera-trap-footage).

**Evidence type:** Practitioner discussion.

**Reported:** Contributors distinguish blank filtering, species identification and individual re-identification, and emphasise review ergonomics.

**Wildlitics proposal:** Measure reviewer time and correction burden, and make individual-ID a separately validated task.

**Priority:** High workflow relevance.

## 2025-12-11 — SpeciesNet Bugs on Addax AI Windows

Source: AddaxAI community; discussion continued 18 December 2025. [Read post](https://forum.addaxai.com/t/speciesnet-bugs-on-addax-ai-windows/251).

**Evidence type:** User troubleshooting with maintainer replies.

**Reported:** The thread discusses NumPy/PyTorch compatibility and a Windows process issue; the exact root cause was not established.

**Wildlitics proposal:** Add Windows installation/inference/cancellation checks and pinned environment diagnostics. Do not prescribe a blanket NumPy downgrade from this anecdote.

**Priority:** High reliability relevance.

## Official documentation and additional foundations

The references below are outside the journal quota. Their inclusion is not a claim that their code or models have been integrated.

- [CameraSweet official tools](https://smallcats.org/camerasweet/) — Official software documentation. Reference for clock corrections, camera groups, occupancy matrices and independent-picture counts; no application code was copied.

- [MegaDetector official documentation](https://microsoft.github.io/MegaDetector/) — Official software documentation. Check model variants, inference options, supported domains and version-specific licensing. Wildlitics already documents MDV6.

- [SpeciesNet official repository](https://github.com/google/cameratrapai) — Official software documentation. Check package/model identities, preprocessing, format migration and classifier-only reuse of saved detections.

- [Camtrap DP standard](https://camtrap-dp.tdwg.org/) — Official data standard. Pin a schema version and validate deployment, media and observation exports.

- [camtrapR CRAN package](https://cran.r-project.org/package=camtrapR) — Official software release documentation. Check current version and local R integration; code and analytical defaults require explicit version tracking.

- [Annotator-Pro](https://github.com/ChaimElchik/Annotator-Pro) — Author repository; linked from WILDLABS comment. Annotation UI and assistance reference. Assess actual licence and dependencies before reuse.

- [BioCLIP: A Vision Foundation Model for the Tree of Life](https://github.com/Imageomics/bioclip) — CVPR 2024 conference paper and official implementation; not counted in journal quota. A biological representation baseline; biological photos and camera-trap images have different distributions.

- [BioCLIP 2: Emergent Properties from Scaling Hierarchical Contrastive Learning](https://imageomics.github.io/bioclip-2/) — NeurIPS 2025 conference paper; not counted in journal quota. Supports the existing BioCLIP 2 feature option. Benchmark local identification and retrieval separately.

- [DINOv2 official implementation](https://github.com/facebookresearch/dinov2) — Official model documentation; outside the DOI-verified journal quota. Candidate encoder for a local classifier/retrieval comparison; its inclusion does not establish a local accuracy gain.

- [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html) — ICML 2017 conference paper; not counted in journal quota. Foundation for post-hoc calibration, complemented here by a camera-trap-specific calibration paper.

- [Estimating species overlap: author resources](https://martinridout.github.io/webfiles/overlap/overlap.html) — Author method/software documentation. Reference implementation and interpretation for circular temporal overlap and uncertainty.
