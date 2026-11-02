"""Whole painted-plane recovery; immutable approved full remains exact.

Production extracts genuine horizontal paving from inspected painted masters,
then uses fixed complete plot plans and whole-source uniform conversions.
No building contact, footing mask, consumer diagnostic or displacement is read.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
BASE = HERE.parent
OUT = HERE / 'complete-floor-selection-v3'
OUT.mkdir(exist_ok=False)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}

def polygon(points):
    mask = Image.new('L',(800,374))
    ImageDraw.Draw(mask).polygon(list(map(tuple,points)),fill=255)
    return mask

index_path = HERE / 'lower-roost-registration-v1/states.json'
index = json.loads(index_path.read_text())
# Released actual full order, independent of the physical draft annotations.
full_order = index['full_scene_states']
approved_path = BASE / 'approved-full-source-v1.png'
approved = Image.open(approved_path).convert('RGBA')
assert sha(approved_path) == '4f8cac4f1801ed366e0bacd4934084e9b76e0d25c282b3f3b36fda3835cd0712'
background_path = PROJECT / index['background']
background = Image.open(background_path).convert('RGBA')
before = background.copy()
budget = Image.new('L',(800,374))
for key in full_order:
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    before = Image.alpha_composite(before,frame)
    budget = ImageChops.lighter(budget,frame.getchannel('A').point(lambda p:255 if p==255 else 0))
if before.tobytes() != approved.tobytes():
    raise ValueError('Actual preserved full order does not match immutable approved RGBA')
budget.save(OUT / 'approved-functional-opaque-budget.png')
plan = json.loads((HERE / 'complete-hidden-beds-v1/plan.json').read_text())
fine_master_path = HERE / 'complete-hidden-beds-v1/fine-paving-master-v1-raw.png'
with Image.open(fine_master_path) as opened:
    fine_master = opened.convert('RGBA')
fine_scale = 256/fine_master.width
fine_native = fine_master.resize((256,round(fine_master.height*fine_scale)),Image.Resampling.LANCZOS)
fine_native.save(OUT / 'city-paving-material-native.png',compress_level=9,optimize=False)
# Exact inspected clear horizontal paving areas, not retaining faces. Uniform
# native conversion and a complete planned floor polygon supply each plot.
masters = {
 'artillery':{'source':HERE / 'complete-hidden-beds-v1/artillery-master-v2-raw.png','crop':[760,458,1425,575],'native_size':[143,25],'placement':[194,173]},
 'tavern':{'source':HERE / 'complete-hidden-beds-v1/tavern-master-v2-raw.png','crop':[720,260,1143,380],'native_size':[145,41],'placement':[504,263]},
 'buhru':{'source':HERE / 'complete-hidden-beds-v1/buhru-master-v2-raw.png','crop':[600,190,1303,390],'native_size':[127,36],'placement':[591,196]},
}
plots = {key:{'polygon':value['horizontal_top_polygon'],'master':key} for key,value in plan['plots'].items()}
# Full back/side ground is authored from the architectural plot plan; these are
# real new painted court planes, not a support-mask relabel of the old cliff.
plots['artillery']['polygon'] = [[194,172],[216,171],[251,174],[291,174],[322,173],[332,181],[330,195],[299,198],[258,195],[221,191],[193,184]]
plots['artillery']['placement'] = [193,171]
plots['tavern']['polygon'] = [[504,258],[528,263],[551,270],[579,277],[610,278],[640,275],[646,286],[641,299],[607,304],[574,298],[542,286],[516,277],[503,268]]
plots['tavern']['placement'] = [503,258]
# Whole additional permanent-quay foundation courts use the same genuine city
# paving source, with independent complete plot outlines fixed before selection.
plots.update({
 'corsair':{'master':'tavern','polygon':[[244,270],[274,270],[316,274],[349,276],[355,285],[344,296],[308,299],[277,293],[251,285],[242,278]],'placement':[242,270],'native_size':[114,32]},
 'warehouse':{'master':'tavern','polygon':[[0,210],[38,211],[81,208],[115,209],[127,217],[124,226],[90,228],[50,228],[12,223],[0,219]],'placement':[0,208],'native_size':[128,36]},
 'foreground-market':{'master':'tavern','polygon':[[350,309],[385,310],[425,312],[469,311],[509,308],[548,309],[552,319],[544,329],[521,334],[477,335],[429,333],[390,329],[355,321]],'placement':[350,308],'native_size':[203,58]},
 'west-black-market':{'master':'tavern','polygon':[[0,306],[36,306],[80,307],[123,307],[163,304],[170,316],[165,327],[142,332],[100,334],[57,330],[20,327],[0,322]],'placement':[0,304],'native_size':[171,49]},
})
selected_union = Image.new('L',(800,374))
records = {}
for key,row in plots.items():
    config = masters[row['master']]
    placement = row.get('placement',config['placement'])
    complete_top = polygon(row['polygon'])
    bounds = complete_top.getbbox()
    fitted_size = [bounds[2]-placement[0],bounds[3]-placement[1]]
    if fitted_size[0]>fine_native.width or fitted_size[1]>fine_native.height:
        raise ValueError('The whole native material cannot cover this planned court')
    raw_path = fine_master_path
    scale = fine_scale
    native = fine_native.crop((0,0,*fitted_size))
    native_path = OUT / (key+'-genuine-paved-top-native.png')
    native.save(native_path,compress_level=9,optimize=False)
    canvas = Image.new('RGBA',(800,374))
    canvas.paste(native,tuple(placement))
    coverage = Image.new('L',(800,374))
    ImageDraw.Draw(coverage).rectangle((placement[0],placement[1],placement[0]+native.width-1,placement[1]+native.height-1),fill=255)
    if ImageChops.subtract(complete_top,coverage).getbbox():
        raise ValueError('Uniform painted-source fit does not cover the whole planned plot: '+key)
    selected = ImageChops.multiply(complete_top,budget)
    selected.save(OUT / (key+'-selected-complete-top.png'))
    background = Image.composite(canvas,background,selected)
    selected_union = ImageChops.lighter(selected_union,selected)
    records[key] = {'planned_complete_top_polygon':row['polygon'],'genuine_master':ref(raw_path),
        'raw_horizontal_paving_crop':'Entire genuine material is uniformly calibrated once; each court is a native crop, never stretched.','uniform_scale':scale,'native_size':fitted_size,
        'native_source':ref(native_path),'whole_native_registration':placement,'selected_complete_top':ref(OUT / (key+'-selected-complete-top.png')),
        'selected_top_pixels':sum(bool(v) for v in selected.get_flattened_data()),
        'plane_kind':'level horizontal city paving; retaining face excluded from the extracted genuine source'}
# Preserve the accepted timber material master. Its complete lower-deck plane
# receives one uniform whole-source registration for this plot; it is not
# regenerated or fitted point-by-point to a footing mask.
wood_path = BASE / 'sailors-hidden-support-native-v2.png'
wood = Image.open(wood_path).convert('RGBA')
wood_native = wood.resize((192,96),Image.Resampling.LANCZOS)
wood_canvas = Image.new('RGBA',(800,374))
wood_canvas.paste(wood_native,(16,198))
wood_top_points = [[43,246],[125,244],[165,244],[171,249],[160,254],[51,252]]
wood_top = polygon(wood_top_points)
wood_selected = ImageChops.multiply(wood_top,budget)
background = Image.composite(wood_canvas,background,wood_selected)
wood_selected.save(OUT / 'sailors-selected-complete-top.png')
selected_union = ImageChops.lighter(selected_union,wood_selected)
wood_native.save(OUT / 'sailors-whole-painted-source-native.png',compress_level=9,optimize=False)
records['sailors'] = {'planned_complete_top_polygon':wood_top_points,'genuine_master':ref(wood_path),
    'uniform_scale':1.6,'native_size':[192,96],'whole_native_registration':[16,198],
    'selected_complete_top':ref(OUT / 'sailors-selected-complete-top.png'),
    'selected_top_pixels':sum(bool(v) for v in wood_selected.get_flattened_data()),
    'plane_kind':'Complete actual lower timber deck top, uniformly transformed with its source. Upper street and public stair faces are excluded from the level plane.'}
selected_union.save(OUT / 'all-selected-complete-horizontal-tops.png')
background_out = OUT / 'background-complete-floor-source.png'
background.save(background_out,compress_level=9,optimize=False)
after = background.copy()
for key in full_order:
    after = Image.alpha_composite(after,Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA'))
assert after.tobytes() == approved.tobytes()
after.save(OUT / 'complete-scene-native.png',compress_level=9,optimize=False)
candidate = deepcopy(index)
candidate['background'] = ref(background_out)['path']
candidate['background_sha256'] = sha(background_out)
candidate['complete_floor_recovery'] = {'helper':ref(Path(__file__)),'planned_native_inputs':ref(HERE / 'complete-hidden-beds-v1/plan.json')}
(OUT / 'states.json').write_text(json.dumps(candidate,indent=2,sort_keys=True)+'\n',encoding='utf-8')
receipt = {'status':'design proposal','before_background':ref(background_path),'approved_full':ref(approved_path),
    'source_cohort':ref(index_path),'actual_full_order':full_order,'genuine_complete_planes':records,
    'new_background':ref(background_out),'new_cohort':ref(OUT / 'states.json'),
    'complete_horizontal_tops':ref(OUT / 'all-selected-complete-horizontal-tops.png'),
    'approved_full_decoded_RGBA_changed_pixels':0,'architecture_frames_modified':0,
    'building_contacts_or_diagnostics_loaded':False,'native_verified':False,'physical_baseline_passed':False}
(OUT / 'selection.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(receipt['new_cohort']))
