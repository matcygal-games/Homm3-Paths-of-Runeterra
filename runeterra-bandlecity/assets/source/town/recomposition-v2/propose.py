"""Review-only deterministic placement of existing own painted masters."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
REPORT = ROOT / 'build/reports/art-review/town/recomposition-v2'
RECTS = {
 'hall': [265, 108, 225, 192],
 'fortification': [282, 4, 167, 127],
 'guild': [174, 17, 86, 113],
 'tavernAcademy': [0, 235, 203, 139],
 'market': [159, 223, 174, 121],
 'engineering': [354, 231, 220, 139],
 'portal': [485, 32, 104, 98],
 'garden': [689, 252, 111, 104],
 'fountain': [301, 258, 76, 101],
 'dwelling1': [4, 184, 161, 117],
 'dwelling2': [140, 111, 137, 106],
 'dwelling3': [644, 133, 156, 130],
 'dwelling4': [552, 221, 173, 139],
 'dwelling5': [513, 109, 127, 133],
 'dwelling6': [7, 68, 144, 112],
 'dwelling7': [641, 2, 151, 139],
 'coast': [703, 311, 97, 63],
 'grailOrnament': [328, 27, 64, 61],
}

def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
 path.parent.mkdir(parents=True, exist_ok=True)
 path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

def fit(master, rectangle):
 image=Image.open(master).convert('RGBA')
 # Same whole-returned-alpha fitting as current production; no recoloring.
 box=image.getchannel('A').getbbox()
 if master.parent.parent.name in ('special4','grail'):
  # Those two isolated masters carry large nearly-transparent outer residue.
  # Crop only outside alpha>=8+8px margin, retaining internal RGBA unchanged.
  b=image.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox()
  box=(max(0,b[0]-8),max(0,b[1]-8),min(image.width,b[2]+8),min(image.height,b[3]+8))
 image=ImageOps.contain(image.crop(box), tuple(rectangle[2:]), Image.Resampling.LANCZOS)
 out=Image.new('RGBA',(800,374))
 x,y,w,h=rectangle
 out.alpha_composite(image,(x+(w-image.width)//2,y+h-image.height))
 return out,list(image.size)

def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 original=json.loads((ROOT/'design/town-visuals.json').read_text())
 bg=ROOT/'assets/source/town/background-v1/native.png'
 canvas=Image.open(bg).convert('RGBA')
 rows=[]
 layers={}
 for site in original['sites']:
  rect=RECTS[site['id']]
  z=rect[1]+rect[3]
  if site['id']=='grailOrnament': z=132
  for state in site['states']:
   master=ROOT/site['source'][state]
   layer,size=fit(master,rect)
   layers[state]=layer
   rows.append({'state':state,'site':site['id'],'master':str(master.relative_to(ROOT)).replace('\\','/'),'master_sha256':sha(master),'composition_rectangle':rect,'native_z':z,'fit_size':size,'visual_approval_granted':False})
 sites=[]
 for site in original['sites']:
  rect=RECTS[site['id']]
  row=next(r for r in rows if r['state']==site['states'][-1])
  sites.append({'id':site['id'],'states':site['states'],'composition_rectangle':rect,'native_z':row['native_z'],'center':[rect[0]+rect[2]//2,rect[1]+rect[3]//2],'old_rectangle':site['composition_rectangle'],'relative_width':round(rect[2]/site['composition_rectangle'][2],3)})
 selected=sorted(sites,key=lambda s:s['native_z'])
 for site in selected: canvas.alpha_composite(layers[site['states'][-1]])
 canvas.save(REPORT/'proposal-native.png')
 annotated=canvas.copy(); draw=ImageDraw.Draw(annotated)
 for site in selected:
  x,y,w,h=site['composition_rectangle']
  draw.rectangle((x,y,x+w-1,y+h-1),outline=(240,190,60,255))
  draw.text((x+2,y+2),site['id'],fill=(255,255,220,255),stroke_width=1,stroke_fill=(20,20,15,255))
 annotated.save(REPORT/'proposal-sites.png')
 above=Image.new('L',(800,374)); metrics=[]
 for site in reversed(selected):
  state=site['states'][-1]
  mask=layers[state].getchannel('A').point(lambda p:255 if p>=128 else 0)
  exposed=ImageChops.subtract(mask,above)
  metrics.append({'site':site['id'],'state':state,'silhouette_pixels':sum(mask.histogram()[128:]),'exposed_click_pixels':sum(exposed.histogram()[128:]),'exposed_bbox':exposed.getbbox()})
  above=ImageChops.lighter(above,mask)
 sheet=Image.new('RGBA',(800,374*2+24),(32,29,24,255))
 old=Image.open(ROOT/'build/reports/art-review/town/conversion-885ec7cbfde7020b/full-town-native.png')
 sheet.alpha_composite(old,(0,0));sheet.alpha_composite(canvas,(0,398))
 ImageDraw.Draw(sheet).text((8,380),'Current native composite above / proposed layout on unchanged terrain below',(255,230,180,255))
 sheet.save(REPORT/'comparison-native.png')
 state_sheet=Image.new('RGBA',(1000,140*7),(34,31,27,255))
 sd=ImageDraw.Draw(state_sheet)
 for i,row in enumerate(rows):
  subject=layers[row['state']]
  box=subject.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox()
  thumb=ImageOps.contain(subject.crop(box),(190,110),Image.Resampling.LANCZOS)
  xx=(i%5)*200;yy=(i//5)*140
  state_sheet.alpha_composite(thumb,(xx+(200-thumb.width)//2,yy))
  sd.text((xx+4,yy+112),row['state'],fill=(240,225,195,255))
  sd.text((xx+4,yy+124),str(row['composition_rectangle'])+' z'+str(row['native_z']),fill=(180,175,160,255))
 state_sheet.save(REPORT/'proposal-all-states.png')
 conservative=[];all_above=Image.new('L',(800,374))
 for site in reversed(selected):
  site_union=Image.new('L',(800,374))
  for state in site['states']:
   mask=layers[state].getchannel('A').point(lambda p:255 if p>=128 else 0)
   exp=ImageChops.subtract(mask,all_above)
   conservative.append({'state':state,'site':site['id'],'silhouette_pixels':sum(mask.histogram()[128:]),'conservative_exposed_click_pixels':sum(exp.histogram()[128:]),'exposed_bbox':exp.getbbox()})
   site_union=ImageChops.lighter(site_union,mask)
  all_above=ImageChops.lighter(all_above,site_union)
 old_union=Image.new('L',(800,374))
 for site in original['sites']:
  state=site['states'][-1]
  old_layer=Image.open(ROOT/site['selected_state_art'][state]['native_layer']).convert('RGBA')
  old_union=ImageChops.lighter(old_union,old_layer.getchannel('A').point(lambda p:255 if p>=128 else 0))
 old_coverage=sum(old_union.histogram()[128:])/(800*374)
 value={'status':'design proposal','canvas':[800,374],'terrain':str(bg.relative_to(ROOT)).replace('\\','/'),'terrain_sha256':sha(bg),'sites':sites,'rows':rows,'exposed_click_metrics':metrics,'conservative_all_states_click_metrics':conservative,'coverage_pixels':sum(above.histogram()[128:]),'canvas_coverage_fraction':sum(above.histogram()[128:])/(800*374),'previous_canvas_coverage_fraction':old_coverage,'note':'Existing own paintings only. Terrain remains unchanged in this proposal; repaint terrain next to follow irregular inhabited clusters. No art acceptance.'}
 write(HERE/'proposal-layout.json',value);write(REPORT/'proposal-layout.json',value)
 print(json.dumps({'report':str(REPORT),'coverage':value['canvas_coverage_fraction'],'min_exposed':min(m['exposed_click_pixels'] for m in metrics),'sites':sites},indent=2))

if __name__=='__main__':main()
