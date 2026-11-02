"""Private native comparison evidence; original pixels never enter own recipes."""
from pathlib import Path
import importlib.util, json, sys
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('derive',HERE/'derive.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
sys.path.insert(0,str(d.WORKSPACE/'scripts'))
from noxus_schema_check import strip_jsonc

def execute():
    out=d.REPORT/('native-review-v%d'%(1+len(list(d.REPORT.glob('native-review-v*')))));out.mkdir(exist_ok=False)
    c=HERE/'candidate';refs=d.WORKSPACE/'runeterra-demacia/references'
    config=d.WORKSPACE/'vcmi-develop/vcmi-develop/config/factions/castle.json'
    original=json.loads(strip_jsonc(config.read_text()))['castle']['town'];castle=Image.open(refs/'images/tbcsback.pcx.png').convert('RGBA')
    states=['capitol','castle','mageGuild4','marketplace','resourceSilo','blacksmith','special1','special2','special3']+['dwellingUpLvl'+str(i) for i in range(1,8)]
    dependencies=[config,refs/'images/tbcsback.pcx.png']
    for state in sorted(states,key=lambda s:original['structures'][s].get('z',0)):
        v=original['structures'][state];p=refs/'frames'/Path(v['animation']).stem.lower()/'g00-f000.png'
        dependencies.append(p);castle.alpha_composite(Image.open(p).convert('RGBA'),(v['x'],v['y']))
    # Private reference composition stays in build/reports, never assets/source.
    castle.save(out/'original-castle-native.png')
    comparisons=[('Approved whole master',Image.open(HERE.parent/'complete-master-v2-native.png'), 'Corrected complete candidate',Image.open(c/'complete-native.png')),
                 ('Extracted original Castle, native coordinates',castle,'Freljord candidate, native coordinates',Image.open(c/'upgraded-native.png')),
                 ('Empty: static painted fjord retained',Image.open(c/'empty-native.png'),'Early construction',Image.open(c/'early-native.png')),
                 ('Base construction',Image.open(c/'base-native.png'),'Upgraded construction',Image.open(c/'upgraded-native.png')),
                 ('Optional Grail',Image.open(c/'grail-native.png'),'Optional dock + one hull',Image.open(c/'coastal-ship-native.png'))]
    sheet=Image.new('RGB',(1600,394*len(comparisons)),(28,30,38));draw=ImageDraw.Draw(sheet)
    for i,(left,a,right,b) in enumerate(comparisons):
        draw.text((4,i*394+3),left,fill='white');draw.text((804,i*394+3),right,fill='white');sheet.paste(a,(0,i*394+20));sheet.paste(b,(800,i*394+20))
    sheet.save(out/'native-comparisons.png')
    contract=d.read(c/'layout-contract.json');im=Image.open(c/'complete-native.png').convert('RGBA')
    for name,color in [('paths_mask',(50,255,80,160)),('stairs_mask',(255,170,0,170))]:
        mask=Image.open(d.PROJECT/contract['silhouette_plan'][name]['path']).convert('L');overlay=Image.new('RGBA',d.SIZE,color);overlay.putalpha(mask.point(lambda p:color[3] if p else 0));im=Image.alpha_composite(im,overlay)
    for state in contract['silhouette_plan']['complete_scene_states']:
        for role,color in [('foundation_mask',(255,40,100,220)),('door_mask',(70,180,255,210))]:
            mask=Image.open(d.PROJECT/contract['silhouette_plan']['states'][state][role]['path']).convert('L');overlay=Image.new('RGBA',d.SIZE,color);overlay.putalpha(mask.point(lambda p:color[3] if p else 0));im=Image.alpha_composite(im,overlay)
    im.save(out/'physical-native-overlay.png')
    d.write(out/'EVIDENCE-v1.json',{'status':'authored configuration','private_reference_only':True,'scale':'Every comparison panel is exactly800x374, no display resampling baked in','original_dependencies':[{'path':p.relative_to(d.WORKSPACE).as_posix(),'sha256':d.digest(p)}for p in dependencies],'candidate_contract':d.ref(c/'layout-contract.json'),'whole_family_transforms':[{'site':site,'scale':.88,'fixed_ground_root':anchor,'all_base_upgrade_layers_masks_doors_contacts_together':True} for site,anchor in [('dwelling-tier-1',[532,351]),('dwelling-tier-6',[695,330])]],'art_review':'Pending independent source-pixel review; technical mask checks are not semantic/art acceptance.','native_verified':False,'release_accepted':False,'output_hashes':{p.name:d.digest(p)for p in sorted(out.glob('*.png'))}})
    html='<!doctype html><meta charset="utf-8"><title>Freljord complete-town candidate native review</title><style>body{background:#191c24;color:#eee;font:16px sans-serif}img{image-rendering:auto;max-width:none}figure{margin:20px 0}</style><h1>Freljord complete-town V2 source candidate</h1><p>Authored configuration. Native-pixel panels; no runtime or release acceptance. Red contacts, blue doors/frontages, green paths, amber stairs.</p><figure><img src="physical-native-overlay.png"></figure><figure><img src="native-comparisons.png"></figure>'
    (out/'index.html').write_text(html,encoding='utf-8')
    print(out)
if __name__=='__main__':execute()
