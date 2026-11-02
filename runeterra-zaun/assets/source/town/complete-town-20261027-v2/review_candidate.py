"""Native source compositions and adversarial actual-consumer checks, no staging."""
from pathlib import Path
import copy,hashlib,json,sys
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPORT=ROOT/'build/reports/complete-town-20261027-v2'
sys.path.insert(0,str(ROOT.parent/'scripts'));import faction_town_layout as geometry
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def count(im):return im.histogram()[255]
def main():
 c=read(HERE/'town-layout.json');sp=c['silhouette_plan'];families=read(HERE/'family-specs.json')['families'];by={f['id']:f for f in families};sites={s['id']:s for s in c['sites']}
 layers={s:Image.open(ROOT/r['path']).convert('RGBA') for s,r in c['frames'].items()};bg=Image.open(ROOT/c['background']['path']).convert('RGBA')
 ordered=sorted(families,key=lambda f:next(s['depth'] for s in c['sites'] if f['states'][0] in s['states']))
 def scene(mode='upgraded',absent=(),choices=None):
  out=bg.copy();selected=[]
  for i,f in enumerate(ordered):
   if f['id'] in absent or f['id'] in ('shipyard','codeOfProgress'):continue
   state=(choices or {}).get(f['id'],f['states'][0 if mode=='base' or mode=='mixed' and i%2==0 else -1]);out.alpha_composite(layers[state]);selected.append(state)
  return out,selected
 compositions={}
 for mode in ('base','upgraded','mixed'):
  full,selected=scene(mode);p=REPORT/'mixed-state-review'/(mode+'-all-native.png');save(p,full);compositions[mode]={'scene':ref(p),'states':selected,'absences':{}}
  annotated=full.copy()
  for state in selected:
   record=sp['states'][state]
   for kind,color in [('foundation_mask',(255,20,70)),('door_mask',(0,255,255))]:
    tint=Image.new('RGBA',full.size,(*color,0));tint.putalpha(Image.open(ROOT/record[kind]['path']));annotated.alpha_composite(tint)
   x,y=record['entrance'];ImageDraw.Draw(annotated).ellipse((x-2,y-2,x+2,y+2),outline=(255,255,255,255))
  p=REPORT/'contact-authoring'/(mode+'-complete-contacts-and-entrances-native.png');save(p,annotated);compositions[mode]['contacts_and_entrances']=ref(p)
  for absent in ('augmentationWorkshop','augmentationClinic','dwellingConstruct','dwellingRavager','scrapExchange'):
   im,sel=scene(mode,(absent,));p=REPORT/'mixed-state-review'/(mode+'-absent-'+absent+'-native.png');save(p,im)
   changed=ImageChops.difference(full.convert('RGB'),im.convert('RGB')).convert('L').point(lambda v:255 if v else 0)
   if not changed.getbbox():raise AssertionError('Functional removal has no visible pixels: '+mode+'/'+absent)
   compositions[mode]['absences'][absent]={'scene':ref(p),'states':sel,'changed_visible_pixels':count(changed),'changed_bounds':list(changed.getbbox())}
 case_rows=[]
 for approval in sp['foundation_occlusions']:
  a,b=approval['behind'],approval['front'];case=read(ROOT/approval['source_case']['path']);case['source_case_file']=approval['source_case'];case['evidence']=approval['evidence'];case['state_intersections']=[]
  for rear in by[a]['states']:
   foot=Image.open(ROOT/sp['states'][rear]['foundation_mask']['path'])
   for front in by[b]['states']:
    body=Image.open(ROOT/sp['states'][front]['body_mask']['path']);hidden=ImageChops.multiply(foot,body)
    if not hidden.getbbox():continue
    choices={a:rear,b:front};full,states=scene(choices=choices);absent,_=scene(absent=(b,),choices=choices);folder=REPORT/'root-state-review'/(a+'--'+b)/(rear+'--'+front)
    save(folder/'full-native.png',full);save(folder/'front-absent-native.png',absent)
    overlay=full.copy();t=Image.new('RGBA',full.size,(255,0,255,0));t.putalpha(hidden);overlay.alpha_composite(t);save(folder/'root-overlay-native.png',overlay)
    bb=hidden.getbbox();crop=(max(0,bb[0]-15),max(0,bb[1]-18),min(800,bb[2]+15),min(374,bb[3]+18));w,h=crop[2]-crop[0],crop[3]-crop[1]
    board=Image.new('RGB',(w*3,h+16),(25,25,25));d=ImageDraw.Draw(board)
    for i,(name,im) in enumerate((('actual selected',full),('front absent',absent),('root intersection',overlay))):board.paste(im.crop(crop),(i*w,16));d.text((i*w+2,2),name,fill='white')
    save(folder/'contact-native-detail.png',board)
    case['state_intersections'].append({'rear':rear,'front':front,'pixels':count(hidden),'bounds':list(bb),'actual_foundation':sp['states'][rear]['foundation_mask'],'detail':ref(folder/'contact-native-detail.png'),'full':ref(folder/'full-native.png'),'front_absent':ref(folder/'front-absent-native.png'),'overlay':ref(folder/'root-overlay-native.png')})
  case_rows.append(case)
 for state,record in sp['states'].items():
  im=bg.copy();im.alpha_composite(layers[state])
  for key,color in [('foundation_mask',(255,20,70)),('door_mask',(0,255,255))]:
   tint=Image.new('RGBA',im.size,(*color,0));tint.putalpha(Image.open(ROOT/record[key]['path']));im.alpha_composite(tint)
  x,y=record['entrance'];ImageDraw.Draw(im).ellipse((x-2,y-2,x+2,y+2),outline='white');save(REPORT/'contact-authoring'/(state+'-contact-and-entrance-native.png'),im)
 write(REPORT/'all-state-root-review.json',{'status':'authored configuration','annotation_basis':'Explicit per-state manually authored lower masonry/platform contact polylines and visible threshold/frontage anchors in contact_traces.py, reviewed against all36 native source crops. A five-pixel contact band clips to actual alpha8. Full source silhouettes remain unchanged. Doors include their genuine threshold-to-court apron. No percentage-width or minimum-height rule and no nearest-free-pixel entrance selection remains. Shared city parapets and external stairs stay terrain.','trace_source':ref(HERE/'contact_traces.py'),'remaining_visual_question':'Coordinator review of complete support-wall contacts, actual visible threshold anchors, and bounded supported-terrace cases. No automatic physical approval.','cases':case_rows,'compositions':compositions,'native_verified':False,'release_accepted':False})
 # Mutations are confined to already isolated converter1; original bytes are
 # restored after every probe. Changed pins deliberately reach physical checks.
 scratch=REPORT/'conversion-1';design_path=scratch/'design/town-visuals.json';contract_path=scratch/(HERE/'town-layout.json').relative_to(ROOT);orig_design=design_path.read_bytes();orig_contract=contract_path.read_bytes();content={'factions':read(ROOT/'content/factions.json')}
 for state,z in read(HERE/'content-z-patch.json')['values'].items():content['factions']['zaun']['town']['structures'][state]['z']=z
 checks=[]
 def probe(name,change,expected):
  contract=copy.deepcopy(c);trial=copy.deepcopy(content);originals={}
  def image_change(reference,fn):
   p=scratch/reference['path'];originals[p]=p.read_bytes();im=Image.open(p).copy();im=fn(im);save(p,im);reference['sha256']=sha(p)
  try:
   change(contract,trial,image_change);write(contract_path,contract);design=read(design_path);design['layout_contract']['sha256']=sha(contract_path);write(design_path,design)
   errors,deps=geometry.inspect(scratch,trial,'zaun');ok=not errors if expected is None else any(expected in e for e in errors)
   checks.append({'name':name,'passed':ok,'expected_error':expected,'actual_errors':errors,'dependencies':len(deps)})
   if not ok:raise AssertionError(checks[-1])
  finally:
   for p,data in originals.items():p.write_bytes(data)
   design_path.write_bytes(orig_design);contract_path.write_bytes(orig_contract)
 def erase_support(contract,trial,edit):
  foundation=Image.open(scratch/contract['silhouette_plan']['states']['marketplace']['foundation_mask']['path']);xy=next((x,y) for y in range(374) for x in range(800) if foundation.getpixel((x,y)))
  def fn(im):im.putpixel(xy,0);return im
  edit(contract['silhouette_plan']['support_mask'],fn)
 def block_path(contract,trial,edit):
  body=Image.open(scratch/contract['silhouette_plan']['states']['capitol']['body_mask']['path']);xy=next((x,y) for y in range(374) for x in range(800) if body.getpixel((x,y)))
  def fn(im):
   near=min(((x,y) for y in range(374) for x in range(800) if im.getpixel((x,y))),key=lambda p:abs(p[0]-xy[0])+abs(p[1]-xy[1]));ImageDraw.Draw(im).line((near,(xy[0],near[1]),xy),fill=255);return im
  edit(contract['silhouette_plan']['paths_mask'],fn)
 def disconnected(contract,trial,edit):
  def fn(im):return Image.new('L',im.size)
  edit(contract['silhouette_plan']['states']['special2']['approach_mask'],fn)
 def wrong_body(contract,trial,edit):
  def fn(im):return Image.new('L',im.size,255)
  edit(contract['silhouette_plan']['states']['special1']['body_mask'],fn)
 def giant_overlap(contract,trial,edit):
  edit(contract['silhouette_plan']['overlaps'][0]['mask'],lambda im:Image.new('L',im.size,255))
 def giant_root(contract,trial,edit):
  edit(contract['silhouette_plan']['foundation_occlusions'][0]['mask'],lambda im:Image.new('L',im.size,255))
 def no_approval(contract,trial,edit):contract['silhouette_plan']['foundation_occlusions']=[]
 def wrong_z(contract,trial,edit):trial['factions']['zaun']['town']['structures']['capitol']['z']+=1
 def no_state(contract,trial,edit):contract['silhouette_plan']['complete_scene_states'].remove('special1')
 def whole_marine(contract,trial,edit):edit(contract['silhouette_plan']['states']['ship']['marine_support_mask'],lambda im:Image.new('L',im.size,255))
 for name,change,expected in [('positive exact candidate',lambda *a:None,None),('unsupported actual root',erase_support,'Actual foundation lacks level support'),('street through actual body',block_path,'Global path passes through'),('missing actual approach',disconnected,'nonempty'),('forged whole body',wrong_body,'Body mask differs'),('giant overlap permission',giant_overlap,'Depth approval must equal'),('giant root permission',giant_root,'Foundation approval must equal'),('missing projected-root approval',no_approval,'unapproved rear foundation'),('wrong native z',wrong_z,'depth must equal'),('missing complete state',no_state,'every ordinary physical site'),('whole-water marine exemption',whole_marine,'Marine support must trace'),('positive after restored negatives',lambda *a:None,None)]:probe(name,change,expected)
 write(REPORT/'actual-negative-checks.json',{'status':'authored configuration','helper':{'path':'../scripts/faction_town_layout.py','sha256':sha(ROOT.parent/'scripts/faction_town_layout.py')},'checks':checks,'checks_passed':len(checks),'source_scratch_restored':design_path.read_bytes()==orig_design and contract_path.read_bytes()==orig_contract,'runtime_verified':False,'release_accepted':False})
 print(json.dumps({'actual_checks_passed':len(checks),'root_cases':len(case_rows),'native_scenes':len(compositions)*6}))
if __name__=='__main__':main()
