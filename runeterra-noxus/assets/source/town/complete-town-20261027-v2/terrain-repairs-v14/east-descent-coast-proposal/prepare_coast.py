"""Read-only source crop and diagnostic overlay for the public coast connector."""
from prepare_inputs import *
def main():
 pins=load(HERE/'input-pins.json');bg=Image.open(ROOT/pins['background']['path']).convert('RGBA');box=(742,155,753,176)
 save(HERE/'coast-target-native16x-v1.png',bg.crop(box).resize((176,336),Image.Resampling.NEAREST))
 body=Image.open(GUIDE/'all36-actual-body128-EXCLUSION.png').convert('L');roots=Image.open(GUIDE/'all36-full-structural-contact-EXCLUSION.png').convert('L');ex=ImageChops.lighter(body,roots)
 annotated=bg.copy();annotated.paste((255,0,90,255),(0,0,800,374),ex);ImageDraw.Draw(annotated).line([(746,158),(746,170),(748,172)],fill=(0,255,200),width=1)
 save(HERE/'coast-source-guide-v1.png',annotated.crop(box).resize((176,336),Image.Resampling.NEAREST))
 before=Image.open(REPORT/'before-coast-native.png');save(HERE/'coast-architecture-context-v1.png',before.crop((725,140,780,195)).resize((440,440),Image.Resampling.NEAREST))
 print('Coast input crops prepared; no artwork painted.')
if __name__=='__main__':main()
