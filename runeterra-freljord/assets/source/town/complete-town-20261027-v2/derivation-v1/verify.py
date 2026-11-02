"""Run actual shared conversion and layout consumers in an isolated source copy."""
from pathlib import Path
import hashlib, importlib.util, json, shutil, sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('derive',HERE/'derive.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
sys.path.insert(0,str(d.WORKSPACE/'scripts'))
import faction_artifacts as fa, faction_pipeline as fp, faction_town_layout as layout, faction_production as prod

def execute():
    candidate=HERE/'candidate'
    out=d.REPORT/('attempt-%03d'%(1+len(list(d.REPORT.glob('attempt-*')))))
    out.mkdir(parents=True,exist_ok=False)
    scratch=out/'isolated-source-project'
    if scratch.exists():
        # Exact resolved target stays inside this worker's assigned report path.
        assert scratch.resolve().is_relative_to(out.resolve())
        shutil.rmtree(scratch)
    destination=scratch/'assets/source/town/complete-town-20261027-v2'
    shutil.copytree(HERE.parent,destination,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(candidate/'recipes',scratch/'assets/recipes')
    (scratch/'design').mkdir();shutil.copyfile(candidate/'town-visuals.json',scratch/'design/town-visuals.json')
    (scratch/'content').mkdir();shutil.copyfile(candidate/'factions.candidate.json',scratch/'content/factions.json')
    d.write(scratch/'assets/manifest.json',{'assets':[]})
    report={'scope':'Actual existing converters and selected town-layout/export consumers; source candidate only','status':'authored configuration','native_verified':False,'release_accepted':False,'helper':d.ref(d.PROJECT/'assets/source/town/complete-town-20261027-v2/derivation-v1/derive.py'),'shared_helper_sha256':d.digest(d.WORKSPACE/'scripts/faction_town_layout.py')}
    conversion=fa.convert(scratch,'freljord');d.write(out/'conversion.json',conversion)
    report['conversion_ok']=conversion['ok'];report['converted_recipes']=len(conversion['converted']);report['conversion_errors']=conversion['errors'];report['conversion_blocked']=conversion['blocked']
    check=fa.convert(scratch,'freljord',check=True);d.write(out/'converter-readonly-preflight.json',check)
    report['readonly_converter_ok']=check['ok']
    content={'factions':d.read(scratch/'content/factions.json')}
    errors,deps=layout.inspect(scratch,content,'freljord')
    report['layout_errors']=errors;report['layout_ok']=not errors;report['layout_dependencies']=len(deps)
    pipeline=fp.Pipeline(scratch,'runeterra-freljord','freljord')
    actual_errors,_=fp.inspect_town_layout(pipeline,content)
    report['actual_pipeline_layout_errors']=actual_errors
    entries=prod._current_town_layout_source_entries(pipeline,{})
    report['actual_source_export_entries']=len(entries)
    report['source_export_exact']=all(entries['runeterra-freljord/'+p.relative_to(scratch).as_posix()]==p.read_bytes() for p in layout.dependency_paths(scratch))
    report['source_export_helper_exact']=entries['scripts/faction_town_layout.py']==(d.WORKSPACE/'scripts/faction_town_layout.py').read_bytes()
    # Independent semantic evidence check: compose each case from ACTUALLY
    # CONVERTED frames and its named front site. Optional Grail must be visible
    # even though it is absent from the default complete-town selected list.
    selected_contract=d.read(scratch/d.read(scratch/'design/town-visuals.json')['layout_contract']['path'])
    def case_scene_checks(contract):
        town=content['factions']['freljord']['town'];native={}
        for state,structure in town['structures'].items():
            definition=d.read(scratch/'assets/generated/Content/Sprites'/structure['animation'])
            resource=definition['basepath']+definition['sequences'][0]['frames'][0]
            native[state]=d.Image.open(scratch/'assets/generated/Content/Sprites'/resource).convert('RGBA')
        def compose(states):
            out=d.Image.open(scratch/contract['background']['path']).convert('RGBA')
            for state in sorted(states,key=lambda s:town['structures'][s]['z']):out=d.Image.alpha_composite(out,native[state])
            return out
        sites={s['id']:s for s in contract['sites']};results=[]
        for row in contract['silhouette_plan']['foundation_occlusions']:
            states=contract['silhouette_plan']['complete_scene_states'].copy();front=sites[row['front']]
            if not any(s in states for s in front['states']):states.append(front['states'][-1])
            full=compose(states);absent=compose([s for s in states if s not in front['states']])
            actualfull=d.Image.open(scratch/row['evidence']['complete_scene']['path']).convert('RGBA');actualabsent=d.Image.open(scratch/row['evidence']['front_absent_scene']['path']).convert('RGBA')
            results.append({'behind':row['behind'],'front':row['front'],'complete_equals_actual_front_present_composition':full.tobytes()==actualfull.tobytes(),'front_absent_equals_actual_front_removed_composition':absent.tobytes()==actualabsent.tobytes(),'front_really_changes_pixels':full.tobytes()!=absent.tobytes()})
        return results
    report['root_case_scene_checks']=case_scene_checks(selected_contract)
    report['root_case_scenes_ok']=all(all(v for k,v in row.items() if k not in ('behind','front')) for row in report['root_case_scene_checks'])
    old_bug=json.loads(json.dumps(selected_contract))
    for row in old_bug['silhouette_plan']['foundation_occlusions']:
        if row['front']=='grail':row['evidence']['complete_scene']=row['evidence']['front_absent_scene']
    buggy=case_scene_checks(old_bug)
    report['grail_case_regression_negative']={'name':'omit-actual-grail-occluder-from-case-full-evidence','passed':any(row['front']=='grail' and not row['complete_equals_actual_front_present_composition'] for row in buggy),'observed':buggy}
    outputs={}
    for p in sorted((scratch/'assets/generated').rglob('*')):
        if p.is_file():outputs[p.relative_to(scratch/'assets/generated').as_posix()]=d.digest(p)
    d.write(out/'compiled-output-hashes.json',outputs);report['compiled_outputs']=len(outputs)
    # Genuine converter negatives use real selected Freljord sources/recipes.
    negatives=[]
    for name,mutate,expected in [
      ('changed-frame-hash',lambda r:r['groups'][0]['frames'][0].update(source_sha256='0'*64),'Source frame checksum changed'),
      ('duplicate-group',lambda r:r['groups'].append(r['groups'][0].copy()),'Duplicate or invalid animation group'),
      ('wrong-native-canvas',lambda r:r.update(canvas=[799,374]),'Frame canvas mismatch'),
      ('frame-path-traversal',lambda r:r['groups'][0]['frames'][0].update(source='../outside.png'),'Unsafe relative path')]:
        recipe=d.read(scratch/'assets/recipes/town/structures/capitol-animation.json');mutate(recipe)
        try:fa.convert_animation(scratch,recipe,d.PREFIX,False,{});observed='UNEXPECTED PASS'
        except (ValueError,OSError,KeyError) as e:observed=str(e)
        negatives.append({'name':name,'expected':expected,'observed':observed,'passed':expected in observed or name=='frame-path-traversal' and 'path' in observed.lower()})
    report['converter_negatives']=negatives
    geometry_negatives=[]
    designpath=scratch/'design/town-visuals.json';originaldesign=d.read(designpath)
    contractpath=scratch/originaldesign['layout_contract']['path'];baseline=d.read(contractpath)
    def localref(path):return {'path':path.relative_to(scratch).as_posix(),'sha256':d.digest(path)}
    def newmask(contract,name,im):
        path=contractpath.parent/'negative-checks'/(name+'.png');path.parent.mkdir(exist_ok=True);im.save(path);return localref(path)
    def checknegative(name,mutator,expected):
        contract=json.loads(json.dumps(baseline));mutator(contract)
        d.write(contractpath,contract);design=json.loads(json.dumps(originaldesign));design['layout_contract']=localref(contractpath);d.write(designpath,design)
        observed,_=layout.inspect(scratch,content,'freljord')
        geometry_negatives.append({'name':name,'expected':expected,'observed':observed,'passed':report['layout_ok'] and bool(observed) and expected in observed[0]})
        d.write(contractpath,baseline);d.write(designpath,originaldesign)
    def maskfrom(reference):return d.Image.open(scratch/reference['path']).convert('L')
    def stairsfoundation(contract):
        rec=contract['silhouette_plan']['states']['capitol'];im=maskfrom(rec['foundation_mask']);im.putpixel((335,135),255);rec['foundation_mask']=newmask(contract,'root-on-real-civic-stair',im)
    checknegative('actual-root-on-civic-stair',stairsfoundation,'Actual foundation lacks level support')
    def forgedsilhouette(contract):
        site=contract['sites'][0];im=maskfrom(site['silhouette_mask']);im.putpixel((0,0),255);site['silhouette_mask']=newmask(contract,'forged-full-silhouette',im)
    checknegative('forged-site-silhouette',forgedsilhouette,'Site silhouette differs')
    def disconnected(contract):
        rec=contract['silhouette_plan']['states']['capitol'];im=d.blank();im.putpixel((330,310),255);rec['approach_mask']=newmask(contract,'disconnected-actual-civic-approach',im)
    checknegative('actual-civic-approach-disconnected',disconnected,'Approach must connect actual doorway')
    def giantmarine(contract):
        rec=contract['silhouette_plan']['states']['ship'];rec['marine_support_mask']=contract['silhouette_plan']['water_mask']
    checknegative('whole-water-instead-of-bounded-hull',giantmarine,'Marine support must trace actual bounded hull/deck')
    if baseline['silhouette_plan']['foundation_occlusions']:
        checknegative('remove-actual-root-projection-approval',lambda c:c['silhouette_plan'].update(foundation_occlusions=[]),'Foreground depth overlap obscures unapproved rear foundation')
    checknegative('omit-registered-state',lambda c:c['frames'].pop('dwellingLvl1'),'Town frame contract must cover every current building state exactly')
    checknegative('wrong-native-state-depth',lambda c:c['sites'][0].update(depth=c['sites'][0]['depth']+1),'Physical site depth must equal its actual native state z')
    def blockedapproach(contract):
        rec=contract['silhouette_plan']['states']['capitol'];im=d.line([[335,130],[335,145],[335,220],[450,220]],1);rec['approach_mask']=newmask(contract,'approach-through-seer-body',im)
    checknegative('actual-approach-through-other-building',blockedapproach,'Actual approach is obscured by another building')
    def displacedbuilding(contract):
        state='dwellingLvl2';old=d.Image.open(scratch/baseline['frames'][state]['path']).convert('RGBA')
        moved=d.Image.new('RGBA',d.SIZE);moved.alpha_composite(old,(0,20))
        path=contractpath.parent/'negative-checks'/'actual-hunter-building-displaced20px.png';moved.save(path)
        contract['frames'][state]=localref(path)
        recipe=d.read(scratch/'assets/recipes/town/structures/dwellingLvl2-animation.json')
        recipe['groups'][0]['frames'][0]={'source':localref(path)['path'],'source_sha256':d.digest(path)}
        # Actual shared converter changes the selected native PNG, not merely
        # annotation metadata. All physical contacts/door/access move together.
        fa.convert_animation(scratch,recipe,d.PREFIX,False,{})
        record=contract['silhouette_plan']['states'][state]
        for role in ('foundation_mask','door_mask','approach_mask','body_mask'):
            oldmask=maskfrom(record[role]);shift=d.blank();shift.paste(oldmask,(0,20));record[role]=newmask(contract,'displaced-hunter-'+role,shift)
        record['entrance']=[238,347]
        site=next(s for s in contract['sites'] if state in s['states'])
        union=d.union(d.Image.open(scratch/contract['frames'][st]['path']).getchannel('A') for st in site['states'])
        site['silhouette_mask']=newmask(contract,'actual-displaced-hunter-all-state-silhouette',union)
        box=union.getbbox();site['box']=[box[0],box[1],box[2]-box[0],box[3]-box[1]]
    checknegative('actual-converted-whole-building-displaced20px',displacedbuilding,'Actual foundation lacks level support')
    fa.convert_animation(scratch,d.read(scratch/'assets/recipes/town/structures/dwellingLvl2-animation.json'),d.PREFIX,False,{})
    report['geometry_negatives']=geometry_negatives
    finalerrors,_=layout.inspect(scratch,content,'freljord');report['restored_layout_ok']=not finalerrors;report['restored_layout_errors']=finalerrors
    report['candidate_inventory']={p.relative_to(candidate).as_posix():d.digest(p) for p in sorted(candidate.rglob('*')) if p.is_file()}
    d.write(out/'VERIFY-v1.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='candidate_inventory'},indent=2))
    return report
if __name__=='__main__':
    report=execute()
    sys.exit(0 if all(report[k] for k in ('conversion_ok','readonly_converter_ok','layout_ok','source_export_exact','source_export_helper_exact','restored_layout_ok','root_case_scenes_ok')) and report['grail_case_regression_negative']['passed'] and all(r['passed'] for r in report['converter_negatives']+report['geometry_negatives']) else 2)
