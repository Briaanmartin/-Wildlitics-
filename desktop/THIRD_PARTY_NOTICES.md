# Third-party components

This desktop prototype is an original implementation. The SpeciesNet JSON adapter in `src/wildlitics_desktop/speciesnet_results.py` is a copy of the original Wildlitics helper from `experimental/data-tools/speciesnet_review.py` for standalone packaging; it contains no copied Google implementation. No Pustaka, Kunci, CameraSweet or unlicensed demonstration-app source or assets are included.

The original Wildlitics application's licence is unchanged. This document does not assign a blanket licence to all repository content, photographs or model weights.

## Graphical distribution

- **PySide6 Essentials 6.12.0 / Shiboken6 6.12.0 / Qt:** upstream offers LGPL-3.0/GPL options; this distribution uses the LGPL option for the dynamically linked components. The complete LGPL-3.0 and GPL-3.0 texts are included in `LICENSES`. Qt libraries are separate files in the one-folder build. Users may replace compatible Qt libraries and debug/reverse-engineer as necessary to modify those LGPL components; no application restriction is asserted against those rights. Upstream source and build materials: [Qt for Python](https://code.qt.io/cgit/pyside/pyside-setup.git/), [Qt base](https://code.qt.io/cgit/qt/qtbase.git/), [Qt downloads](https://download.qt.io/). Select the matching 6.12.0 source release. No Qt/PySide source modifications are made here. Qt's individual included modules and third-party parts retain their supplied notices.
- **Pillow:** MIT-CMU; the installed wheel's licence text is copied into the packaged `LICENSES/Pillow` folder.
- **Python:** Python Software Foundation licence and bundled notices supplied by the interpreter/PyInstaller runtime. Python includes third-party components with their own notices. Sources: [Python 3.12](https://www.python.org/downloads/source/).
- **SQLite:** public domain; used through Python's standard library.
- **PyInstaller:** GPL with its distribution exception for generated applications; build tooling, not a licence imposed on the original application. [Official licence](https://pyinstaller.org/en/stable/license.html).

The build copies available licence files from installed wheels and keeps this notice with the executable. Preserve those files when redistributing a build.

## Separate AI runtime

The GUI does not bundle SpeciesNet, PyTorch, a detector implementation, model weights, training images or inference outputs. `Install-AI.cmd` / `scripts/setup_ai.py` explicitly install a separate local environment from upstream sources. Each installed component and selected model retains its own terms, including transitive detector dependencies; the SpeciesNet repository's Apache-2.0 licence is not a blanket licence for the full stack.

- [SpeciesNet](https://github.com/google/cameratrapai): Google Camera Traps AI team and contributors; Apache-2.0 repository code. Cite Gadot et al. (2024), DOI [10.1049/cvi2.12318](https://doi.org/10.1049/cvi2.12318).
- [MegaDetector](https://github.com/microsoft/MegaDetector): Microsoft AI for Good and contributors; check the selected detector version and its dependencies. This prototype's default official SpeciesNet cascade uses upstream MDv5a weights.
- [PyTorch](https://pytorch.org/): PyTorch contributors; BSD-style terms and individual third-party notices.

No model weights or wildlife photographs are included in this source or graphical package. The optional real-inference smoke check uses an upstream sample in a private validation workspace, with its source/credit recorded separately; that photograph is not part of the distribution. The six-camera demo uses generated geometric fixtures and explicit synthetic labels only.
