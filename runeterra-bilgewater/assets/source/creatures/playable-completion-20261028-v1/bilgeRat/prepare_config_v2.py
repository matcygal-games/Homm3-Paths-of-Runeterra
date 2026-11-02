"""Prepare a versioned proposal retaining actual painted source pose ancestry."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent;PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(SOURCE));from split_painted_islands import islands
old=json.loads((HERE/'cohort-candidate-v1.json').read_text());cfg={'unit':'bilgeRat','version':2,'battle_canvas':[450,400],'battle_root':[197,266],'plates':{},'groups':{},'companions':{'pose':'idle','scale':.135,'map_root':[76,60],'encounter_root':[44,60],'portrait_crop':[90,96,262,270]},'unresolved':['Source contact/leg-overlap and ordered gait require independent native-size motion review','Both native facings, turn and movement transitions have not been observed','Exact regional crest legibility needs independent native-size review','Canonical source-policy and archive admission have not run']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
labels={1:['ready','idle'],2:['ready'],3:['hurt0','hurt1','ready'],4:['defend','ready'],5:['death0','death1','death2','death3'],7:['unusedTurn0','turn1','turn2','turn3'],8:['turn3','turn2','turn1','unusedTurn0'],11:['up0','up1','up2','ready'],12:['front0','front1','front2','ready'],13:['down0','down1','down2','ready'],22:['death3']}
for group,names in labels.items():
    entries=[r for r in old['frames']if r['group']==group]
    for label,row in zip(names,entries):
        path=PROJECT/row['master'];plate_name=path.name;relative=path.relative_to(SOURCE).as_posix()
        if plate_name not in cfg['plates']:cfg['plates'][plate_name]={'source':relative,'source_sha256':sha(path),'expected_islands':len(islands(Image.open(path).convert('RGBA'))),'scale':row['plate_pixel_scale'],'poses':{}}
        actual=islands(Image.open(path).convert('RGBA'));index=next(i for i,item in enumerate(actual)if item['box']==row['source_island_box'])
        cfg['plates'][plate_name]['poses'][label]={'island':index,'root':row['source_anatomical_root']}
for name,scale,annotations in [('near-half-v2-raw.png',.112,[('near0',2,335),('near1',0,965),('near2',1,1575)]),('far-half-v2-raw.png',.108,[('far0',0,315),('far1',1,820),('far2',2,1330)])]:
    path=HERE/name;floor=770 if name.startswith('near') else 900
    cfg['plates'][name]={'source':path.relative_to(SOURCE).as_posix(),'source_sha256':sha(path),'expected_islands':3,'scale':scale,'poses':{label:{'island':i,'root':[x,floor]}for label,i,x in annotations}}
cfg['groups']={str(k):v for k,v in labels.items()};cfg['groups']['0']=['near0','near1','near2','far0','far1','far2'];cfg['groups']['7']=['ready','turn1','turn2','turn3'];cfg['groups']['8']=['turn3','turn2','turn1','ready'];cfg['groups']['20']=['ready','near0'];cfg['groups']['21']=['far2','ready']
cfg['excluded_source_keys']=[{'pose':'unusedTurn0','reason':'Native half-turn begins/ends at exact HOLDING; preserve unused earlier turn study'},{'master':'walk-v3-raw.png','reason':'Earlier broad cohort has unresolved opposite support; replaced by independently painted contact/support half cohorts'}]
cfg['generation_reference_inputs']=[{'path':(HERE/f).relative_to(PROJECT).as_posix(),'sha256':sha(HERE/f),'use':'Original painted2D identity/contact source used by built-in generation, not runtime source frame'}for f in ['contact-A-v2-raw.png','contact-B-v2-raw.png','walk-near-contact-v1-raw.png','atlas-v1-raw.png']]
cfg['private_original_controls']={'contactA_native_sha256':'1853569d4631760d27afe12d9d64f3b38192bac241388ca08be6c5f1fd839e4b','contactB_native_sha256':'42e187f2588ef5327fe8afdc503f901239cb1fc3ed6cdc4ecb8fe88c6404255a','use':'Lower-body generic weight/occlusion only; private originals never copied into final sprite or bundle'}
path=HERE/'assembly-config-v2.json';data=(json.dumps(cfg,sort_keys=True,indent=2)+'\n').encode()
if path.exists()and path.read_bytes()!=data:raise RuntimeError('Preserve previous source proposal; create new version')
if not path.exists():path.write_bytes(data)
