"""Read-only production planning and geometry checks for the new town cohort."""
import hashlib
import json
import sys
from types import SimpleNamespace
from PIL import Image, ImageChops, ImageFilter
from propose import ROOT, HERE, REPORT, sha, write

sys.path.insert(0,str(ROOT.parent/'scripts'))
from faction_art_compile import create_compiler
from faction_production import source_payload_allowed

def main():
 handoff=json.loads((HERE/'coordinator-handoff.json').read_text())
 compiler=create_compiler('bandlecity')
 outputs={};plans=[];errors=[];sources=set();masks=[]
 for name in handoff['recipe_paths']:
  path=ROOT/name
  try:
   planned,receipt=compiler.plan(ROOT,path)
   for target,data in planned.items():
    if target in outputs:raise ValueError('Duplicate planned output '+target)
    outputs[target]=hashlib.sha256(data).hexdigest()
   plans.append({'recipe':name,'recipe_sha256':sha(path),'planned_outputs':len(planned)})
   for record in receipt['outputs']:
    if 'source' in record:sources.add(record['source'])
  except Exception as error:errors.append(name+': '+str(error))
 for row in handoff['states']:
  state=row['state'];image=Image.open(ROOT/row['native_layer']).convert('RGBA')
  mask=image.getchannel('A').point(lambda p:255 if p>=128 else 0)
  area=Image.open(HERE/'structures'/state/'area.png').getchannel('A')
  border=Image.open(HERE/'structures'/state/'border.png').getchannel('A')
  if ImageChops.difference(mask,area).getbbox():errors.append('Mask mismatch '+state)
  expected=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),mask)
  if ImageChops.difference(expected,border).getbbox():errors.append('Border mismatch '+state)
  if sha(ROOT/row['master'])!=row['master_sha256']:errors.append('Master changed '+state)
  sources.add(row['master'])
  if not mask.getbbox():errors.append('Empty area '+state)
  masks.append({'state':state,'size':list(image.size),'click_bbox':mask.getbbox(),'click_pixels':sum(mask.histogram()[128:]),'area_exact':True,'border_exact':True})
 sources.update([handoff['terrain']['master'],handoff['terrain']['native']])
 pipeline=SimpleNamespace(root=ROOT)
 excluded=[s for s in sorted(sources) if not source_payload_allowed(pipeline,s)]
 missing=[s for s in sorted(sources) if not (ROOT/s).is_file()]
 if excluded or missing:errors.append('Missing/excluded selected dependencies')
 proposal=json.loads((HERE/'proposal-layout.json').read_text())
 conservative=proposal['conservative_all_states_click_metrics']
 if min(r['conservative_exposed_click_pixels'] for r in conservative)<=0:errors.append('Hidden construction state')
 ordinary=[s for s in handoff['sites'] if s['id'] not in ('coast','grailOrnament')]
 if len(ordinary)!=16 or len(handoff['states'])!=35:errors.append('Site/state contract violation')
 result={'ok':not errors,'check':'Actual shared compiler read-only plan; exact area/border derivation; conservative state exposure; selected-source export closure','status':'authored configuration','visual_approval_granted':False,'outputs_written':False,'recipe_count':len(plans),'planned_output_count':len(outputs),'selected_dependency_count':len(sources),'errors':errors,'excluded_selected_dependencies':excluded,'missing_selected_dependencies':missing,'sources':sorted(sources),'plans':plans,'planned_outputs':outputs,'masks':masks,'conservative_all_states_click_metrics':conservative}
 write(REPORT/'technical-plan-and-export-closure.json',result)
 print(json.dumps({key:result[key] for key in ['ok','recipe_count','planned_output_count','selected_dependency_count','outputs_written','errors']}))
 return 0 if result['ok'] else 2

if __name__=='__main__':raise SystemExit(main())
