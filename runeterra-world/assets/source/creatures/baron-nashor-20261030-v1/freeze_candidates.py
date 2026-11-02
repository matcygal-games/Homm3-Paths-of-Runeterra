"""Freeze this owned candidate after actual assembly and author pixel inspection."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-world')
ROOT=next(p for p in HERE.parents if (p/'scripts/faction_art_compile.py').is_file())
REPORT=ROOT/'reports/world-baron-nashor-art-20261030-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf8')
def main():
    technical=json.loads((REPORT/'technical-verification.json').read_text(encoding='utf8'))
    assert technical['recipe_count']==7 and technical['compiled_output_count']==51 and technical['battle_frames']==37
    assert '20' not in technical['battle_groups'] and '21' not in technical['battle_groups']
    for row in technical['source_consumer_checks']:
        assert row['double_real_assembly_identical'] and row['negative_source_pin_mutations_rejected']==2
    native=HERE/'native'
    board=Image.new('RGB',(1000,350),(57,63,52));draw=ImageDraw.Draw(board)
    for name,x in [('large.png',10),('small.png',150),('attackLeft.png',240),('attackRight.png',370),('map/g00-f000.png',510),('site.png',750)]:
        im=Image.open(native/name);board.paste(im,(x,30),im);draw.text((x,5),name,fill='white')
        zoom=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);board.paste(zoom,(x,145),zoom)
    board.save(REPORT/'native-other-roles.png')
    pngs=[]
    for p in sorted(HERE.rglob('*.png')):
        im=Image.open(p);assert not im.info,(p,list(im.info))
        pngs.append({'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'mode':im.mode,'size':list(im.size),'metadata_keys':[]})
    refs=[ROOT/'runeterra-demacia/references/frames/cgriff/g02-f000.png']
    dump(REPORT/'author-native-inspection.json',{'status':'authored configuration','review_kind':'author native-size inspection, not independent acceptance','inspected':['native-action-sheet.png','native-other-roles.png','native-site.png'],'pngs':pngs,'all_png_metadata_empty':True,'observations':['Tall purple-plum armored wyrm silhouette with pale ribbed belly, multiple magenta eyes and ivory mandibles.','Movement undulates the connected coils and counterbalances the neck while keeping the base on the terrain plane.','High, level and low attacks articulate neck, jaws and foreclaws.','Grounded idle, movement and reactions have visibly supporting coils.','Death lowers and topples the neck into a prone inert body; the persistent corpse matches the last death frame.','Pit has an open southern land entrance and a distinct asymmetric jagged Void rim.','No flight, teleportation, acid projectile or new spell is represented.'],'limitations':['Native gameplay timing, obstruction, balance, visiting and rewards are not tested here.','The six-frame idle loop uses four unique painted poses with repeated endpoints.','The initial identity study is retained as generation provenance only; its clipped edges are not used in any final native frame.','No new audio, final artistic acceptance or redistribution rights approval is asserted.'],'original_references_inspected':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'use':'visual inspection only; no pixels supplied to imagegen'}for p in refs]})
    files=[p for p in HERE.rglob('*')if p.is_file()]
    files.sort(key=lambda p:p.relative_to(PROJECT).as_posix())
    rows=[{'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in files]
    digest=hashlib.sha256(('\n'.join(f"{r['path']}\t{r['sha256']}\t{r['bytes']}"for r in rows)+'\n').encode('utf8')).hexdigest()
    freeze={'status':'authored configuration','source_folder':HERE.relative_to(PROJECT).as_posix(),'candidate_project_root_relative_to_workspace':PROJECT.relative_to(ROOT).as_posix(),'publication_state':'Isolated owned report tree; shared World source hold preserved.','file_count':len(rows),'total_bytes':sum(r['bytes']for r in rows),'aggregate_sha256':digest,'aggregate_rule':'UTF8 path TAB sha256 TAB decimal bytes LF records in explicit case-sensitive lexical POSIX-path order; final LF included.','files':rows,'technical_verification_sha256':sha(REPORT/'technical-verification.json'),'writer_released':True,'native_runtime':'not_run','release_accepted':False}
    dump(REPORT/'frozen-source-inventory.json',freeze)
    (REPORT/'REPORT.md').write_text(f'''# Baron Nashor and Nashor Pit source candidate

Status: **authored configuration**, unselected. No canonical content, shared selection, stage or desktop was changed. The candidate project is isolated at `{PROJECT.relative_to(ROOT).as_posix()}`; the shared World source hold was preserved.

Seven actual World compiler recipes assembled twice into 51 byte-identical outputs: 37 battle frames, six adventure frames, two portraits, two mirrored encounter images, a pit sprite and three animation descriptors. Fourteen negative source/master-pin mutations were rejected. Source isolation found eight motion, sixteen combat and four death actors with no complete-actor source-edge clips. The retained initial identity study is provenance only and supplies no final extracted pose.

The grounded living two-hex physical-melee adaptation visibly undulates its connected coils. No flight, obstacle crossing, burrow teleport, acid shooting, regeneration, immunity or global/siege aura is inferred. Unique exclusion flags, finite guard stacks, stats and rewards belong to mechanics integration.

Frozen source: `{freeze['source_folder']}`. {freeze['file_count']} files / {freeze['total_bytes']:,} bytes. Aggregate SHA256: `{digest}`. Technical receipt SHA256: `{freeze['technical_verification_sha256']}`. Per-source and per-output hashes are in the JSON receipts.

Riot's [Baron development article](https://www.leagueoflegends.com/en-au/news/dev/dev-cat-cults-rift-mechs-and-baron-s-revamp/) supplies the Voidborn wyrm and late-game pit-objective basis. Original painted source pixels and ordinary native ground movement are project adaptations.

Independent review, canonical integration and native timing, obstruction, balance, site visiting, rewards, final art and redistribution acceptance remain separate work. Browser playback is illustrative.
''',encoding='utf8')
    print(json.dumps({'file_count':len(rows),'total_bytes':freeze['total_bytes'],'aggregate_sha256':digest,'technical_sha256':sha(REPORT/'technical-verification.json'),'freeze_sha256':sha(REPORT/'frozen-source-inventory.json')}))
if __name__=='__main__':main()
