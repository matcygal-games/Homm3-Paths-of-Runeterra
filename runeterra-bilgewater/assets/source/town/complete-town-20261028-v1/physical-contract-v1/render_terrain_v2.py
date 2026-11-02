"""Render the second explicit manual terrain trace without changing V1 history."""
from pathlib import Path
import render_terrain as original
HERE = Path(__file__).resolve().parent
original.TRACE = HERE / 'terrain-trace-v2'
original.REPORT = original.REPORT / 'terrain-v2'
if __name__ == '__main__':
    original.main()
