"""Reproduce the reviewed DMC1 native state pixels from preserved painted sources.

Run with --output pointing to a fresh directory. This performs only technical
masking, alpha normalization, crop, uniform fit and composition. It does not
select content, regenerate creative artwork, stage a mod or grant acceptance.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json

ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
def derive(output):
    if output.exists():raise ValueError('Fresh output directory required')
    pins=json.loads((ROOT/'replay-inputs.json').read_text())
    for row in pins['files']:
        raw=ROOT/row['relative_to_component'];resolved=raw.resolve()
        if not resolved.is_relative_to(ROOT.resolve()) or raw.is_symlink() or not raw.is_file() or sha(raw)!=row['sha256']:raise ValueError('Preserved replay input missing or changed')
    output.mkdir(parents=True)
    geometry=module('_dmc1_geometry',ROOT/'replay_geometry.py');geometry.assemble(output/'geometry')
    earlier=module('_dmc1_earlier',ROOT/'earlier/derive_native.py');earlier.run(output/'earlier')
    watch=module('_dmc1_watch',ROOT/'watchtower/derive_native.py');(output/'watchtower').mkdir();watch.run(output/'watchtower/native-v1')
    states=module('_dmc1_states',ROOT/'replay_states.py');states.GEOMETRY=output/'geometry';states.EARLIER=output/'earlier';states.WATCHTOWER=output/'watchtower';states.assemble(output/'states')
    selected=json.loads((ROOT/'source-ledger.json').read_text());checked=[]
    for key,row in selected['states'].items():
        for filename,pin in [('frame.png',row['frame']),('architecture-mask.png',row['architecture_mask']),('area.png',row['area']),('border.png',row['border']),('prepared-master.png',row['master'])]:
            actual=output/'states/states'/key/filename
            if sha(actual)!=pin['sha256']:raise ValueError('Native state replay differs: '+key+'/'+filename)
            checked.append({'state':key,'file':filename,'sha256':sha(actual)})
    if sha(output/'states/background.png')!=selected['background']['sha256']:raise ValueError('Background replay differs')
    receipt={'status':'authored configuration','selected_for_runtime':False,'native_execution_performed':False,'states':35,'checked_state_files':checked,'background_sha256':sha(output/'states/background.png'),'replay_input_inventory_sha256':sha(ROOT/'replay-inputs.json')}
    (output/'replay-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=derive(a.output.resolve());print('DMC1 replay verified',len(r['checked_state_files']),'state files and background')
