"""T2/T3 v5 technical guide/capture/assembly. Never paints sprites or drives VCMI."""
from pathlib import Path
import hashlib,json,shutil,sys,os
from PIL import Image,ImageDraw

ROOT=Path(os.environ.get('ZAUN_T23_ROOT',Path(__file__).resolve().parents[1])).resolve()
UNITS={'chemRavager':'human','mutantBerserker':'human','chemtechConstruct':'machine','reinforcedConstruct':'machine'}
BASE={'human':'chemRavager','machine':'chemtechConstruct'}
LAYOUTS={
 'hold-reactions':{'columns':3,'rows':3,'frames':[(2,0)]+[(1,i) for i in range(4)]+[(3,i) for i in range(4)]},
 'defend-turns':{'columns':4,'rows':3,'frames':[(4,i) for i in range(4)]+[(7,i) for i in range(4)]+[(8,i) for i in range(4)]},
 'melee-up-front':{'columns':4,'rows':3,'frames':[(11,i) for i in range(6)]+[(12,i) for i in range(6)]},
 'death-melee-down':{'columns':4,'rows':3,'frames':[(5,i) for i in range(6)]+[(13,i) for i in range(6)]},
 'shoot-up':{'columns':4,'rows':2,'frames':[(14,i) for i in range(8)]},
 'shoot-front':{'columns':4,'rows':2,'frames':[(15,i) for i in range(8)]},
 'shoot-down':{'columns':4,'rows':2,'frames':[(16,i) for i in range(8)]}}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def pin(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def prepare():
 for family,unit in BASE.items():
  old=ROOT/f'assets/source/creatures/{unit}/painted-battle-v3'
  dest=ROOT/f'assets/source/creatures/{unit}/painted-battle-v5'
  dest.mkdir(parents=True,exist_ok=True)
  identity=Image.open(old/'walk-painted/master.png').convert('RGBA')
  crop=(65,10,440,300) if family=='human' else (30,10,512,310)
  identity.crop(crop).save(dest/'upperbody-identity.png')
  for name,spec in LAYOUTS.items():
   if family=='human' and name.startswith('shoot'):continue
   cols,rows=spec['columns'],spec['rows']
   pad=128 if rows==3 and cols==4 else 0
   sheet=Image.new('RGBA',(cols*512+2*pad,rows*512))
   frames=[]
   for i,(g,f) in enumerate(spec['frames']):
    p=old/f'action-guides-v4/g{g:02d}/g{g:02d}-f{f:03d}.png'
    im=Image.open(p).convert('RGBA')
    sheet.alpha_composite(im,(pad+(i%cols)*512,(i//cols)*512))
    frames.append({'group':g,'frame':f,'guide':pin(p),'guide_cell':[pad+(i%cols)*512,(i//cols)*512,512,512]})
   path=dest/'guides'/(name+'.png');path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path)
   dump(dest/'guides'/(name+'.json'),{'status':'own pose guide only; not final art','family':family,'unit':unit,
        'columns':cols,'rows':rows,'source_size':list(sheet.size),'padding_x':pad,'frames':frames,
        'guide_helper':pin(ROOT/'scripts/zaun_t23_pose_guides_v3.py'),
        'death_cohort_camera_note':'Only g05 guide uses 1.16 orthographic factor and shift_y -0.08 to keep collapse within the source camera.'})
 for unit in ('mutantBerserker','reinforcedConstruct'):
  old=ROOT/f'assets/source/creatures/{unit}/painted-battle-v3/identity-upperbody.png'
  new=ROOT/f'assets/source/creatures/{unit}/painted-battle-v5/upperbody-identity.png'
  new.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,new)
 print(json.dumps({'guide_families':2,'base_cohorts':11,'source_only':True}))

def save(record):
 data=json.loads(Path(record).read_text(encoding='utf-8'));unit=data['unit'];name=data['cohort'];version=data.pop('version',5)
 if version not in (5,6):raise ValueError('unsupported own source version')
 if unit not in UNITS or not name.replace('-','').isalnum():raise ValueError('unowned or unsafe source')
 target=ROOT/f'assets/source/creatures/{unit}/painted-battle-v{version}/{name}/master.png'
 target.parent.mkdir(parents=True,exist_ok=True)
 source=Path(data.pop('generated_path'))
 if target.exists() and sha(target)!=sha(source):raise FileExistsError('preserve previous genuine attempt')
 shutil.copy2(source,target)
 im=Image.open(target);alpha=im.getchannel('A') if 'A' in im.getbands() else None
 inputs=[{'path':str(Path(p).resolve()),'sha256':sha(Path(p))} for p in data.pop('inputs')]
 meta={'status':'authored configuration; painted candidate','art_accepted':False,'provider':'OpenAI built-in image_gen',
       'model':None,'model_note':'The built-in tool did not expose its model identifier.',
       'rights':'Unresolved; no redistribution grant inferred.','image_generation_used':True,'inputs':inputs,
       'source_generated_path':str(source),'source_generated_sha256':sha(source),'master':pin(target),
       'geometry':{'size':list(im.size),'mode':im.mode,'alpha_extrema':list(alpha.getextrema()) if alpha else None},**data}
 dump(target.parent/'generation.json',meta)
 print(json.dumps({'unit':unit,'cohort':name,'master_sha256':sha(target),'size':im.size}))

def prepare_hardware():
 unit='reinforcedConstruct';folder=ROOT/f'assets/source/creatures/{unit}/painted-battle-v5'
 layouts={**LAYOUTS,'walk':{'columns':3,'rows':2,'frames':[(0,i) for i in range(6)]}}
 for name,spec in layouts.items():
  cols,rows=spec['columns'],spec['rows'];pad=128 if rows==3 and cols==4 else 0
  sheet=Image.new('RGBA',(cols*512+2*pad,rows*512));inputs=[]
  for i,(g,f) in enumerate(spec['frames']):
   source=folder/(f'hardware-guides/g{g:02d}/'+(f'phase{f}.png' if g==0 else f'g{g:02d}-f{f:03d}.png'))
   im=Image.open(source).convert('RGBA');sheet.alpha_composite(im,(pad+(i%cols)*512,(i//cols)*512));inputs.append(pin(source))
  path=folder/'guides-hardware'/(name+'.png');path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path)
  dump(path.with_suffix('.json'),{'status':'own guide only; no final art','frames':spec['frames'],'sources':inputs,
       'helper':pin(ROOT/'scripts/zaun_t23_hardware_guides_v5.py'),'dimensions':sheet.size,'padding_x':pad})
 print(json.dumps({'unit':unit,'hardware_guide_cohorts':len(layouts)}))

def assemble(unit,version=5):
 if unit not in UNITS:raise ValueError('unowned unit')
 # Read-only deterministic atlas cut utility; no other owner's helper is edited.
 import zaun_t57_atlas as atlas
 folder=ROOT/f'assets/source/creatures/{unit}/painted-battle-v{version}'
 report=ROOT/'review/t23-painted-battle-v5-20261021'
 out=folder/'native-candidate';groups={};masters=[];selections=[]
 names=['hold-reactions','defend-turns','melee-up-front','death-melee-down']
 if UNITS[unit]=='machine':names+=['shoot-up','shoot-front','shoot-down']
 for name in ['walk']+names:
  if name=='walk':
   master=folder/'walk/master.png'
   if unit=='reinforcedConstruct' and version==5 and (folder/'walk-hardware-green/master.png').exists():master=folder/'walk-hardware-green/master.png'
   if not master.exists():master=ROOT/f'assets/source/creatures/{unit}/painted-battle-v3/walk-painted/master.png'
   if unit=='reinforcedConstruct' and 'painted-battle-v3' in str(master):raise ValueError('rejected Reinforced v3 alpha must not enter assembly')
   spec={'columns':3,'rows':2,'frames':[(0,i) for i in range(6)]};scale=.20
   if version==6 and unit in ('chemRavager','mutantBerserker'):
    # A single whole-walk viewport camera correction, never per-pose fitting.
    scale={'chemRavager':.192,'mutantBerserker':.18}[unit]
  else:
   master=folder/name/'master.png';spec=LAYOUTS[name]
   if unit=='reinforcedConstruct' and version==5 and (folder/(name+'-hardware-green')/'master.png').exists():
    master=folder/(name+'-hardware-green')/'master.png'
   # Whole-source-viewport camera, not fitting individual body bounds.
   if spec['columns']==3:scale=.20/(Image.open(master).height/1536)
   elif spec['rows']==3:scale=.30
   else:scale=.20/(Image.open(master).height/1024)
  if version==6 and (folder/(name+'-clear')/'master.png').exists():master=folder/(name+'-clear')/'master.png'
  im=Image.open(master).convert('RGBA');labels,found=atlas.components(im,threshold=128)
  rows,extras=atlas.assign_rows(found,[spec['columns']]*spec['rows'],minimum_area=1500)
  ordered=[body for row in rows for body in row]
  ownership=atlas.ownership(labels,ordered,extras)
  first=ordered[0]
  # One reference contact anchor for this whole painted viewport. Repeated row
  # and column offsets are fixed; no per-frame body/foot alignment is allowed.
  anchor0=(first.centroid[0],float(first.bbox[3]))
  if name=='walk':
   stride=(im.width/spec['columns'],im.height/spec['rows'])
   registration_basis='Fixed source guide cell grid; no contact phase is individually fitted.'
  else:
   # The tool can preserve every pose yet compress atlas gutters. First and
   # last slots are the same neutral/recovered stance, so they define ONE
   # measured regular grid. This corrects layout, never individual anatomy.
   last=ordered[-1]
   stride=((last.centroid[0]-first.centroid[0])/(spec['columns']-1),
           (last.bbox[3]-first.bbox[3])/(spec['rows']-1))
   registration_basis='One regular grid measured between genuine first neutral and final recovered-neutral poses; no per-frame fitting.'
  master_record={'cohort':name,'master':pin(master),'scale':scale,'reference_anchor':list(anchor0),
                 'fixed_stride':list(stride),'reference_basis':registration_basis,
                 'native_registration_target':[175,266],'animation_pivot':[197,266]}
  masters.append(master_record)
  for i,((g,f),body) in enumerate(zip(spec['frames'],ordered)):
   part,evidence=atlas.subject(im,labels,body,extras,ordered,cell_ownership=ownership)
   if evidence['opaque_touches_source_edge']:raise ValueError(f'{unit}/{name} frame{i}: clipped body at master edge')
   anchor=(anchor0[0]+(i%spec['columns'])*stride[0],anchor0[1]+(i//spec['columns'])*stride[1])
   frame=atlas.register(part,evidence,scale=scale,canvas=(450,400),pivot=(175,266),anchor=anchor)
   path=out/f'g{g:02d}/g{g:02d}-f{f:03d}.png';path.parent.mkdir(parents=True,exist_ok=True);frame.save(path)
   record={'source':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'painted_master':pin(master),
           'cohort':name,'cell':i,'source_contact_anchor':list(anchor),'selection':evidence}
   groups.setdefault(str(g),[]).append(record);selections.append({'group':g,'frame':f,**record})
 # Native DEAD intentionally uses precisely the actual final painted collapse.
 death=out/'g05/g05-f005.png';dead=out/'g22/g22-f000.png';dead.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(death,dead)
 groups['22']=[{'source':dead.relative_to(ROOT).as_posix(),'sha256':sha(dead),
                'deliberate_semantics':'same already-painted final DEATH pose; no filler idle','death_source':pin(death)}]
 required=json.loads((ROOT/f'assets/recipes/creatures/{unit}-battle.json').read_text())
 for group in required['groups']:
  g=str(group['group'])
  if len(groups.get(g,[]))!=len(group['frames']):raise ValueError('incomplete actual group '+g)
 total_rows=sum((len(frames)+5)//6 for frames in groups.values())
 sheet=Image.new('RGB',(1080,total_rows*166),(52,54,51));draw=ImageDraw.Draw(sheet)
 row=0
 for g,frames in sorted(groups.items(),key=lambda p:int(p[0])):
  for i,rec in enumerate(frames):
   native=Image.open(ROOT/rec['source']).convert('RGBA');crop=native.crop((92,138,272,282))
   x=(i%6)*180;slotrow=row+i//6;y=slotrow*166+20
   sheet.paste(crop,(x,y),crop);draw.text((x+3,slotrow*166+3),f'g{int(g):02d} f{i}',fill=(235,225,201))
  row+=(len(frames)+5)//6
 sheet_path=report/(unit+f'-native-actions-v{version}.png');sheet_path.parent.mkdir(parents=True,exist_ok=True);sheet.save(sheet_path)
 producer_snapshot=ROOT/'assets/source/creatures/t23-production-v5/helpers'/(sha(Path(__file__))+'.py')
 producer_snapshot.parent.mkdir(parents=True,exist_ok=True)
 if not producer_snapshot.exists():shutil.copy2(Path(__file__),producer_snapshot)
 atlas_path=ROOT/'scripts/zaun_t57_atlas.py'
 atlas_snapshot=producer_snapshot.parent/(sha(atlas_path)+'-atlas.py')
 if not atlas_snapshot.exists():shutil.copy2(atlas_path,atlas_snapshot)
 record={'status':'authored configuration; full native source candidate, independent review pending',
         'art_accepted':False,'visual_approval_granted':False,'unit':unit,'canvas':[450,400],'pivot':[197,266],
         'complete_group_counts':{g:len(f) for g,f in groups.items()},'masters':masters,'groups':groups,
         'contact_sheet':pin(sheet_path),'assembly':'Only technical source alpha-cell selection, uniform whole-viewport scale and fixed grid registration. No painting, limb deformation, mirrored poses or individually fitted bodies.',
         'atlas_selector':pin(atlas_snapshot),'producer':pin(producer_snapshot),
         'reproduction':'Set ZAUN_T23_ROOT to the absolute project root, add its scripts directory to PYTHONPATH, verify the pinned atlas utility against scripts/zaun_t57_atlas.py, then execute this immutable producer snapshot with assemble <unit> or assemble-green <unit>.',
         'rights':'Unresolved; no redistribution grant inferred.'}
 dump(folder/f'battle-cohort-v{version}.json',record)
 print(json.dumps({'unit':unit,'native_source_frames':sum(len(v) for v in groups.values()),'contact_sheet':str(sheet_path),'recipes_changed':False}))

if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='save':save(sys.argv[2])
 elif sys.argv[1]=='prepare-hardware':prepare_hardware()
 elif sys.argv[1]=='assemble':assemble(sys.argv[2])
 elif sys.argv[1]=='assemble-green':assemble(sys.argv[2],6)
 else:raise ValueError('unknown technical command')
