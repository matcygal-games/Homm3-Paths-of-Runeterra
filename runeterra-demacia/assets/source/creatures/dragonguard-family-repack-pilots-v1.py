"""Actual reviewed same-pose source regions; no creative bitmap edits."""
from pathlib import Path
import sys
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'scripts'))
from creature_dragonguard_motion_art import repack

REGIONS={
 'dragonguard':[
  [[91,65,466,498]],[[624,72,987,496]],[[1079,142,1536,493]],
  [[64,630,668,760],[64,760,638,958]],
  [[668,631,1081,760],[638,760,1081,963]],[[1134,558,1505,975]]],
 'veteranDragonguard':[
  [[67,46,453,478]],[[607,93,1012,475]],[[1078,120,1524,477]],
  [[41,613,626,740],[41,740,618,960]],
  [[626,583,1044,740],[618,740,1044,959]],[[1126,558,1509,964]]],
}
for unit,regions in REGIONS.items():
 folder=PROJECT/'assets/source/creatures'/unit/'dragonguard-rig-v3';frames=[]
 for index,rectangles in enumerate(regions):
  ox,oy=index%3*512,index//3*512
  frames.append({'reviewed':True,'neighbor_pixels_absent':True,
   'basis':'Actual full atlas and coordinate-labeled shared-gutter crop inspected. Sourcecell3 extended thrust tip and cell4 rear butt occupy separate vertical bands. These exact pieces retain all genuine pose limbs/weapon at one common64px translation, excluding adjacent figure pixels and faint exterior speckles; no resize, alpha paint or warp.',
   'pieces':[{'source_rect':r,'destination_offset':[r[0]-ox+64,r[1]-oy+64]} for r in rectangles]})
 repack(PROJECT,folder/'paint-action-g12-atlas-v1-generation.json',frames)
 print(unit,'actual thrust recovered losslessly into768px cells')
