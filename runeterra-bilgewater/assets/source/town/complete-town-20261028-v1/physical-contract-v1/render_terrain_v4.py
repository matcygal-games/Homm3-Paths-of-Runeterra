"""Render manually corrected actual stair/level traces, preserving V1/V2."""
from pathlib import Path
import render_terrain as original
HERE=Path(__file__).resolve().parent
original.TRACE=HERE/'terrain-trace-v4'
original.REPORT=original.REPORT/'terrain-v4'
if __name__=='__main__':original.main()
