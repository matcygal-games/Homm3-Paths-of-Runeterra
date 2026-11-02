"""Resumable painted 2D bridgehead/fort candidate. No canonical writes."""
from pathlib import Path
import hashlib,io,json
import numpy as np
from PIL import Image,ImageChops,ImageDraw,ImageFilter

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
WORKSPACE=PROJECT.parent
PREVIOUS=PROJECT/'assets/source/town/approved-BC1-completion-20261030-v1'
REPORT=WORKSPACE/'reports/bandle-bulwark-site-repair-20261030-v1'
OUT=SOURCE/'states-v3'
ROI=(212,54,307,119)
GATE_DOOR=(270,75)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def png(image):
    output=io.BytesIO();image.save(output,format='PNG');return output.getvalue()
def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=raw:raise ValueError('Candidate differs '+str(path))
    if not path.exists():path.write_bytes(raw)
def clean(image):
    a=np.array(image.convert('RGBA'));alpha=a[:,:,3]
    alpha[alpha<=16]=0;alpha[alpha>=192]=255
    a[:,:,3]=alpha;a[alpha==0,:3]=0
    return Image.fromarray(a)
def registered(raw,box,door,size):
    cell=clean(raw.crop(box));bounds=cell.getbbox();assert bounds
    crop=cell.crop(bounds);scale=min(size[0]/crop.width,size[1]/crop.height)
    art=clean(crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS))
    root=((door[0]-box[0]-bounds[0])*scale,(door[1]-box[1]-bounds[1])*scale)
    at=(round(GATE_DOOR[0]-root[0]),round(GATE_DOOR[1]-root[1]))
    layer=Image.new('RGBA',(800,374));layer.alpha_composite(art,at)
    assert layer.getchannel('A').getbbox()[0]>=239
    return layer,{'sheet_box':list(box),'alpha_bounds':list(bounds),'source_door':list(door),
                  'scale':scale,'target_door':list(GATE_DOOR),'location':list(at),'size':list(art.size)}

def main():
    bgpath=PREVIOUS/'background-v7.png';base=Image.open(bgpath).convert('RGBA')
    provider=Image.open(SOURCE/'background-provider-v1.png').convert('RGBA').resize((800,374),Image.Resampling.LANCZOS)
    mask=Image.new('L',(800,374));ImageDraw.Draw(mask).polygon([(222,62),(242,60),(297,62),(301,77),(298,101),(276,110),(237,111),(216,103),(216,80)],fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(2));limit=Image.new('L',(800,374));ImageDraw.Draw(limit).rectangle((ROI[0],ROI[1],ROI[2]-1,ROI[3]-1),fill=255);mask=ImageChops.multiply(mask,limit)
    background=Image.composite(provider,base,mask)
    put(OUT/'background.png',png(background));put(OUT/'background-change-mask.png',png(mask))
    raw=Image.open(PREVIOUS/'civic-states-v1.png').convert('RGBA')
    castle=Image.open(SOURCE/'castle-provider-v1.png').convert('RGBA')
    data=[('fort',raw,(1180,0,1536,500),(1336,460),(46,60)),
          ('citadel',raw,(0,500,455,1024),(232,947),(54,65)),
          ('castle',castle,(0,0,castle.width,castle.height),(616,1230),(58,74))]
    records={}
    for state,master,box,door,size in data:
        layer,record=registered(master,box,door,size)
        area_mask=layer.getchannel('A').point(lambda a:255 if a>=128 else 0)
        area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(area_mask)
        ring=ImageChops.subtract(area_mask.filter(ImageFilter.MaxFilter(5)),area_mask)
        border=Image.new('RGBA',(800,374),(255,223,96,0));border.putalpha(ring)
        crop=layer.crop(layer.getbbox());crop.thumbnail((58,64),Image.Resampling.LANCZOS)
        campaign=Image.new('RGBA',(58,64));campaign.alpha_composite(crop,((58-crop.width)//2,(64-crop.height)//2))
        # Scene-backed construction card, centered on this same distant gate plot.
        scene=background.copy();scene.alpha_composite(layer)
        # A 150:70 field of view retains the same building proportions.
        hall=scene.crop((195,8,345,78))
        for role,im in [('layer',layer),('area',area),('border',border),('campaign',campaign),('hall',hall)]:put(OUT/state/(role+'.png'),png(im))
        records[state]={**record,'bounds':list(layer.getbbox()),'native_z':80,
                        'outputs':{role:sha(OUT/state/(role+'.png')) for role in ('layer','area','border','campaign','hall')}}
    diff=ImageChops.difference(base,background)
    opaque_diff=Image.fromarray(np.where(np.any(np.array(base)!=np.array(background),axis=2),255,0).astype('uint8'))
    bounds=opaque_diff.getbbox();assert bounds and bounds[0]>=ROI[0] and bounds[1]>=ROI[1] and bounds[2]<=ROI[2] and bounds[3]<=ROI[3]
    receipt={'status':'authored configuration','selected':False,'roi':list(ROI),'background_changed_pixels':opaque_diff.histogram()[255],
      'background_change_bounds':list(bounds),'door':list(GATE_DOOR),'states':records,
      'inputs':{p.relative_to(PROJECT).as_posix():sha(p) for p in (bgpath,PREVIOUS/'civic-states-v1.png',SOURCE/'background-provider-v1.png',SOURCE/'castle-provider-v1.png',Path(__file__))}}
    put(OUT/'derivation.json',encoded(receipt))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
