"""Targeted raised near-hind guide variant; geometry guide only, never final art.

Kept with unselected source experiments rather than active production scripts.
"""
from pathlib import Path
base = Path(__file__).with_name('druvask_walk_v5_poseguide.py')
source = base.read_text(encoding='utf-8')
source = source.replace("walk-v5/poseguides'", "walk-v5/poseguides-refined'")
source = source.replace("(-.54,-.54,.17)", "(-.34,-.54,.42)")
exec(compile(source, str(base), 'exec'), globals())
