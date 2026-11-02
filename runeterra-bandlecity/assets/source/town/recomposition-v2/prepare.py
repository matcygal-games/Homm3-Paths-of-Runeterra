"""Prepare the reviewed Bandle recomposition without staging or design writes.

Only this revision's source/report folders and the coordinator-agreed 106 town
recipes are writable. Original masters and historical evidence remain inputs.
"""
import argparse
import copy
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter, ImageOps
from propose import ROOT, HERE, REPORT, fit, sha, write

def relative(path): return path.relative_to(ROOT).as_posix()

def save(path,image):
 path.parent.mkdir(parents=True,exist_ok=True)
 image.convert('RGBA').save(path,compress_level=9,optimize=False)
 return {'source':relative(path),'source_sha256':sha(path),'source_canvas':list(image.size)}

def replace_recipe(path,value):
 snapshot=HERE/'previous-recipes'/path.relative_to(ROOT/'assets/recipes')
 if not snapshot.exists():
  snapshot.parent.mkdir(parents=True,exist_ok=True)
  snapshot.write_bytes(path.read_bytes())
 write(path,value)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--prepare',action='store_true')
 parser.add_argument('--select-recipes',action='store_true')
 args=parser.parse_args()
 if not args.prepare: parser.print_help(); return
 proposal=json.loads((HERE/'proposal-layout.json').read_text())
 bgmaster=HERE/'background/master.png'
 if not bgmaster.exists(): raise SystemExit('Missing real imagegen terrain master')
 terrain=HERE/'background/native.png'
 save(terrain,ImageOps.fit(Image.open(bgmaster).convert('RGBA'),(800,374),Image.Resampling.LANCZOS))
 bggen=json.loads((HERE/'background/generation.json').read_text())
 bggen.update(painted_master=relative(bgmaster),painted_master_sha256=sha(bgmaster),master_canvas=list(Image.open(bgmaster).size))
 bggen['prompt']=(HERE/'background/prompt.txt').read_text().strip()
 for reference in bggen['reference_images']:
  reference['sha256']=sha(ROOT/reference['path'])
 write(HERE/'background/generation.json',bggen)
 rows=[];layers={};recipe_paths=[]
 for row in proposal['rows']:
  state=row['state'];master=ROOT/row['master']
  if sha(master)!=row['master_sha256']: raise ValueError('Changed own master: '+state)
  layer,size=fit(master,row['composition_rectangle'])
  layers[state]=layer
  source=HERE/'structures'/state/'layer.png'
  descriptor=save(source,layer)
  mask=layer.getchannel('A').point(lambda p:255 if p>=128 else 0)
  border=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),mask)
  original=ROOT/'assets/recipes/town/structures'/f'{state}-animation.json'
  recipe=json.loads(original.read_text())
  generation=copy.deepcopy(recipe['generation'])
  generation['conversion'].update(composition_rectangle=row['composition_rectangle'],native_z=row['native_z'],fit_size=size,native_canvas=[800,374],recomposition_revision='recomposition-v2',technical_source_crop='Alpha>=8 bounds+8px margin only for fountain/Grail; unchanged RGBA inside crop; all other masters whole returned-alpha bounds')
  master_image=Image.open(master).convert('RGBA')
  bounds=master_image.getchannel('A').getbbox()
  if state in ('special4','grail'):
   b=master_image.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox()
   bounds=(max(0,b[0]-8),max(0,b[1]-8),min(master_image.width,b[2]+8),min(master_image.height,b[3]+8))
  generation['conversion']['source_alpha_bbox']=list(bounds)
  recipe['generation']=generation
  recipe['groups'][0]['frames']=[descriptor]
  if args.select_recipes: replace_recipe(original,recipe)
  recipe_paths.append(relative(original))
  for suffix,channel in [('area',mask),('border',border)]:
   technical=Image.new('RGBA',(800,374),(255,224,0,0));technical.putalpha(channel)
   desc=save(source.with_name(suffix+'.png'),technical)
   path=original.with_name(state+'-'+suffix+'.json')
   value=json.loads(path.read_text());value.update(desc)
   value['generation']['painted_source_provenance']=copy.deepcopy(generation)
   if args.select_recipes:replace_recipe(path,value)
   recipe_paths.append(relative(path))
  rows.append({**row,'native_layer':descriptor['source'],'native_layer_sha256':descriptor['source_sha256'],'click_bbox':list(mask.getbbox()),'click_pixels':sum(mask.histogram()[128:]),'source_alpha_extrema':list(Image.open(master).getchannel('A').getextrema())})
 bgpath=ROOT/'assets/recipes/town/background.json'
 bgrecipe=json.loads(bgpath.read_text());bgrecipe.update(source=relative(terrain),source_sha256=sha(terrain),source_canvas=[800,374],generation=bggen)
 if args.select_recipes:replace_recipe(bgpath,bgrecipe)
 recipe_paths.append(relative(bgpath))
 selected=sorted(proposal['sites'],key=lambda s:s['native_z'])
 full=Image.open(terrain).convert('RGBA')
 land=full.copy()
 for site in selected:
  state=site['states'][-1]
  full.alpha_composite(layers[state])
  if site['id'] not in ('coast','grailOrnament'):land.alpha_composite(layers[state])
 full.save(REPORT/'full-town-native.png');land.save(REPORT/'land-town-native.png')
 before=ROOT/'build/reports/runtime/20261022-prep-v7/human-1792679572120103100/03-single-scenario/after.png'
 comparison=Image.new('RGBA',(800,768),(32,29,24,255))
 comparison.alpha_composite(Image.open(before).convert('RGBA').crop((0,0,800,374)),(0,0))
 comparison.alpha_composite(full,(0,394))
 comparison.save(REPORT/'native-before-after.png')
 evidence={'status':'authored configuration','visual_approval_granted':False,'full_town_sha256':sha(REPORT/'full-town-native.png'),'terrain_master':relative(bgmaster),'terrain_master_sha256':sha(bgmaster),'terrain_native':relative(terrain),'terrain_native_sha256':sha(terrain),'masters':rows,'sites':proposal['sites'],'selected_click_overlap_metrics':proposal['exposed_click_metrics'],'conservative_all_states_click_metrics':proposal['conservative_all_states_click_metrics'],'coverage':proposal['canvas_coverage_fraction'],'previous_coverage':proposal['previous_canvas_coverage_fraction'],'recipe_paths':recipe_paths,'source_conversion_script':relative(Path(__file__)),'source_conversion_script_sha256':sha(Path(__file__)),'proposal_script_sha256':sha(HERE/'propose.py'),'limitations':['Static composition is not native click/construction/gameplay acceptance','All art remains built-unreviewed','Rights and external visual review remain pending']}
 write(REPORT/'conversion-evidence.json',evidence)
 selection={'status':'authored configuration','visual_approval_granted':False,'review_evidence':relative(REPORT/'conversion-evidence.json'),'states':rows,'terrain_master':relative(bgmaster),'terrain_master_sha256':sha(bgmaster)}
 write(HERE/'selection-v2.json',selection)
 write(HERE/'coordinator-handoff.json',{'status':'authored configuration','selection':relative(HERE/'selection-v2.json'),'selection_sha256':sha(HERE/'selection-v2.json'),'terrain':{'master':relative(bgmaster),'master_sha256':sha(bgmaster),'native':relative(terrain),'native_sha256':sha(terrain)},'sites':proposal['sites'],'states':rows,'recipe_paths':recipe_paths,'recipe_selection_written':args.select_recipes,'not_written':['content','design','manifest','staging','shared scripts']})
 print(json.dumps({'states':len(rows),'recipes':len(recipe_paths),'selected':args.select_recipes,'handoff':relative(HERE/'coordinator-handoff.json')}))

if __name__=='__main__':main()
