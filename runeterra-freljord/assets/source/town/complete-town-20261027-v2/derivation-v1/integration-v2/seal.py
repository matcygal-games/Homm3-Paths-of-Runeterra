"""Prepare exact, reviewable coordinator integration plan without active writes."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    candidate=HERE.parent/'candidate';reports=PROJECT/'build/reports/complete-town-20261027-v2/derivation-finish-v1'
    receipts=sorted(reports.glob('attempt-*/VERIFY-v1.json'));receipt=receipts[-1];value=read(receipt)
    assert value['layout_ok'] and value['restored_layout_ok'] and value['readonly_converter_ok']
    assert value['root_case_scenes_ok'] and value['grail_case_regression_negative']['passed']
    assert all(r['passed'] for r in value['converter_negatives']+value['geometry_negatives'])
    old=read(PROJECT/'content/factions.json');new=read(candidate/'factions.candidate.json');flavor=read(HERE.parent/'flavor-deltas.json')
    # Normalize only the authorized structure positions/depths and exact flavor
    # fields, then require every other content/mechanic/ID byte value unchanged.
    normalized=json.loads(json.dumps(new))
    for state,v in normalized['freljord']['town']['structures'].items():
        assert v['x']==v['y']==0
        v['x']=old['freljord']['town']['structures'][state]['x'];v['y']=old['freljord']['town']['structures'][state]['y'];v['z']=old['freljord']['town']['structures'][state]['z']
    for delta in flavor['deltas']:
        p=normalized;q=old
        for k in delta['pointer'][:-1]:p=p[k];q=q[k]
        k=delta['pointer'][-1];assert p[k]==delta['new'] and q[k]==delta['old'];p[k]=q[k]
    assert normalized==old,'Unapproved content/ID/mechanic difference'
    changes=[]
    pairs=[(p,'assets/recipes/'+p.relative_to(candidate/'recipes').as_posix())for p in sorted((candidate/'recipes').rglob('*.json'))]
    pairs += [(candidate/'town-visuals.json','design/town-visuals.json'),(candidate/'factions.candidate.json','content/factions.json')]
    for source,name in pairs:
        target=PROJECT/name;changes.append({'source':source.relative_to(PROJECT).as_posix(),'destination':name,'before_sha256':sha(target) if target.is_file()else None,'after_sha256':sha(source)})
    inventory={p.relative_to(PROJECT).as_posix():sha(p)for p in sorted(HERE.parent.parent.rglob('*')) if p.is_file() and '__pycache__'not in p.parts and not p.is_relative_to(HERE)}
    plan={'status':'authored configuration','coordinator_only':True,'worker_applied':False,'native_verified':False,'release_accepted':False,'integrator_sha256':sha(HERE/'integrate.py'),'shared_geometry_helper_sha256':sha(PROJECT.parent/'scripts/faction_town_layout.py'),'verification_receipt':{'path':receipt.relative_to(PROJECT).as_posix(),'sha256':sha(receipt)},'changes':changes,'source_inventory':inventory,'content_scope':'Current structures x0/y0/native z only and the two exact root-authorized flavor fields; no IDs, costs, prerequisites, recruitment, growth, hero or mechanic changes.'}
    (HERE/'plan.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'plan_sha256':sha(HERE/'plan.json'),'integrator_sha256':sha(HERE/'integrate.py'),'canonical_change_files':len(changes),'source_pins':len(inventory),'receipt':plan['verification_receipt']},indent=2))
if __name__=='__main__':main()
