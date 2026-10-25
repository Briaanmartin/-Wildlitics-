# Wildlitics research review and development priorities

Research cutoff: **24 October 2026**. Prepared for Brian Martin.

The next useful development step is to establish a trustworthy local benchmark, improve the training/review data, and connect identification quality to ecological inference. Adding more backbones can then be tested against that baseline. The literature supports several promising methods, but it does not establish Wildlitics' present accuracy or guarantee that any one change will improve it.

## Research library

| Requested topic | Journal articles in the topic list |
|---|---:|
| 1. Enhancing identification models | 100 |
| 2. Species data analysis and camera-trap workflows | 100 |
| 3. Detection, accuracy and reducing confusion | 100 |

There are **200 unique journal articles and 300 topic placements**. Papers can appear in more than one topic, especially topics 1 and 3. Every included DOI was checked against publisher-deposited Crossref metadata. This is 100 articles per topic, not 100 different journal titles or 300 different papers.

This is a targeted research review, not a systematic review or a full-text reading of 200 papers. All entries were screened by title and bibliographic metadata; 28 priority sources received closer abstract or accessible-content assessment for the synthesis. Other entries are a reading library, with relevance questions rather than unverified findings. Preprints, conference papers, software documentation and community posts are identified separately and excluded from the journal counts. See [METHODOLOGY.md](METHODOLOGY.md) and [KEY_EVIDENCE.md](KEY_EVIDENCE.md).

The searchable [library](index.html), CSV and RIS bibliography provide the full references. The RIS file can be imported into a reference manager such as Zotero. No paywalled full texts or copied abstracts are bundled.

## What the current Wildlitics work already contains

The public README describes version 2.3.3 using MDV6, SpeciesNet 4.0.3a/package 5.0.5 and BioCLIP 2, with human review, camera/deployment metadata, offline maps, descriptive activity reports and optional local BioCLIP-head training. Its public repository does not contain the desktop application's source code.

Draft PR #1 adds experimental annotation exports, grouped dataset splits, timestamped video sampling and a SpeciesNet review importer. Those are separately tested helpers, not an installed-app update. The separate open-method prototype contains retrieval/DINOv2 and document/taxonomy adapters, with real local GLM-OCR/Qwen validation still pending. This research review changes no application models or statistical outputs.

## 1. Enhancing the identification models

