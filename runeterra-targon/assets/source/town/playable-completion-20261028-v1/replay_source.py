"""Replay only the selected painted town source derivation, without staging."""
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


def main():
    for script in ('prepare_background_v3.py','prepare_terrain_v9.py','assemble_town.py','derive_resources.py','prepare_physical_contract.py'):
        subprocess.run([sys.executable,'-B',str(HERE/script)],check=True)


if __name__=='__main__':main()
