"""Reproduce native opaque cards from pinned selected own painted inputs."""
from pathlib import Path
import hashlib, json
from PIL import Image

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    selection=json.loads((HERE/'selection.json').read_text(encoding='utf-8'))
    descriptor=selection['background'];background=PROJECT/descriptor['path']
    if sha(background)!=descriptor['sha256']:raise ValueError('Painted background changed')
    scene=Image.open(background).convert('RGBA').crop(descriptor['crop']).resize((58,64),Image.Resampling.LANCZOS)
    scene.save(HERE/'scenic-background.png',compress_level=9)
    if sha(HERE/'scenic-background.png')!=selection['native_background']['sha256']:
        raise ValueError('Native background changed')
    for row in selection['portraits']:
        figure=PROJECT/row['figure']['path']
        if sha(figure)!=row['figure']['sha256']:raise ValueError('Selected unit source changed')
        card=scene.copy();card.alpha_composite(Image.open(figure).convert('RGBA'))
        target=PROJECT/row['source'];target.parent.mkdir(parents=True,exist_ok=True)
        card.save(target,compress_level=9)
        if sha(target)!=row['sha256']:raise ValueError('Derived native portrait changed')
    print(json.dumps({'portraits':len(selection['portraits']),'exact_pins':True}))

if __name__=='__main__':main()
