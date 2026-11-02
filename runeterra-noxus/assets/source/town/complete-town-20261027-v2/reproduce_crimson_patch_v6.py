"""Exact deterministic native crop of the genuine painted Crimson apron master."""
from pathlib import Path
from PIL import Image,ImageOps
import hashlib
HERE=Path(__file__).resolve().parent
im=ImageOps.fit(Image.open(HERE/'terrain/crimson-apron-master-v6.png').convert('RGBA').crop((0,57,2172,661)),(162,44),Image.Resampling.LANCZOS)
p=HERE/'terrain-repairs-v6/crimson-proposal/patch-native-v1.png'
im.save(p,compress_level=9)
assert hashlib.sha256(p.read_bytes()).hexdigest()=='6d86bd42146d7b65eed0a55c75c9305fd72915e7f857e39a48e38b33d7b70452'
