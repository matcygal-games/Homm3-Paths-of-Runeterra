"""Create candidate recipes for the selected whole-town cohort, never canonical files.

Run only after ACTIVE-COHORT.json explicitly releases source frames/background.
The actual configured compiler is invoked separately; JSON creation is not a build.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
PREFIX="Content/Sprites/runeterra/ionia/"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rel(p):
    return Path(p).relative_to(PROJECT).as_posix()

def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def own(name):
    if not isinstance(name,str) or not name or ":" in name or "\\" in name or any(x in ("",".","..") for x in name.split("/")):
        raise ValueError("Unsafe candidate source name")
    p=HERE/name
    for q in (p,*p.parents):
        if q==HERE:
            break
        if q.is_symlink() or getattr(q.lstat(),"st_file_attributes",0)&0x400:
            raise ValueError("Candidate source redirect")
    if not p.is_file() or not p.resolve().is_relative_to(HERE):
        raise ValueError("Missing candidate source")
    return p

def main():
    active=read(HERE/"ACTIVE-COHORT.json")
    for item in active["pins"]:
        if sha(own(item["path"]))!=item["sha256"]:
            raise ValueError("Selected source freeze drift: "+item["path"])
    frame_index=read(own(active["frame_index"]))
    cohort=active["prepared"]
    folder=HERE/active["recipe_folder"]
    if folder.exists():
        raise ValueError("Never overwrite existing candidate recipe cohort")
    source_record=HERE/active["source_index"]
    if source_record.exists():
        raise ValueError("Never overwrite sealed source-input record")
    dependencies=[{"path":rel(own(name)),"sha256":sha(own(name))} for name in active["source_files"]]
    source_record.write_text(json.dumps({"status":"authored configuration","method":"Own genuine painted2D full-town masters and explicit deterministic extraction inputs; no private or 3D artwork dependencies.","dependencies":dependencies,"native_execution":False,"release_accepted":False},indent=2)+"\n")
    inputs=[{"path":rel(source_record),"sha256":sha(source_record)},
            {"path":rel(HERE/"derive.py"),"sha256":sha(HERE/"derive.py")}]
    common={"status":"painted-candidate","production_status":"painted-master-complete-unapproved",
        "visual_approval_granted":False,"credits":{"author":"Project-directed OpenAI built-in imagegen; deterministic native assembly","license":None,"redistribution":"unresolved; release prohibited"},
        "generation":{"image_generation_used":False,"method":"Deterministic raw-painted master conversion, protected 2D compositing and actual architectural extraction. Genuine art/prompt ancestry and technical inputs declared in the source record.","source_record":{"path":rel(source_record),"sha256":sha(source_record)},"technical_producer":{"path":rel(HERE/"derive.py"),"sha256":sha(HERE/"derive.py")}},
        "inputs":inputs,"acceptance":"authored configuration; native clicks/gameplay, final art and redistribution remain separate"}
    recipes=[]
    def save(kind,name,data):
        path=folder/kind/name;path.parent.mkdir(parents=True,exist_ok=True)
        encoded=(json.dumps({**common,**data},indent=2,ensure_ascii=False)+"\n").encode()
        path.write_bytes(encoded);recipes.append({"candidate":rel(path),"canonical":"assets/recipes/"+kind+"/"+name,"sha256":hashlib.sha256(encoded).hexdigest(),"output_path":data["output_path"]})
    def source(path):
        p=own(path)
        return {"source":rel(p),"source_sha256":sha(p),"source_canvas":list(Image.open(p).size)}
    def raster(kind,name,src,output,technical=False):
        descriptor=source(src)
        save(kind,name,{"recipe_type":"raster","canvas":descriptor["source_canvas"],"fit":"exact","require_alpha":True,"output_path":PREFIX+output,**descriptor,
                        **({"production_status":"derived-technical-mask-complete"} if technical else {})})
    raster("town","background.png.json",cohort+"/town/background.png","town/background.png")
    for state in frame_index["frames"]:
        descriptor=source(cohort+"/town/structures/"+state+"/layer.png")
        save("town","structures_"+state+".json.json",{"recipe_type":"vcmi_animation","canvas":[800,374],"pivot":{"x":0,"y":0},"groups":[{"group":0,"frames":[{**descriptor,"sha256":descriptor["source_sha256"]}]}],"output_path":PREFIX+"town/structures/"+state+".json"})
        for role in ("area","border","campaign"):
            raster("town","structures_"+state+"_"+role+".png.json",cohort+"/town/structures/"+state+"/"+role+".png","town/structures/"+state+"_"+role+".png",role!="campaign")
    ids=read(own(active["building_ids"]))["ids"]
    frames=[]
    for state in sorted(frame_index["frames"],key=lambda key:ids[key]):
        frames.append({**source(cohort+"/town/structures/"+state+"/icon.png"),"building":state,"frame":ids[state]})
    save("town","buildingIcons.json.json",{"recipe_type":"indexed_animation","canvas":[150,70],"pivot":{"x":0,"y":0},"frames":frames,"output_path":PREFIX+"town/buildingIcons.json"})
    for state in ("village","fort"):
        for variant in ("normal","built"):
            for size in ("large","small"):
                name=state+"_"+variant+"_"+size+".png"
                raster("town","icons_"+name+".json",cohort+"/town/icons/"+name,"town/icons/"+name)
    for height in (120,130):
        name="creatureBackground"+str(height)+".png"
        raster("ui",name+".json",cohort+"/ui/"+name,"ui/"+name)
    for record in recipes:
        if not (PROJECT/record["canonical"]).is_file():
            raise ValueError("Replacement does not match an existing producer: "+record["canonical"])
    if len({r["output_path"] for r in recipes})!=len(recipes):
        raise ValueError("Duplicate candidate producer")
    output=HERE/active["recipe_index"]
    output.write_text(json.dumps({"status":"authored configuration","recipes":recipes,"preserved":"Five existing adventure-town map animation producers remain untouched; roster/economy and all unrelated art are unchanged.","native_execution":False,"release_accepted":False},indent=2)+"\n")
    print(json.dumps({"status":"authored configuration","replacement_recipes":len(recipes),"source_dependencies":len(dependencies),"recipe_index":rel(output),"canonical_writes":False}))

if __name__=="__main__":
    main()
