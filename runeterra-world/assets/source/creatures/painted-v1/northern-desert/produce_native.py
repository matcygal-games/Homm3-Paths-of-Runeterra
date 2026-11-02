"""Deterministic whole painted-actor registration; no art generation or staging."""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,json,sys
from PIL import Image,ImageOps,ImageDraw
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
PROJECT=next(p for p in BASE.parents if p.name=="runeterra-world")
WORKSPACE=PROJECT.parent
REPORT=WORKSPACE/"reports/world-immersion-20261026-v1/neutral-art"
FIDGET=(0,1,1,2,2,3,0)
GROUPS={0:("motion",(4,5,6,7,8,9)),1:("motion",FIDGET),2:("motion",(0,)),3:("motion",(10,0)),4:("motion",(11,)),5:("death",(0,1,2,3)),7:("motion",(0,12,14)),8:("motion",(14,12,0)),11:("combat",(0,1,2,3)),12:("combat",(4,5,6,7)),13:("combat",(8,9,10,11)),22:("death",(3,))}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def box(im):return im.getchannel("A").point(lambda a:255 if a>=8 else 0).getbbox()
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def render(row,cohort,root,canvas,multiplier=1.,mirror=False):
    source=PROJECT/row["image"]
    assert sha(source)==row["sha256"] and sha(PROJECT/row["source"])==row["source_sha256"],"Painted source drift"
    actor=Image.open(source).convert("RGBA");point=cohort["roots"][row["index"]];scale=cohort["scale"]*multiplier
    local=[point[i]-row["crop"][i]for i in (0,1)]
    actor=actor.resize(tuple(max(1,round(v*scale))for v in actor.size),Image.Resampling.LANCZOS)
    offset=[root[i]-round(local[i]*scale)for i in (0,1)]
    if mirror:actor=ImageOps.mirror(actor);offset[0]=root[0]-(actor.width-1-round(local[0]*scale))
    b=box(actor)
    assert b and 0<=offset[0]+b[0]<offset[0]+b[2]<=canvas[0] and 0<=offset[1]+b[1]<offset[1]+b[3]<=canvas[1],("Whole painted subject clipping",row["image"],offset,b,canvas)
    final=Image.new("RGBA",canvas,(0,0,0,0));final.alpha_composite(actor,tuple(offset))
    return final,{"source":row["image"],"source_sha256":row["sha256"],"painted_source":row["source"],"source_root":point,"fixed_cohort_scale":cohort["scale"],"role_scale_multiplier":multiplier,"native_root":list(root),"offset":offset,"mirror":mirror,"alpha_bbox_8":box(final)}
