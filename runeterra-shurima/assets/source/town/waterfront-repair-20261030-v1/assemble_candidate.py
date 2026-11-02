"""Bounded painted waterfront repair; never writes canonical assets or stages."""
from pathlib import Path
import hashlib, io, json, sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
WORKSPACE=PROJECT.parent
OLD=PROJECT/'assets/source/town/approved-sh1-integration-20261030-v4'
REPORT=WORKSPACE/'reports/shurima-waterfront-repair-20261030-v1'
SIZE=(800,374)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,im):
    p.parent.mkdir(parents=True,exist_ok=True); im.save(p,compress_level=9)
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf8')
def polygon(points):
    out=Image.new('L',SIZE);ImageDraw.Draw(out).polygon(points,fill=255);return out
def union(*masks):
    out=Image.new('L',SIZE)
    for m in masks:out=ImageChops.lighter(out,m)
    return out
def seamless(source,target,selection):
    box=selection.getbbox();l,t,r,b=box
    box=(max(0,l-1),max(0,t-1),min(800,r+1),min(374,b+1))
    src=np.asarray(source.convert('RGB').crop(box),dtype=float)
    dst=np.asarray(target.convert('RGB').crop(box),dtype=float)
    active=np.asarray(selection.crop(box))>0
    yy,xx=np.nonzero(active);n=len(xx)
    indexes=np.full(active.shape,-1,dtype=int);indexes[yy,xx]=np.arange(n)
    degree=np.zeros(n);rhs=np.zeros((n,3));neighbours=[]
    height,width=active.shape
    for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
        nx,ny=xx+dx,yy+dy;valid=(nx>=0)&(nx<width)&(ny>=0)&(ny<height)
        ids=np.nonzero(valid)[0];vx,vy=nx[valid],ny[valid]
        degree[ids]+=1;rhs[ids]+=src[yy[valid],xx[valid]]-src[vy,vx]
        ni=indexes[vy,vx];inside=ni>=0;neighbours.append((ids[inside],ni[inside]))
        rhs[ids[~inside]]+=dst[vy[~inside],vx[~inside]]
    def multiply(value):
        out=degree*value
        for ids,other in neighbours:out[ids]-=value[other]
        return out
    solved=[];proof=[]
    for channel in range(3):
        value=dst[yy,xx,channel].copy();residual=rhs[:,channel]-multiply(value)
        direction=residual/degree;rz=float(residual@direction)
        for iteration in range(4000):
            if float(np.max(np.abs(residual)))<1e-8:break
            ad=multiply(direction);alpha=rz/float(direction@ad)
            value+=alpha*direction;residual-=alpha*ad
            preconditioned=residual/degree;new_rz=float(residual@preconditioned)
            direction=preconditioned+(new_rz/rz)*direction;rz=new_rz
        solved.append(value);proof.append({'channel':channel,'iterations':iteration,'residual':float(np.max(np.abs(residual)))})
    out=dst.copy();out[yy,xx]=np.clip(np.rint(np.stack(solved,axis=1)),0,255)
    result=target.convert('RGB');result.paste(Image.fromarray(out.astype('uint8')),box)
    return result.convert('RGBA'),proof

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    oldbg=Image.open(OLD/'background-native.png').convert('RGBA')
    approved=Image.open(OLD/'approved-full-native.png').convert('RGBA')
    hidden=Image.open(OLD/'hidden-face-completion-native-v1.png').convert('RGBA')
    raw=Image.open(HERE/'empty-water-painted-raw-v1.png').convert('RGBA')
    clean=raw.resize((200,99),Image.Resampling.LANCZOS)
    save(HERE/'empty-water-painted-native-v1.png',clean)
    # The generated whole-crop painter supplies the removed pier and water only.
    # Existing dry landscape outside this exact shoreline/water budget is fixed.
    source=oldbg.copy();source.paste(clean,(600,275))
    budget=polygon([(632,316),(643,310),(655,311),(670,314),(683,317),(701,319),
                    (712,316),(727,306),(743,295),(762,292),(766,309),(782,309),
                    (799,310),(799,373),(574,373),(594,353),(618,342),(632,332)])
    # Use the original unobscured water as the boundary target, not the faulty
    # rectangular recovery. Its full-coast architecture is covered by the paint.
    target=oldbg.copy();water=Image.open(OLD/'geometry/water.png').convert('L')
    water_budget=ImageChops.multiply(water,budget)
    target=Image.composite(approved,target,water_budget)
    background,proof=seamless(source,target,budget)
    save(HERE/'water-repair-budget.png',budget)
    save(HERE/'background-candidate.png',background)
    # Native source-pixel annotations trace only the constructed pier deck,
    # posts and pilings, not the natural water surrounding it.
    dock=polygon([(638,320),(645,317),(653,317),(660,319),(668,320),(676,320),
                  (682,320),(689,317),(692,317),(693,321),(699,322),(701,319),
                  (703,319),(704,323),(710,324),(712,321),(714,321),(715,325),
                  (725,327),(729,326),(732,326),(733,329),(744,331),(751,332),
                  (756,333),(759,333),(760,357),(756,360),
                  (749,358),(737,354),(724,352),(710,349),(700,347),(692,347),
                  (686,345),(681,344),(676,350),(672,350),(671,344),(668,343),
                  (664,343),(662,340),(655,338),(652,343),(648,343),(646,338),
                  (641,335),(638,332)])
    posts=polygon([(646,315),(648,315),(648,337),(646,337)])
    dock=union(dock,posts)
    # Traced actual hull contact excludes old opaque reflected-water polygons.
    # Sail/rigging retains the source's exact native layout.
    hull=polygon([(693,336),(703,334),(715,338),(724,340),(739,343),(755,347),
                  (766,346),(771,339),(773,338),(775,344),(774,352),(770,358),
                  (766,360),(755,360),(742,357),(723,353),(708,350),(696,347)])
    sail=polygon([(715,329),(752,301),(756,300),(756,339),(723,334)])
    rigging=Image.new('L',SIZE);rd=ImageDraw.Draw(rigging)
    rd.line([(757,296),(757,344)],fill=255,width=2)
    rd.line([(708,338),(757,297)],fill=255,width=1)
    boat=union(hull,sail,rigging)
    dock_image=hidden.copy();dock_image.putalpha(dock)
    ship_image=approved.copy();ship_image.putalpha(union(dock,boat))
    # The old coarse coast mask included a fixed far-bank retaining-wall strip.
    # Restore that natural/municipal shoreline to the background rather than
    # making it disappear when the optional pier is absent.
    old_coast=Image.open(OLD/'frames/ship.png').getchannel('A')
    fixed_shore=ImageChops.multiply(ImageChops.subtract(old_coast,ship_image.getchannel('A')),
                                   ImageChops.invert(budget))
    fixed_shore=ImageChops.multiply(fixed_shore,polygon([(600,275),(799,275),(799,321),(600,321)]))
    fixed_shore=fixed_shore.point(lambda a:255 if a else 0)
    background=Image.composite(approved,background,fixed_shore)
    save(HERE/'fixed-shore-ownership.png',fixed_shore)
    save(HERE/'background-candidate.png',background)
    save(HERE/'shipyard-candidate.png',dock_image);save(HERE/'ship-candidate.png',ship_image)
    save(HERE/'shipyard-body.png',dock);save(HERE/'ship-body.png',ship_image.getchannel('A'))
    for name,im in [('empty',background),('shipyard',Image.alpha_composite(background,dock_image)),
                    ('ship',Image.alpha_composite(background,ship_image))]:
        save(REPORT/(name+'.png'),im)
        save(REPORT/(name+'-water-closeup.png'),im.crop((600,275,800,374)).resize((1200,594)))
    # Full town assembly uses the original native family highest-state order.
    content=json.loads((PROJECT/'content/factions.json').read_text())['shurima']['town']
    structures=content['structures'];states=json.loads((OLD/'layout-acceptance-contract-v2.json').read_text())['silhouette_plan']['complete_scene_states']
    full=background.copy()
    for state in sorted(states,key=lambda s:structures[s]['z']):
        image=ship_image if state=='ship' else dock_image if state=='shipyard' else Image.open(OLD/'frames'/(state+'.png')).convert('RGBA')
        full=Image.alpha_composite(full,image)
    save(REPORT/'full-candidate.png',full)
    diff=np.any(np.asarray(full.convert('RGB'))!=np.asarray(approved.convert('RGB')),axis=2)
    outside=np.asarray(budget)==0
    dump(REPORT/'assembly.json',{'status':'authored configuration','candidate_only':True,
        'approved_full_changed_pixels':int(diff.sum()),'approved_full_changes_outside_water_budget':int((diff&outside).sum()),
        'poisson_solves':proof,'native_family':'SHIP replaces SHIPYARD; SHIP is complete quay plus boat',
        'inputs':{str(p.relative_to(PROJECT)):sha(p) for p in [OLD/'background-native.png',OLD/'approved-full-native.png',OLD/'hidden-face-completion-native-v1.png',HERE/'empty-water-painted-raw-v1.png']},
        'outputs':{str(p.relative_to(PROJECT)):sha(p) for p in [HERE/'background-candidate.png',HERE/'shipyard-candidate.png',HERE/'ship-candidate.png']}})
    (REPORT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Shurima waterfront candidate</title><style>body{background:#222;color:#eee;font:17px Georgia;max-width:1200px;margin:30px auto}img{max-width:100%}</style><h1>Shurima waterfront repair candidate</h1><p>Authored configuration; source candidate only. New empty-water painting, complete quay and complete SHIP replacement. Not staged or accepted.</p>'+''.join('<h2>'+n+'</h2><img src="'+n+'.png"><img src="'+n+'-water-closeup.png">' for n in ['empty','shipyard','ship'])+'<h2>Full town</h2><img src="full-candidate.png">',encoding='utf8')
    print(json.dumps({'changed_pixels':int(diff.sum()),'outside_budget':int((diff&outside).sum())}))

if __name__=='__main__':main()
