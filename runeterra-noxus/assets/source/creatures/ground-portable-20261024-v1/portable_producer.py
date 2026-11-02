"""Producer-side portable source authoring and exact Noxus recipe replay.

Authoring preserves original tool records privately. Verification/replay uses
only the produced public inputs and actual local Noxus compiler, never the
original Codex image cache or the earlier private authoring records.
"""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,importlib.util,io,json,re
from PIL import Image

SELF=Path(__file__).resolve()
P=next(p for p in SELF.parents if (p/'content/factions.json').is_file()and(p/'scripts/art_compile.py').is_file())
PUBLIC=SELF.parent
R=P/'build/reports/ground-heraldry-20261024-v1/portable-v9'
CAND=P/'assets/candidates/painted-ground-heraldry-20261024-v1/recipes-v9-portable'
OLD=P/'assets/candidates/painted-ground-20261024-v1/recipes-v8'
ABSOLUTE=re.compile(r'(?:[A-Za-z]:[\\/]|/(?:Users|home)/)')
def enc(value):return(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def sha(data):return hashlib.sha256(data).hexdigest()
def rel(path):return path.relative_to(P).as_posix()
def put(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists()and path.read_bytes()!=data:raise ValueError('Preserve changed artifact/version it: '+str(path))
    path.write_bytes(data)
def compiler():
    spec=importlib.util.spec_from_file_location('portable_noxus_art_compile',P/'scripts/art_compile.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def author():
    mapped={};native_records=[];png_records=[];private_records=[]
    def portable(path):
        path=path.resolve();name=rel(path)
        if name in mapped:return mapped[name]
        if not name.startswith('assets/source/'):raise ValueError('Authoring dependency outside own source: '+name)
        if path.suffix=='.py'and path.name.startswith('prepare-v'):
            mapped[name]=SELF
            private_records.append({'kind':'superseded-authoring-producer','raw_sha256':sha(path.read_bytes()),'replacement':'portable_producer.py; actual Noxus compiler replay uses already-authored frames'})
            return SELF
        destination=PUBLIC/'inputs'/path.relative_to(P/'assets/source')
        mapped[name]=destination
        data=path.read_bytes()
        if path.suffix.lower()=='.png':
            with Image.open(io.BytesIO(data))as opened:
                opened.load();rgba=opened.convert('RGBA');pixels=rgba.tobytes();information=sorted(opened.info)
            if information:
                stream=io.BytesIO();rgba.save(stream,format='PNG',compress_level=9,optimize=False);public_data=stream.getvalue()
            else:public_data=data
            with Image.open(io.BytesIO(public_data))as public_image:
                assert public_image.convert('RGBA').tobytes()==pixels
                assert not public_image.info
            put(destination,public_data)
            png_records.append({'public_path':rel(destination),'source_file_sha256':sha(data),'public_file_sha256':sha(public_data),'rgba_sha256':sha(pixels),'dimensions':list(rgba.size),'removed_metadata_keys':information,'decoded_pixels_unchanged':True})
        elif path.suffix.lower()=='.json':
            value=json.loads(data)
            if path.name.endswith('.generation.json'):
                private=R/'private-receipts'/(sha(data)[:16]+'-'+path.name);put(private,data)
                public={key:deepcopy(value[key])for key in ('provider','prompt','reference','role','status','release_accepted','additional_reference')if key in value}
                public.update(schema_version=1,image_generation_used=True,model='not exposed by built-in tool',raw_receipt_sha256=sha(data),raw_receipt_preserved_privately=True,portability='New producer-side record; original private local-output locator is deliberately not a public dependency.')
                private_records.append({'kind':'generation-receipt','raw_sha256':sha(data),'public_path':rel(destination),'private_path':rel(private)})
                value=public
            put(destination,enc(rewrite(value)))
        else:raise ValueError('Unexpected selected source type: '+name)
        return destination
    def rewrite(value):
        if isinstance(value,list):return[rewrite(v)for v in value]
        if isinstance(value,str)and value.startswith('assets/source/'):
            return rel(portable(P/value))
        if not isinstance(value,dict):return value
        result={}
        for key,v in value.items():
            if key=='original_generated_path':
                raise ValueError('Private locator outside the explicit generation-record producer: '+str(v))
            result[key]=rewrite(v)
        for key,pins in {'source':('source_sha256','sha256'),'raw_source_master':('raw_source_master_sha256',),'painted_master':('painted_master_sha256',),'generation_record':('generation_record_sha256',),'path':('sha256',)}.items():
            if isinstance(result.get(key),str)and result[key].startswith(rel(PUBLIC)+'/'):
                target=P/result[key]
                if not target.is_file():raise ValueError('Portable dependency not finalized: '+str(target))
                for pin in pins:
                    if pin in result or pin==pins[0]:result[pin]=sha(target.read_bytes())
        return result
    recipe_pins={}
    for path in sorted(OLD.glob('*.json')):
        recipe=json.loads(path.read_bytes())
        raw=recipe['generation']
        if 'original_generated_path'in raw:
            data=enc(raw);private=R/'private-receipts'/('embedded-'+sha(data)[:16]+'.json');put(private,data)
            generation={key:deepcopy(v)for key,v in raw.items()if key!='original_generated_path'}
            generation.update(raw_embedded_receipt_sha256=sha(data),raw_receipt_preserved_privately=True)
            recipe['generation']=generation
            private_records.append({'kind':'embedded-generation-record','raw_sha256':sha(data),'private_path':rel(private)})
        recipe=rewrite(recipe)
        target=CAND/path.name;put(target,enc(recipe));recipe_pins[rel(target)]=sha(target.read_bytes())
    if len(recipe_pins)!=25:raise ValueError('Expected complete 25-resource cohort')
    expected=json.loads((P/'build/reports/painted-ground-replacements-20261024-v1/handoff-v8.json').read_bytes())['output_inventory']
    public_files={rel(path):sha(path.read_bytes())for path in sorted(PUBLIC.rglob('*'))if path.is_file()and path.name not in('selection-v9.json',)}
    manifest={'schema_version':1,'status':'authored configuration','scope':'Metadata-only portable producer inputs; no crest pixels changed by this pass','recipes':recipe_pins,'public_inputs':public_files,'expected_output_inventory':expected,'raw_receipts_are_private_dependencies':False,'png_pixel_checks':png_records,'compiler_sha256':sha((P/'scripts/art_compile.py').read_bytes())}
    put(PUBLIC/'selection-v9.json',enc(manifest));put(R/'private-preservation.json',enc(private_records))
    return verify()
def verify():
    selection=json.loads((PUBLIC/'selection-v9.json').read_bytes());own=compiler();inventories=[]
    for name,pin in selection['public_inputs'].items():
        path=P/name
        if not path.is_file()or sha(path.read_bytes())!=pin:raise ValueError('Portable selected source missing/changed: '+name)
        if path.suffix.lower()=='.json'and ABSOLUTE.search(path.read_text(encoding='utf-8')):raise ValueError('Private absolute path in public JSON: '+name)
    for pass_name in ('own-assembly-a','own-assembly-b'):
        actual={}
        for name,pin in selection['recipes'].items():
            candidate=P/name
            if not candidate.is_file():
                # Exported active recipes can use another filename. Resolve by
                # output identity inside this same project only, never host paths.
                original_name=Path(name).name
                found=list((P/'assets/recipes').rglob(original_name))
                if len(found)!=1:raise ValueError('Portable recipe absent in extracted project: '+original_name)
                candidate=found[0]
            if sha(candidate.read_bytes())!=pin:raise ValueError('Portable recipe checksum changed: '+str(candidate))
            if ABSOLUTE.search(candidate.read_text()):raise ValueError('Private path in portable recipe')
            outputs,receipt=own.plan(P,candidate)
            for output,data in outputs.items():
                actual[output]=sha(data);put(R/pass_name/output,data)
        if actual!=selection['expected_output_inventory']:raise ValueError('Metadata-only replay changed actual native bytes')
        inventories.append(actual)
    assert inventories[0]==inventories[1]
    result={'status':'authored configuration','result':'pass','logical_recipes':25,'physical_outputs':len(inventories[0]),'exact_v8_native_bytes_preserved':True,'two_actual_Noxus_compiler_passes_identical':True,'public_inputs':len(selection['public_inputs']),'png_decoded_pixel_checks':len(selection['png_pixel_checks']),'generation_private_records':'private-preservation.json','runtime_or_release_acceptance':False}
    put(R/'result.json',enc(result));print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--author-from-v8',action='store_true');args=parser.parse_args()
    author()if args.author_from_v8 else verify()