def produce(unit):
    folder=BASE/unit;index_path=folder/"isolated-source-map-v1.json";index=json.loads(index_path.read_text(encoding="utf-8"))["cohorts"]
    roots_path=folder/"pose-roots-v1.json";roots=json.loads(roots_path.read_text(encoding="utf-8"))
    assert set(index)>={"motion","combat","death"},"Complete genuine action cohorts required"
    for name,rows in index.items():
        assert len(rows)==len(roots[name]["roots"]),(unit,name,"manual anatomical annotations incomplete")
        assert not any(r["principal_touches_source_edge"]for r in rows),(unit,name,"painted core touches outer source edge")
    ledger=folder/"generation-ledger-v1.json"
    masters=sorted({PROJECT/r["source"]for rows in index.values()for r in rows}|{folder/"portrait-v1.png"})
    dump(ledger,{"status":"authored configuration","provider":"OpenAI built-in imagegen","model":"not exposed","sources":[{"path":rel(p),"sha256":sha(p),"prompt":rel(p.with_suffix(".prompt.txt")),"prompt_sha256":sha(p.with_suffix(".prompt.txt"))}for p in masters],"visual_approval_granted":False,"method":"Newly painted2D source poses, no original pixels or3D. Technical alpha-component separation preserves body RGB/core alpha; whole-actor fixed-cohort registration only."})
    portrait=folder/"portrait-v1.png";native=folder/"native";recipes=[];records=[]
    groups_spec=deepcopy(GROUPS)
    holding_cohort="holding" if "holding" in index else "motion"
    groups_spec[1]=(holding_cohort,FIDGET);groups_spec[2]=(holding_cohort,(0,))
    dependencies=[Path(__file__),BASE/"extract_sources.py",roots_path,index_path,ledger,portrait]+masters+sorted({PROJECT/r["image"]for rows in index.values()for r in rows})+sorted(folder.glob("*.prompt.txt"))
    dependencies=sorted(set(dependencies))
    common={"production_status":"painted-master-complete-unapproved","generation":{"image_generation_used":True,"provider":"OpenAI built-in imagegen","model":"not exposed","prompt":(folder/"motion-v1.prompt.txt").read_text(encoding="utf-8"),"painted_master":rel(folder/"motion-v1.png"),"painted_master_sha256":sha(folder/"motion-v1.png"),"action_source_ledger":rel(ledger),"action_source_ledger_sha256":sha(ledger),"method":"Fixed uniform whole painted-cohort scale and annotated anatomical roots; no per-frame fitting, anatomy warp, code-painted replacement or final approval."},"production_inputs":[{"path":rel(p),"sha256":sha(p)}for p in dependencies]}
    def descriptor(p,i,size):return {"frame":i,"source":rel(p),"sha256":sha(p),"source_sha256":sha(p),"source_canvas":list(size)}
    def recipe(role,data):
        p=PROJECT/"assets/recipes/creatures/northern-desert"/unit/(role+".recipe.json")
        dump(p,dict(deepcopy(common),**data));recipes.append(rel(p))
    groups=[]
    for group,(cohort,order)in sorted(groups_spec.items()):
        frames=[]
        for frame,i in enumerate(order):
            actual_cohort=holding_cohort if (group==3 and frame==1)or(group==7 and frame==0)or(group==8 and frame==2) else cohort
            im,record=render(index[actual_cohort][i],roots[actual_cohort],tuple(roots["battle_root"]),(450,400))
            p=native/"battle"/f"g{group:02d}-f{frame:03d}.png";save(p,im);frames.append(descriptor(p,frame,im.size))
            record.update(group=group,frame=frame,cohort=actual_cohort,source_index=i,native_frame=rel(p),sha256=sha(p));records.append(record)
        groups.append({"group":group,"frames":frames,"generateShadow":1,"generateOverlay":0})
    recipe("battle",{"recipe_type":"vcmi_animation","output_path":f"Content/Sprites/runeterra/world/creatures/{unit}/battle.json","canvas":[450,400],"pivot":dict(zip(("x","y"),roots["battle_root"])),"groups":groups})
    frames=[];adventure=[]
    for frame,i in enumerate(FIDGET):
        im,record=render(index[holding_cohort][i],roots[holding_cohort],tuple(roots["map_root"]),(96,64),roots["adventure_role_scale"],True)
        assert box(im)[0]>=32,("Source exceeds native two-column visible mask",unit,box(im))
        p=native/"map"/f"g00-f{frame:03d}.png";save(p,im);frames.append(descriptor(p,frame,im.size));adventure.append(record)
    recipe("map",{"recipe_type":"vcmi_animation","output_path":f"Content/Sprites/runeterra/world/creatures/{unit}/map.json","canvas":[96,64],"pivot":dict(zip(("x","y"),roots["map_root"])),"groups":[{"group":0,"frames":frames,"generateShadow":1,"generateOverlay":0}]})
    for role,mirror in (("attackLeft",False),("attackRight",True)):
        # The compact genuine level-bite windup is a complete encounter actor;
        # the extended impact is reserved for its450pxbattle canvas.
        im,record=render(index["combat"][4],roots["combat"],tuple(roots["encounter_root"]),(64,64),roots["adventure_role_scale"],mirror)
        p=native/(role+".png");save(p,im);adventure.append(dict(record,role=role))
        recipe(role,{"recipe_type":"raster","output_path":f"Content/Sprites/runeterra/world/creatures/{unit}/{role}.png","canvas":[64,64],"source":rel(p),"source_sha256":sha(p),"source_canvas":[64,64],"fit":"exact"})
    portrait_generation=deepcopy(common["generation"]);portrait_generation.update(prompt=(folder/"portrait-v1.prompt.txt").read_text(encoding="utf-8"),painted_master=rel(portrait),painted_master_sha256=sha(portrait))
    for role,size in (("large",(58,64)),("small",(32,32))):
        im=ImageOps.fit(Image.open(portrait).convert("RGBA"),size,Image.Resampling.LANCZOS);p=native/(role+".png");save(p,im)
        recipe(role,{"recipe_type":"raster","output_path":f"Content/Sprites/runeterra/world/creatures/{unit}/{role}.png","canvas":list(size),"source":rel(p),"source_sha256":sha(p),"source_canvas":list(size),"fit":"exact","generation":portrait_generation})
    corpse=native/"battle/g22-f000.png";terminal=native/"battle/g05-f003.png";hold=native/"battle/g02-f000.png"
    assert Image.open(corpse).tobytes()==Image.open(terminal).tobytes() and Image.open(corpse).tobytes()!=Image.open(hold).tobytes(),"Real persistent corpse contract"
    report={"status":"authored configuration","unit":unit,"battle_groups":{str(g):len(order)for g,(_,order)in groups_spec.items()},"battle_frames":len(records),"battle_root":roots["battle_root"],"holding_alpha_bbox_8":box(Image.open(hold)),"whole_subject_native_clip_count":0,"registration":records,"adventure_registration":adventure,"recipe_paths":recipes,"terminal_corpse_matches_final_death_pixels":True,"native_motion_observed":False,"visual_approval_granted":False,"source_bytes":sum(p.stat().st_size for p in folder.rglob("*")if p.is_file()and p.name!="native-registration-v1.json"),"source_bytes_scope":"Own actor files excluding this self-referential registration; other actors cannot alter this value"}
    dump(folder/"native-registration-v1.json",report);dump(REPORT/(unit+"-native-candidate-v1.json"),report)
    # Reference/display assembly only, no artistic drawing.
    sheet=Image.new("RGB",(1200,1190),(64,62,54));draw=ImageDraw.Draw(sheet)
    for i,rec in enumerate(records):
        x=(i%6)*200;y=(i//6)*170;draw.text((x+2,y+2),f"g{rec['group']} f{rec['frame']}",fill=(245,235,211))
        im=Image.open(PROJECT/rec["native_frame"]);view=im.crop((110,140,310,280));sheet.paste(view,(x,y+20),view)
    save(REPORT/(unit+"-native-actions-v1.png"),sheet)
    print(json.dumps({"unit":unit,"recipes":len(recipes),"battle_frames":len(records),"holding_bounds":report["holding_alpha_bbox_8"],"source_bytes":report["source_bytes"]},indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("unit",choices=("rimefangWolf","rockbear"));args=p.parse_args();produce(args.unit)
