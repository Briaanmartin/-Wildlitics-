# Search and verification method

Cutoff and retrieval date: 24 October 2026. Purpose: a practical evidence map and development review for Wildlitics.

## Discovery

48 targeted OpenAlex searches returned 1,270 distinct indexed candidate records (deduplicated by DOI or OpenAlex ID); three foundational DOIs were also added directly. Each search requested up to 60 ranked records, with article/journal, non-retracted and publication-date filters. Query strings, API URLs and returned counts are in search-audit.json. Web searches additionally located primary papers, author resources and community discussions.

Searches were organised around model enhancement; ecological analysis; and detection/accuracy/confusion. Search-result membership alone was not used as proof of topical relevance. Shortlisted titles were inspected for relevant tasks, recognised journal venues and a usable DOI. General medical/microbiome, unrelated engineering, theses, broad student demonstrations, conference abstracts, preprint-only and no-DOI discovery results were not included in the journal quota. Related camera-trap taxa and individual-ID papers are marked by focus tags; they are not all direct tests of Bornean species recognition.

223 unique shortlisted DOI records were checked against Crossref. The final topic selections contain 200 unique articles, each with matching journal-article metadata. Citation years use issue/print years where available; first publication dates are stored separately. This explains entries such as the calibration paper first online in 2024 but in a 2025 issue, and the independence-filter counter-study first online in December 2024 but in a 2025 issue.

## Verification scope

For every included record: Crossref returned the DOI, title, journal, authors and a publication date; the record type was journal-article; an available publication date was on or before the cutoff. The first-publication field normally records the earliest date deposited in Crossref, which can omit an earlier online release. The SpeciesNet fine-tuning paper uses the earlier PubMed Epub date with its basis recorded explicitly. OpenAlex and Crossref titles were compared where both were present. DOI, normalised-title and within-topic duplicates were checked. No update-to notice was present in these included Crossref records and no retraction was flagged in the available OpenAlex records. These metadata checks are not a comprehensive assessment of research integrity, peer-review quality or all post-publication notices.

All final entries received title/metadata screening. 28 priority sources received closer abstract, accessible-section or author/publisher method assessment; their findings, limits and proposals are in KEY_EVIDENCE.md. Other library rows have reading questions, not asserted study conclusions. The pipeline does not pretend an abstract was read just because it was retrieved. No full abstracts or papers are redistributed.

100 articles appear in each topic list. There are 300 topic placements and 200 unique papers; overlap is explicit. Lists include methods, reviews, software-method articles and relevant empirical applications. The article type alone does not guarantee quality, and citation counts were not used as a performance or quality score.

## Limits

This is a targeted review, not a registered systematic review or meta-analysis. The 60-result cap and search terms can miss relevant work; the OpenAlex article filter can omit separately indexed reviews. English-language discovery and available metadata influence coverage. Not all linked publisher pages or full texts were accessible or opened. Bibliographic verification is separate from assessing a study's methods and validity. No pooled performance estimate, universal training-set size or guaranteed Wildlitics improvement is calculated.

WILDLABS.net is the conservation technology site used here (the requested wildlibs.com was interpreted from the established conversation context). Ten dated community items and eleven technical references are separated from journal evidence. Community/vendor claims are not independently reproduced results. The search is a dated snapshot, not a scheduled monitoring service.

## Reproducibility and files

literature.json and literature.csv contain the final records, topic memberships, reading questions, review level, verification dates, Crossref API URLs and SHA-256 fingerprints of the metadata records checked. library.ris supports reference-manager import. selected-topics.json fixes the DOI membership of each list; search-audit.json preserves discovery requests. The build and discovery scripts are included under scripts, alongside the original synthesis notes. Raw API responses containing abstracts are kept outside the shared package.

The report contains original paraphrases and application proposals with linked sources. It does not adopt a new licence for Wildlitics, copy third-party application code, update the installed app, or validate field accuracy.

To rebuild after extracting the package: install scripts/requirements.txt, run python scripts/verify.py to fetch metadata for the frozen DOI selections, then python scripts/build.py. The build writes a new output directory and ZIP. Discovery can be repeated separately with python scripts/collect.py; its new rankings do not automatically change the curated selections. Exact original metadata snapshots can change upstream, so fingerprints may differ in a later rebuild. Fonts for PDF output use the standard Linux DejaVu Sans paths in the build script; adjust those paths on other platforms.

## Exact discovery queries


### 1. Enhancing identification models

- camera trap deep learning
- camera trap transfer learning
- camera trap species classification
- camera trap self supervised
- camera trap foundation models
- camera trap vision transformer
- camera trap fine tuning
- camera trap semi supervised
- camera trap active learning
- camera trap domain adaptation
- camera trap few shot learning
- camera trap ensemble learning
- camera trap synthetic data augmentation
- camera trap continual learning
- camera trap feature extraction
- wildlife image classification deep learning

### 2. Species data analysis and workflows

- camera trap activity overlap
- camera trap occupancy detection probability
- camera trap density random encounter
- camera trap data management software
- camera trap species richness sampling
- camera trap spatial capture recapture
- camera trap detection rate abundance
- camera trap false positive occupancy
- camera trap sampling design effort
- camera trap independent events
- camera trap biodiversity community monitoring
- camera trap circular activity estimation
- camera trap metadata data standard
- occupancy models imperfect detection
- species richness sample coverage rarefaction
- camera trap distance sampling

### 3. Detection, accuracy and confusion

- camera trap animal detection
- camera trap object detection
- camera trap small animals
- camera trap classification accuracy generalization
- camera trap confidence calibration
- camera trap class imbalance
- camera trap uncertainty classification
- camera trap misclassification
- camera trap false positive
- camera trap image sequences classification
- camera trap human expert validation
- camera trap empty images
- camera trap label noise
- camera trap out of distribution
- camera trap open set recognition
- camera trap evaluation deep learning
