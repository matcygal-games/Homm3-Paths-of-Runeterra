"""RT-022 deterministic full-canvas reduction only; no painting or AI calls here."""
from pathlib import Path
import hashlib, json, platform
from PIL import Image, ImageDraw, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(__file__).resolve().parent
REPORT = ROOT / 'runeterra-ionia/build/reports/issue-resolution-20261023/icons-painted-v1'
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p, value):
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')
def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    renders = REPORT / 'renders'
    renders.mkdir(exist_ok=True)
    heroes_path = ROOT / 'runeterra-ionia/content/heroes.json'
    heroes = json.loads(heroes_path.read_text(encoding='utf-8'))
    receipts = json.loads((SOURCE / 'generation-receipts.json').read_text(encoding='utf-8'))
    chosen = {r['selection_id']: r for r in receipts['records'] if r['chosen']}
    assert set(chosen) == set(heroes)
    native = Image.new('RGB', (930, 410), (39, 33, 27))
    draw = ImageDraw.Draw(native)
    draw.text((5, 4), 'Native pixels: painted 44 / 32 | unchanged selected 44 / 32. Offline review only.', fill='white')
    enlarged = Image.new('RGB', (930, 1130), (39,33,27))
    edraw = ImageDraw.Draw(enlarged)
    edraw.text((5,4), '4x NEAREST diagnostic only; native contact is the review authority.', fill='white')
    cases=[]
    assets=[]
    for index, hero in enumerate(heroes):
        r=chosen[hero]
        master=SOURCE / (r['id']+'-master.png')
        img=Image.open(master).convert('RGB')
        assert img.size[0] == img.size[1]
        row=index//3; col=index%3
        x=col*310+5; y=row*76+28
        draw.text((x,y),hero,fill='white')
        ex=col*310+5; ey=row*220+26
        edraw.text((ex,ey),hero,fill='white')
        for label,size,offset in [('large',44,0),('small',32,50)]:
            output=renders/(hero+'-'+label+'.png')
            reduced=img.resize((size,size),Image.Resampling.LANCZOS).convert('RGBA')
            reduced.save(output)
            replay=img.resize((size,size),Image.Resampling.LANCZOS).convert('RGBA')
            assert reduced.tobytes() == replay.tobytes()
            assert Image.open(output).size==(size,size)
            assert reduced.getchannel('A').getextrema()==(255,255)
            native.paste(reduced,(x+offset,y+17))
            if label=='large': enlarged.paste(reduced.resize((176,176),Image.Resampling.NEAREST),(ex,ey+18))
            else: enlarged.paste(reduced.resize((128,128),Image.Resampling.NEAREST),(ex+178,ey+18))
            cases.append({'hero':hero,'consumer':label,'size':[size,size],'source_sha256':digest(master),'output':str(output.relative_to(ROOT)).replace('\\','/'),'sha256':digest(output),'pixel_replay':True,'opaque':True,'state':'built-unreviewed','mechanic':heroes[hero]['specialty']})
        assets.append({'hero':hero,'master':str(master.relative_to(ROOT)).replace('\\','/'),'sha256':digest(master),'source_canvas':list(img.size),'prompt_sha256':hashlib.sha256(r['prompt'].encode()).hexdigest(),'state':'built-unreviewed'})
    native.save(REPORT/'native-contact.png')
    enlarged.save(REPORT/'diagnostic-4x.png')
    # Comparison pixels are report-only and never read for candidate conversion.
    native_context=Image.open(REPORT/'native-contact.png').convert('RGB')
    nd=ImageDraw.Draw(native_context)
    for index,hero in enumerate(heroes):
        x=(index%3)*310+5;y=(index//3)*76+28
        for label,offset in [('specialtyLarge',95),('specialtySmall',145)]:
            icon=heroes[hero]['images'][label]
            p=ROOT/'runeterra-ionia/assets/generated/Content/Sprites'/(icon+'.png')
            if p.exists():
                selected=Image.open(p).convert('RGBA')
                native_context.paste(selected,(x+offset,y+17),selected)
    native_context.save(REPORT/'native-contact.png')
    total=sum(p.stat().st_size for p in SOURCE.glob('*-master.png'))
    assert total <= 200*1024*1024
    write_json(REPORT/'native-checks.json',{'executed_native_cases':len(cases),'passed':len(cases),'cases':cases,'review_scope':'Technical replay/dimensions only. Producer visual observations recorded separately; no art acceptance.'})
    write_json(REPORT/'conversion.json',{'python':platform.python_version(),'pillow':pillow_version,'method':'Full square RGB master to square RGBA native size using LANCZOS; no crop, segmentation, repainting, threshold, sharpening, overlays or filters. Generated umber background retained.','assets':assets,'master_bytes':total,'heroes_sha256':digest(heroes_path),'native_or_release_run':False})
    write_json(REPORT/'closure.json',{'sha256':{str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in sorted([*SOURCE.glob('*'),*renders.glob('*.png'),REPORT/'native-contact.png',REPORT/'diagnostic-4x.png',REPORT/'native-checks.json',REPORT/'conversion.json']) if p.is_file()},'excluded_self':'closure.json cannot self-hash','status':'authored configuration','selected':False,'release_accepted':False})
    print(json.dumps({'native_cases':len(cases),'pass':len(cases),'master_bytes':total}))
if __name__ == '__main__':
    main()
