"""One-time lossless PNG privacy preparation, preserving every raw provider byte.

Authoring helper only. Portable replay uses the public painted PNGs directly.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
S=Path(__file__).resolve().parent;P=S.parents[3]
R=P/'build/reports/playable-creatures-20261028-v1';private=R/'private-provider';private.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
raws=list(S.glob('*/*master*.png'))
for raw in raws:
 if raw.stem.endswith('-public'):continue
 image=Image.open(raw).convert('RGBA');clean=Image.frombytes('RGBA',image.size,image.tobytes())
 public=raw.with_name(raw.stem+'-public.png');clean.save(public,format='PNG',compress_level=9)
 assert Image.open(public).convert('RGBA').tobytes()==image.tobytes()
 dest=private/raw.parent.name/raw.name;dest.parent.mkdir(parents=True,exist_ok=True)
 assert raw.resolve().is_relative_to(S.resolve())and dest.resolve().is_relative_to(private.resolve())
 records.append({'public_source':public.relative_to(P).as_posix(),'public_sha256':sha(public),'raw_provider_sha256':sha(raw),
                 'decoded_rgba_sha256':hashlib.sha256(image.tobytes()).hexdigest(),'dimensions':list(image.size),'decoded_rgba_exact':True})
 assert not dest.exists(),'Refuse to overwrite preserved provider master'
 raw.rename(dest)
# Two genuine painted identity ancestors were actually used as generation input.
for unit,v in [('resistanceBlade','v1'),('resistanceVeteran','v2')]:
 raw=P/f'assets/source/creatures/painted-20261025-revision-v1/t6/{unit}/identity-master-{v}.png'
 image=Image.open(raw).convert('RGBA');public=S/'ancestry'/f'{unit}-identity-{v}-public.png';public.parent.mkdir(exist_ok=True)
 Image.frombytes('RGBA',image.size,image.tobytes()).save(public,format='PNG',compress_level=9)
 records.append({'public_source':public.relative_to(P).as_posix(),'public_sha256':sha(public),'raw_provider_sha256':sha(raw),
                 'decoded_rgba_sha256':hashlib.sha256(image.tobytes()).hexdigest(),'dimensions':list(image.size),'decoded_rgba_exact':True})
 # Preserve original inputs, read-only; no old identity source is moved/rewritten.
selected=[]
for item in records:
 n=item['public_source']
 rejected=('ionianDisciple/combat-master-v1-public' in n or 'enlightenedWarrior/adventure-master-v1-public'in n or 'enlightenedWarrior/adventure-master-v2-public'in n)
 if not rejected:selected.append(item)
(S/'public-source-lineage.json').write_text(json.dumps({'status':'authored configuration','method':'Lossless RGBA re-encoding only, no image filtering/body alteration; raw provider bytes remain private historical evidence','sources':selected,'private_native_function_controls':['7da01b8a2de5c42ad251851e1e0a8e34ce9e6370ad2804c2fcef231ac1c97023','1853569d4631760d27afe12d9d64f3b38192bac241388ca08be6c5f1fd839e4b'],'official_crest_reference_sha256':'c8df47b7021ed103cf646b72fdb2275211a97846cd921923893f0a756659c535'},sort_keys=True,indent=2)+'\n')
(private/'raw-public-pins.json').write_text(json.dumps(records,sort_keys=True,indent=2)+'\n')
print(json.dumps({'preserved_raw_provider_masters':len(raws),'public_rgba_exact_sources':len(records),'declared_public_sources':len(selected)}))
