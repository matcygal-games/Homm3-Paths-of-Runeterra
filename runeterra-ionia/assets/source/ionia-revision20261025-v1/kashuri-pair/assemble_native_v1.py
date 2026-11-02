"""Replay whole genuine painted 2D poses into native canvases.

Only ownership, crop, uniform cohort scaling, physical root registration,
native adventure affine projection and alpha composition occur here.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageOps
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent
sys.path.insert(0,str(S));sys.path.insert(0,str(P/'scripts'))
from pose_tools import sha,png,put,enc,rel
from ionia_adventure_projection import project,measure,bounds

def checked(name,digest):
    p=P/name
    if not p.is_file() or sha(p)!=digest: raise ValueError('Missing or stale current painted source: '+name)
    return p

def whole(record):
    p=checked(record['master'],record['master_sha256']);m=checked(record['mask'],record['mask_sha256']);expected=checked(record['whole'],record['whole_sha256'])
    a=np.array(Image.open(p).convert('RGBA').crop(tuple(record['source_window'])))
    mask=np.array(Image.open(m).convert('L'))>0
    if a.shape[:2]!=mask.shape:raise ValueError('Ownership dimensions differ')
    a[~mask]=0;im=Image.fromarray(a)
    if im.tobytes()!=Image.open(expected).convert('RGBA').tobytes():raise ValueError('Original painted pixels/alpha no longer match owned whole pose')
    return im

def native(record):
    if 'existing_native' in record:
        checked(record['gait_contract'],record['gait_contract_sha256'])
        return Image.open(checked(record['existing_native'],record['existing_native_sha256'])).convert('RGBA')
    im=whole(record);scale=record['scale'];im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    x,y=record['physical_root_local'];offset=(round(197-x*scale),round(266-y*scale))
    out=Image.new('RGBA',(450,400));out.alpha_composite(im,offset)
    return out

def portrait(record,background,size):
    im=whole(record);scale=max(size[0]/im.width,size[1]/im.height)
    im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    im=im.crop(((im.width-size[0])//2,0,(im.width-size[0])//2+size[0],size[1]))
    source=Image.open(checked(background['source'],background['source_sha256'])).convert('RGBA')
    checked(background['lineage'],background['lineage_sha256'])
    backdrop=ImageOps.fit(source.crop(tuple(background['crop'])),size,Image.Resampling.LANCZOS)
    backdrop.alpha_composite(im);return backdrop

def main():
    contract=S/'native-assembly-contract-v1.json';data=json.loads(contract.read_text());report={'status':'authored configuration','units':{},'contract':rel(contract),'contract_sha256':sha(contract),'producer':rel(Path(__file__).resolve()),'producer_sha256':sha(Path(__file__).resolve()),'runtime_verified':False,'release_accepted':False}
    for unit,info in data['units'].items():
        out=S/unit/'native-v1';frames=[];pictures={}
        for row in info['frames']:
            im=native(row);g,f=row['group'],row['frame'];p=out/f'g{g:02d}-f{f:03d}.png';png(p,im);pictures[g,f]=im
            frames.append({'group':g,'frame':f,'source':rel(p),'source_sha256':sha(p),'source_canvas':[450,400],'alpha8_bounds':bounds(im),'whole_pose_record':row})
        assert pictures[22,0].tobytes()==pictures[5,5].tobytes(),'Final corpse continuity'
        assert pictures[22,0].tobytes()!=pictures[2,0].tobytes(),'Corpse must not stand'
        guards=[native(r) for r in info['guards']]
        gp=[]
        for name,im in zip(['attackLeft-full','attackRight-full'],guards):
            p=out/(name+'.png');png(p,im);gp.append(p)
        # One uniform scale per unit, shared across maps and both encounter views.
        inputs=[(pictures[0,f],False) for f in range(6)]+[(guards[0],True),(guards[1],False)]
        scale=next(s for s in [.5,.45,.4,.375,.35,.325,.3] if all(measure(im,[197,266],s,mirror)['opaque_pixels_outside_canvas']==0 for im,mirror in inputs))
        maps=[];attacks=[]
        for f in range(6):
            src=out/f'g00-f{f:03d}.png';im=project(pictures[0,f],[197,266],scale);p=out/f'map-f{f:03d}.png';png(p,im)
            pc={'source':rel(src),'source_sha256':sha(src),'pivot':[197,266],'scale':scale,'mirrored':False,'anchor':[80,60],'canvas':[96,64]}
            maps.append({'source':rel(p),'source_sha256':sha(p),'source_canvas':[96,64],'projection_contract':pc,'projection_measure':measure(pictures[0,f],[197,266],scale)})
        for role,src,im,mirror in zip(['attackLeft','attackRight'],gp,guards,[True,False]):
            p=out/(role+'.png');png(p,project(im,[197,266],scale,mirror))
            pc={'source':rel(src),'source_sha256':sha(src),'source_facing':'right','pivot':[197,266],'scale':scale,'mirrored':mirror,'anchor':[80,60],'canvas':[96,64]}
            attacks.append({'role':role,'source':rel(p),'source_sha256':sha(p),'projection_contract':pc,'projection_measure':measure(im,[197,266],scale,mirror)})
        portraits=[]
        for role,rec,size in zip(['large','small'],info['portraits'],[(58,64),(32,32)]):
            p=out/(role+'.png');png(p,portrait(rec,info['portrait_background'],size));portraits.append({'role':role,'source':rel(p),'source_sha256':sha(p),'source_canvas':list(size),'fresh_close_portrait':True,'portrait_record':rec,'background':info['portrait_background']})
        report['units'][unit]={'frames':frames,'map_frames':maps,'attacks':attacks,'portraits':portraits,'adventure_uniform_scale':scale,'dead22_matches_final_death5':True,'no_old_live_templates':True}
    projectile=S/'projectile-v1.png';im=Image.open(projectile).convert('RGBA');box=bounds(im,16);crop=im.crop(box);scale=10/crop.width;crop=crop.resize((10,max(1,round(crop.height*scale))),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(40,40));canvas.alpha_composite(crop,(20-crop.width//2,20-crop.height//2));proj=[]
    for i,angle in enumerate([90,45,0,-45,-90]):
        p=S/'projectile-native-v1'/f'g00-f{i:03d}.png';png(p,canvas.rotate(angle,Image.Resampling.BICUBIC,center=(20,20)));proj.append({'source':rel(p),'source_sha256':sha(p),'source_canvas':[40,40],'angle':angle})
    report['projectile']={'master':rel(projectile),'master_sha256':sha(projectile),'crop':list(box),'uniform_scale':scale,'native_canvas':[40,40],'pivot':[20,20],'frames':proj,'method':'One genuine painted physical pellet; fixed whole-projectile rotations, no fabricated creature artwork'}
    put(S/'native-production-v1.json',enc(report));print(json.dumps({'units':{u:{'battle':len(v['frames']),'map':len(v['map_frames']),'scale':v['adventure_uniform_scale']}for u,v in report['units'].items()},'projectiles':len(proj)}))

if __name__=='__main__':main()
