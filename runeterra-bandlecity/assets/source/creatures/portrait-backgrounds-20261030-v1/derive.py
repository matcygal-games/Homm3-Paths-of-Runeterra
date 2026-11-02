"""Reproduce native Bandle portrait composites from selected own painted sources."""
import hashlib, io, json, sys
from pathlib import Path
from PIL import Image, ImageDraw

W=next(p for p in Path(__file__).resolve().parents if (p/'runeterra-bandlecity').is_dir())
P=W/'runeterra-bandlecity'
R=W/'reports/bandle-creature-portrait-backgrounds-20261030-v1'
S=P/'assets/source/creatures/portrait-backgrounds-20261030-v1'
sys.path.insert(0,str(W/'scripts'))
import faction_art_compile as fa

def sha(data): return hashlib.sha256(data).hexdigest()
def enc(obj): return (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def png(im):
    b=io.BytesIO(); im.save(b,format='PNG',compress_level=9); return b.getvalue()
def emit(path,data): path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
def original_raster(recipe):
    payload,record=fa.raster_bytes(P,recipe)
    return payload

def main():
    S.mkdir(parents=True,exist_ok=True)
    creatures=json.loads((P/'content/creatures.json').read_text(encoding='utf-8'))
    backdrop=P/'assets/source/town/approved-BC1-completion-20261030-v1/background-v7.png'
    bg=Image.open(backdrop).convert('RGBA')
    units=list(creatures)
    # A native-scale canopy/blue-hills crop supplies broad quiet shapes behind
    # the subject rather than shrinking a whole busy town into each card.
    crops=[[38,0,96,64]]
    records=[]; board=Image.new('RGB',(760,((len(units)+1)//2)*155),(38,41,44)); draw=ImageDraw.Draw(board)
    for i,unit in enumerate(units):
        rp=P/f'assets/recipes/creatures/{unit}-large.json'
        old_path=S/'recipe-before'/rp.name
        if not old_path.exists(): emit(old_path,rp.read_bytes())
        old=json.loads(old_path.read_text(encoding='utf-8'))
        oldbytes=original_raster(old)
        foreground=Image.open(io.BytesIO(oldbytes)).convert('RGBA')
        assert foreground.size==(58,64)
        original_path=S/unit/'foreground.png'; emit(original_path,oldbytes)
        crop=crops[(i//2)%len(crops)]
        background=bg.crop(crop).resize((58,64),Image.Resampling.LANCZOS)
        assert background.getextrema()[3]==(255,255)
        final=background.copy(); final.alpha_composite(foreground)
        out=S/unit/'large.png'; emit(out,png(final))
        bg_path=S/unit/'background.png'; emit(bg_path,png(background))
        recipe=json.loads(json.dumps(old)); recipe.update({'source':out.relative_to(P).as_posix(),'source_sha256':sha(out.read_bytes()),'source_canvas':[58,64],'size':[58,64],'fit':'exact','require_alpha':False})
        recipe.pop('canvas',None); recipe.pop('sha256',None); recipe.pop('crop',None); recipe.pop('crop_sha256',None); recipe.pop('background',None); recipe.pop('content_box',None)
        recipe.setdefault('generation',{}).update({'portrait_background_method':'Deterministic opaque native scenic portrait; selected foreground preserved over crop of existing approved own painted Bandle town background. Native small icons remain unchanged.','portrait_derivation':'assets/source/creatures/portrait-backgrounds-20261030-v1/derivation.json','portrait_background_source':backdrop.relative_to(P).as_posix(),'portrait_background_source_sha256':sha(backdrop.read_bytes()),'portrait_foreground_source':old['source'],'portrait_foreground_source_sha256':old['source_sha256']})
        candidate=R/'candidate-recipes'/rp.name; emit(candidate,enc(recipe))
        records.append({'unit':unit,'recipe':rp.relative_to(P).as_posix(),'old_recipe':old_path.relative_to(P).as_posix(),'old_recipe_sha256':sha(old_path.read_bytes()),'foreground':original_path.relative_to(P).as_posix(),'foreground_sha256':sha(oldbytes),'background_source':backdrop.relative_to(P).as_posix(),'background_source_sha256':sha(backdrop.read_bytes()),'crop':crop,'background':bg_path.relative_to(P).as_posix(),'background_sha256':sha(bg_path.read_bytes()),'source':out.relative_to(P).as_posix(),'source_sha256':sha(out.read_bytes()),'candidate_recipe_sha256':sha(candidate.read_bytes())})
        x=(i%2)*380; y=(i//2)*155
        draw.text((x+5,y+4),unit+'  old / repaired',(235,235,235))
        board.paste(foreground,(x+5,y+26),foreground); board.paste(final,(x+70,y+26)); board.paste(final.resize((116,128),Image.Resampling.NEAREST),(x+140,y+24))
    emit(S/'derivation.json',enc({'status':'authored configuration','method':'Native scenic background assembly from existing painted source; no new artwork, original game pixels or 3D production.','producer':'assets/source/creatures/portrait-backgrounds-20261030-v1/derive.py','records':records}))
    emit(R/'before-after-native.png',png(board))
    emit(R/'index.html',b'<!doctype html><meta charset="utf-8"><title>Bandle creature portrait backgrounds</title><style>body{background:#24282b;color:#eee;font:16px system-ui;margin:28px}img{image-rendering:pixelated;max-width:100%}a{color:#bde}</style><h1>Bandle City creature portrait backgrounds</h1><p>Authored configuration. Old transparent card, repaired opaque scenic card and 2x native view. Small icons and all action images remain unchanged.</p><img src="before-after-native.png" alt="Fourteen old and repaired creature portraits"><p><a href="REPORT.md">Report</a></p>')
    print(json.dumps({'units':len(records),'source':str(S),'gallery':str(R/'index.html')}))
if __name__=='__main__': main()
