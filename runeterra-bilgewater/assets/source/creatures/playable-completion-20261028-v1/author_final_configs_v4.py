"""Final proposed camera/gait/turn contracts, preserving all prior candidates."""
from pathlib import Path
import json,hashlib,copy
S=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data={'bilgeRat':(3,'t1',1,.105,[570,824]),'seaDog':(3,'t1',0,.105,[1195,824]),'corsair':(3,'t2',0,.097,[630,858]),'pirateMarksman':(3,'t2',1,.098,[1170,858]),'shellshotGunner':(2,'t3',0,.095,[545,774]),'reefBombardier':(2,'t3',1,.102,[1395,774]),'krakenPriest':(2,'t4',0,.101,[465,946]),'tideHierophant':(2,'t4',1,.103,[1070,946]),'boardingCaptain':(2,'t6',0,.104,[558,856]),'fleetVeteran':(2,'t6',1,.107,[1200,856])}
for unit,(old,family,index,scale,root)in data.items():
 c=json.loads((S/unit/f'assembly-config-v{old}.json').read_text());c['version']=4
 p=S/f'turn-fronts-v1/{family}-raw.png';c['plates']['turn-front-centred-v1']={'source':p.relative_to(S).as_posix(),'source_sha256':sha(p),'expected_islands':2,'scale':scale,'poses':{'turnFront':{'island':index,'root':root}}}
 c['technical_pose_transforms']={'turnFrontNativeR':{'source_pose':'turnFront','operation':'native_turn_full_canvas_mirror_translate','translation':[-58,0],'reason':'Native facing flip reflects full450px then stack x changes-58 for onehex; exact displayed endpoint compensation, no invented painted intermediate'}}
 c['groups']['7'][-2:]=['turnFront','turnFront'];c['groups']['8'][:2]=['turnFrontNativeR','turnFrontNativeR'];c['groups']['7'][0]='ready';c['groups']['8'][-1]='ready'
 if unit in ['bilgeRat','krakenPriest','tideHierophant','boardingCaptain','fleetVeteran']:
  c['groups']['0']=['near0','near0','near1','far2','far0','far0','far1','near2'];c['groups']['20']=['ready','near0'];c['groups']['21']=['near2','ready']
 c['turn_contract']={'status':'authored configuration','native_full_canvas_width':450,'one_hex_stack_position_delta':-58,'turn7_end':'New genuinely painted frontal centred-weapon pose','turn8_start':'Exact fullcanvas reflected turn7 endpoint translated-58','holding_join':'turn7first and turn8last reuse exact selected ready pose','native_execution':False,'limitation':'Native displayed endpoint algebra is independently checked; intermediate painted quarter continuity/handedness, tiny onehex pivot quantization and final visual acceptance still require in-game review.'}
 c.setdefault('excluded_source_keys',[]).append({'pose':'turn3','reason':'Older asymmetric frontal study retained in source history; new centred-weapon frontal pose selected at facing boundary.'})
 c['unresolved']=[x for x in c['unresolved']if 'turn'not in x.lower()]+['Actual native turn quarter continuity/handedness and full visual acceptance remain pending despite exact displayed endpoint match']
 dest=S/unit/'assembly-config-v4.json';b=(json.dumps(c,sort_keys=True,indent=2)+'\n').encode()
 if dest.exists()and dest.read_bytes()!=b:raise RuntimeError('Preserve earlier final config '+unit)
 if not dest.exists():dest.write_bytes(b)
