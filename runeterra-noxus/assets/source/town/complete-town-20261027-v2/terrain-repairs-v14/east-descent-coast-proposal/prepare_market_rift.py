"""Reference crops only for root-authorized third public flight."""
from prepare_inputs import *
def main():
 pins=load(HERE/'input-pins.json');bg=Image.open(ROOT/pins['background']['path']).convert('RGBA');box=(554,222,580,237)
 save(HERE/'market-rift-target-native16x-v1.png',bg.crop(box).resize((416,240),Image.Resampling.NEAREST))
 body=Image.open(GUIDE/'all36-actual-body128-EXCLUSION.png').convert('L');roots=Image.open(GUIDE/'all36-full-structural-contact-EXCLUSION.png').convert('L');ex=ImageChops.lighter(body,roots)
 annotated=bg.copy();annotated.paste((255,0,90,255),(0,0,800,374),ex);ImageDraw.Draw(annotated).line([(579,233),(571,233),(564,233),(559,233)],fill=(0,255,200),width=1)
 save(HERE/'market-rift-source-guide-v1.png',annotated.crop(box).resize((416,240),Image.Resampling.NEAREST))
 before=Image.open(REPORT/'before-full-native.png');save(HERE/'market-rift-architecture-context-v1.png',before.crop((530,200,600,260)).resize((560,480),Image.Resampling.NEAREST))
 print('Market-Rift inputs prepared; no artwork painted.')
if __name__=='__main__':main()
