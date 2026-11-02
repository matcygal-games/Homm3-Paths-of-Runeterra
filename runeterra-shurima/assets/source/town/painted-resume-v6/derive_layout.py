"""Bounded report-only layout candidate from35 selected painted layers.

No source design/faction, active producer, generated resource or stage writes.
Uniform scale is per family. Complete family union crops preserve all pixels;
all states retain their original horizontal site center and share new contact.
"""
from pathlib import Path
from PIL import Image
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];WS=PROJECT.parent
REPORT=PROJECT/'build/reports/town-layout-candidate-20261024-v6'
HELPER=PROJECT/'assets/source/town/painted-resume-v2/derive_states.py'
HELPER_SHA='9244b8e0109d40de74eab4b9716d43ac7cb170f6aaebdda3daa96b045d4eb56f'
PREFIX='Content/Sprites/runeterra/shurima/town/structures/'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,raw):
    assert any(p.resolve().is_relative_to(r) for r in (HERE,REPORT));p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw)
def write(p,v):put(p,(json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
def helper():
    assert sha(HELPER)==HELPER_SHA
    spec=importlib.util.spec_from_file_location('painted_v2_technical',HELPER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def main():
    h=helper();analysis=read(REPORT/'v2/analysis.json');selected=read(REPORT/'selected-inputs.json');plan=read(REPORT/'layout-plan-v2.json')
    manifest=read(PROJECT/'assets/manifest.json');manifest_outputs={r['output_path']:r for r in manifest['assets']}
    protected={}
    for directory in ('assets/source/town/buildings-v1','assets/source/town/buildings-v2','assets/source/town/painted-resume-v1','assets/source/town/painted-resume-v2','assets/source/town/painted-resume-v3','assets/source/town/painted-resume-v4','assets/source/town/painted-resume-v5','assets/recipes/town'):
        for p in (PROJECT/directory).rglob('*'):
            if p.is_file():protected[p.relative_to(PROJECT).as_posix()]=sha(p)
    for name in ('content/factions.json','design/town-visuals.json','assets/manifest.json','assets/source/town/landscape-v1/native-rgba.png'):
        protected[name]=sha(PROJECT/name)
    producers={}
    for path in (PROJECT/'assets/recipes').rglob('*.json'):
        r=read(path)
        if r.get('output_path'):producers.setdefault(r['output_path'],[]).append(path)
    active={};campaign={}
    for key,pin in selected['lookup'].items():
        name=PREFIX+key+'.json';paths=producers[name];assert len(paths)==1
        path=paths[0];recipe=read(path);frame=recipe['groups'][0]['frames'][0]
        assert frame['source']==pin['source'] and frame['source_sha256']==pin['sha256']==sha(PROJECT/pin['source']),(key,'Actual selected producer differs')
        assert manifest_outputs[name]['source']['recipe_path']==path.relative_to(PROJECT).as_posix(),(key,'Manifest pointer mismatch')
        active[key]=(path,recipe)
        cp=producers[PREFIX+key+'_campaign.png'];assert len(cp)==1;campaign[key]=read(cp[0])
    write(REPORT/'conversion-input-baseline.json',{'protected':protected,'selected35_verified_against_actual_active_producers_and_manifest':True,'plan_sha256':sha(REPORT/'layout-plan-v2.json'),'analysis_sha256':sha(REPORT/'v2/analysis.json'),'native_execution':False})
    faction=read(PROJECT/'content/factions.json')['shurima']['town'];design=read(PROJECT/'design/town-visuals.json')
    sites={**design['sites'],**design['special_sites']};unionboxes={}
    for family,site in sites.items():
        boxes=[analysis['jobs'][k]['native_alpha_bbox'] for k in site['keys']]
        b=[min(v[0] for v in boxes),min(v[1] for v in boxes),max(v[2] for v in boxes),max(v[3] for v in boxes)]
        site['box']=[b[0],b[1],b[2]-b[0],b[3]-b[1]];unionboxes[family]=site['box']
    design['camera']='Low frontal original Heroes III perspective; rear monumental structures retain greater apparent mass than foreground services. All site families use explicit coherent terrace registration.'
    design['plate_rules']=[r for r in design['plate_rules'] if r!='Back monuments retain physical mass while near services read closer and larger']+['Rear monumental silhouettes retain greater apparent mass than foreground domestic/service buildings','No unintended structural layer intersections; shadow fringe remains distinct','Dry-land foundation bands remain on dry terraces; only the intentional coast family meets the visible channel']
    design['visual_approval_granted']=False;design['review']='V6 authored layout candidate only: all35 selected painted states, no native/runtime/art approval. Manual conservative water annotation qualifies contact checks; coordinator integration remains pending.'
    write(REPORT/'town-visuals.candidate.json',design)
    sys.path.insert(0,str(WS/'scripts'));import faction_art_compile
    sys.path.insert(0,str(PROJECT/'scripts'));import art_policy
    compiler=faction_art_compile.create_compiler('shurima');records=[];compiled={};receipts=[];policy={}
    for key in sorted(selected['lookup']):
        job=analysis['jobs'][key];path,oldrecipe=active[key]
        with Image.open(REPORT/'v2'/(key+'.png')) as im:frame=im.convert('RGBA')
        with Image.open(PROJECT/oldrecipe['generation']['painted_master']) as im:master=im.convert('RGBA')
        surfaces=h.surfaces(frame,master)
        campaign_source=PROJECT/campaign[key]['source'];assert sha(campaign_source)==campaign[key]['source_sha256']
        with Image.open(campaign_source) as im:surfaces['campaign']=im.convert('RGBA')
        sources={}
        for role,im in surfaces.items():
            source=HERE/key/(role+'.png');put(source,h.png(im));sources[role]={'path':source.relative_to(PROJECT).as_posix(),'sha256':sha(source)}
        common={k:oldrecipe[k] for k in ('status','production_status','generation','credits','visual_approval_granted') if k in oldrecipe}
        common['status']='painted-candidate';common['visual_approval_granted']=False
        mappings=[]
        for role,recipe in h.recipe_set(key,sources,common,{'native_site_box':unionboxes[job['family']]}).items():
            rp=REPORT/'recipe-payload'/(key+'-'+role+'.json');write(rp,recipe)
            errors=art_policy.recipe_errors(PROJECT,recipe);assert not errors,(key,role,errors);policy[rp.name]=errors
            outputs,receipt=compiler.plan(PROJECT,rp);receipts.append(receipt)
            for name,raw in outputs.items():
                assert name not in compiled;put(REPORT/'compiled'/name,raw);compiled[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'recipe_path':rp.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(rp)}
            mappings.append({'output_path':recipe['output_path'],'recipe_path':rp.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(rp)})
        records.append({'key':key,'registration':job,'prior_recipe':path.relative_to(PROJECT).as_posix(),'prior_recipe_sha256':sha(path),'painted_master':oldrecipe['generation']['painted_master'],'painted_master_sha256':sha(PROJECT/oldrecipe['generation']['painted_master']),'derived_sources':sources,'outputs':mappings})
    assert len(records)==35 and len(receipts)==140 and len(compiled)==175
    assert all(sha(PROJECT/p)==pin for p,pin in protected.items()),'Protected source/manifest drift during conversion'
    write(HERE/'registration.json',{'families':plan['families'],'states':records,'helper_sha256':HELPER_SHA,'new_image_generation_calls':0,'technical_only':True,'native_execution':False,'visual_approval_granted':False})
    write(REPORT/'conversion.json',{'states':records,'results':receipts,'compiled_outputs':compiled,'actual_converter_sha256':sha(WS/'scripts/faction_art_compile.py'),'recipe_policy':policy,'new_image_generation_calls':0,'native_execution':False,'active_producer_writes':False,'manifest_written':False,'stage_written':False,'shared_design_written':False,'visual_approval_granted':False})
    print(json.dumps({'states':len(records),'recipes':len(receipts),'compiled_resources':len(compiled),'policy_errors':0,'native_execution':False}))
if __name__=='__main__':main()
