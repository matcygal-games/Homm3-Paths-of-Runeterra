"""Register seven original painted environmental stills; never draw map artwork."""
from pathlib import Path
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent;PROJECT=next(p for p in HERE.parents if p.name=='runeterra-world')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def relative(p):return p.relative_to(PROJECT).as_posix()
def main():
 plan_path=HERE/'native-plan-v1.json';plan=json.loads(plan_path.read_text());objects=json.loads((PROJECT/'content/objects.json').read_text());rows=[]
 for key,r in plan['objects'].items():
  template=(objects['runeterraScenery']['types'][key]if r['role']=='scenery'else objects[key]['types'][key])['templates']['normal']
  assert template['mask']==r['mask'] and template['animation']==f'runeterra/world/{r["role"]}/{key}/map.json','Current authored consumer differs'
  folder=HERE/key;master=folder/'master-v1.png';prompt=folder/'prompt-v1.txt';generation_path=folder/'generation-v1.json';g=json.loads(generation_path.read_text());im=Image.open(master).convert('RGBA');assert sha(master)==g['master_sha256']
  alpha=im.getchannel('A');box=alpha.point(lambda a:255 if a>=8 else 0).getbbox()
  assert box and box[0]>0 and box[1]>0 and box[2]<im.width and box[3]<im.height,'Whole visible painted object must have source margins'
  sprite=im.crop(box);scale=r['scale'];size=tuple(max(1,round(n*scale))for n in sprite.size);sprite=sprite.resize(size,Image.Resampling.LANCZOS)
  root=plan['ground_root'];point=r['source_root'];offset=[root[a]-round((point[a]-box[a])*scale)for a in(0,1)]
  sb=sprite.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox();assert sb and 0<=offset[0]+sb[0]<offset[0]+sb[2]<=96 and 0<=offset[1]+sb[1]<offset[1]+sb[3]<=96,('Native whole object clips',key,offset,sb)
  out=Image.new('RGBA',(96,96),(0,0,0,0));out.alpha_composite(sprite,tuple(offset));native=folder/'native-v1.png';out.save(native,compress_level=9)
  deps=[master,prompt,generation_path,plan_path,HERE/'shadow-decision-v1.json',Path(__file__)]
  recipe={'recipe_type':'vcmi_animation','production_status':'painted-master-complete-unapproved','output_path':'Content/Sprites/'+template['animation'],'canvas':[96,96],'pivot':{'x':48,'y':94},'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by tool','prompt':prompt.read_text().strip(),'painted_master':relative(master),'painted_master_sha256':sha(master),'method':plan['method']},'groups':[{'group':0,'generateShadow':1,'generateOverlay':0,'frames':[{'frame':0,'source':relative(native),'source_sha256':sha(native),'sha256':sha(native),'source_canvas':[96,96]}]}],'production_inputs':[{'path':relative(p),'sha256':sha(p)}for p in deps],'credits':{'author':'Runeterra project-directed original painted image generation','license':'pending','redistribution':'unresolved'}}
  recipe_path=PROJECT/f'assets/recipes/environments/{key}.json';write(recipe_path,recipe)
  row={'id':key,'role':r['role'],'native_canvas':[96,96],'source_canvas':list(im.size),'visible_source_alpha_bbox_8':list(box),'uniform_scale':scale,'source_root':point,'native_root':root,'native_offset':offset,'native_object_size':list(size),'native_alpha_bbox_8':out.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox(),'native_sha256':sha(native),'mask':r['mask'],'contact_note':r['contact_note'],'painted_soft_contact_shade_retained':True,'faint_provider_alpha_tail_trimmed_outside_visible_bbox':True,'recipe':relative(recipe_path),'recipe_sha256':sha(recipe_path),'status':'authored configuration','native_execution_performed':False,'visual_approval_granted':False}
  write(folder/'calibration-v1.json',row);rows.append(row)
 write(HERE/'candidate-recipes-v1.json',{'status':'authored configuration','recipes':[r['recipe']for r in rows],'objects':rows,'visual_approval_granted':False})
 print(json.dumps(rows))
if __name__=='__main__':main()
