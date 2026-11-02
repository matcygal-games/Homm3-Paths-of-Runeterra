"""Review-only views from actual selected images; never artwork or runtime inputs."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import json
import assemble_packets as common
S=common.SOURCE;P=common.PROJECT;R=common.REPORT/'heraldry-v1';payload=S/'recipe-payload-heraldry-v1'
def load(p):return json.loads(p.read_text())
def main():
 units=[p.parent.name for p in sorted(payload.glob('*/battle.json'))]
 for part in range(2):
  cohort=units[part*7:(part+1)*7];sheet=Image.new('RGBA',(1000,7*180),(35,35,35,255));draw=ImageDraw.Draw(sheet)
  for i,u in enumerate(cohort):
   draw.text((2,i*180+2),u,fill='white')
   for j,role in enumerate(('map','attackLeft','attackRight','large','small')):
    rr=load(payload/u/(role+'.json'));src=rr['groups'][0]['frames'][0]['source'] if role=='map' else rr['source'];im=Image.open(P/src).convert('RGBA');bg=common.checkbg(im.size);bg.alpha_composite(im);sheet.paste(bg,(j*120,i*180+25));draw.text((j*120+2,i*180+95),role,fill='white')
   battle=load(payload/u/'battle.json');standing=next(g for g in battle['groups'] if g['group']==2)['frames'][0];im=Image.open(P/standing['source']).convert('RGBA').crop((130,155,315,285));bg=common.checkbg(im.size);bg.alpha_composite(im);sheet.paste(bg,(610,i*180+22));draw.text((610,i*180+155),'battle actual native 1x',fill='white')
   mirror=ImageOps.mirror(Image.open(P/standing['source']).convert('RGBA'));shift=Image.new('RGBA',mirror.size);shift.paste(mirror,(-58 if battle['pivot']['x']==196 else -14,0));im=shift.crop((130,155,315,285));bg=common.checkbg(im.size);bg.alpha_composite(im);sheet.paste(bg,(805,i*180+22));draw.text((805,i*180+155),'native left same hex',fill='white')
  common.png(R/f'final-companions-and-standing-part{part+1}.png',sheet)
 shoot=Image.new('RGBA',(1200,4*500),(35,35,35,255));draw=ImageDraw.Draw(shoot)
 for i,u in enumerate(('shurimanArcher','sunArcher','sunPriest','highPriest')):
  battle=load(payload/u/'battle.json');groups={g['group']:g['frames'] for g in battle['groups']}
  for j,g in enumerate((14,15,16)):
   im=Image.open(P/groups[g][3]['source']).convert('RGBA').crop((155,160,265,285));bg=common.checkbg(im.size);bg.alpha_composite(im);shoot.paste(bg.resize((396,450),Image.Resampling.NEAREST),(j*400,i*500+25));draw.text((j*400+2,i*500+2),u+' climax4 g'+str(g)+' x155..265 y160..285;3.6x',fill='white')
 common.png(R/'final-four-shooter-climax4-detail.png',shoot)
 print('Created actual-source companion/standing and climax4 detail boards.')
if __name__=='__main__':main()
