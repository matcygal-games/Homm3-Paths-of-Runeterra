"""Portable ancestry resolution, no artistic operations or historical writes."""
from pathlib import Path
import json,hashlib,os
ACTUAL=Path(__file__).resolve().parent
P=Path(os.environ.get('IONIA_ANCESTRY_REVIEW_PROJECT',str(ACTUAL.parents[3]))).absolute()
META=P/"assets/source/creatures/playable-completion-20261028-v2-portable"
OVERLAY=Path(os.environ['IONIA_ANCESTRY_REVIEW_OVERLAY']).absolute()if'IONIA_ANCESTRY_REVIEW_OVERLAY'in os.environ else None
def input_path(path):
 path=Path(path);name=path.relative_to(P).as_posix()
 if OVERLAY is not None and (OVERLAY/name).is_file():return OVERLAY/name
 return path
def read_text(path):return input_path(path).read_text(encoding='utf-8-sig')
def read_json(path):return json.loads(read_text(path))
def digest(path):return hashlib.sha256(input_path(path).read_bytes()).hexdigest()
def output_path(path):
 path=Path(path)
 if not path.is_relative_to(META):raise ValueError('Portable producer cannot overwrite historical input')
 return (OVERLAY/path.relative_to(P))if OVERLAY is not None else path
def rewrite(value):
 spec=read_json(META/'relocation-pins.json');mapping=spec['relocations'];pins=spec['new_sha256'];oldpins=spec['before_sha256']
 def visit(v):
  if isinstance(v,str):return mapping.get(v,v)
  if isinstance(v,list):return[visit(x)for x in v]
  if not isinstance(v,dict):return v
  out={mapping.get(k,k):visit(x)for k,x in v.items()}
  for k,x in v.items():
   if k in mapping and isinstance(x,str)and x==oldpins.get(k):out[mapping[k]]=pins[mapping[k]]
   if isinstance(x,str)and x in mapping:
    for hk in(k+'_sha256','sha256'):
     if v.get(hk)==oldpins.get(x):out[hk]=pins[mapping[x]]
  return out
 return visit(value)
