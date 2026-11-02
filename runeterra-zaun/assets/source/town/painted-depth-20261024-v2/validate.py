"""Actual selected-pixel placement checks and destructive negative controls."""
from pathlib import Path
import json, hashlib, copy
from PIL import Image,ImageChops,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/town-depth-20261024-v2'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mask(im):return im.getchannel('A').point(lambda a:255 if a>=128 else 0)
def count(im):return sum(im.histogram()[128:])
def polygon(points):
    im=Image.new('L',(800,374));ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=255);return im

def geometry(plan,layers,*,water=None,floor=None):
    failures=[];checks=0
    def check(ok,kind,item):
        nonlocal checks
        checks+=1
        if not ok:failures.append({'kind':kind,'item':item})
    water=water if water is not None else polygon(plan['terrain']['water_polygon'])
    floor=floor if floor is not None else polygon(plan['terrain']['buildable_floor_polygon'])
    rows={r['state']:r for r in plan['states']};masks={s:mask(im) for s,im in layers.items()}
    for state,im in layers.items():
        bb=masks[state].getbbox();check(im.size==(800,374) and bb is not None,'canvas',state)
        if bb is None:continue
        row=rows[state];foot=masks[state].copy();foot.paste(0,(0,0,800,bb[3]-8))
        if row['site']!='shipyard':
            check(count(ImageChops.multiply(foot,water))==0,'water',state)
            check(count(ImageChops.multiply(foot,ImageChops.invert(floor)))==0,'unsupported',state)
        check(row['native_z']==row['composition_rectangle'][1]+row['composition_rectangle'][3],'depth',state)
        check(count(masks[state])>=40,'click',state)
    names=sorted(masks)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            if rows[a]['site']!=rows[b]['site']:
                check(count(ImageChops.multiply(masks[a],masks[b]))==0,'overlap',[a,b])
    sites={s['id']:s for s in plan['sites']}
    check((len(sites),len(layers))==(20,36),'contract','20 sites/36 states')
    check(len({s['native_z'] for s in sites.values()})==20,'independent-z','20 distinct sites')
    for tier in range(1,8):
        check(rows[f'dwellingLvl{tier}']['site']==rows[f'dwellingUpLvl{tier}']['site'],'tier-site',tier)
    # Selected buildings, not abstract rectangle labels: compare actual opaque
    # heights/widths of foreground framing with the distant civic monument.
    near=masks['dwellingUpLvl1'].getbbox();far=masks['capitol'].getbbox()
    check(near[3]-near[1]>(far[3]-far[1])*1.2,'apparent-depth','foreground frame taller than distant civic building')
    near2=masks['dwellingUpLvl2'].getbbox();far2=masks['dwellingUpLvl7'].getbbox()
    check(near2[2]-near2[0]>(far2[2]-far2[0])*1.1,'apparent-depth','near worker yard wider than distant foundry')
    for back in ['capitol','castle','mageGuild4','dwellingUpLvl7']:
        check(rows[back]['native_z']<rows['dwellingUpLvl1']['native_z'],'rear-z',back)
    return {'ok':not failures,'checks':checks,'failures':failures}

def main():
    plan=read(HERE/'layout.json')
    layers={r['state']:Image.open(ROOT/r['native_layer']).convert('RGBA') for r in plan['states']}
    result=geometry(plan,layers);extra=[]
    def check(ok,label):extra.append({'ok':bool(ok),'check':label})
    for row in plan['states']:
        state=row['state'];folder=HERE/'structures'/state;m=mask(layers[state])
        check(sha(ROOT/row['master'])==row['master_sha256'],state+' painted master pinned')
        check(sha(ROOT/row['native_layer'])==row['native_layer_sha256'],state+' native layer pinned')
        area=Image.open(folder/'area.png').convert('RGBA');border=Image.open(folder/'border.png').convert('RGBA')
        check(area.getchannel('A').tobytes()==m.tobytes(),state+' click exact alpha')
        check(border.getchannel('A').tobytes()==ImageChops.subtract(m.filter(ImageFilter.MaxFilter(3)),m).tobytes(),state+' outward border')
        check(Image.open(folder/'construction.png').size==(150,70),state+' construction size')
    for binding in plan['recipe_bindings']:
        path=ROOT/binding['candidate'];recipe=read(path)
        check(sha(path)==binding['sha256'],binding['active']+' recipe pinned')
        for dep in recipe.get('dependencies',[]):
            check((ROOT/dep['path']).is_file() and sha(ROOT/dep['path'])==dep['sha256'],binding['active']+' dependency '+dep['path'])
    expected=layers['shipyard'].copy();expected.alpha_composite(Image.open(HERE/'structures/ship/boat-only.png').convert('RGBA'))
    check(expected.tobytes()==layers['ship'].tobytes(),'native ship includes exact dock+boat replacement')
    mutations=[]
    def negative(name,kind,p,l,**kwargs):
        outcome=geometry(p,l,**kwargs)
        mutations.append({'name':name,'expected':kind,'rejected':any(f['kind']==kind for f in outcome['failures']),'failures':outcome['failures']})
    bad=dict(layers);crop=layers['blacksmith'].crop(layers['blacksmith'].getchannel('A').getbbox())
    moved=Image.new('RGBA',(800,374));target=mask(layers['special2']).getbbox();moved.alpha_composite(crop,(target[0],target[1]));bad['blacksmith']=moved
    negative('actual selected body moved over clinic','overlap',plan,bad)
    bad=dict(layers);moved=Image.new('RGBA',(800,374));moved.alpha_composite(crop,(690,330));bad['blacksmith']=moved
    negative('dry service moved into actual coastal water','water',plan,bad)
    floor=polygon(plan['terrain']['buildable_floor_polygon']);bb=mask(layers['capitol']).getbbox();ImageDraw.Draw(floor).rectangle((bb[0],bb[3]-8,bb[2],bb[3]),fill=0)
    negative('support removed under actual civic foundation','unsupported',plan,layers,floor=floor)
    bad=copy.deepcopy(plan);next(r for r in bad['states'] if r['state']=='capitol')['native_z']=370
    negative('actual civic state depth corrupted','depth',bad,layers)
    bad=dict(layers);small=layers['dwellingUpLvl1'].crop(mask(layers['dwellingUpLvl1']).getbbox());small.thumbnail((60,50));moved=Image.new('RGBA',(800,374));moved.alpha_composite(small,(20,320));bad['dwellingUpLvl1']=moved
    negative('foreground actual painted body shrunk below distant monument','apparent-depth',plan,bad)
    determinism=read(REPORT/'compiler-determinism.json')
    check(determinism['ok'] and determinism['recipe_count']==145,'145 affected recipes replay exact actual converter')
    output={'ok':result['ok'] and all(x['ok'] for x in extra) and all(x['rejected'] for x in mutations),
            'status':'authored configuration','geometry':result,'additional_checks':extra,'negative_controls':mutations,
            'executed_checks':result['checks']+len(extra)+len(mutations),'visual_approval_granted':False,'runtime_verified':False}
    (REPORT/'geometry-validation.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'ok':output['ok'],'checks':output['executed_checks'],'failures':result['failures'],
                      'extra_failed':[x for x in extra if not x['ok']],'negative_rejections':[x['rejected'] for x in mutations]}))
    return 0 if output['ok'] else 2

if __name__=='__main__':raise SystemExit(main())
