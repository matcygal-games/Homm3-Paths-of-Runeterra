"""Meaningful bounded coastline regressions against the unchanged consumer."""
from prepare_candidate import *

def probe(kind):
    with tempfile.TemporaryDirectory(prefix='waterfront-negative-',dir=REPORT) as tmp:
        project=Path(tmp);shutil.copytree(PROJECT/'assets/source/town',project/'assets/source/town')
        shutil.copytree(PROJECT/'assets/generated',project/'assets/generated');shutil.copytree(REPORT/'native-candidate',project/'assets/generated',dirs_exist_ok=True)
        contract=read(HERE/'layout-contract-candidate.json')
        if kind=='missing-piling-support':
            reference=contract['silhouette_plan']['states']['shipyard']['marine_support_mask'];target=project/reference['path'];im=Image.open(target).convert('L');xy=next((x,y) for y in range(374) for x in range(800) if im.getpixel((x,y)));im.putpixel(xy,0);save(target,im);reference['sha256']=sha(target)
        elif kind=='changed-selected-coast':
            structure=read(PROJECT/'content/factions.json')['shurima']['town']['structures']['ship'];animation=read(project/'assets/generated/Content/Sprites'/structure['animation']);target=project/'assets/generated/Content/Sprites'/(animation['basepath']+animation['sequences'][0]['frames'][0]);im=Image.open(target).convert('RGBA');im.putpixel((638,323),(255,0,0,255));save(target,im)
        target=project/HERE.relative_to(PROJECT)/'layout-contract-candidate.json';dump(target,contract)
        design=read(PROJECT/'design/town-visuals.json');design['layout_contract']={'path':target.relative_to(project).as_posix(),'sha256':sha(target)};dump(project/'design/town-visuals.json',design)
        faction=read(PROJECT/'content/factions.json');errors,_=faction_town_layout.inspect(project,{'factions':faction},'shurima')
    expected={'positive':None,'missing-piling-support':'Actual foundation lacks level support','changed-selected-coast':'Current selected town pixels differ'}[kind]
    return {'case':kind,'passed':not errors if expected is None else any(expected in e for e in errors),'expected':expected,'actual_errors':errors}

def main():
    checks=[probe(k) for k in ['positive','missing-piling-support','changed-selected-coast']]
    coast=Image.open(HERE/'ship-body.png').convert('L');dock=Image.open(HERE/'shipyard-body.png').convert('L')
    checks.append({'case':'ship-native-replacement-retains-full-quay','passed':ImageChops.subtract(dock,coast).getbbox() is None and ImageChops.subtract(coast,dock).getbbox() is not None})
    bad=ImageChops.subtract(coast,dock)
    checks.append({'case':'boat-only-regression-detected','passed':ImageChops.subtract(dock,bad).getbbox() is not None})
    packet=read(HERE/'integration-plan.json');oldpins=read(OLD/'candidate-selection.json')['native_output_pins'];icons={k:v for k,v in packet['native_output_pins'].items() if 'buildingIcons-frames/' in k};changed=[k for k,v in icons.items() if oldpins[k]!=v]
    checks.append({'case':'only-two-coastal-hall-icons-change','passed':len(changed)==2,'total_icons':len(icons),'changed':changed})
    checks.append({'case':'canonical-ten-recipe-roots-preserved','passed':all(sha(PROJECT/r['target'])==r['before_sha256'] for r in packet['recipes'])})
    # Native-size comparison against extracted original Castle coastal sprites.
    canvas=Image.new('RGB',(640,180),(35,35,35));draw=ImageDraw.Draw(canvas);references=[]
    for i,state in enumerate(['shipyard','ship']):
        original=WORKSPACE/'runeterra-demacia/references/frames'/('tbcsdock' if state=='shipyard' else 'tbcsboat')/'g00-f000.png';references.append({'path':original.relative_to(WORKSPACE).as_posix(),'sha256':sha(original)})
        refim=Image.open(original).convert('RGBA');candidate=Image.open(HERE/(state+'-candidate.png')).convert('RGBA');candidate=candidate.crop(candidate.getchannel('A').getbbox())
        canvas.paste(refim,(i*320,30),refim);canvas.paste(candidate,(i*320+160,30),candidate);draw.text((i*320+4,8),'Castle original / Shurima '+state,fill='white')
    save(REPORT/'native-original-comparison.png',canvas)
    html=REPORT/'index.html';markup=html.read_text(encoding='utf8')
    if 'native-original-comparison.png' not in markup:
        html.write_text(markup+'<h2>Native original reference comparison (1:1)</h2><img src="native-original-comparison.png"><p><a href="HANDOFF.txt">Coordinator handoff</a> · <a href="candidate-proof.json">Actual compile and layout proof</a> · <a href="focused-regressions.json">Seven executed regressions</a></p>',encoding='utf8')
    result={'status':'authored configuration','candidate_only':True,'runtime_verified':False,'release_accepted':False,'checks':checks,'executed_cases':len(checks),'passed':sum(c['passed'] for c in checks),'ok':all(c['passed'] for c in checks),'original_readonly_reference_comparison':references}
    dump(REPORT/'focused-regressions.json',result);print(json.dumps(result));return result

if __name__=='__main__':sys.exit(0 if main()['ok'] else 2)
