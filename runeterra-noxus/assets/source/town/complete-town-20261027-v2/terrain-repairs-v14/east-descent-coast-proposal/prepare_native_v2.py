"""Deterministic isolated native previews for tighter creative iteration."""
from prepare_inputs import *
from PIL import ImageOps
def main():
 master=Image.open(HERE/'coast-master-v2.png').convert('RGBA');print('Coast master size',master.size)
 coast=ImageOps.fit(master.crop((150,67,857,1417)),(11,21),method=Image.Resampling.LANCZOS);save(HERE/'coast-native-v2-preview.png',coast);save(REPORT/'coast-native-v2-preview-32x.png',coast.resize((352,672),Image.Resampling.NEAREST))
 bg=Image.open(ROOT/load(HERE/'input-pins.json')['background']['path']).convert('RGBA');box=(554,231,580,237);save(HERE/'market-rift-target-native32x-v2.png',bg.crop(box).resize((832,192),Image.Resampling.NEAREST))
if __name__=='__main__':main()
