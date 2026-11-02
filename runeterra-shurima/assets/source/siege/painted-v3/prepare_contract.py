"""Measure native read-only siege inputs and make private placement guides."""
from pathlib import Path
import math
import hashlib,json,struct
from PIL import Image,ImageDraw

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
REPORT=PROJECT/'build/reports/painted-siege-20261024-v3'
INDEX=PROJECT/'assets/references/siege/native-siege-index.json'
faction=json.loads((PROJECT/'content/factions.json').read_text())['shurima']['town']['siege']
sizes={Path(item['resource']).stem.upper().removeprefix('SGCS'):item['dimensions'] for item in json.loads(INDEX.read_text())['files']}
positions={
 'BACK':[0,0], 'TPWL':[600,49], 'ARCH':[477,238], 'WA2':[512,347],
 'WA5':[489,79], 'MOAT':[410,90], 'MLIP':[403,80], 'MANC':[720,158],
 'TW1C':[602,500], 'TW2C':[557,24], 'DRWC':[399,274],
 'MAN1':[720,158], 'MAN2':[720,158], 'TW11':[602,500], 'TW12':[602,500],
 'TW21':[569,35], 'TW22':[569,35]}
for piece,position in [('WA1',[528,350]),('WA3',[469,291]),('WA4',[470,127]),('WA6',[524,32]),('DRW',[399,274])]:
 for state in (1,2,3):positions[piece+str(state)]=position
mapping={'TPWL':faction['static']['background'],'ARCH':faction['gate']['arch'],
 'WA2':faction['static']['bottom'],'WA5':faction['static']['top'],
 'MOAT':faction['moat']['moat'],'MLIP':faction['moat']['bank'],
 'MANC':faction['towers']['keep']['battlement'],'TW1C':faction['towers']['bottom']['battlement'],
 'TW2C':faction['towers']['top']['battlement'],'DRWC':faction['gate']['gate']}
for name,pair in mapping.items():assert positions[name]==[pair['x'],pair['y']]
assets=[]
for suffix,position in sorted(positions.items()):
 ref=PROJECT/f'assets/references/siege/sgcs{suffix.lower()}.png'
 image=Image.open(ref).convert('RGBA')
 assert list(image.size)==sizes[suffix]
 if suffix!='BACK':
  image.putdata([(r,g,b,0 if (r,g,b)==(0,255,255) else a) for r,g,b,a in image.getdata()])
 item={'id':'SGSH'+suffix,'suffix':suffix,'position':position,'size':sizes[suffix],
       'native_geometry_reference':'core:castle/SGCS'+suffix,
       'native_reference_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),
       'source_canvas':[800,600], 'alpha_required':suffix!='BACK'}
 assets.append(item)
 if suffix!='BACK':
  guide=Image.new('RGBA',(800,600))
  guide.alpha_composite(image,tuple(position))
  path=REPORT/'private'/f'placement-{suffix}.png'
  path.parent.mkdir(parents=True,exist_ok=True)
  guide.save(path)
  width=max(image.width,math.ceil(image.height/2.8))
  local=Image.new('RGBA',(width,image.height))
  padding=(width-image.width)//2
  local.alpha_composite(image,(padding,0))
  local.save(REPORT/'private'/f'local-{suffix}.png')
  item['local_source_canvas']=[width,image.height]
  item['local_crop']=[padding,0,padding+image.width,image.height]
for name,size,resource in [('towerLarge',[58,64],'twcrport.def'),('towerSmall',[32,32],'cprsmall.def')]:
 raw=PROJECT.parent/'runeterra-demacia/references/raw'/resource
 header=struct.unpack('<4I',raw.read_bytes()[:16])
 assert list(header[1:3])==size
 assets.append({'id':name,'suffix':None,'position':None,'size':size,'alpha_required':True,
                'consumer':'CFaction::registerIcons group1 '+resource,
                'native_header':list(header),'native_reference_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
                'source_canvas':None})
contract={'status':'authored configuration','image_prefix':faction['imagePrefix'],
          'native_battle_canvas':[800,556],'source_placement_canvas':[800,600],
          'source_canvas_reason':'NativeWA2extendsbelow battlefieldto600; retain originalassetdimensions.',
          'assets':assets,'gate_consumer':'Closed/blocked gate renders noDRWpiece. DRW1transition,DRW2open,DRW3destroyed;DRWCforegroundonlywhenopen.',
          'damage_consumer':'MAN/TW have intact/destroyed states1/2; WA1/3/4/6 have intact/damaged/destroyed1/2/3.',
          'tower_positions':faction['towers'],'visual_approval_granted':False}
(SOURCE/'native-geometry-contract-v1.json').write_text(json.dumps(contract,sort_keys=True,indent=2)+'\n')
print(json.dumps({'assets':len(assets),'private_guides':len(positions)-1,'image_prefix':faction['imagePrefix']}))
