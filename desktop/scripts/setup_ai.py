"""Explicit, local CPU AI installation. Does not run inference or upload images."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import venv


def main():
    default=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local/share'))/'Wildlitics'/'ai-runtime'
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path,default=default)
    args=parser.parse_args();folder=args.directory.expanduser().resolve()
    if sys.version_info[:2]!=(3,12):
        raise SystemExit('Run this installer using Python 3.12. The desktop UI itself has its own bundled Python.')
    print('Preparing AI environment at',folder,flush=True)
    venv.EnvBuilder(with_pip=True).create(folder)
    python=folder/('Scripts/python.exe'if os.name=='nt'else'bin/python')
    commands=[
        [str(python),'-m','pip','install','--upgrade','pip'],
        [str(python),'-m','pip','install','torch==2.9.1','torchvision==0.24.1','--index-url','https://download.pytorch.org/whl/cpu'],
        [str(python),'-m','pip','install','speciesnet==5.0.6'],
        [str(python),'-m','speciesnet.scripts.run_model','--help'],
    ]
    for command in commands:
        subprocess.run(command,check=True)
    print('\nAI environment installed. Select this Python in Wildlitics:\n'+str(python),flush=True)
    print('Model weights download on first inference. Images remain local.',flush=True)


if __name__=='__main__':main()
