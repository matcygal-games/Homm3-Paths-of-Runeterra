"""Technical single-identity pilot only; no active recipes or 3D inputs."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops
S=Path(__file__).resolve().parent
P=next(p for p in S.parents if p.name=='runeterra-targon')
W=P.parent
D=S/'rakkorTrailguard'
MASTER=D/'identity-master-v1.png'
SCALE=.065
SOURCE_CONTACT=(420,1368)
NATIVE_ROOT=(196,267)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def dump(p,value):p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def run():
 with Image.open(MASTER) as image:
  image=image.convert('RGBA');assert image.size==(1024,1536)
  # A fixed threshold removes only the generated low-alpha diffuse background;
  # retain the painted source colours, opaque actor and compact contact shadow.
  image.putalpha(image.getchannel('A').point(lambda a:a if a>=32 else 0))
  inverse=(1/SCALE,0,SOURCE_CONTACT[0]-NATIVE_ROOT[0]/SCALE,
           0,1/SCALE,SOURCE_CONTACT[1]-NATIVE_ROOT[1]/SCALE)
  native=image.transform((450,400),Image.Transform.AFFINE,inverse,
                         resample=Image.Resampling.BICUBIC)
  assert native.getchannel('A').getbbox() is not None
  native_path=D/'holding-native-pilot-v1.png';native.save(native_path)
 inputs=[MASTER,D/'actual-sent-prompt-v1.txt',Path(__file__),native_path,S/'original-technical-contract-v1.json']
 ledger={'workflow':'image-based-painted-2d','derived_from_blender':False,'user_rejected':False,
  'status':'authored configuration','scope':'Single source identity pilot; no complete action set or active selection',
  'assembly_operations':['fixed-canvas','root-placement','alpha-cleanup','png-conversion'],
  'origins':[{'kind':'image-generation','path':rel(MASTER),'sha256':sha(MASTER)}],
  'files_sha256':{rel(p):sha(p) for p in inputs},
  'provider':'OpenAI built-in imagegen','model_id_exposed':False,
  'source_contact':list(SOURCE_CONTACT),'native_root':list(NATIVE_ROOT),'scale':SCALE,
  'alpha_cleanup_threshold':32,'native_execution':False,'visual_approval_granted':False,
  'release_accepted':False,
  'external_read_only_style_reference':{'path':'runeterra-demacia/references/frames/cpkman/g02-f000.png',
   'sha256':sha(W/'runeterra-demacia/references/frames/cpkman/g02-f000.png'),'bundled':False},
  'external_read_only_crest_reference':{'url':'https://dd.b.pvp.net/7_10_0/core/en_us/img/regions/icon-targon.png',
   'sha256':'241c6fd4473ad6eff7f8516609433ecf9ccfb3139906ab0de926f883236ea4d9','bundled':False}}
 ledger_path=D/'generation-identity-pilot-v1.json';dump(ledger_path,ledger)
 recipe={'recipe_type':'vcmi_animation','unit':'rakkorTrailguard','canvas':[450,400],
  'pivot':{'x':196,'y':267},'generateOverlay':0,'generateShadow':0,
  'output_path':'Content/Sprites/runeterra/targon/creatures/rakkorTrailguard/holding-pilot.json',
  'groups':[{'group':2,'frames':[{'source':rel(native_path),'sha256':sha(native_path),'source_canvas':[450,400]}]}],
  'generation':{'workflow':'image-based-painted-2d','image_generation_used':True,
    'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','model_id_exposed':False,
    'prompt':(D/'actual-sent-prompt-v1.txt').read_text(encoding='utf-8'),'painted_master':rel(MASTER),
    'source_generation_ledger':rel(ledger_path),'source_generation_ledger_sha256':sha(ledger_path),
    'producer_source':rel(Path(__file__))},
  'production_status':'painted-master-complete-unapproved','status':'authored configuration',
  'visual_approval_granted':False,'credits':{'author':'Project-directed built-in imagegen and technical2D conversion',
   'license':None,'redistribution':'unresolved; release prohibited'},
  'acceptance':'Single standing SOURCE PILOT only. All canonical actions, native observations and rights remain pending.'}
 recipe_path=D/'holding-pilot-recipe-v1.json';dump(recipe_path,recipe)
 print(json.dumps({'native_path':rel(native_path),'native_alpha_bbox':native.getchannel('A').getbbox(),
  'recipe':rel(recipe_path),'native_execution':False,'active_selection':False}))
if __name__=='__main__':run()
