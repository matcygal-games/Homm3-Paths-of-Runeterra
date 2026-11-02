from pathlib import Path
import sys,json,hashlib,io
from PIL import Image,ImageDraw
sys.path.insert(0,'scripts')
from faction_art_compile import create_compiler
root=Path('runeterra-bandlecity').resolve()
compiler=create_compiler('bandlecity')
results=[]
all_outputs={}
for path in sorted((root/'assets/recipes/heroes').glob('*.json')):
 outputs,receipt=compiler.plan(root,path)
 results.append({'recipe':path.relative_to(root).as_posix(),'recipe_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'output_count':len(outputs),'frame_count':receipt['frame_count']})
 for name,data in outputs.items():
  if name in all_outputs: raise ValueError('Duplicate '+name)
  all_outputs[name]=data
(root/'assets/source/heroes/conversion-plan-v1.json').write_text(json.dumps({'ok':True,'recipes':results,'recipe_count':len(results),'output_count':len(all_outputs),'writes':'No compiled outputs written; plan only','art_accepted':False},indent=2)+'\n')
heroes=['teemo','tristana','lulu','rumble','yuumi','corki','veigar']
sheet=Image.new('RGBA',(700,210),(36,40,40,255)); draw=ImageDraw.Draw(sheet)
for i,h in enumerate(heroes):
 draw.text((i*100,2),h,fill='white')
 for role,y in [('large',20),('small',90),('specialtyLarge',130),('specialtySmall',178)]:
  name='Content/Sprites/runeterra/bandlecity/heroes/'+h+'/'+role+'.png'
  im=Image.open(io.BytesIO(all_outputs[name]));sheet.alpha_composite(im,(i*100,y))
sheet.convert('RGB').save(root/'assets/source/heroes/native-raster-review-v1.png')
for cls in ['bandleMarshal','gladeKeeper']:
 for kind,canvas in [('battle',(150,175)),('map',(96,64))]:
  sheet=Image.new('RGBA',(canvas[0]*4,canvas[1]*5),(36,40,40,255))
  for r in range(5):
   for c in range(4):
    p=root/'assets/source/heroes/classes'/cls/(kind+'-frames-v1')/('r%02d-c%02d.png'%(r,c))
    sheet.alpha_composite(Image.open(p),(c*canvas[0],r*canvas[1]))
  sheet.convert('RGB').save(root/'assets/source/heroes/classes'/cls/(kind+'-native-review-v1.png'))
print(json.dumps({'ok':True,'recipes':len(results),'planned_outputs':len(all_outputs),'generated_output_writes':0}))
