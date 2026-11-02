"""Check actual native replacement families and authored construction dependencies."""
from pathlib import Path
import json,hashlib,sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ionia')
WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_pipeline as fp
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 path=WORKSPACE/'vcmi-develop/vcmi-develop/config/buildingsLibrary.json';native=fp.utility('common').parse_jsonc(path.read_text());factions=read(PROJECT/'content/factions.json');town=factions['ionia']['town'];mapping=read(HERE/'native-state-map.json');keys=set(town['buildings']);effective={s:{**native[s],**town['buildings'][s]}for s in keys};errors=[];families={};links=[]
 def base(s):
  seen=set()
  while effective[s].get('upgrades'):
   if s in seen:raise ValueError('Native replacement cycle at '+s)
   seen.add(s);older=effective[s]['upgrades']
   if older not in keys:raise ValueError('Native replacement leaves actual town: '+s+'/'+older)
   links.append({'state':s,'upgrades':older,'native_ID':native[s]['id']});s=older
  return s
 for site,row in mapping['sites'].items():
  roots={base(s)for s in row['states']};families[site]={'states':row['states'],'native_base_states':sorted(roots)}
  if len(roots)!=1:errors.append('Unrelated actual native states share site '+site)
 if {s for r in mapping['sites'].values()for s in r['states']}!=keys:errors.append('Actual building keys not exactly covered')
 if len({native[s]['id']for s in keys})!=len(keys):errors.append('Native building IDs are not unique')
 def requirements(value,built):
  if not value:return True
  if isinstance(value,str):
   if value not in keys:raise ValueError('Unknown actual building prerequisite '+value)
   return value in built
  if not isinstance(value,list):raise ValueError('Unsupported authored requirement expression')
  if value[0]=='allOf':return all(requirements(x,built)for x in value[1:])
  if value[0]=='anyOf':return any(requirements(x,built)for x in value[1:])
  if value[0]=='noneOf':return not any(requirements(x,built)for x in value[1:])
  return all(requirements(x,built)for x in value)
 built=set();order=[]
 while True:
  available=[s for s in sorted(keys-built)if requirements(effective[s].get('requires',[]),built)and(not effective[s].get('upgrades')or effective[s]['upgrades']in built)]
  if not available:break
  built.update(available);order.append(available)
 if built!=keys:errors.append('Unresolved construction prerequisites: '+','.join(sorted(keys-built)))
 result={'status':'authored configuration','native_ID_library_sha256':sha(path),'factions_sha256':sha(PROJECT/'content/factions.json'),'ordinary_land_sites':16,'coastal_sites':1,'Grail_sites':1,'actual_state_count':len(keys),'families':families,'actual_native_replacement_links':links,'prerequisite_waves':order,'all_authored_prerequisites_resolvable':built==keys,'special_native_state_limits':{'grail':'Native Grail/artifact construction mode; source prerequisite resolution is not a claim that this can be bought normally.','ship':'Inherited native ship.upgrades=shipyard; native boat/dock state, click target remains shipyard. Source resolution is not a claim that ship and empty shipyard coexist.'},'errors':errors,'native_execution':False,'release_accepted':False}
 report=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v2/construction-receipt.json';report.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'actual_states':len(keys),'sites':len(families),'errors':errors}));return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
