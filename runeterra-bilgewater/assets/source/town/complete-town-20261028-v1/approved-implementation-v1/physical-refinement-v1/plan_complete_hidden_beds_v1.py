"""Freeze complete missing plot planes before genuine painted production."""
from pathlib import Path
import json
import hashlib
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
BASE = HERE.parent
OUT = HERE / 'complete-hidden-beds-v1'
OUT.mkdir(exist_ok=False)
background_path = BASE / 'background-hidden-support-v6.png'
approved_path = BASE / 'approved-full-source-v1.png'
background = Image.open(background_path).convert('RGBA')
def ref(path):
    return {'path':path.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
plots = {
 'artillery':{'native_context':[186,138,338,206], 'horizontal_top_polygon':[[195,174],[215,173],[250,177],[291,177],[321,177],[331,183],[327,193],[299,197],[259,194],[223,190],[194,185]],'colour':[40,220,255],
    'intent':'Complete level stone shelf beneath the cannon battery, connecting basin east frontage and central street. Separate its horizontal top from its lower retaining face; detached masonry pier soles are retained.'},
 'tavern':{'native_context':[496,251,653,309], 'horizontal_top_polygon':[[506,263],[527,266],[550,272],[577,278],[609,279],[638,276],[645,286],[641,298],[607,303],[575,297],[543,285],[517,277],[504,270]],'colour':[255,210,20],
    'intent':'Complete oblique level tavern foundation court/shelf, with a coherent back/side retaining foundation, connecting the lower civic street and eastern quay. Preserve all basal masonry and actual entry sole.'},
 'buhru':{'native_context':[586,190,720,237], 'horizontal_top_polygon':[[593,198],[622,199],[652,199],[681,196],[707,196],[714,204],[711,219],[695,231],[651,230],[620,228],[599,220],[591,209]],'colour':[240,100,255],
    'intent':'Complete supported Buhru temple plot behind the existing preserved narrow front cap. Include back/side foundation ground, all alternate shrine/temple masonry soles, the developed central stair sole and a left public landing; no stairs are declared level under the masonry.'},
}
guide = background.copy()
draw = ImageDraw.Draw(guide)
for name,row in plots.items():
    draw.line(list(map(tuple,row['horizontal_top_polygon']+[row['horizontal_top_polygon'][0]])),fill=tuple(row['colour']),width=2)
    mask = Image.new('L',(800,374))
    ImageDraw.Draw(mask).polygon(list(map(tuple,row['horizontal_top_polygon'])),fill=255)
    mask.save(OUT / (name+'-planned-complete-top.png'))
guide.save(OUT / 'planned-whole-background-guide.png')
record = {'status':'design proposal','background':ref(background_path),'immutable_approved_full':ref(approved_path),'plots':plots,
    'selection_policy':'New genuinely painted recovery is restricted to complete preplanned plot planes and current approved full opaque actor pixels. Existing selected paintings stay preserved; no visible full scene change is authorized.',
    'structural_masks_used_to_fit_plan':False,'terrain_support_mask_pass_claimed':False,'native_or_release_accepted':False}
(OUT / 'plan.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(ref(OUT / 'plan.json')))
