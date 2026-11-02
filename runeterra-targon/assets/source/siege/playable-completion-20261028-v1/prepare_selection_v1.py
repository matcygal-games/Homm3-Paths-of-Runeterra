"""Measured uniform technical registration; no painting or source replacement."""
from pathlib import Path
from PIL import Image
import hashlib,json
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 geometry=json.loads((HERE/'geometry-contract-v1.json').read_text());assets=[]
 for entry in geometry['assets']:
  ident=entry['id'];version='v2' if ident.startswith('SGTGDRW') else 'v1';master=HERE/'modular'/ident/('master-'+version+'-raw.png');im=Image.open(master).convert('RGBA');local=entry['local_canvas'];crop=entry['local_crop'];scale=min(local[0]/im.width,local[1]/im.height);size=[round(im.width*scale),round(im.height*scale)]
  # A small fixed family offset fits complete material inside the original
  # narrowed ARCH/MAN target. No material may be shaved to match a rectangle.
  translation=[1,0] if ident=='SGTGARCH' else ([-8,0] if ident.startswith('SGTGMAN') else [0,0])
  generation={'workflow':'image-based-painted-2d','image_generation_used':True,'derived_from_blender':False,'provider':'OpenAI built-in image_gen','model':'Not exposed by built-in tool','prompt':(master.parent/('prompt-'+version+'.txt')).read_text(),'painted_master':master.relative_to(PROJECT).as_posix(),'painted_master_sha256':sha(master)}
  assets.append({'id':ident,'master':master.relative_to(PROJECT).as_posix(),'master_sha256':sha(master),'master_dimensions':list(im.size),'local_canvas':local,'resized_dimensions':size,'local_crop':crop,'local_translation':translation,'native_size':entry['native_size'],'position':entry['position'],'prepared':(HERE/'native-v1'/(ident+'.png')).relative_to(PROJECT).as_posix(),'recipe':(HERE/'proposed-v1/recipes'/entry['canonical_recipe']).relative_to(PROJECT).as_posix(),'output_path':entry['output_path'],'require_alpha':True,'generation':generation})
 bg=PROJECT/'assets/source/town/siege/painted-background-v2/SGTGBACK.png';baseline={'generation':json.loads((HERE/'background-origin-v1.json').read_text()),'output_path':'Content/Sprites/runeterra/targon/siege/SGTGBACK.png'}
 assets.append({'id':'SGTGBACK','master':bg.relative_to(PROJECT).as_posix(),'master_sha256':sha(bg),'master_dimensions':[800,556],'local_canvas':[800,556],'resized_dimensions':[800,556],'local_crop':[0,0,800,556],'native_size':[800,556],'position':[0,0],'prepared':(HERE/'native-v1/SGTGBACK.png').relative_to(PROJECT).as_posix(),'recipe':(HERE/'proposed-v1/recipes/assets/recipes/town/siege/SGTGBACK.json').relative_to(PROJECT).as_posix(),'output_path':baseline['output_path'],'require_alpha':False,'generation':baseline['generation']})
 selected={'status':'authored configuration','shared_inputs':[],'assets':assets,'private_native_reference_pixels_are_not_production_inputs':True}
 (HERE/'selection-v1.json').write_text(json.dumps(selected,sort_keys=True,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
