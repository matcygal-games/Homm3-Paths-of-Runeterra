"""Reproduce frozen whole-pose isolation, native registration and candidate binding."""
from prepare_pose_sources import run as isolate
from assemble_native_v2 import run as assemble
from bind_recipes import run as bind
isolate()
assemble()
bind()
