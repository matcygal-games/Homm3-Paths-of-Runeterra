"""Technical crop/scale/composition of genuine generated terrain, no painted edits."""
from pathlib import Path
import hashlib,json,argparse
from PIL import Image,ImageOps,ImageChops
HERE=Path(__file__).resolve().parent
TOWN=HERE.parents[1]
ROOT=TOWN.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2/terrain-repairs-v6/upper-left-proposal'
BOX=(0,104,398,178)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',type=int,default=1);a=ap.parse_args();v=a.version
    bg=Image.open(TOWN/'terrain/final-native-v5.png').convert('RGBA')
    master=Image.open(HERE/f'generated-master-v{1 if v==1 else 2}.png').convert('RGBA')
    native=ImageOps.fit(master,(800,374) if v==1 else (400,178),method=Image.Resampling.LANCZOS)
    correction=None
    if v==3:
        floor=ImageOps.fit(Image.open(HERE/'college-right-master-v3.png').convert('RGBA'),(73,41),method=Image.Resampling.LANCZOS,centering=(0.5,0))
        native.alpha_composite(floor,(325,137));floor.save(HERE/'college-right-native-v3.png')
        correction={'master':'college-right-master-v3.png','master_sha256':sha(HERE/'college-right-master-v3.png'),'native_box':[325,137,398,178],'method':'Uniform coverfit73x41, top aligned; broad visible floor correction, not root-shaped masking.'}
    if v>=4:
        floor=ImageOps.fit(Image.open(HERE/'college-material-master-v4.png').convert('RGBA'),(98,48),method=Image.Resampling.LANCZOS)
        native.alpha_composite(floor,(300,130));floor.save(HERE/'college-material-native-v4.png')
        correction={'master':'college-material-master-v4.png','master_sha256':sha(HERE/'college-material-master-v4.png'),'native_box':[300,130,398,178],'method':'Uniform coverfit98x48; broad coherent painted forecourt floor and material transition, not root-shaped masking.'}
    if v==5:
        academy=ImageOps.fit(Image.open(HERE/'academy-left-master-v5.png').convert('RGBA'),(25,18),method=Image.Resampling.LANCZOS)
        native.alpha_composite(academy,(0,114));academy.save(HERE/'academy-left-native-v5.png')
        correction=[correction,{'master':'academy-left-master-v5.png','master_sha256':sha(HERE/'academy-left-master-v5.png'),'native_box':[0,114,25,132],'method':'Uniform coverfit25x18; broad genuine horizontal paving extends left landing above actual root row118.'}]
    patch=native.crop(BOX);patch.save(HERE/f'patch-native-v{v}.png')
    merged=bg.copy();merged.alpha_composite(patch,BOX[:2]);merged.save(HERE/f'terrain-recomposed-v{v}.png')
    diff=ImageChops.difference(bg.convert('RGB'),merged.convert('RGB'))
    s=json.loads((TOWN/'candidate-final-v5/selection.json').read_text())
    rows={r['state']:r for r in s['states']}
    for mode in ('empty','full','base'):
        im=merged.copy()
        chosen=[] if mode=='empty' else [site['states'][0] if mode=='base' else site['top'] for site in s['sites'] if site['id'] not in ('coast','grail')]
        for state in sorted(chosen,key=lambda k:rows[k]['native_z']):im.alpha_composite(Image.open(ROOT/rows[state]['native_layer']).convert('RGBA'))
        im.save(REPORT/f'{mode}-native-v{v}.png')
        im.crop((0,100,400,178)).resize((1600,312),Image.Resampling.NEAREST).save(REPORT/f'{mode}-repair-detail-4x-v{v}.png')
    receipt={'status':'design proposal','master_sha256':sha(HERE/f'generated-master-v{1 if v==1 else 2}.png'),'patch_sha256':sha(HERE/f'patch-native-v{v}.png'),'terrain_sha256':sha(HERE/f'terrain-recomposed-v{v}.png'),'native_patch_box':BOX,'actual_changed_bbox':diff.getbbox(),'master_size':master.size,'native_target_size':native.size,'correction':correction,'conversion':'Uniform cover fit with LANCZOS; crop exactnative rectangle; alpha composite atsame position. No artistic raster manipulation.','unchanged_building_states':len(rows),'not_integrated':True,'geometry_pass_claimed':False,'runtime_verified':False,'release_accepted':False}
    (REPORT/f'receipt-v{v}.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
