# Priority evidence and its limits

28 sources assessed through abstracts, accessible article sections or author/publisher method content. These notes distinguish reported findings from proposed Wildlitics changes. No performance number is a local Wildlitics result.

## 1. Local SpeciesNet fine-tuning

**AI and computer vision for wildlife identification in camera trap images: Fine-tuning SpeciesNet outperforms local models for species classification**. Science of The Total Environment, 2026. [DOI](https://doi.org/10.1016/j.scitotenv.2026.181926)

**Reported evidence:** A comparison using 15 common Australian rainforest species favoured local fine-tuning of SpeciesNet, including evaluation on withheld cameras.

**Limit:** The balanced common-species experiment does not establish results for rare Bornean taxa. Its reported learning-curve plateau is not a universal sample requirement.

**Wildlitics proposal:** Compare a frozen local head and modest SpeciesNet fine-tuning on identical site and encounter holdouts before selecting a backbone.

## 2. Crop-based classification

**To crop or not to crop: Comparing whole‐image and cropped classification on a large dataset of camera trap images**. IET Computer Vision, 2024. [DOI](https://doi.org/10.1049/cvi2.12318)

**Reported evidence:** Across three datasets, detector-based crops improved classification relative to whole-image baselines.

**Limit:** Missed detections remain a bottleneck; the paper did not evaluate multi-species images or prove gains for every size of animal.

**Wildlitics proposal:** Retain crop-to-object associations and benchmark missed animals alongside species classification.

## 3. Habitat and camera generalisation

**Can CNN‐based species classification generalise across variation in habitat within a camera trap survey?**. Methods in Ecology and Evolution, 2023. [DOI](https://doi.org/10.1111/2041-210x.14031)

**Reported evidence:** Classification generalisation deteriorated at unseen cameras and habitat disturbance levels; crops and more varied training backgrounds helped in the study.

**Limit:** Higher random-split accuracy did not guarantee performance in a new habitat.

**Wildlitics proposal:** Hold out complete sites/deployments and test across habitat, camera hardware, day/night and seasons.

## 4. Data volume and background shift

**Three critical factors affecting automated image species recognition performance for camera traps**. Ecology and Evolution, 2020. [DOI](https://doi.org/10.1002/ece3.6147)

**Reported evidence:** Performance varied with class training volume and unseen locations in a modest-sized, imbalanced camera-trap collection.

**Limit:** Reported image counts and accuracy thresholds are dataset-specific.

**Wildlitics proposal:** Publish per-species learning curves and use encounter counts as well as image counts when allocating labelling effort.

## 5. Active learning

**A deep active learning system for species identification and counting in camera trap images**. Methods in Ecology and Evolution, 2021. [DOI](https://doi.org/10.1111/2041-210x.13504)

**Reported evidence:** Combining human annotation, transfer learning and object crops reduced annotation requirements in the studied workflow.

**Limit:** Its large annotation-saving estimate is not a forecast for Wildlitics.

**Wildlitics proposal:** Offer a diverse review queue covering model disagreement, uncertain cases, unfamiliar backgrounds and rare classes.

## 6. Confidence calibration

**Being confident in confidence scores: calibration in deep learning models for camera trap image sequences**. Remote Sensing in Ecology and Conservation, 2025. [DOI](https://doi.org/10.1002/rse2.412)

**Reported evidence:** A European camera-trap study examined calibration over five models and independent test sets; sequence-logit averaging and optional temperature scaling were useful.

**Limit:** Calibration can change under domain shift. Sequences can contain multiple animals or species.

**Wildlitics proposal:** Use a separate calibration subset, retain logits when available and evaluate Brier score, log loss and reliability plots.

## 7. Context across animal crops

**Paying attention to other animal detections improves camera trap classification models**. Methods in Ecology and Evolution, 2026. [DOI](https://doi.org/10.1111/2041-210x.70260)

**Reported evidence:** A learned attention module used context from crop embeddings within images/sequences to improve classification over independent-crop baselines.

**Limit:** Part of the multi-species evaluation used synthetic or weakly annotated sequences.

**Wildlitics proposal:** Explore context after a baseline is measured; preserve individual object predictions instead of forcing one species across an encounter.

## 8. Background-diverse augmentation

**Copy‐Paste Augmentation Improves Automatic Species Identification in Camera Trap Images**. Ecology and Evolution, 2025. [DOI](https://doi.org/10.1002/ece3.72357)

**Reported evidence:** Copy-paste training augmentation improved generalisation to unseen locations in the reported experiments.

**Limit:** Benefits varied by species, and very small training sets produced mixed results.

**Wildlitics proposal:** Test augmentation only after group splitting, with traceable source masks and no held-out backgrounds entering training.

## 9. Training quality and ecological error

**Deep learning‐based ecological analysis of camera trap images is impacted by training data quality and quantity**. Remote Sensing in Ecology and Conservation, 2026. [DOI](https://doi.org/10.1002/rse2.70052)

**Reported evidence:** Rare or visually similar species were especially sensitive to training quality/quantity; species-level occupancy and activity could diverge even when community richness appeared stable.

**Limit:** The study used two ecosystems and does not prove that architecture choice never matters.

**Wildlitics proposal:** Prioritise clean labels and class coverage, then evaluate ecological outputs against expert-labelled data.

## 10. AI-derived occupancy: promising but conditional

**Identification of camera trap images by artificial intelligence and human experts produces similar multi‐species occupancy models**. Journal of Applied Ecology, 2026. [DOI](https://doi.org/10.1111/1365-2664.70370)

**Reported evidence:** After specified processing, AI- and expert-derived multi-species occupancy results were often similar across three study areas.

**Limit:** Rare species showed some of the largest divergences; agreement depended on processing choices.

**Wildlitics proposal:** Build an ecological agreement benchmark before allowing unattended AI-labelled analyses.

## 11. Validate the ecological endpoint

**Robust ecological analysis of camera trap data labelled by a machine learning model**. Methods in Ecology and Evolution, 2021. [DOI](https://doi.org/10.1111/2041-210x.13576)

**Reported evidence:** A Central African study directly compared richness, activity and occupancy from AI and expert labels; acceptance thresholds affected the endpoints differently.

**Limit:** Agreement for several tested species does not establish general equivalence or one best threshold for every analysis.

**Wildlitics proposal:** Compare image errors and downstream ecological estimates separately, documenting rejected and unresolved records.

## 12. Precision, night images and occupancy bias

**Essential tools but overlooked bias: Artificial intelligence and citizen science classification affect camera trap data**. Methods in Ecology and Evolution, 2025. [DOI](https://doi.org/10.1111/2041-210x.70132)

**Reported evidence:** An expert holdout and simulations showed classification error varying by species and illumination; low precision could substantially bias occupancy estimates.

**Limit:** The compared classifiers and species groups do not cover all camera-trap deployments.

**Wildlitics proposal:** Report day/night per-class precision and recall, and separately audit rare-species false positives.

## 13. Formal data quality control

**A protocol for error prevention and quality control in camera trap datasets**. Journal of Applied Ecology, 2025. [DOI](https://doi.org/10.1111/1365-2664.70010)

**Reported evidence:** The proposed protocol covers malfunction checks, time/storage corrections, classification and post-classification quality control.

**Limit:** A protocol reduces avoidable errors but cannot establish that every identification or timestamp is correct.

**Wildlitics proposal:** Add a pre-analysis quality report covering operational effort, clock edits, processing failures, duplicate media and reviewer audit samples.

## 14. Evidence against routine independence filters

**The inappropriate use of time‐to‐independence biases estimates of activity patterns of free‐ranging mammals derived from camera traps**. Ecology and Evolution, 2022. [DOI](https://doi.org/10.1002/ece3.9408)

**Reported evidence:** The study found that time-to-independence filtering altered activity estimates and discarded substantial information, with differing effects across taxa.

**Limit:** Its conclusion is debated; the contrasting Smith study below identifies behavioural reasons filters may sometimes help.

**Wildlitics proposal:** Retain raw detections and make filtered/unfiltered activity results available with their sampling units.

## 15. Counter-evidence on independence filters

**An empirical assessment of the role of independence filters in temporal activity analyses using camera trapping data**. Behavioral Ecology and Sociobiology, 2025. [DOI](https://doi.org/10.1007/s00265-024-03544-6)

**Reported evidence:** An empirical counter-argument found that lingering or resting animals and herding could distort activity densities, and that filtering could address those behaviours.

**Limit:** This is not proof that a fixed 60-minute rule is suitable for every habitat or estimator.

**Wildlitics proposal:** Offer sensitivity comparisons and record the biological rationale for the chosen activity treatment.

## 16. Occupancy and temporal autocorrelation

**Guidelines for estimating occupancy from autocorrelated camera trap detections**. Methods in Ecology and Evolution, 2024. [DOI](https://doi.org/10.1111/2041-210x.14359)

**Reported evidence:** Simulations and a mammal case study evaluated autocorrelation; larger detection windows could mitigate bias, while inserting gaps discarded data without solving it.

**Limit:** Appropriate occasion duration depends on detection rates, design and model assumptions.

**Wildlitics proposal:** Build explicit occasion histories, test fit/autocorrelation and distinguish occasion width from encounter grouping.

## 17. Interoperable camera-trap records

**Camtrap DP: an open standard for the FAIR exchange and archiving of camera trap data**. Remote Sensing in Ecology and Conservation, 2024. [DOI](https://doi.org/10.1002/rse2.374)

**Reported evidence:** Camtrap DP specifies linked deployment, media and observation tables supporting human and AI classification workflows.

**Limit:** A valid exchange package does not validate survey design or scientific interpretation.

**Wildlitics proposal:** Add a version-pinned Camtrap DP export with schema validation and stable IDs while preserving raw AI and accepted observations.

## 18. camtrapR foundations

**camtrapR: an R package for efficient camera trap data management**. Methods in Ecology and Evolution, 2016. [DOI](https://doi.org/10.1111/2041-210x.12600)

**Reported evidence:** The package links camera-trap organisation, extraction and summaries to detection histories for occupancy and capture-recapture analysis.

**Limit:** Species and individual identification require their own workflows and quality control.

**Wildlitics proposal:** Export compatible record tables and camera-operation matrices rather than inventing a separate ecological data format.

## 19. camtrapR version 3: a current integration reference

**The camtrapR R package: From data management to interactive ecological analysis of camera trap data**. Methods in Ecology and Evolution, 2026. [DOI](https://doi.org/10.1111/2041-210x.70409)

**Reported evidence:** Published online on 21 October 2026, the paper describes an end-to-end workflow including a dashboard, covariates, occupancy models, spatial predictions and diagnostics.

**Limit:** Advanced models still require appropriate designs, covariates and diagnostic interpretation; a dashboard does not remove those requirements.

**Wildlitics proposal:** Evaluate a local R analysis adapter and reusable exports before independently reimplementing every statistical method.

## 20. Occupancy with imperfect detection

**ESTIMATING SITE OCCUPANCY RATES WHEN DETECTION PROBABILITIES ARE LESS THAN ONE**. Ecology, 2002. [DOI](https://doi.org/10.1890/0012-9658(2002)083%5B2248:esorwd%5D2.0.co;2)

**Reported evidence:** The occupancy framework distinguishes species occurrence from the probability of observing it during repeat surveys.

**Limit:** Closure, sampling and detection assumptions remain necessary; an unprocessed or inactive camera occasion is not a nondetection.

**Wildlitics proposal:** Export 1/0/NA histories based on observed detections and documented operational effort, with model assumptions visible.

## 21. False-positive occupancy

**GENERALIZED SITE OCCUPANCY MODELS ALLOWING FOR FALSE POSITIVE AND FALSE NEGATIVE ERRORS**. Ecology, 2006. [DOI](https://doi.org/10.1890/0012-9658(2006)87%5B835:gsomaf%5D2.0.co;2)

**Reported evidence:** The model extends occupancy analysis to include false-positive as well as false-negative observations.

**Limit:** Such models need an identifiable design and suitable validation information; AI scores alone are not automatically enough.

**Wildlitics proposal:** Preserve validation/audit observations so future error-aware models have defensible inputs.

## 22. Daily activity overlap

**Estimating overlap of daily activity patterns from camera trap data**. Journal of Agricultural, Biological, and Environmental Statistics, 2009. [DOI](https://doi.org/10.1198/jabes.2009.08038)

**Reported evidence:** The paper compares methods for estimating overlap between circular daily activity distributions.

**Limit:** Overlap describes temporal coincidence and does not establish species interaction or causation.

**Wildlitics proposal:** Add tested circular overlap estimates and uncertainty, reporting estimator, sample sizes and preprocessing.

## 23. Activity level needs extra assumptions

**Quantifying levels of animal activity using camera trap data**. Methods in Ecology and Evolution, 2014. [DOI](https://doi.org/10.1111/2041-210x.12278)

**Reported evidence:** The proposed activity-level estimator uses time-of-detection distributions and an assumption about activity at the daily peak.

**Limit:** The proportion of time active cannot be read directly from a normalised histogram or a basic density curve.

**Wildlitics proposal:** Keep descriptive timing charts distinct from an optional, assumption-documented activity-level model.

## 24. Diversity with sample coverage

**iNEXT: an R package for rarefaction and extrapolation of species diversity ( H ill numbers)**. Methods in Ecology and Evolution, 2016. [DOI](https://doi.org/10.1111/2041-210x.12613)

**Reported evidence:** iNEXT supports abundance- and incidence-based rarefaction/extrapolation for Hill-number diversity and sample completeness.

**Limit:** Camera detections are not automatically independent counts of individual abundance.

**Wildlitics proposal:** Prioritise incidence-based sampling units, coverage curves and uncertainty for camera-trap diversity comparisons.

## 25. Comparable sampling completeness

**Coverage‐based rarefaction and extrapolation: standardizing samples by completeness rather than size**. Ecology, 2012. [DOI](https://doi.org/10.1890/11-1952.1)

**Reported evidence:** Coverage-based rarefaction/extrapolation compares communities at similar sample completeness instead of merely equal sample size.

**Limit:** Appropriate sampling units and uncertainty still matter.

**Wildlitics proposal:** Display effort and completeness next to richness comparisons, with clearly stated incidence units.

## 26. Individual identification is a separate error problem

**Identification errors in camera-trap studies result in systematic population overestimation**. Scientific Reports, 2020. [DOI](https://doi.org/10.1038/s41598-020-63367-z)

**Reported evidence:** A controlled snow-leopard identification experiment showed that human individual-ID errors could inflate abundance estimates.

**Limit:** This concerns individual recognition and capture-recapture, not a measured error rate for species classification in Wildlitics.

**Wildlitics proposal:** Keep future individual-ID features separate and require their own independent validation before density estimation.

## 27. Unmarked density: required inputs

**Estimating animal density using camera traps without the need for individual recognition**. Journal of Applied Ecology, 2008. [DOI](https://doi.org/10.1111/j.1365-2664.2008.01473.x)

**Reported evidence:** The random encounter model relates encounter rates to density using movement, group size and camera detection geometry.

**Limit:** Camera placement and parameter measurement affect validity; encounter counts alone do not identify population density.

**Wildlitics proposal:** Defer a density button until the survey and calibration inputs required by its chosen estimator are available.

## 28. CameraSweet's methodological roots

**Automatic Storage and Analysis of Camera Trap Data**. The Bulletin of the Ecological Society of America, 2010. [DOI](https://doi.org/10.1890/0012-9623-91.3.352)

**Reported evidence:** The article presents structured storage and automated tabulation to reduce manual data entry and make camera-trap analyses easier to combine.

**Limit:** Historical directory-based conventions need adaptation to modern per-object AI records and explicit observation provenance.

**Wildlitics proposal:** Adopt reproducible tables, clock correction history and documented effort while preserving original media.
