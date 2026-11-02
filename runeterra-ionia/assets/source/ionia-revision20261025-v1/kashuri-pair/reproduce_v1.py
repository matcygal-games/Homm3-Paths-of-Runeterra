"""Deterministic local replay, including AFTER canonical recipe selection.

No image generation/network/native desktop/stage/content/live-manifest writes.
Use --recipes assets/recipes/creatures only in an isolated source copy when
reproducing a selected packet. Default stays in the source candidate lane.
"""
from pathlib import Path
import runpy,sys
S=Path(__file__).resolve().parent;sys.path.insert(0,str(S))

def main():
    recipes='assets/candidates/ionia-revision20261025-kashuri-v2/recipes'
    if '--recipes' in sys.argv:recipes=sys.argv[sys.argv.index('--recipes')+1]
    runpy.run_path(str(S/'prepare_reference_inputs_v1.py'),run_name='__main__')
    runpy.run_path(str(S/'assemble_base_gait.py'),run_name='__main__')
    runpy.run_path(str(S/'prepare_gait_reference.py'),run_name='__main__')
    runpy.run_path(str(S/'assemble_native_v1.py'),run_name='__main__')
    sys.argv=[str(S/'bind_recipes_v2.py'),'--recipes',recipes]
    runpy.run_path(str(S/'bind_recipes_v2.py'),run_name='__main__')

if __name__=='__main__':main()
