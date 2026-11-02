import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'runeterra-zaun/scripts')
import zaun_painted_town as t
P=Path('runeterra-zaun')
plan=json.loads((P/'assets/source/town/painted-v3/selection.json').read_text())
h=json.loads((P/'assets/source/town/chemtech-v5-background/handoff.json').read_text())
plan['background']={k:h[k] for k in ('master','master_sha256','provenance')}
plan['revision']='chemtech-v5-organic-candidate'
plan['not_done']=['All36 building states have own newly painted chemtech source candidates; native source review is independent from final acceptance.','Canonical recipes remain unchanged during --preview; native runtime clicks, lighting and final visual acceptance pending.']
sites={
'villageHall':[175,20,180,125],'townHall':[175,20,180,125],'cityHall':[175,20,180,125],'capitol':[175,20,180,125],
'fort':[0,40,190,118],'citadel':[0,40,190,118],'castle':[0,40,190,118],
'mageGuild1':[350,8,160,225],'mageGuild2':[350,8,160,225],'mageGuild3':[350,8,160,225],'mageGuild4':[350,8,160,225],
'resourceSilo':[130,185,120,110],'special1':[42,118,138,110],'special2':[220,135,125,102],'special3':[485,180,115,112],'special4':[685,76,110,110],
'dwellingLvl1':[0,244,140,130],'dwellingUpLvl1':[0,244,140,130],
'dwellingLvl2':[125,257,155,117],'dwellingUpLvl2':[125,257,155,117],
'dwellingLvl3':[400,265,150,109],'dwellingUpLvl3':[400,265,150,109],
'dwellingLvl4':[510,115,125,125],'dwellingUpLvl4':[510,115,125,125],
'dwellingLvl5':[600,160,132,112],'dwellingUpLvl5':[600,160,132,112],
'dwellingLvl6':[325,210,150,115],'dwellingUpLvl6':[325,210,150,115],
'dwellingLvl7':[550,25,140,125],'dwellingUpLvl7':[550,25,140,125],
'tavern':[266,267,145,107],'marketplace':[535,272,130,102],'blacksmith':[633,256,130,118],
'grail':[720,20,65,125],'shipyard':[700,192,98,80],'ship':[738,292,60,70]}
families={
'halls':{'villageHall':[150,100,710,415],'townHall':[880,0,1480,416],'cityHall':[12,530,766,965],'capitol':[769,412,1535,985]},
'rampart':{'fort':[0,280,700,645],'citadel':[713,150,1420,640],'castle':[1427,25,2172,645]},
'services':{'tavern':[25,0,759,447],'marketplace':[778,25,1530,470],'blacksmith':[18,446,768,996],'resourceSilo':[800,490,1525,992]},
'dw1':{'dwellingLvl1':[0,50,815,760]},
'dw2':{'dwellingLvl2':[0,120,981,730],'dwellingUpLvl2':[1010,0,2048,750]},
'dw3':{'dwellingLvl3':[4,85,947,675],'dwellingUpLvl3':[951,8,2171,686]},
'guild':{'mageGuild1':[180,85,670,418],'mageGuild2':[880,5,1444,420],'mageGuild3':[150,416,642,1000]}}
families['halls'].pop('townHall')
families['halls'].pop('capitol')
families.update({
'townhall':{'townHall':[156,52,1500,978]},
'capitol':{'capitol':[132,29,1440,1006]},
'guild4':{'mageGuild4':[5,30,1145,1363]},
'dw1up':{'dwellingUpLvl1':[160,57,1463,1000]},
'dw4':{'dwellingLvl4':[5,0,895,790],'dwellingUpLvl4':[930,0,1920,807]},
'dw5':{'dwellingLvl5':[0,165,785,849],'dwellingUpLvl5':[775,0,1774,887]},
'dw6':{'dwellingLvl6':[18,138,943,715],'dwellingUpLvl6':[940,36,1978,792]},
'dw7':{'dwellingLvl7':[10,194,772,802],'dwellingUpLvl7':[787,0,1772,881]},
'specials':{'special1':[15,0,774,486],'special2':[800,16,1527,506],'special3':[3,486,778,1024],'special4':[782,503,1536,1017]},
'grail':{'grail':[92,2,1277,1184]},
'port':{'shipyard':[15,0,1108,724],'ship':[1216,16,2151,716]}})
for e in plan['states']:
 b=e['building']; e['site_box']=sites[b]
 scale={'villageHall':(118,74),'townHall':(145,96),'cityHall':(165,110),'capitol':(180,125),'fort':(180,78),'citadel':(180,103),'castle':(185,118),'mageGuild1':(92,90),'mageGuild2':(112,125),'mageGuild3':(115,185),'mageGuild4':(160,225)}.get(b,tuple(sites[b][2:]))
 e['render_size']=list(scale)
 if b.startswith('dwellingLvl'):
  # Same ground site; poorer base buildings occupy less of it than upgrades.
  e['render_size']=[round(sites[b][2]*0.82),round(sites[b][3]*0.82)]
 for fam,mapping in families.items():
  if b in mapping:
   master=P/f'assets/source/town/chemtech-v4-buildings/{fam}-master.png'
   e.update(master=master.relative_to(P).as_posix(),master_sha256=t.digest(master),provenance=f'assets/source/town/chemtech-v4-buildings/{fam}-provenance.json',crop=mapping[b])
content=json.loads((P/'content/factions.json').read_text())['zaun']['town']['structures']
plan['partial_composition']=sorted(plan['partial_composition'],key=lambda b:content[b]['z'])
handoff_path=P/'assets/source/town/chemtech-v5-map-and-icons/handoff.json'
map_handoff=json.loads(handoff_path.read_text())
plan['adventure']=map_handoff['adventure']
plan['icons']=map_handoff['icons']
plan['revision']='chemtech-v5-organic-complete-source'
plan['status']='authored configuration'
plan['asset_state']='built-unreviewed'
plan['canonical_source_selection_completed']=True
plan['visual_approval_granted']=False
plan['source_handoffs']=[{'path':handoff_path.relative_to(P).as_posix(),'sha256':t.digest(handoff_path)},
 {'path':'assets/source/town/chemtech-v5-background/handoff.json','sha256':t.digest(P/'assets/source/town/chemtech-v5-background/handoff.json')}]
plan['not_done']=['Twenty native town sites and36 building states, five4-frame adventure appearances, eight icons and36 native-indexed construction frames have complete source geometry.','Final native game visual/click/construction/ownership and release acceptance remain pending. Rights remain unresolved.']
t.write_json(P/'assets/source/town/chemtech-v4-buildings/selection.json',plan)

