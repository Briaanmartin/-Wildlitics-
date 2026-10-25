"""Build a one-folder native UI; large AI dependencies remain in a separate venv."""
from importlib.metadata import distribution
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed',
                    '--name','Wildlitics','--paths',str(ROOT/'src'),str(ROOT/'run_desktop.py')],cwd=ROOT,check=True)
    target=ROOT/'dist'/'Wildlitics'
    for name in ['README.md','THIRD_PARTY_NOTICES.md','Install-AI.cmd']:
        shutil.copyfile(ROOT/name,target/name)
    (target/'scripts').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'scripts'/'setup_ai.py',target/'scripts'/'setup_ai.py')
    shutil.copytree(ROOT/'LICENSES',target/'LICENSES',dirs_exist_ok=True)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file():shutil.copyfile(python_license,target/'LICENSES'/'Python-LICENSE.txt')
    # Preserve any further licence files carried by the installed wheels.
    for name in ['PySide6-Essentials','shiboken6','Pillow']:
        dist=distribution(name)
        for item in dist.files or []:
            if 'license' in str(item).lower() or 'copying' in item.name.lower():
                source=Path(dist.locate_file(item))
                if source.is_file():
                    dest=target/'LICENSES'/name/item.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    print('Desktop build:',target)


if __name__=='__main__':main()
