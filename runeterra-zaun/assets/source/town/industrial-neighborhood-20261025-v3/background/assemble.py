"""Technical resizing and two locally generated graffiti inserts; no drawn artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import json
HERE = Path(__file__).resolve().parent

def assemble():
    base = Image.open(HERE / 'raw-v2.png').convert('RGBA').resize((800,374),Image.Resampling.LANCZOS)
    paint = Image.open(HERE / 'raw-v3.png').convert('RGBA').resize((800,374),Image.Resampling.LANCZOS)
    for source, target in [((269,234,379,300),(304,239,338,261)), ((350,176,432,204),(375,176,405,191))]:
        x,y,r,b = target
        patch=paint.crop(source).resize((r-x,b-y),Image.Resampling.LANCZOS)
        mask=Image.new('L',patch.size,0)
        ImageDraw.Draw(mask).rectangle((2,2,patch.width-3,patch.height-3),fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(1.0))
        base.paste(patch,(x,y),mask)
    # Genuine painted dry quay edit, adopted only in bounded lower-right region.
    dry=Image.open(HERE / 'raw-v4.png').convert('RGBA').resize((800,374),Image.Resampling.LANCZOS)
    patchmask=Image.new('L',(800,374),0)
    ImageDraw.Draw(patchmask).rectangle((600,275,820,394),fill=255)
    patchmask=patchmask.filter(ImageFilter.GaussianBlur(5))
    base=Image.composite(dry,base,patchmask)
    # Restore genuinely painted water only inside the preplanned dock inlet.
    plan=json.loads((HERE.parent/'prepaint-plan-v4/placement-plan.json').read_text())
    water=Image.new('L',(800,374),0)
    ImageDraw.Draw(water).polygon([tuple(x) for x in plan['planned_inlet_polygon']],fill=255)
    original=Image.open(HERE / 'raw-v2.png').convert('RGBA').resize((800,374),Image.Resampling.LANCZOS)
    base=Image.composite(original,base,water)
    water.save(HERE / 'water-mask-v2.png')
    patchmask.save(HERE / 'quay-adoption-mask-v2.png')
    base.save(HERE / 'master-v2.png')

if __name__ == '__main__': assemble()
