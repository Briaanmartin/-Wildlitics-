@echo off
setlocal
echo Wildlitics local CPU AI setup
echo Requires Python 3.12. This downloads PyTorch and SpeciesNet dependencies.
py -3.12 "%~dp0scripts\setup_ai.py"
if errorlevel 1 (
  echo Setup failed. Install Python 3.12 from https://www.python.org/downloads/windows/ and try again.
) else (
  echo Setup finished. Open Wildlitics and use Check runtime.
)
pause
