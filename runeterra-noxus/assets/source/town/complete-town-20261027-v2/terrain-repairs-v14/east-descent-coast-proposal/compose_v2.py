"""Three genuine 2D public connector crops, no new code-drawn artwork."""
from prepare_inputs import *
from PIL import ImageOps
from compose_proposal import PLAN
from copy import deepcopy
def main():
 pins=load(HERE/'input-pins.json');bgp=ROOT/pins['background']['path'];assert sha(bgp)==pins['background']['sha256']
 actual_index=TOWN/'native-transforms-v14/states.json';assert sha(actual_index)=='e5101798a4336583495f9fbcb04ad780e54cca81275677b94e191ac69f233023';current=load(actual_index);rows={r['state']:r for r in current['states']}
 for r in pins['states']:
  assert sha(ROOT/rows[r['state']]['frame']['path'])==rows[r['state']]['frame']['sha256'];assert sha(ROOT/r['frame']['path'])==r['frame']['sha256'];assert sha(ROOT/r['painted_master']['path'])==r['painted_master']['sha256']
  current_frame=Image.open(ROOT/rows[r['state']]['frame']['path']).convert('RGBA');guide_frame=Image.open(ROOT/r['frame']['path']).convert('RGBA');assert current_frame.getchannel('A').tobytes()==guide_frame.getchannel('A').tobytes()
  dr,dg,db=ImageChops.difference(current_frame.convert('RGB'),guide_frame.convert('RGB')).split();opaque=guide_frame.getchannel('A').point(lambda a:255 if a==255 else 0);assert ImageChops.multiply(ImageChops.lighter(ImageChops.lighter(dr,dg),db),opaque).getbbox()is None
 for p in pins['exclusions'].values():assert sha(ROOT/p['path'])==p['sha256']
 body=Image.open(ROOT/pins['exclusions']['all36-actual-body128-EXCLUSION.png']['path']).convert('L');roots=Image.open(ROOT/pins['exclusions']['all36-full-structural-contact-EXCLUSION.png']['path']).convert('L');ex=ImageChops.lighter(body,roots)
 plan=deepcopy(PLAN);plan['coast'].update(master='coast-master-v2.png',crop=(150,67,857,1417))
 plan['market-rift']={'master':'market-rift-master-v2.png','box':(554,231,580,237),'crop':(0,117,2170,609),'polygon':[(554,231),(579,231),(579,236),(554,236)],'preserve_through_row':230}
 bg=Image.open(bgp).convert('RGBA');merged=bg.copy();allowed=Image.new('L',bg.size);records=[]
 for name,p in plan.items():
  box=p['box'];master=HERE/p['master'];source=Image.open(master).convert('RGBA');crop=p['crop']
  if crop=='remove-black-letterbox':crop=source.convert('RGB').getbbox()
  if crop:source=source.crop(crop)
  native=ImageOps.fit(source,(box[2]-box[0],box[3]-box[1]),method=Image.Resampling.LANCZOS);save(HERE/f'{name}-native-v2.png',native)
  mask=Image.new('L',bg.size);ImageDraw.Draw(mask).polygon(p['polygon'],fill=255);mask=ImageChops.multiply(mask,ImageChops.invert(ex));ImageDraw.Draw(mask).rectangle((0,0,799,p['preserve_through_row']),fill=0)
  extraction=None
  if name=='coast':
   wood=Image.new('L',native.size)
   for y in range(native.height):
    for x in range(native.width):
     r,g,b,a=native.getpixel((x,y));wood.putpixel((x,y),255 if r>=b+8 and g>=b-3 and r>=25 else 0)
   component=Image.new('L',bg.size);component.paste(wood,box[:2]);mask=ImageChops.multiply(mask,component);extraction='Technical warm wood-vs-blue-water alpha extraction from genuine native painted pixels: r>=b+8,g>=b-3,r>=25. No RGB pixels invented; wood surface is not automatically walking floor.'
  allowed=ImageChops.lighter(allowed,mask);save(HERE/f'{name}-composition-mask-v2.png',mask)
  patch=native.copy();patch.putalpha(mask.crop(box));save(HERE/f'{name}-patch-rgba-v2.png',patch);merged.alpha_composite(patch,box[:2]);single=bg.copy();single.alpha_composite(patch,box[:2]);save(HERE/f'{name}-terrain-proposal-v2.png',single)
  records.append({'name':name,'master':ref(master),'master_size':Image.open(master).size,'source_crop':crop,'native_box':box,'composition_polygon':p['polygon'],'rgba_patch':ref(HERE/f'{name}-patch-rgba-v2.png'),'mask':ref(HERE/f'{name}-composition-mask-v2.png'),'conversion':'Uniform LANCZOS cover-fit of genuine painted crop; technical source-body/root exclusion and alpha composition only.','wood_alpha_extraction':extraction})
 save(HERE/'terrain-proposal-v2.png',merged);diff=ImageChops.difference(bg.convert('RGB'),merged.convert('RGB'));r,g,b=diff.split();changed=ImageChops.lighter(ImageChops.lighter(r,g),b).point(lambda a:255 if a else 0)
 assert ImageChops.multiply(changed,ImageChops.invert(allowed)).getbbox()is None;assert ImageChops.multiply(changed,body).getbbox()is None;assert ImageChops.multiply(changed,roots).getbbox()is None
 coastmask=Image.open(HERE/'coast-composition-mask-v2.png').convert('L');coastdiff=ImageChops.difference(bg.crop((742,155,753,176)).convert('RGB'),merged.crop((742,155,753,176)).convert('RGB'));cr,cg,cb=coastdiff.split();coastchanged=ImageChops.lighter(ImageChops.lighter(cr,cg),cb).point(lambda a:255 if a else 0);assert ImageChops.multiply(coastchanged,ImageChops.invert(coastmask.crop((742,155,753,176)))).getbbox()is None
 s=load(TOWN/'candidate-final-v5/selection.json')
 for mode in('empty','base','full','coast'):
  im=merged.copy();chosen=[]if mode=='empty'else[site['states'][0]if mode=='base'else site['top']for site in s['sites']if site['id']not in('coast','grail')]
  if mode=='coast':chosen.append('ship')
  for state in sorted(chosen,key=lambda k:rows[k]['native_z']):im.alpha_composite(Image.open(ROOT/rows[state]['frame']['path']).convert('RGBA'))
  save(REPORT/f'after-{mode}-native-v2.png',im)
  for name,p in plan.items():
   box=p['box'];save(REPORT/f'after-{mode}-{name}-native-v2.png',im.crop(box));save(REPORT/f'after-{mode}-{name}-16x-v2.png',im.crop(box).resize(((box[2]-box[0])*16,(box[3]-box[1])*16),Image.Resampling.NEAREST))
 receipt={'status':'design proposal','source':pins['background'],'actual_current_source_index':ref(actual_index),'source_exclusion_guide':pins['source_guide'],'source_input_pins':ref(HERE/'input-pins.json'),'patches':records,'output':ref(HERE/'terrain-proposal-v2.png'),'script':ref(Path(__file__)),'generation_records':[ref(HERE/'generation-records-v1.json'),ref(HERE/'generation-records-v2.json')],'changed_pixels':changed.histogram()[255],'outside_composition_changes':0,'opaque_body_changes':0,'structural_root_changes':0,'unchanged_building_frames':36,'unchanged_painted_masters':36,'coast_blue_water_outside_actual_painted_wood_exact':True,'geometry_pass_claimed':False,'runtime_verified':False,'release_accepted':False}
 (REPORT/'receipt-v2.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'output':receipt['output'],'changed_pixels':receipt['changed_pixels'],'body_and_root_changes':0,'patches':[{'name':r['name'],'crop':r['source_crop']}for r in records]}))
if __name__=='__main__':main()
