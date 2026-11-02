"""Reproduce two bounded painted floor proposals. No final art is code-drawn.

Only uniform cover-fit, crop and alpha composition are applied to imagegen masters.
The masks are broad crop-edge seams, never root-shaped support or painted geometry.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageOps,ImageChops
HERE=Path(__file__).resolve().parent
TOWN=HERE.parents[1]
ROOT=TOWN.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2/terrain-repairs-v6/lower-proposal'
PLAN={
 'tavern':{'master':'tavern-master-v2.png','input_box':(0,300,270,374),'patch_box':(0,310,235,374),'seams':['top','right'],'state':'tavern','threshold':[191,346]},
 'foundry':{'master':'foundry-master-v1.png','input_box':(570,305,800,374),'patch_box':(590,321,800,374),'seams':['top','left'],'state':'blacksmith','threshold':[682,353]},
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def render(bg,s,mode):
 im=bg.copy();rows={r['state']:r for r in s['states']}
 chosen=[] if mode=='empty' else [site['states'][0] if mode=='base' else site['top'] for site in s['sites'] if site['id']not in('coast','grail')]
 for state in sorted(chosen,key=lambda k:rows[k]['native_z']):im.alpha_composite(Image.open(ROOT/rows[state]['native_layer']).convert('RGBA'))
 return im
def main():
 pins=json.loads((HERE/'input-pins.json').read_text());bgp=ROOT/pins['terrain']['path'];assert sha(bgp)==pins['terrain']['sha256']
 s=json.loads((TOWN/'candidate-final-v5/selection.json').read_text());assert sha(TOWN/'candidate-final-v5/selection.json')==pins['selection_sha256']
 assert all(sha(ROOT/r['path'])==r['sha256']for r in list(pins['frames'].values())+list(pins['masters'].values()))
 bg=Image.open(bgp).convert('RGBA');merged=bg.copy();allowed=Image.new('L',bg.size);records=[]
 for name,p in PLAN.items():
  ib=p['input_box'];pb=p['patch_box'];master=HERE/p['master'];native=ImageOps.fit(Image.open(master).convert('RGBA'),(ib[2]-ib[0],ib[3]-ib[1]),method=Image.Resampling.LANCZOS)
  save(HERE/f'{name}-native-v1.png',native)
  local=(pb[0]-ib[0],pb[1]-ib[1],pb[2]-ib[0],pb[3]-ib[1]);patch=native.crop(local);w,h=patch.size
  mask=Image.new('L',(w,h),255)
  for y in range(h):
   for x in range(w):
    distance=min([4]+([y]if'top'in p['seams']else[])+([w-1-x]if'right'in p['seams']else[])+([x]if'left'in p['seams']else[]))
    mask.putpixel((x,y),round(255*distance/4))
  patch.putalpha(mask);save(HERE/f'{name}-patch-rgba-v1.png',patch)
  fullmask=Image.new('L',bg.size);fullmask.paste(mask,pb[:2]);save(HERE/f'{name}-composition-mask-v1.png',fullmask)
  allowed=ImageChops.lighter(allowed,fullmask.point(lambda v:255 if v else 0))
  merged.alpha_composite(patch,pb[:2]);single=bg.copy();single.alpha_composite(patch,pb[:2]);save(HERE/f'{name}-terrain-proposal-v1.png',single)
  records.append({'site':name,'state':p['state'],'master':ref(master),'native':ref(HERE/f'{name}-native-v1.png'),'rgba_patch':ref(HERE/f'{name}-patch-rgba-v1.png'),'composition_mask':ref(HERE/f'{name}-composition-mask-v1.png'),'source_crop':'Uniform LANCZOS cover-fit to input rectangle, central crop if aspect differs.','context_input_rectangle':ib,'bounded_patch_rectangle':pb,'local_native_crop':local,'edge_alpha':'Four native-pixel linear crop-edge seam on '+','.join(p['seams'])+'; all other pixels fully opaque.','actual_entry_threshold':p['threshold'],'floor_review':'Broad horizontal paving candidate. Independent source-pixel floor/contact review remains required.'})
 save(HERE/'terrain-proposal-v1.png',merged)
 diff=ImageChops.difference(bg.convert('RGB'),merged.convert('RGB'));red,green,blue=diff.split();changed=ImageChops.lighter(ImageChops.lighter(red,green),blue).point(lambda x:255 if x else 0)
 outside=ImageChops.multiply(changed,ImageChops.invert(allowed));assert outside.getbbox()is None
 assert ImageChops.difference(bg.crop((407,316,590,365)).convert('RGB'),merged.crop((407,316,590,365)).convert('RGB')).getbbox()is None
 for mode in('empty','base','full'):
  im=render(merged,s,mode);save(REPORT/f'{mode}-native-v1.png',im)
  for name,p in PLAN.items():
   b=p['input_box'];save(REPORT/f'{mode}-{name}-native-v1.png',im.crop(b));save(REPORT/f'{mode}-{name}-4x-v1.png',im.crop(b).resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.NEAREST))
 receipt={'status':'design proposal','inputs':pins,'patches':records,'output':ref(HERE/'terrain-proposal-v1.png'),'actual_changed_bbox':changed.getbbox(),'changed_pixels':changed.histogram()[255],'outside_allowed_changed_pixels':outside.histogram()[255],'preserved_minotaur_rectangle':[407,316,590,365],'minotaur_pixels_exact':True,'unchanged_source_building_states':len(pins['frames']),'generation_records':ref(HERE/'generation-records.json'),'reproduction_script':ref(Path(__file__)),'integration':'Review candidate only. Sourceowner merges bounded RGBA patches onto owned terrain.','geometry_pass_claimed':False,'runtime_verified':False,'release_accepted':False,'limitations':['No source-plane admission inferred from generated image.','Foundry roots x582..589 remain on unchanged V5 Minotaur apron and need independent confirmation.','Ground texture seam and perspective need independent native-size review.','No native runtime performed.']}
 receipt['full_prompt_provenance']=ref(HERE/'provenance-v1.json')
 (REPORT/'receipt-v1.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'output':receipt['output'],'changed_pixels':receipt['changed_pixels'],'outside_changed':receipt['outside_allowed_changed_pixels'],'minotaur_preserved':True}))
if __name__=='__main__':main()
