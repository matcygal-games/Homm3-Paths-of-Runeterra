"""Technical fixed-cohort assembly of six genuine painted animal variants."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from assemble_humanoids import (HERE,PROJECT,ROOT,REPORT,ORIGINAL,CANVAS,atlas_cells,
 native_pose,clean_alpha,png,dump,make_recipes,compile_candidates,relative,register_settled_ground)

ANIMALS=['crystalIbex','crestedCrystalIbex','solariSunhawk','crownedSunhawk','stellacorn','resplendentStellacorn']
PIVOT=(218,267)

def build_animal(unit,background):
    original=ORIGINAL/(unit+'-atlas-v1.png')
    rows=7 if unit=='stellacorn' else 8
    old,old_record=atlas_cells(original,4,rows,128)
    supplement=HERE/'animals'/(unit+'-supplement-v1.png')
    star='Stellacorn' in unit or unit=='stellacorn'
    flyer=unit in ['solariSunhawk','crownedSunhawk','stellacorn','resplendentStellacorn']
    newrows=3 if star else 2
    fresh,new_record=atlas_cells(supplement,4,newrows,128)
    ow,oh=old_record['canvas'];nw,nh=new_record['canvas']
    holdcell=old[6];hb=holdcell['visible_bbox'];origin=holdcell['source_cell_origin']
    sx=(hb[0]+hb[2])/2-origin[0];sy=hb[3]-origin[1]
    target_height=94 if unit in ['crystalIbex','crestedCrystalIbex'] else (100 if not star else 108)
    oldscale=target_height/(hb[3]-hb[1])
    nb=fresh[4]['visible_bbox'];nx=(nb[0]+nb[2])/2;ny=nb[3]-nh/newrows
    newscale=target_height/(nb[3]-nb[1])
    selected=[];extra_dependencies=[HERE/'animals/effective-prompts-v1.json']
    def o(i):
        c=old[i];r,col=divmod(i,4);selected.append(('original',i))
        return native_pose(c,oldscale,(sx+col*ow/4,sy+r*oh/rows),CANVAS,PIVOT)
    def n(i):
        c=fresh[i];r,col=divmod(i,4);selected.append(('supplement',i))
        return native_pose(c,newscale,(nx+col*nw/4,ny+r*nh/newrows),CANVAS,PIVOT)
    stellar_cast=None
    if star:
        flight_path=HERE/'animals'/(unit+'-flight-v2.png');cast_path=HERE/'animals'/(unit+'-cure-dead-v2.png')
        fc,flight_record=atlas_cells(flight_path,2,2,128);cc,cast_record=atlas_cells(cast_path,2,2,128)
        extra_dependencies += [flight_path,cast_path,HERE/'animals/stellar-repair-prompts-v2.json']
        # Both bounded repair sheets share a constant physical body scale,
        # measured once from their upright Cure-settle control.
        cb=cc[2]['visible_bbox'];cw,ch=cast_record['canvas'];fw,fh=flight_record['canvas']
        repair_scale=target_height/(cb[3]-cb[1]);cx=(cb[0]+cb[2])/2;cy=cb[3]-ch/2
        flight_baselines={r:max(fc[i]['visible_bbox'][3] for i in range(r*2,r*2+2))+12/repair_scale for r in range(2)}
        def f(i):
            r,col=divmod(i,2);selected.append(('flight-v2',i))
            # Constant root within each measured source row; genuine flap
            # articulation is preserved. Twelve native pixels above ground.
            return native_pose(fc[i],repair_scale,(cx+col*fw/2,flight_baselines[r]),CANVAS,PIVOT)
        def c(i):
            r,col=divmod(i,2);selected.append(('cure-dead-v2',i))
            return native_pose(cc[i],repair_scale,(cx+col*cw/2,cy+r*ch/2),CANVAS,PIVOT)
        flight=[f(i) for i in range(4)];stellar_cast=[c(i) for i in range(4)]
    else:flight=[n(i) for i in range(4)]
    hold=o(6);hold2=o(7)
    turn=[n(i) for i in ([5,6,7] if unit=='resplendentStellacorn' else [4,5,6,7])]
    reflected=ImageOps.mirror(turn[-1]);join=Image.new('RGBA',CANVAS,(0,0,0,0))
    join.alpha_composite(reflected,(2*PIVOT[0]-(CANVAS[0]-1),0))
    groups={0:flight,1:[hold,hold2,hold,hold2],2:[hold,hold2,hold,hold2],
            7:turn,8:[join,turn[0],hold]}
    # All contact poses are real horn/talon strikes from the actual painted
    # atlas, not shifted holding silhouettes or wing flaps substituted as hits.
    for g,inds in [(11,[12,13,14]),(12,[8,9,10,11]),(13,[16,17,18])]:
        if unit=='crestedCrystalIbex' and g==12:inds=[8,10,11]
        if unit=='crestedCrystalIbex' and g==11:inds=[12,14,15]
        poses=[o(i) for i in inds]
        contact=poses[2] if g==12 and len(poses)==4 else poses[1]
        groups[g]=[hold,poses[0],poses[0],contact,poses[-1],hold]
    groups[3]=[hold,o(20),o(21),o(22),hold]
    if unit=='crestedCrystalIbex':groups[4]=[hold,o(24),o(25),o(24),hold]
    elif star:groups[4]=[hold,o(17),o(18),hold2,hold]
    else:groups[4]=[hold,o(24),o(25),o(26),hold]
    death_indices=[24,25,26,27] if rows==7 else [28,29,30,31]
    groups[5]=[hold]+[o(i) for i in death_indices]
    if star:
        cast=[hold,stellar_cast[0],stellar_cast[0],stellar_cast[1],stellar_cast[2],hold]
        for group in [17,18,19,30,31,32]:groups[group]=cast
        # New complete painted settled corpse replaces the clipped old endpoint.
        groups[5][-1]=stellar_cast[3]
    registered=[register_settled_ground(frame) for frame in groups[5]]
    groups[5]=[frame for frame,offset in registered]
    groups[22]=[groups[5][-1].copy()]
    if flyer:
        # Source has actual articulated raised-wing/takeoff poses; preserve
        # transitions rather than translate a rigid holding bird vertically.
        groups[20]=[hold,o(24),o(25),flight[0]] if not star else [hold,o(12),flight[0]]
        groups[21]=[flight[-1],o(26),hold2,hold] if not star else [flight[-1],o(14),hold2,hold]
    else:
        groups[20]=[hold,flight[0],flight[1]];groups[21]=[flight[-2],flight[-1],hold]
    root=HERE/'animals'/unit;descriptors={}
    for group,frames in sorted(groups.items()):
        descriptors[group]=[]
        for i,image in enumerate(frames):
            desc=png(root/'battle'/f'g{group:02d}-f{i:03d}.png',image);desc['frame']=i;descriptors[group].append(desc)
    # Native adventure uses a separate compact framing and a rightmost-tile
    # anchor. Its source root is advanced toward the front grounded foot,
    # independent from the two-hex battle centre. Never fit individual frames.
    mapscale=0.30;map_source_root=(260,267)
    def map_image(image,mirror=False):
        c={'image':image,'bbox':[0,0,*CANVAS]}
        return native_pose(c,mapscale,map_source_root,(96,64),(80,60),mirror)
    maps=[map_image(i) for i in groups[2]];map_desc=[]
    for i,image in enumerate(maps):
        desc=png(root/'map'/f'hold-{i}.png',image);desc['frame']=i;map_desc.append(desc)
    # Encounter-facing reflections preserve the same physical map source root.
    # A compact braced/hit gesture is used; full two-hex battle lunges are not
    # forced through the much narrower adventure-object footprint.
    reaction_desc={}
    for name,mirror in [('attackRight',False),('attackLeft',True)]:
        reaction_desc[name]=png(root/'map'/(name+'.png'),map_image(groups[3][2],mirror))
    from map_assembly import make_map_resources
    map_desc,reaction_desc,compact_map,map_dependencies=make_map_resources(unit,root)
    extra_dependencies += map_dependencies
    subject=fresh[7]['image'];b=subject.getchannel('A').getbbox();h=b[3]-b[1]
    top=b[1];headheight=round(h*(0.60 if flyer else 0.68));cx=(b[0]+b[2])/2
    crop=subject.crop((round(cx-headheight*.56),top,round(cx+headheight*.56),top+headheight))
    portrait=background.copy().resize((58,64),Image.Resampling.LANCZOS)
    ratio=min(58/crop.width,64/crop.height);crop=crop.resize((round(crop.width*ratio),round(crop.height*ratio)),Image.Resampling.LANCZOS)
    portrait.alpha_composite(crop,((58-crop.width)//2,64-crop.height))
    large=png(root/'portrait-large.png',clean_alpha(portrait));small=png(root/'portrait-small.png',clean_alpha(portrait.resize((32,32),Image.Resampling.LANCZOS)))
    record={'status':'authored configuration','unit':unit,'battle_canvas':list(CANVAS),'battle_root':list(PIVOT),
            'original_map':old_record,'supplement_map':new_record,'selected_cells':sorted(set(selected)),
            'cohort_scale':oldscale,'supplement_cohort_scale':newscale,'target_height':target_height,
            'group_frame_counts':{str(g):len(v) for g,v in groups.items()},'map_canvas':[96,64],
            'map_root':[80,60],'map_source_root':list(map_source_root),'map_scale_from_battle':mapscale,
            'map_mask':['VV','VA'],'map_anchor_tile':[64,32,96,64],
            'native_execution':False,'art_acceptance':False,
            'limitations':['Candidate source assembly; final native crop/motion and external visual/rights acceptance pending']}
    if star:record.update({'flight_repair_map':flight_record,'cure_dead_repair_map':cast_record,'repair_cohort_scale':repair_scale})
    record.update({'map_canvas':[64,64],'map_root':[48,60],'map_source_root':None,'map_scale_from_battle':None,
                   'map_anchor_tile':[32,32,64,64],'compact_adventure':compact_map})
    record['death_contact_registration']={'ground_y':267,'native_y_offsets':[offset for frame,offset in registered],
              'method':'Explicit physical-contact translation of the complete painted death poses; no scale or anatomy changes'}
    dump(root/'assembly.json',record)
    return {'unit':unit,'root':root,'groups':groups,'battle':descriptors,'map':map_desc,'reactions':reaction_desc,
            'large':large,'small':small,'record':record,'original':original,'supplement':supplement,'producer':Path(__file__),
            'extra_dependencies':extra_dependencies,'extra_origins':[p for p in extra_dependencies if p.suffix=='.png']}

def review_animal(data):
    unit=data['unit'];groups=data['groups'];out=REPORT/'animals'/unit;out.mkdir(parents=True,exist_ok=True)
    crop=(90,115,365,290);cell=(275,195);rows=[]
    for g,frames in sorted(groups.items()):
        strip=Image.new('RGBA',(cell[0]*max(6,len(frames)),cell[1]),(52,49,46,255));d=ImageDraw.Draw(strip)
        d.text((3,3),f'{unit} group {g}',fill='white')
        for i,frame in enumerate(frames):strip.alpha_composite(frame.crop(crop),(i*cell[0],20))
        rows.append(strip)
        if g in [0,5,7,8,11,12,13,20,21,31]:
            views=[]
            for frame in frames:
                bg=Image.new('RGBA',(275,175),(52,49,46,255));bg.alpha_composite(frame.crop(crop));views.append(bg.convert('RGB'))
            views[0].save(out/f'g{g:02d}.gif',save_all=True,append_images=views[1:],duration=170,loop=0,disposal=2)
    page=Image.new('RGBA',(max(r.width for r in rows),cell[1]*len(rows)),(52,49,46,255))
    for i,row in enumerate(rows):page.alpha_composite(row,(0,i*cell[1]))
    page.convert('RGB').save(out/'actions-native.png')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--unit',action='append');args=parser.parse_args()
    background_path=HERE/'portrait-background-v1.png';background=Image.open(background_path).convert('RGBA')
    records=[];recipes=[]
    for unit in args.unit or ANIMALS:
        data=build_animal(unit,background);records.append(data['record']);recipes+=make_recipes(data,background_path);review_animal(data)
    errors=compile_candidates(recipes,'animal')
    dump(REPORT/'animal-assembly-summary.json',{'status':'authored configuration','units':records,'errors':errors,'art_acceptance':False,'native_execution':False})
    print(json.dumps({'units':len(records),'recipes':len(recipes),'errors':errors},indent=2))
    return 2 if errors else 0
if __name__=='__main__':raise SystemExit(main())
