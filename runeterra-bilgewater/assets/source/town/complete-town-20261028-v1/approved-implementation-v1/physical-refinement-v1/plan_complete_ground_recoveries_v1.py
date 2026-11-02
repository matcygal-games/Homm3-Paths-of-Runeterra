"""Freeze missing hidden horizontal floor recovery plots before selection.

These are complete architectural ground plots, not actor-contact masks. The
single genuine painted horizontal pavement master is cropped/scaled uniformly;
only already occluded pixels can be admitted into the locked BL2 composition.
"""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'complete-ground-recoveries-v1'
OUT.mkdir(exist_ok=False)
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
frozen=json.loads((HERE/'complete-hidden-beds-v1/plan.json').read_text())
plots={k:{'polygon':v['horizontal_top_polygon'],'observation':v['intent']} for k,v in frozen['plots'].items() if k in ('artillery','buhru')}
plots.update({
 'sailors':{'polygon':[[65,238],[86,237],[119,239],[143,240],[150,245],[149,253],[139,256],[100,255],[72,253],[65,248]],'observation':'Whole timber-house ground plot: recover the horizontal court beneath the retained wall rather than treating the earlier source vertical support posts as level ground. The already genuine lower front deck remains outside this selection.'},
 'corsairs':{'polygon':[[242,267],[267,266],[301,268],[331,269],[353,276],[356,284],[346,291],[313,294],[282,291],[254,284],[242,276]],'observation':'Whole boat-shaped guild-house court behind its existing lower civic street; hull-shaped house masonry is retained as architecture and not trimmed.'},
 'warehouse':{'polygon':[[0,205],[32,205],[65,206],[101,207],[124,212],[127,220],[114,225],[71,225],[32,223],[0,220]],'observation':'Whole warehouse-side source terrace, above its unchanged public quay retaining face.'},
 'tavern-upper':{'polygon':[[509,249],[530,252],[552,258],[577,264],[602,265],[611,269],[610,275],[594,277],[572,274],[549,268],[529,262],[511,258]],'observation':'Upper main tavern court. The permanent diagonal outdoor stair below it remains stairs, with its upper and lower level caps kept separate.'},
 'tavern-lower-annex':{'polygon':[[605,262],[626,260],[641,268],[644,280],[638,294],[623,299],[607,293],[602,279]],'observation':'Lower eastern annex landing around the retained actual public-facing entry stair; lower own-stair soles are preserved separately.'},
 'basin':{'polygon':[[94,173],[126,174],[163,177],[194,176],[200,187],[171,192],[127,192],[94,186]],'observation':'Previously planned genuine poolside hidden paved top, retaining all actual pedestal toes and sculpture columns. Open spray is excluded from selection when not opaque.'},
})
material=HERE/'complete-hidden-beds-v1/platform-ground-master-v1-raw.png'
prompt=HERE/'complete-hidden-beds-v1/platform-ground-prompt-v1.txt'
plan={'status':'design proposal','source':ref(material),'prompt':ref(prompt),
 'source_crop':[320,300,1630,520],
 'material_interpretation':'Interior of genuinely painted horizontal paved platform; source vertical retaining face and transparent margins excluded before uniform scale.',
 'source_index':ref(HERE/'ownership-separation-v3/states.json'),
 'approved_full':frozen['immutable_approved_full'],'ancestry':ref(HERE/'complete-hidden-beds-v1/plan.json'),
 'plots':plots,'contact_masks_or_failed_results_read':False,
 'selection_policy':'Frozen whole plot polygon AND exact approved full opaque architecture; never visible full pixels, public stairs, water or masks grown around desired feet. Original admitted paintings remain preserved.'}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
print(ref(OUT/'plan.json'))
