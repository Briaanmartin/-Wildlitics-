"""PyInstaller entry point, also usable with Python from the source checkout."""
import sys

if '--self-test' in sys.argv:
    from wildlitics_desktop.selfcheck import main
else:
    from wildlitics_desktop.app import main

raise SystemExit(main())
