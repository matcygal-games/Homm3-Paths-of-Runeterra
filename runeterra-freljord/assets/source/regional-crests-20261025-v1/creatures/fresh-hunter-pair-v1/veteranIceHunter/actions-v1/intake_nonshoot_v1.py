"""Private provider receipt intake into portable painted action source records."""
from pathlib import Path
import json,hashlib,re,shutil,sys
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
MOD=ROOT/'runeterra-freljord'
REPORT=ROOT/'build/reports/regional-crests-20261025-v1/freljord-unit-art/fresh-hunter-pair-v1/upgrade-actions-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(p):return {'path':p.relative_to(MOD).as_posix(),'sha256':sha(p)}
def main():
    receipt=Path(sys.argv[1]).resolve();assert receipt.is_relative_to(REPORT)
    record=json.loads(receipt.read_text());stem=record['stem'];assert re.fullmatch(r'nonshoot-[a-z-]+',stem)
    target=HERE/f'{stem}-raw-v1.png';assert not target.exists()
    generated=Path(re.search(r' as (.*?) by default',record['response_metadata']['output_hint']).group(1));shutil.copyfile(generated,target)
    prompt=HERE/f'{stem}-prompt-v1.txt';assert prompt.read_text()==record['request']['prompt']+'\n'
    refs=[]
    for i,p in enumerate(record['request']['referenced_image_paths']):
        path=Path(p).resolve();included=path.is_relative_to(MOD/'assets/source/regional-crests-20261025-v1/creatures/fresh-hunter-pair-v1')
        ref={'role':record['input_roles'][i],'included_in_source_package':included,'sha256':sha(path)}
        if included:ref['path']=path.relative_to(MOD).as_posix()
        refs.append(ref)
    public={'status':'design proposal','selected':False,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','method':'Genuine new painted2D action from clean own identity, actual originalHoMM3 motion/style and official regionalcrest only. No old guided/primitive/3D body pixels.','raw':local(target),'prompt':local(prompt),'input_references':refs,'actual_input_count':len(refs),'identity_ancestry':local(HERE.parent/'identity-generation-v1.json'),'private_provider_receipt_outside_source':True,'native_execution':False,'release_accepted':False}
    meta=HERE/f'{stem}-generation-v1.json';meta.write_text(json.dumps(public,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps({'raw':local(target),'generation':local(meta)},indent=2))
if __name__=='__main__':main()
