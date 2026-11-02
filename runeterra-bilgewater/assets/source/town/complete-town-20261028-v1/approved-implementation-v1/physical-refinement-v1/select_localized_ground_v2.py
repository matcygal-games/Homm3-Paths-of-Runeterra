"""Select genuine contextual floor recoveries below locked opaque architecture.

No geometry masks or failing contacts are inputs. Each hand-observed floor-top
contour belongs to its actual painted source. The whole source is registered
uniformly, with a bounded rigid offset against its already frozen plot.
"""
from pathlib import Path
import hashlib,json,math
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'localized-ground-selection-v2'
OUT.mkdir(exist_ok=False)
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def poly(points):
 im=Image.new('L',(800,374));ImageDraw.Draw(im).polygon(list(map(tuple,points)),fill=255);return im
plan_path=HERE/'complete-ground-recoveries-v1/plan.json';plan=json.loads(plan_path.read_text())
index_path=HERE/'ownership-separation-v5/states.json';index=json.loads(index_path.read_text())
ground=Image.open(PROJECT/index['background']).convert('RGBA')
budget=Image.new('L',(800,374))
for key in index['full_scene_states']:
 a=Image.open(PROJECT/index['states'][key]['frame']).getchannel('A').point(lambda v:255 if v==255 else 0)
 budget=ImageChops.lighter(budget,a)
sources={
 'sailors':{'plots':['sailors'],'offset':[0,0],
   'observed_horizontal_top':[[60,241],[111,241],[142,242],[153,241],[154,249],[144,252],[104,250],[64,249]],
   'note':'Source-visible timber boardwalk top. Rear retaining wall, braces below the front edge and right stair are not level.'},
 'buhru':{'plots':['buhru'],'offset':[0,0],
   'observed_horizontal_top':[[598,199],[621,201],[648,202],[678,203],[709,203],[717,208],[714,216],[691,219],[657,219],[627,217],[607,214],[598,207]],
   'note':'Source-visible broad lower stone temple court, preserving separate upper public street and left stair.'},
 'artillery':{'plots':['artillery'],'offset':[0,4],
   'observed_horizontal_top':[[186,174],[214,175],[247,176],[283,176],[315,175],[335,177],[336,183],[320,187],[289,187],[254,185],[218,183],[188,179]],
   'note':'Actual lower source stone shelf top, rigidly placed four native pixels below the contextual reference. The upper street remains separate; no vertical face is admitted.'},
 'warehouse':{'plots':['warehouse'],'offset':[0,-8],
   'observed_horizontal_top':[[0,214],[32,214],[65,215],[101,215],[125,215],[132,218],[130,225],[106,227],[68,226],[28,224],[0,222]],
   'note':'Actual horizontal service-terrace top; whole source registered to the frozen higher rear court eight pixels above its contextual recovery. Existing front street cap remains unchanged.'},
 'corsairs':{'plots':['corsairs'],'offset':[0,-6],
   'observed_horizontal_top':[[242,279],[263,277],[289,277],[317,274],[349,272],[358,281],[354,294],[330,300],[295,300],[262,292],[242,286]],
   'note':'Actual horizontal civic court, whole source registered six pixels upward against the previously frozen boat-guild plot. No hull or pier anatomy is removed by this recovery.'},
 'tavern':{'plots':['tavern-upper','tavern-lower-annex'],'offset':[0,5],
   'observed_horizontal_tops':[
      [[503,242],[527,244],[550,245],[577,249],[600,249],[612,253],[607,263],[588,269],[562,268],[539,263],[516,256],[503,251]],
      [[603,277],[615,275],[631,276],[643,280],[643,287],[632,291],[612,289],[603,285]]],
   'note':'Two actual horizontal source level planes, separated by retained public outdoor treads. Whole painting is placed five pixels lower against the frozen two-level plot; vertical retaining masonry is not level.'},
}
rows={};all_levels=Image.new('L',(800,374))
for key,data in sources.items():
 folder=HERE/('localized-'+key+'-ground-v1');reg=json.loads((folder/'registration.json').read_text());box=reg['native_context'];w,h=box[2]-box[0],box[3]-box[1]
 raw=Image.open(folder/'master-raw.png').convert('RGBA');scale=w/raw.width
 converted=raw.resize((w,math.ceil(raw.height*scale)),Image.Resampling.LANCZOS)
 native=converted.crop((0,0,w,h));canvas=Image.new('RGBA',(800,374));dx,dy=data['offset'];canvas.paste(native,(box[0]+dx,box[1]+dy))
 planned=Image.new('L',(800,374))
 for name in data['plots']:planned=ImageChops.lighter(planned,poly(plan['plots'][name]['polygon']))
 selected=ImageChops.multiply(planned,budget)
 selected=ImageChops.multiply(selected,canvas.getchannel('A').point(lambda v:255 if v==255 else 0))
 ground=Image.composite(canvas,ground,selected)
 planes=data.get('observed_horizontal_tops',[data.get('observed_horizontal_top')])
 top=Image.new('L',(800,374))
 for contour in planes:top=ImageChops.lighter(top,poly([[x+dx,y+dy]for x,y in contour]))
 actual_level=ImageChops.multiply(top,selected);all_levels=ImageChops.lighter(all_levels,actual_level)
 for role,im in [('registered-source',canvas),('selected-source',selected),('source-horizontal-plane',top),('selected-horizontal-plane',actual_level)]:im.save(OUT/(key+'-'+role+'.png'),compress_level=9,optimize=False)
 rows[key]={**data,'raw_source':ref(folder/'master-raw.png'),'prompt':ref(folder/'prompt.txt'),'registration_plan':ref(folder/'registration.json'),'frozen_plot_plan':ref(plan_path),'uniform_scale':scale,'native_context':box,'registered_source':ref(OUT/(key+'-registered-source.png')),'selection':ref(OUT/(key+'-selected-source.png')),'observed_plane':ref(OUT/(key+'-source-horizontal-plane.png')),'actual_selected_floor':ref(OUT/(key+'-selected-horizontal-plane.png')),'actual_selected_floor_pixels':sum(bool(v)for v in actual_level.get_flattened_data())}
