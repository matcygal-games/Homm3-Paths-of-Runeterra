"""Execute actual compiled-pixel native-consumer semantics and counterexamples."""
from pathlib import Path
import copy,io,json,sys
from PIL import Image,ImageOps,ImageChops
from assemble import HERE,PROJECT,WORKSPACE,REPORT,sha,png,record,box
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_creature_preview as preview

def decode(raw):return Image.open(io.BytesIO(raw)).convert('RGBA')
def mask(im):return im.getchannel('A').point(lambda v:255 if v>=128 else 0)
def signature(im):
    m=mask(im);b=m.getbbox();return (m.crop(b).size,m.crop(b).tobytes())
def compose(im,x,reverse=False):
    out=Image.new('RGBA',(1000,500));out.alpha_composite(ImageOps.mirror(im)if reverse else im,(x,0));return out

def semantics(groups,flyer):
    hold=groups[2][0]
    required={0,1,2,3,4,5,7,8,11,12,13,20,21,22}
    assert set(groups)==required,'Wrong actual action group coverage'
    assert len(groups[0])==8 and len({signature(im)for im in groups[0]})>=6,'No six genuine nonrigid locomotion silhouettes'
    assert len(groups[5])==8 and groups[22][0].tobytes()==groups[5][-1].tobytes(),'DEAD differs terminal DEATH'
    corpse=groups[22][0];cb=box(corpse);hb=box(hold)
    assert corpse.tobytes()!=hold.tobytes()and cb[3]-cb[1]<(hb[3]-hb[1])*.72,'Corpse is upright/alive'
    assert 264<=cb[3]<=268,'Terminal corpse floats above ground or penetrates ground'
    assert len({im.tobytes()for im in groups[5]})>=4,'No genuine collapse stages'
    assert groups[7][0].tobytes()==hold.tobytes()and groups[8][-1].tobytes()==hold.tobytes(),'Turn endpoints do not return to actual holding'
    assert len({signature(im)for im in groups[7]})>=3,'Turn has no actual facing-angle changes'
    before=groups[7][-1];after=groups[8][0]
    assert compose(before,300).tobytes()==compose(after,286,True).tobytes(),'Right-to-left native turn display join jumps'
    assert compose(before,286,True).tobytes()==compose(after,300).tobytes(),'Left-to-right native turn display join jumps'
    assert len(groups[8])==5 and groups[8][0].tobytes()==groups[8][1].tobytes(),'Held front changes before genuine quarter-return'
    for g in [11,12,13]:
        assert len(groups[g])==8,'Wrong melee cadence'
        assert groups[g][3].tobytes()!=hold.tobytes(),'Native climax4 is idle'
    assert len({groups[g][3].tobytes()for g in [11,12,13]})==3,'Directional contacts were flattened'
    assert any(im.tobytes()!=hold.tobytes()for im in groups[3]),'Pain is idle'
    assert any(im.tobytes()!=hold.tobytes()for im in groups[4]),'Defend is idle'
    if flyer:
        assert len(groups[20])==5 and len({signature(im)for im in groups[20]})>=4,'Takeoff lacks real crouch/push/flap'
        assert len(groups[21])==5 and len({signature(im)for im in groups[21]})>=4,'Landing lacks real braking/foot-contact/fold'
    for im in [*groups[1],*groups[2]]:
        for h in [120,130]:assert preview.measure_rgba(png(im),[170,155,270,155+h])['outside_pixels']==0,'Holding/fidget clips actual stock preview'
    for ims in groups.values():
        for im in ims:
            b=box(im);assert b and b[0]>0 and b[1]>0 and b[2]<450 and b[3]<400,'Battle actor is clipped/empty'
    return True

def unit_test(unit,version,outputs):
    prefix=f'Content/Sprites/runeterra/bilgewater/creatures/{unit}/';definition=json.loads(outputs[prefix+'battle.json'])
    groups={row['group']:[decode(outputs['Content/Sprites/'+definition['basepath']+name])for name in row['frames']]for row in definition['sequences']}
    semantics(groups,unit in ['cliffwing','stormwing'])
    left=decode(outputs[prefix+'attackLeft.png']);right=decode(outputs[prefix+'attackRight.png'])
    assert left.size==right.size==(64,64)
    assert left.getchannel('A').point(lambda a:255 if a>=8 else 0).histogram()[255]==right.getchannel('A').point(lambda a:255 if a>=8 else 0).histogram()[255],'Encounter reflection cropped native-visible physical pixels'
    for role,size in [('large.png',(64,64)),('small.png',(32,32))]:assert decode(outputs[prefix+role]).size==size
    mutations=[]
    def rejects(label,changed):
        try:semantics(changed,unit in ['cliffwing','stormwing'])
        except AssertionError as exc:mutations.append({'mutation':label,'rejected':True,'reason':str(exc)})
        else:raise AssertionError('Meaningless mutation accepted '+label)
    d=copy.deepcopy(groups);d[22]=[groups[2][0]];rejects('DEAD22 substituted with holding',d)
    d=copy.deepcopy(groups);d[0]=[]
    for i in range(8):
        im=Image.new('RGBA',(450,400));im.paste(groups[2][0],(i-3,0));d[0].append(im)
    rejects('Movement replaced by translated upright holding',d)
    d=copy.deepcopy(groups)
    for g in [11,12,13]:d[g][3]=groups[2][0]
    rejects('Actual native climax4 replaced with idle',d)
    d=copy.deepcopy(groups);d[8][0]=groups[7][-1];rejects('Uncorrected source-equal front before native flip',d)
    d=copy.deepcopy(groups);d[8][-1]=ImageOps.mirror(groups[2][0]);rejects('Return turn ends intrinsically backwards',d)
    d=copy.deepcopy(groups)
    for g in [5,22]:
        for i,im in enumerate(d[g]):
            moved=Image.new('RGBA',(450,400));moved.paste(im,(0,-20));d[g][i]=moved
    rejects('Death sequence and corpse float20px above ground',d)
    d=copy.deepcopy(groups);moved=Image.new('RGBA',(450,400));moved.paste(d[2][0],(-12,0));d[2][0]=moved;d[7][0]=moved;d[8][-1]=moved
    rejects('Holding shifted beyond actual100px native body crop',d)
    measured=[preview.measure_rgba(png(im),[170,155,270,155+h])for im in [*groups[1],*groups[2]]for h in [120,130]]
    return {'unit':unit,'version':version,'ok':True,'groups':{str(g):len(fs)for g,fs in groups.items()},'holding_and_fidget_crops':measured,'exact_native_turn_joins_both_starting_facings':True,'return_half_last_matches_opposite_holding':True,'mutations':mutations,'native_game_executed':False,'art_acceptance':False}

if __name__=='__main__':raise SystemExit('Run through finalize_packet.py actual candidate output bytes')
