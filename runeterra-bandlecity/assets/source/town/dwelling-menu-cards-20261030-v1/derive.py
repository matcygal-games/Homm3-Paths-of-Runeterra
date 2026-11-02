from pathlib import Path
import hashlib, io, json
from PIL import Image
S=Path(__file__).resolve().parent
P=S.parents[3]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=json.loads((S/'plan.json').read_text())
    bgp=P/plan['background']['path']
    if sha(bgp)!=plan['background']['sha256']: raise ValueError('Background pin changed')
    with Image.open(bgp) as opened: bg=opened.convert('RGBA').crop(tuple(plan['crop'])).resize((150,70),Image.Resampling.LANCZOS)
    # Own painted background is opaque; output-native alpha cannot reveal the hall backdrop.
    bg.putalpha(255)
    for row in plan['cards']:
        src=P/row['source']
        if sha(src)!=row['source_sha256']: raise ValueError('Building source pin changed')
        with Image.open(src) as opened: front=opened.convert('RGBA')
        if front.size!=(150,70): raise ValueError('Native building frame changed')
        result=Image.alpha_composite(bg,front)
        result.putalpha(255)
        out=S/row['target']; out.parent.mkdir(parents=True,exist_ok=True)
        result.save(out,format='PNG',compress_level=9)
if __name__=='__main__': main()
