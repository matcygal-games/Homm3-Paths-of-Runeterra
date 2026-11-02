"""Native-mask geometry validation plus destructive in-memory negative controls."""
from pathlib import Path
import json,hashlib,copy
from PIL import Image,ImageChops,ImageFilter,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/painted-town-community-20261024-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def opaque(im):return im.getchannel('A').point(lambda p:255 if p>=128 else 0)
def pixels(im):return sum(im.histogram()[128:])
def poly(points):
 im=Image.new('L',(800,374));ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=255);return im
def geometry(data,layers,water=None,floor=None):
 failures=[];checks=0;stats={};water=water if water is not None else poly(data['terrain']['water_polygon']);floor=floor if floor is not None else poly(data['terrain']['buildable_floor_polygon'])
 by={r['state']:r for r in data['states']};masks={s:opaque(im) for s,im in layers.items()}
 def check(ok,code,detail):
  nonlocal checks
  checks+=1
  if not ok:failures.append({'code':code,'detail':detail})
 for state,im in layers.items():
  row=by[state];m=masks[state];bb=m.getbbox();check(im.mode=='RGBA' and im.size==(800,374) and bb is not None,'canvas',state)
  if bb is None:continue
  foot=m.copy();foot.paste(0,(0,0,800,max(0,bb[3]-8)))
  wet=pixels(ImageChops.multiply(foot,water));air=pixels(ImageChops.multiply(foot,ImageChops.invert(floor)))
  if row['site']!='shipyard':
   check(wet==0,'water',{'state':state,'pixels':wet});check(air==0,'unsupported',{'state':state,'pixels':air})
  check(row['native_z']==row['composition_rectangle'][1]+row['composition_rectangle'][3],'depth',state)
  check(pixels(m)>=40,'click',state)
  stats[state]={'opaque_pixels':pixels(m),'footing_water_pixels':wet,'footing_unsupported_pixels':air}
 names=sorted(masks)
 for i,a in enumerate(names):
  for b in names[i+1:]:
   if by[a]['site']==by[b]['site']:continue
   n=pixels(ImageChops.multiply(masks[a],masks[b]));check(n==0,'body-overlap',{'states':[a,b],'pixels':n})
 check(len(data['sites'])==20 and len(layers)==36,'contract','20sites/36states')
 for tier in range(1,8):check(by['dwellingLvl'+str(tier)]['site']==by['dwellingUpLvl'+str(tier)]['site'],'tier-site',tier)
 for landmark in ['foundryHall','sumpRampart','shimmerInstitute','dwellingPredator']:
  site=next(s for s in data['sites'] if s['id']==landmark)
  check(site['composition_rectangle'][1]<10 and site['native_z']<160,'rear-monument',landmark)
 return {'ok':not failures,'checks':checks,'failures':failures,'stats':stats}
def main():
 data=read(ROOT/'design/town-visuals-painted-community-20261024-v1.candidate.json')
 layers={r['state']:Image.open(ROOT/r['native_layer']).convert('RGBA') for r in data['states']}
 result=geometry(data,layers);extra=[]
 def check(ok,label):extra.append({'ok':bool(ok),'check':label})
 for row in data['states']:
  state=row['state'];folder=HERE/'structures'/state;im=layers[state];m=opaque(im)
  check(sha(ROOT/row['master'])==row['master_sha256'],state+' selected master SHA')
  check(sha(ROOT/row['native_layer'])==row['native_layer_sha256'],state+' native layer SHA')
  area=Image.open(folder/'area.png').convert('RGBA');border=Image.open(folder/'border.png').convert('RGBA')
  check(ImageChops.difference(area.getchannel('A'),m).getbbox() is None,state+' exact click mask')
  check(ImageChops.difference(border.getchannel('A'),ImageChops.subtract(m.filter(ImageFilter.MaxFilter(3)),m)).getbbox() is None,state+' outward onepx border')
  check(Image.open(folder/'construction.png').size==(150,70),state+' HALL150x70')
  check(Image.open(folder/'campaign.png').size==(58,64),state+' optional campaign58x64')
 for binding in data['recipe_bindings']:
  recipe=read(ROOT/binding['candidate']);check(sha(ROOT/binding['candidate'])==binding['sha256'],binding['active']+' recipe SHA')
  for dep in recipe.get('dependencies',[]):check((ROOT/dep['path']).is_file() and sha(ROOT/dep['path'])==dep['sha256'],binding['active']+' dependency '+dep['path'])
 dock=layers['shipyard'];boat=Image.open(HERE/'structures/ship/boat-only.png').convert('RGBA');expected=dock.copy();expected.alpha_composite(boat)
 check(ImageChops.difference(expected,layers['ship']).getbbox() is None,'ship replacement includes exact selected dock+boat')
 checks=[]
 # Move an actual full selected body onto another physical site, preserving its pixels.
 bad=dict(layers);im=layers['blacksmith'];b=opaque(im).getbbox();target=opaque(layers['special2']).getbbox();shifted=Image.new('RGBA',(800,374));shifted.alpha_composite(im.crop(im.getchannel('A').getbbox()),(target[0],target[1]));bad['blacksmith']=shifted
 checks.append(('actual body moved over clinic','body-overlap',geometry(data,bad)))
 # Put an actual selected footprint into annotated coastal water.
 bad=dict(layers);crop=layers['blacksmith'].crop(layers['blacksmith'].getchannel('A').getbbox());im=Image.new('RGBA',(800,374));im.alpha_composite(crop,(690,330));bad['blacksmith']=im
 checks.append(('actual dry service moved into coastal water','water',geometry(data,bad)))
 # Remove a support patch under the real selected civic foundation.
 floor=poly(data['terrain']['buildable_floor_polygon']);m=opaque(layers['capitol']);bb=m.getbbox();ImageDraw.Draw(floor).rectangle((bb[0],bb[3]-8,bb[2],bb[3]),fill=0)
 checks.append(('canyon void under civic foundation','unsupported',geometry(data,layers,floor=floor)))
 bad=copy.deepcopy(data);next(r for r in bad['states'] if r['state']=='dwellingUpLvl7')['native_z']=370
 checks.append(('rear monument rendered at foreground depth','depth',geometry(bad,layers)))
 negatives=[{'mutation':name,'expected_code':code,'rejected':not out['ok'] and any(f['code']==code for f in out['failures']),'observed_failures':out['failures']} for name,code,out in checks]
 determinism=read(REPORT/'compiler-determinism.json');check(determinism['byte_identical'] and determinism['recipe_count']==146,'actual146recipe converter repeated byteidentical')
 output={'status':'authored configuration','ok':result['ok'] and all(x['ok'] for x in extra) and all(n['rejected'] for n in negatives),'geometry':result,'additional_checks':extra,'negative_controls':negatives,'executed_check_count':result['checks']+len(extra)+len(negatives),'visual_approval_granted':False,'runtime_verified':False}
 (REPORT/'geometry-validation.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'ok':output['ok'],'checks':output['executed_check_count'],'geometry_failures':result['failures'],'additional_failed':[x for x in extra if not x['ok']],'negative_rejections':[n['rejected'] for n in negatives]}))
 return 0 if output['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
