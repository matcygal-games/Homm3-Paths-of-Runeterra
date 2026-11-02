"""Create a compact public source manifest; keep raw execution artifacts separate."""
import json
from pathlib import Path
import re
import prepare_patch as p

receipt_path=p.HERE/'raw-receipts/v3/result.json'
receipt=json.loads(receipt_path.read_bytes())
assert receipt['passed'] and receipt['variants']['patched']['cases']==26
summary={'status':'authored configuration','native_execution':False,
 'scope':receipt['scope'],'raw_receipt':'raw-receipts/v3/result.json','raw_receipt_sha256':p.sha(receipt_path.read_bytes()),
 'compiler_sha256':receipt['compiler_sha256'],'apply_check_exit_code':receipt['apply_check_exit_code'],
 'variants':{name:{k:v for k,v in item.items() if k in ('compile_exit_code','source_sha256','run_exit_code','binary_sha256','cases','failures')}
             for name,item in receipt['variants'].items()},
 'limits':['Copied actual consumers with dependency fixtures','No full engine, native AI, socket, serializer, save/load, GUI or network acceptance']}
p.write_new(p.HERE/'consumer-verification.json',p.jb(summary))
paths=[p.HERE/name for name in ('README.md','LICENSE.md','prepare_patch.py','handleSaveCommand.cpp',
 'run_regression.py','seal_selection.py','tests/fixture.hpp','tests/cases.cpp',
 '0003-make-console-save-use-owned-headless-player.patch','official-source-tree.json',
 'source-provenance-v4.json','consumer-verification.json','patched-v3/client/ClientCommandManager.cpp')]
paths+=sorted(path for path in (p.HERE/'upstream').rglob('*') if path.is_file())
files={}
for path in paths:
    raw=path.read_bytes(); name=path.relative_to(p.HERE).as_posix()
    assert path.suffix.lower() not in ('.exe','.dll','.obj','.pdb','.lib','.zip'),name
    assert not re.search(rb'[A-Za-z]:[\\/]+Users[\\/]',raw,re.I),name
    assert 'raw-receipts' not in path.relative_to(p.HERE).parts,name
    files[name]={'sha256':p.sha(raw),'bytes':len(raw)}
manifest={'status':'authored configuration','source_only':True,'native_execution':False,
 'license':'GPL-2.0-or-later','official_commit':p.COMMIT,
 'selected_patch':'0003-make-console-save-use-owned-headless-player.patch',
 'files':files,'file_count':len(files),'total_bytes':sum(v['bytes'] for v in files.values()),
 'excluded':['raw-receipts/**','__pycache__/**','0001-*.patch','0002-*.patch','patched/**','patched-v2/**',
             'source-provenance.json','source-provenance-v2.json','source-provenance-v3.json'],
 'limits':['No production/stage/runtime selection','Coordinator and independent review required before integration',
           'Raw executed evidence retained separately by the exact receipt hash']}
p.write_new(p.HERE/'selected-manifest.json',p.jb(manifest))
print(json.dumps({'files':len(files),'bytes':manifest['total_bytes'],'manifest_sha256':p.sha((p.HERE/'selected-manifest.json').read_bytes())}))