bg=OUT/'background.png';ground.save(bg,compress_level=9,optimize=False)
index['background']=ref(bg)['path'];index['background_sha256']=ref(bg)['sha256']
scene_refs={}
for name,keys in [('empty',[]),('base',index['base_scene_states']),('full',index['full_scene_states'])]:
 scene=ground.copy()
 for key in keys:scene.alpha_composite(Image.open(PROJECT/index['states'][key]['frame']).convert('RGBA'))
 dest=OUT/(name+'-native.png');scene.save(dest,compress_level=9,optimize=False);scene_refs[name]=ref(dest)
approved=Image.open(PROJECT/plan['approved_full']['path']).convert('RGBA');full=Image.open(PROJECT/scene_refs['full']['path']).convert('RGBA')
delta=sum(any(v)for v in ImageChops.difference(approved,full).get_flattened_data())
if delta:raise ValueError('Immutable selected full changed: '+str(delta))
(OUT/'states.json').write_text(json.dumps(index,indent=2,sort_keys=True)+'\n')
all_levels.save(OUT/'all-selected-source-floor-tops.png')
receipt={'status':'authored configuration','ancestor':ref(index_path),'frozen_plan':ref(plan_path),'source_selection_budget':'Approved highest ordinary architecture alpha255 only; no world-visible complete composition change.','states':ref(OUT/'states.json'),'background':ref(bg),'sources':rows,'scenes':scene_refs,'approved_full_rgba_changed_pixels':delta,'all35frames_byte_identical':True,'all_source_paintings_preserved':True,'whole_physical_baseline_passed':False,'appearance_acceptance_claimed':False}
(OUT/'selection-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({'states':receipt['states'],'full_delta':delta,'actual_source_floor_counts':{k:r['actual_selected_floor_pixels']for k,r in rows.items()}}))
