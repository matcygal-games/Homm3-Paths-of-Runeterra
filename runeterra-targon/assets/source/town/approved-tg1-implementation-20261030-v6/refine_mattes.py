"""Refine TG1 candidate architecture silhouettes; no canonical writes."""
import importlib.util
import json
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'approved-tg1-implementation-20261030-v5'
spec=importlib.util.spec_from_file_location('tg1_ownership',PREVIOUS/'finish_sources.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
PROJECT=core.PROJECT

def polygon(points):
    result=Image.new('L',(800,374));ImageDraw.Draw(result).polygon([tuple(p)for p in points],fill=255);return result

def main():
    source=core.read(PREVIOUS/'candidate-frames.json')
    contours=core.read(HERE.parent/'approved-tg1-implementation-20261030-v4/contours.json')
    layers={};union=Image.new('L',(800,374))
    for state,row in source['states'].items():
        key=row['site'];points=contours['state_outlines'].get(state,contours['sites'][key]['outline'])
        mask=polygon(points)
        if row['source_tag']=='approved':
            for points in contours.get('approved_additions',{}).get(key,[]):mask=ImageChops.lighter(mask,polygon(points))
        previous=core.image(PROJECT/row['frame']['path']);mask=ImageChops.multiply(mask,previous.getchannel('A'))
        previous.putalpha(mask);layers[state]=previous
        if state in source['complete_scene_states']:union=ImageChops.lighter(union,mask)
        core.save(HERE/'frames'/(state+'.png'),previous)
    approved=core.image(core.ORIGINAL/'approved-full-native.png')
    background=approved.copy();background.paste(core.image(core.ORIGINAL/'empty-recovery-native.png'),(0,0),union)
    replay=background.copy()
    for state in source['complete_scene_states']:replay.alpha_composite(layers[state])
    if replay.tobytes()!=approved.tobytes():raise ValueError('Full town changed')
    core.save(HERE/'background-native.png',background);core.save(HERE/'fully-built.png',replay)
    report=core.WORKSPACE/'reports/targon-tg1-implementation-20261030-v6';report.mkdir(parents=True,exist_ok=True)
    for key in contours['sites']:
        matching=[s for s,r in source['states'].items()if r['site']==key]
        canvas=Image.new('RGB',(400,160*len(matching)),(28,31,30));draw=ImageDraw.Draw(canvas)
        for n,state in enumerate(matching):
            im=layers[state];bg=Image.new('RGBA',im.size,(57,59,61,255));bg.alpha_composite(im)
            crop=bg.crop(im.getchannel('A').getbbox());crop.thumbnail((390,130),Image.Resampling.NEAREST)
            canvas.paste(crop.convert('RGB'),((400-crop.width)//2,n*160+24));draw.text((5,n*160+5),state,fill='white')
        core.save(report/(key+'-states.png'),canvas)
    print(json.dumps({'states':len(layers),'full_RGBA_changes':0,'status':'authored configuration','physical_pass':False}))

if __name__=='__main__':main()
