"""Explicit native masks for Demacia's already isolated architectural layers."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import town_hover_outlines as h
REPORT=Path(__file__).parent
PROJECT=ROOT/'runeterra-demacia'

def main():
    folder=REPORT/'masks-v1'
    if folder.exists():raise ValueError('Preserve earlier candidates')
    folder.mkdir()
    content=h.read(PROJECT/'content/factions.json')['demacia']['town']['structures']
    index=h.recipe_index(PROJECT);selections={};derivations={}
    for state,row in content.items():
        _,recipe=index['Content/Sprites/'+row['animation']]
        source=PROJECT/recipe['groups'][0]['frames'][0]['source']
        layer=h.load(source);mask=h.binary(layer.getchannel('A'))
        h.border_from_mask(mask)
        path=folder/(state+'.png');mask.save(path)
        selections['demacia/'+state]={'path':path.relative_to(ROOT).as_posix(),'sha256':h.digest(path),
            'method':'Exact native alpha128 architecture of an already isolated layer; subject geometry unchanged, finite visual review pending.'}
        derivations[state]={'source':{'path':source.relative_to(ROOT).as_posix(),'sha256':h.digest(source)},
            'mask':selections['demacia/'+state],'alpha_threshold':128,
            'geometry_modified':False,'manual_tracing_used':False}
    h.write(folder/'mask-selections.json',selections)
    h.write(REPORT/'derivations-v1.json',derivations)
    h.candidate(ROOT,REPORT/'candidate-v1',regions=('demacia',),mask_selections=selections)
    print(REPORT/'candidate-v1/index.html')

if __name__=='__main__':main()
