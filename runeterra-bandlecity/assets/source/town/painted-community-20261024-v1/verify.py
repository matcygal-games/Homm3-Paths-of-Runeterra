"""Bounded pixel/pin review of candidate only; no acceptance gate changes."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops,ImageFilter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/painted-town-community-20261024-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    checks=[]
    def check(name,condition):checks.append({'check':name,'ok':bool(condition)})
    handoff=json.loads((HERE/'coordinator-handoff.json').read_text())
    metrics=json.loads((REPORT/'source-state-checks.json').read_text())
    current=json.loads((ROOT/'design/town-visuals.json').read_text())
    check('16 ordinary land plots',len([s for s in handoff['sites'] if s['id'] not in ['coast','grailOrnament']])==16)
    states=[s for site in handoff['sites'] for s in site['states']]
    check('35 functional states preserved',len(states)==35 and len(set(states))==35)
    check('one optional coastal site',len([s for s in handoff['sites'] if s['id']=='coast'])==1)
    check('Grail remains ornament',len([s for s in handoff['sites'] if s['id']=='grailOrnament'])==1)
    for tier in range(1,8):
        site=next(s for s in handoff['sites'] if s['id']=='dwelling'+str(tier))
        check(f'tier{tier} base/up share one site',site['states']==['dwellingLvl'+str(tier),'dwellingUpLvl'+str(tier)])
    originals={state:site for site in current['sites'] for state in site['states']}
    retained=0;new=0
    for row in metrics['rows']:
        state=row['state'];d=HERE/'structures'/state;master=ROOT/row['master']
        check(state+' source pin',sha(master)==row['master_sha256'])
        check(state+' native layer pin',sha(d/'layer.png')==row['native_layer_sha256'])
        layer=Image.open(d/'layer.png');check(state+' RGBA native canvas',layer.mode=='RGBA' and layer.size==(800,374))
        mask=layer.getchannel('A').point(lambda p:255 if p>=128 else 0)
        area=Image.open(d/'area.png').getchannel('A');border=Image.open(d/'border.png').getchannel('A')
        check(state+' exact click mask',ImageChops.difference(mask,area).getbbox() is None)
        expected=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),mask)
        check(state+' exact outline',ImageChops.difference(expected,border).getbbox() is None)
        check(state+' hall150x70 campaign58x64',Image.open(d/'hall-icon.png').size==(150,70) and Image.open(d/'campaign.png').size==(58,64))
        check(state+' nonempty silhouette',mask.getbbox() is not None)
        if row['site']!='coast':check(state+' dry annotated footing',row['footing_water_pixels']==0)
        if 'painted-community-20261024-v1' not in row['master']:
            retained+=1;check(state+' preserved existing master',row['master_sha256']==originals[state]['sha256'][state])
        else:
            new+=1;generation=json.loads((master.parent/'generation.json').read_text())
            check(state+' actual built-in generation',generation['image_generation_used'] and generation['tool']=='image_gen.imagegen' and generation['painted_master_sha256']==sha(master))
    check('29 existing and6new masters',retained==29 and new==6)
    check('every state conservatively click-exposed',min(s['exposed_click_pixels'] for s in metrics['conservative_exposure'])>0)
    yard=Image.open(HERE/'structures/shipyard/layer.png').getchannel('A').point(lambda p:255 if p>=128 else 0)
    boat=Image.open(HERE/'structures/ship/layer.png').getchannel('A').point(lambda p:255 if p>=128 else 0)
    yard_exposed=sum(ImageChops.subtract(yard,boat).histogram()[128:])
    check('independent moored ship leaves dock visibly exposed',yard_exposed>0)
    compile=json.loads((REPORT/'compiler-determinism.json').read_text())
    check('actual shared compiler twice identical',compile['actual_shared_compiler'] and compile['ok'] and compile['runs']==2 and compile['identical_bytes'] and not compile['errors'])
    # Independent compare every stored payload byte against declared compiler output.
    for target,pin in compile['outputs'].items():
        check('two payload byte pins '+target,sha(REPORT/'compiler-run-1'/target)==pin and sha(REPORT/'compiler-run-2'/target)==pin)
    output={'ok':all(c['ok'] for c in checks),'checks_executed':len(checks),'failed':[c for c in checks if not c['ok']],
        'checks':checks,'status':'authored configuration','visual_approval_granted':False,
        'scope':'Source/pixel/byte candidate checks only; no native runtime, human visual, or rights acceptance',
        'simultaneous_shipyard_exposed_click_pixels':yard_exposed,
        'minimum_exposed_click_pixels':min(s['exposed_click_pixels'] for s in metrics['conservative_exposure'])}
    (REPORT/'executed-checks.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:output[k] for k in ['ok','checks_executed','failed','minimum_exposed_click_pixels']}))
    return 0 if output['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