**Start with local adaptation of the existing models.** A 2026 study comparing global, local and fine-tuned classifiers favoured fine-tuned SpeciesNet on a balanced set of 15 common Australian rainforest species, including withheld-camera tests. That is a strong reason to test the approach locally, with explicit rare-species evaluation. It is not evidence that its reported performance or sample-size plateau transfers to Borneo. [Rajmohan et al.](https://doi.org/10.1016/j.scitotenv.2026.181926)

Compare the current Wildlitics model policy with: the existing frozen BioCLIP head; a frozen DINOv2 head; and a modest SpeciesNet fine-tune. Use the same reviewed animal crops, class definitions, held-out sites and test encounters. Keep reference-photo retrieval as a separately evaluated source of evidence. A correct nearest reference and a correct closed-set classification are different tasks.

**Improve label quality and representation of difficult classes.** The 2026 training-quality study found that species-level occupancy and activity could suffer for rare or similar taxa even when community richness appeared stable. This argues for label audits, night images, partial views and confusing taxa before an extensive architecture sweep. [Bevan et al.](https://doi.org/10.1002/rse2.70052)

**Use human review to acquire useful new data.** An active-learning queue should combine uncertainty, model disagreement and coverage of different sites, illumination and rare species. An uncertainty-only queue can keep selecting almost identical frames. Preserve a representative expert-labelled audit sample as well as the actively selected corrections. The camera-trap active-learning literature supports the approach; its reported labelling savings require local verification. [Norouzzadeh et al.](https://doi.org/10.1111/2041-210x.13504)

**Treat augmentation and sequence models as experiments.** Background-diverse copy-paste augmentation and attention over related animal crops are promising additions. Apply augmentation only within training partitions, retain source provenance, and test real mixed-species encounters. A sequence model should preserve separate animals and allow multiple species. [Copy-paste study](https://doi.org/10.1002/ece3.72357), [multi-crop attention study](https://doi.org/10.1111/2041-210x.70260)

## 2. Species analysis: useful CameraSweet ideas and stronger statistical methods

**Make operational effort and timestamps explicit.** CameraSweet's official workflow includes clock correction, camera grouping and matrices for occupancy and abundance-style analyses. Wildlitics should extend its existing deployment records with auditable operating intervals, downtime, time zones, clock edits and processing coverage. Preserve original timestamps as well as corrected values. [CameraSweet documentation](https://smallcats.org/camerasweet/), [Harris et al.](https://doi.org/10.1890/0012-9623-91.3.352)

**Add compatible analytical exports first.** Camtrap DP provides linked deployment, media and observation records. camtrapR supports camera-operation matrices, record tables and analytical workflows. A particularly relevant update was published online on **21 October 2026**: camtrapR version 3's paper describes a dashboard, covariate preparation, activity, occupancy, spatial prediction and model diagnostics. A tested local R adapter or export path is a practical way to build on those methods. [Camtrap DP](https://doi.org/10.1002/rse2.374), [camtrapR 2026](https://doi.org/10.1111/2041-210x.70409)

**Distinguish detection history from a presence map.** Wildlitics already describes observed presence/nondetection handling. Formal occupancy analysis additionally estimates occurrence and observation processes from repeated occasions. Export `1` for a qualifying detection, `0` for a qualifying operational occasion without a detection, and `NA` for unsampled/inactive occasions or insufficient processing coverage under a documented policy. An observed zero remains a nondetection, with imperfect detection handled by the statistical model. [MacKenzie et al.](https://doi.org/10.1890/0012-9658(2002)083%5B2248:ESORWD%5D2.0.CO;2)

**Give activity filtering its own settings and sensitivity analysis.** A 2022 study argues against routine time-to-independence filtering for activity estimates; a 2024-online/2025-issue counter-study finds behavioural situations in which filtering helps. These conflicting results support retaining the raw data and reporting estimator-specific choices. Compare unfiltered, sequence-based and 30/60-minute treatments as sensitivity scenarios where appropriate. Encounter separation, occupancy occasion width and activity sampling units should be stored separately. [Peral et al.](https://doi.org/10.1002/ece3.9408), [Smith](https://doi.org/10.1007/s00265-024-03544-6), [occupancy autocorrelation guidelines](https://doi.org/10.1111/2041-210x.14359)

**Extend descriptive charts with validated estimators.** Useful additions are circular temporal overlap with uncertainty, incidence-based diversity/sample-coverage curves, and formal occupancy models with fit diagnostics. A basic activity density curve does not by itself estimate the fraction of time active; that requires additional assumptions. Likewise, camera encounter totals do not establish individual abundance. [Ridout and Linkie](https://doi.org/10.1198/jabes.2009.08038), [Rowcliffe et al.](https://doi.org/10.1111/2041-210x.12278), [iNEXT](https://doi.org/10.1111/2041-210x.12613)

Density estimation should follow later, with a specific supported method and its required survey inputs. Random-encounter approaches require movement and camera-geometry information; capture-recapture requires defensible individual identities. [Random encounter model](https://doi.org/10.1111/j.1365-2664.2008.01473.x), [individual-ID error study](https://doi.org/10.1038/s41598-020-63367-z)

## 3. Detection, accuracy and species confusion

**Measure each stage of the pipeline.** Report: animal-box recall and precision against reviewed boxes; conditional species accuracy on valid crops; and end-to-end species recall on all annotated animals, including animals the detector missed. Also record failures, processing time, memory and reviewer effort. Detector confidence, classification scores, reference similarity and ecological detection probability are distinct quantities.

**Build a confusion dashboard.** Show per-class precision, recall and F1, support in independent encounters, common confusion pairs, unresolved rates and human corrections. Break results down by day/night, site, camera model, apparent animal size and partial/obscured views. Preserve genus/family suggestions and unexpected taxa for review. Avoid forcing a local-checklist match. Habitat and background shift can cause large generalisation losses. [Norman et al.](https://doi.org/10.1111/2041-210x.14031), [Schneider et al.](https://doi.org/10.1002/ece3.6147)

**Calibrate and choose review thresholds using held-out development data.** Save full classifier logits when available, assess calibration separately from classification, and choose any per-class acceptance policy using validation/calibration data. Test it once on untouched data. Evaluate confidence reliability and selective risk/coverage, not merely the number of predictions above a threshold. Top-k-only probabilities cannot reconstruct a full-distribution temperature-scaling calculation. The current FAISS cosine scores need their own empirical validation before any probability interpretation. [Camera-trap calibration study](https://doi.org/10.1002/rse2.412)

**Audit both unexpected positives and presumed blanks.** Prioritise rare-species positives, model disagreements and difficult night records, while retaining random audits of ordinary and blank predictions. Compare detector variants, threshold changes, context padding or optional slicing on the same holdout; measure their runtime and false-positive tradeoffs. Every downstream classifier depends on the crops it receives.

**Validate ecological conclusions independently.** Recent studies show both encouraging agreement between AI and expert occupancy models and important failures for rare species or low-precision classifications. The relevant question is whether Wildlitics preserves the ecological result for the intended survey, not whether another study reported high image accuracy. [Thornton et al. 2026](https://doi.org/10.1111/1365-2664.70370), [classification-bias study](https://doi.org/10.1111/2041-210x.70132), [Whytock et al.](https://doi.org/10.1111/2041-210x.13576)

## Development order and evidence required

The phases below are a proposed sequence, not calendar commitments or implemented features.

| Priority | Concrete change | Evidence required before adoption |
|---|---|---|
| P0 | Expert-reviewed benchmark with stable media/object IDs and site/encounter holdouts | Label audit; no related encounters crossing splits; all failures and unknowns retained |
| P0 | Confusion/error dashboard and stratified audit queue | Reproducible per-class, day/night and end-to-end metrics with group-based uncertainty |
| P0 | Operational-effort, clock and data-quality audit | Correct active/inactive histories and traceable edits on representative projects |
| P1 | Camtrap DP and camtrapR-compatible exports | Schema validation and agreement with a pinned reference workflow |
| P1 | Local model comparison and optional SpeciesNet fine-tuning | Matched field holdouts; learning curves; no unexplained regression in priority taxa |
| P1 | Calibration and review policy | Independent calibration subset; reliability and risk/coverage evaluation; rare-class limitations shown |
| P1 | Activity sensitivity, overlap and coverage-based diversity | Numerical agreement with reference methods and reported assumptions/uncertainty |
| P2 | Single-species occupancy, then community models | Sampling assumptions checked; fit/convergence diagnostics; comparison with expert-derived results |
| P2 | Targeted detector/crop improvements, augmentation and sequence context | Paired ablations on the same holdout; runtime and review burden included |
| P3 | Individual-ID, density models, aerial imagery or audio | A separate validated use case, suitable survey inputs and component licence review |

For a first model experiment, fit learning curves at feasible per-class sample levels rather than collecting a large number of nearly identical burst frames. Use the actual target Windows hardware for throughput and cancellation/recovery checks. Preserve a known-working model and activate a candidate only after its evaluation is recorded.

OCR, GBIF matching and Qwen assistance can remain separate document/taxonomy work alongside this sequence. Their outputs should retain source evidence and human-review status.

## Current community and software updates

Ten dated community items and eleven technical references are catalogued separately in [COMMUNITY_UPDATES.md](COMMUNITY_UPDATES.md). The highest immediate relevance is assisted annotation, recoverable video intake, review-interface design and Windows reliability. The October drone/audio announcements are useful watch items for future use cases. Community performance numbers are author reports, not validation of Wildlitics.

The research supports a disciplined route to a better application: trusted survey data, measured local identification, reproducible ecological analysis, and upgrades accepted on evidence. Production integration still depends on the actual application source and representative labelled field data.
