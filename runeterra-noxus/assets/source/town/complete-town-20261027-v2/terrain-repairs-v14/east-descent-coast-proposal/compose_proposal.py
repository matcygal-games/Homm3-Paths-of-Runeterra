"""Uniform crop/scale/composition of genuine painted connectors only.

Composition guards preserve every existing structural root and alpha128 body.
These guards never classify their remaining pixels as walkable terrain.
"""
from prepare_inputs import *
PLAN={
 'descent':{'master':'descent-master-v1.png','box':(654,160,711,215),'crop':None,'polygon':[(660,166),(676,166),(678,181),(687,185),(699,193),(700,215),(684,215),(682,202),(674,196),(663,188),(657,180)],'preserve_through_row':165},
 'coast':{'master':'coast-master-v1.png','box':(742,155,753,176),'crop':(144,45,888,1465),'polygon':[(744,158),(749,158),(750,176),(743,176),(743,165)],'preserve_through_row':157},
}
def main():
 pins=load(HERE/'input-pins.json');bgp=ROOT/pins['background']['path'];assert sha(bgp)==pins['background']['sha256']
 body=Image.open(ROOT/pins['exclusions']['all36-actual-body128-EXCLUSION.png']['path']).convert('L');roots=Image.open(ROOT/pins['exclusions']['all36-full-structural-contact-EXCLUSION.png']['path']).convert('L');ex=ImageChops.lighter(body,roots)
 for p in pins['exclusions'].values():assert sha(ROOT/p['path'])==p['sha256']
 for r in pins['states']:assert sha(ROOT/r['frame']['path'])==r['frame']['sha256']and sha(ROOT/r['painted_master']['path'])==r['painted_master']['sha256']
 bg=Image.open(bgp).convert('RGBA');merged=bg.copy();allowed=Image.new('L',bg.size);records=[]
 for name,p in PLAN.items():
  box=p['box'];master=HERE/p['master'];source=Image.open(master).convert('RGBA')
  if p['crop']:source=source.crop(p['crop'])
  native=ImageOps.fit(source,(box[2]-box[0],box[3]-box[1]),method=Image.Resampling.LANCZOS);save(HERE/f'{name}-native-v1.png',native)
  mask=Image.new('L',bg.size);ImageDraw.Draw(mask).polygon(p['polygon'],fill=255);mask=ImageChops.multiply(mask,ImageChops.invert(ex));ImageDraw.Draw(mask).rectangle((0,0,799,p['preserve_through_row']),fill=0)
  allowed=ImageChops.lighter(allowed,mask);save(HERE/f'{name}-composition-mask-v1.png',mask)
  patch=native.copy();patch.putalpha(mask.crop(box));save(HERE/f'{name}-patch-rgba-v1.png',patch)
  merged.alpha_composite(patch,box[:2]);single=bg.copy();single.alpha_composite(patch,box[:2]);save(HERE/f'{name}-terrain-proposal-v1.png',single)
  records.append({'name':name,'master':ref(master),'master_original_size':Image.open(master).size,'source_crop':p['crop'],'native_box':box,'composition_polygon':p['polygon'],'preserve_through_row':p['preserve_through_row'],'native':ref(HERE/f'{name}-native-v1.png'),'rgba_patch':ref(HERE/f'{name}-patch-rgba-v1.png'),'composition_mask':ref(HERE/f'{name}-composition-mask-v1.png'),'method':'Uniform LANCZOS cover-fit of genuine painted source crop, then alpha composition. Broad polygon clipped by protected original opaque bodies/full structural roots. No creative raster operations or floor classification.'})
 save(HERE/'terrain-proposal-v1.png',merged)
 diff=ImageChops.difference(bg.convert('RGB'),merged.convert('RGB'));r,g,b=diff.split();changed=ImageChops.lighter(ImageChops.lighter(r,g),b).point(lambda a:255 if a else 0)
 assert ImageChops.multiply(changed,ImageChops.invert(allowed)).getbbox()is None
 assert ImageChops.multiply(changed,body).getbbox()is None
 assert ImageChops.multiply(changed,roots).getbbox()is None
 s=load(TOWN/'candidate-final-v5/selection.json');rows={r['state']:r for r in pins['states']}
 for mode in('empty','base','full','coast'):
  im=merged.copy();chosen=[]if mode=='empty'else[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in('coast','grail')]
  if mode=='coast':chosen.append('ship')
  for state in sorted(chosen,key=lambda k:rows[k]['native_z']):im.alpha_composite(Image.open(ROOT/rows[state]['frame']['path']).convert('RGBA'))
  save(REPORT/f'after-{mode}-native-v1.png',im)
  for name,p in PLAN.items():
   box=p['box'];save(REPORT/f'after-{mode}-{name}-native-v1.png',im.crop(box));save(REPORT/f'after-{mode}-{name}-12x-v1.png',im.crop(box).resize(((box[2]-box[0])*12,(box[3]-box[1])*12),Image.Resampling.NEAREST))
 receipt={'status':'design proposal','source':pins['background'],'source_guide':pins['source_guide'],'source_index':pins['source_index'],'approved_silo_override':pins['approved_silo_override'],'patches':records,'output':ref(HERE/'terrain-proposal-v1.png'),'script':ref(Path(__file__)),'generation_records':ref(HERE/'generation-records-v1.json'),'changed_pixels':changed.histogram()[255],'outside_composition_changes':0,'opaque_body_changes':0,'structural_root_changes':0,'unchanged_building_frames':36,'unchanged_painted_masters':36,'coast_water_rule':'Only bounded new opaque painted construction may occlude former water. All pixels outside actual composition mask remain exact. Visible water classification awaits independent source review.','geometry_pass_claimed':False,'runtime_verified':False,'release_accepted':False}
 (REPORT/'receipt-v1.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'output':receipt['output'],'changed_pixels':receipt['changed_pixels'],'body_and_root_changes':0}))
if __name__=='__main__':
 from PIL import ImageOps
 main()
