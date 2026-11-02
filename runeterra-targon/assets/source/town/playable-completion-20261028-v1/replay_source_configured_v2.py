"""Reproduce selected artwork and configured recipes without staging or3D."""
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


def main():
    for name in ('prepare_background_v3.py','prepare_terrain_v9.py','assemble_town.py','derive_resources_configured_v2.py','prepare_physical_contract.py'):
        subprocess.run([sys.executable,'-B',str(HERE/name)],check=True)


if __name__=='__main__':main()
