# Wildlitics Desktop 0.1.0

An independent native desktop prototype for **camera folders → local wildlife AI → per-object human review → descriptive reports**. It builds on the combined development and research branch. It is a new implementation, separate from the original Wildlitics 2.3.3 Windows application, whose source is absent from this repository.

## What works

- Create and reopen local SQLite projects.
- Import one camera folder or a collection of camera subfolders, with distinct camera IDs and no two-camera display cap.
- Keep every registered camera visible, including cameras with no images or no verified records.
- Run the official SpeciesNet 5.0.6 CLI in a separate local Python environment, with captured logs, cancellation and saved-job resume.
- Use SpeciesNet 4.0.3a for animal crops or 4.0.3b for whole-image classification, with optional country filtering.
- Import supported SpeciesNet JSON while preserving individual boxes, original predictions, raw candidates, taxonomic rank, decision source and classification scope.
- Confirm/correct or reject predictions with a reviewer identity and append-only review history.
- View camera coverage, recorded taxon labels, descriptive encounter-hour histograms and missing-time information.
- Export PDF, offline HTML and observation CSV under the selected camera/verification policy.
- Explore an explicit synthetic demo with six cameras; no demo prediction is represented as a real inference result.

The standard official SpeciesNet cascade uses its upstream **MegaDetector v5a** detector. This prototype does not yet recreate the original application's MDV6/BioCLIP conditional model policy. Existing MDV6 integration, BioCLIP/DINOv2 model comparison, training, IUCN workbooks, maps and formal occupancy/diversity estimators remain future application work. No independent field-accuracy improvement is claimed.

## Windows portable build

The desktop workflow builds a one-folder Windows x64 application. Download its `Wildlitics-Windows-x64` artifact, extract the entire ZIP and run **Wildlitics.exe**. Keep the adjacent `_internal` files and licence notices together. The graphical interface bundles its own Python/Qt libraries; it does not bundle the large AI environment or weights.

For local AI:

1. Install **Python 3.12** from [python.org](https://www.python.org/downloads/windows/), including its `py` launcher.
2. Run the supplied **Install-AI.cmd**. It creates `%LOCALAPPDATA%\Wildlitics\ai-runtime` and installs CPU PyTorch 2.9.1, torchvision 0.24.1 and SpeciesNet 5.0.6. This explicit setup requires internet and disk space for large dependencies.
3. Open Wildlitics, create a project, and add camera folders.
4. In **AI workbench**, check the AI Python path and click **Check runtime**. The default points to the installed environment.
5. Choose the model, optional country and threshold, then **Run wildlife AI**. First use downloads the official weights; later inference can use the cached model. The application passes local filepaths to the local model process.
6. Open **Review records**, inspect each object and enter a human-confirmed label/reviewer. The dashboard and reports default to verified records.

The supplied installer is a CPU baseline. A suitable GPU PyTorch environment can be selected separately; runtime diagnostics and model logs identify the device. Do not install a second Qt GUI stack into the AI environment merely to run inference.

## Run from source

Use Python 3.10–3.14 for the UI (3.12 tested):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e desktop
wildlitics-desktop
```

AI setup is independent and uses Python 3.12:

```bash
python desktop/scripts/setup_ai.py
```

Select the printed AI interpreter path in the application. A pre-existing environment with SpeciesNet 5.0.6 can also be selected. Package/model versions are deliberately distinct; the runtime probe enforces the supported package version.

```bash
# Create a new synthetic demo from the command line:
wildlitics-desktop --demo /path/to/new-demo-project
```

## Project and review behaviour

- Original media are referenced, never moved, renamed or rewritten. Keep their source folders available.
- The project contains `wildlitics.sqlite`, original input manifests, raw results, logs and exports. Back up the project and original media together; close the app before copying a database manually.
- Input hashes are checked before new/resumed inference and result import. Changed or missing inputs are refused.
- Reimporting the same JSON is idempotent. Reprocessing with a different inference run preserves older predictions/history while making the newer run the current review queue; new suggestions require review.
- Relative prediction paths resolve against the JSON's directory. Match absolute paths or place the JSON at the appropriate image root. Filenames alone are never used to guess camera associations.
- Legacy image-level predictions remain unassociated with individual boxes. Category 0 remains whole-image scope. The review screen exposes that scope.
- Unreadable files, unprocessed images, component failures and reported empty results remain separate states. No detections does not establish ecological absence.
- Capture dates come from readable EXIF date fields; missing/invalid times remain unknown. The current UI does not yet correct camera clocks or time zones.
- Deployment dates are optional explicit metadata. Their difference is a **declared continuous duration**, not validated operational trap-days; downtime modelling is pending.
- Encounter grouping uses a gap from the preceding same-camera/taxon detection. It is configurable separately from image counts. The histogram is descriptive and does not estimate the proportion of time animals are active.
- Taxon/category labels and model scores require interpretation. No GBIF/IUCN status is guessed, no score is called measured accuracy, and no population/occupancy estimate is generated.
- Reports apply the selected camera, verification and gap settings. CSV retains review/model fields; when verification filtering is disabled it includes suggestions. CSV can contain local source paths, so review it before sharing.

The desktop currently imports image folders, not live streams or videos. The existing [FFmpeg data helper](../experimental/data-tools/README.md) can prepare timestamped frames, but linking video offsets to camera capture time remains explicit integration work.

## Validation and packaging

```bash
python -m unittest discover -s desktop/tests -v
```

The suite exercises more than two cameras, empty-camera visibility, filtering, source preservation, review history, per-object/legacy import, cancellation of a silent subprocess and native offscreen UI/PDF export. Synthetic tests measure software behaviour, not wildlife recognition. A real local SpeciesNet run on the upstream public camera-trap sample is recorded separately in `validation.json` when completed.

```bash
python -m pip install pyinstaller==6.22.3
python desktop/scripts/build_desktop.py
```

The build uses dynamic Qt libraries in a replaceable one-folder layout and preserves third-party notices. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The Windows build is a portable prototype, not a signed production installer. CI tests the source and packaged GUI, then installs a separate CPU AI environment and exercises real model inference on an upstream public sample. A successful Windows artifact includes `packaged-validation.json` and `real-ai-validation.json`; the sample photograph and AI environment are excluded from that artifact.
