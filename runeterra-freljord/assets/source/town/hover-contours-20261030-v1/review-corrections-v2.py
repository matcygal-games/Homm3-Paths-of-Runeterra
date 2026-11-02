"""Finite reviewer corrections: retain T5 rear roof planes and full timber pier."""
from pathlib import Path
import sys
from PIL import Image, ImageChops, ImageDraw
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import town_hover_outlines as h
REPORT=Path(__file__).parent

def main():
    traces=h.read(REPORT/'architecture-traces.json')
    for state in ('dwellingLvl5','dwellingUpLvl5'):
        points=traces[state]['polygons_local'][0]
        start=points.index([49,15])+1 if state=='dwellingLvl5' else points.index([46,11])+1
        end=points.index([111,42]) if state=='dwellingLvl5' else points.index([118,44])
        points[start:end]=[[54,14],[62,15],[70,16],[78,18],[86,20],[94,23],
                           [102,27],[109,30],[116,34],[120,37],[119,41]]
        traces[state]['review_revision']='Retain the actual attached upper-right shingled/snow roof; only sunset and snow scenery is excluded.'
    traces['shipyard']['polygons_local'][0]=[
        [1,28],[4,19],[7,13],[13,6],[16,2],[20,0],[24,4],[29,7],[32,12],
        [34,20],[39,21],[44,22],[52,22],[58,22],[63,23],[67,23],[67,29],
        [63,31],[60,32],[60,34],[51,35],[42,35],[33,32],[23,31],[11,30]]
    traces['shipyard']['review_revision']='Retain the full timber pier through the far-right post, excluding only water.'
    trace_path=REPORT/'architecture-traces-v2.json'
    if trace_path.exists():raise ValueError('Preserve historical revision')
    h.write(trace_path,traces)
    masks=REPORT/'masks-v2';masks.mkdir(exist_ok=False)
    selections={}
    for state,entry in traces.items():
        source=h.safe_input(ROOT,entry['source']['path'])
        if h.digest(source)!=entry['source']['sha256']:raise ValueError('Selected source changed')
        layer=h.load(source);box=layer.getchannel('A').getbbox()
        if list(box)!=entry['source_bbox']:raise ValueError('Source crop changed')
        mask=Image.new('L',h.SIZE);draw=ImageDraw.Draw(mask)
        for polygon in entry['polygons_local']:
            draw.polygon([(x+box[0],y+box[1]) for x,y in polygon],fill=255)
        mask=ImageChops.multiply(mask,h.binary(layer.getchannel('A')))
        h.border_from_mask(mask)
        path=masks/(state+'.png');mask.save(path)
        selections['freljord/'+state]={'path':path.relative_to(ROOT).as_posix(),'sha256':h.digest(path)}
    h.write(masks/'mask-selections.json',selections)
    result=h.candidate(ROOT,REPORT/'candidate-v2',regions=('freljord',),mask_selections=selections)
    h.write(REPORT/'reproduction-v2.json',{'status':'design proposal','source_mutations':0,
            'traces':{'path':trace_path.relative_to(ROOT).as_posix(),'sha256':h.digest(trace_path)},
            'producer':{'path':Path(__file__).resolve().relative_to(ROOT).as_posix(),'sha256':h.digest(__file__)},
            'states':len(result['states']),'masks':selections,'runtime_observed':False,'visual_approval_granted':False})

if __name__=='__main__':main()
