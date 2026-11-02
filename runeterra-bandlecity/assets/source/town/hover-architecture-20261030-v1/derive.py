"""Reproduce Bandle-only technical outline candidates; never changes selected recipes."""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'scripts'))
import town_hover_outlines as h
BASE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve()
    if not out.is_relative_to(ROOT/'reports'):raise ValueError('Candidate output must be inside workspace reports')
    if out.exists(): raise ValueError('Use new output directory, preserve prior candidates')
    out.mkdir(parents=True)
    traces=json.loads((BASE/'traces.json').read_text())
    selections={}; originals={}
    for name,row in traces['states'].items():
        source=ROOT/row['source']['path']
        if h.digest(source)!=row['source']['sha256']:raise ValueError('Source changed '+name)
        image=h.load(source);alpha=h.binary(image.getchannel('A'))
        if row['points_native']:
            env=Image.new('L',h.SIZE);ImageDraw.Draw(env).polygon([tuple(p) for p in row['points_native']],fill=255)
            mask=ImageChops.multiply(env,alpha)
        else:mask=alpha
        path=out/(name+'-architecture.png');mask.save(path)
        selections['bandlecity/'+name]={'path':path.relative_to(ROOT).as_posix(),'sha256':h.digest(path)}
        originals[name]={'source_sha256':h.digest(source),'old_border_sha256':row['original_border']['sha256'],'removed_alpha_pixels':sum(1 for p in ImageChops.subtract(alpha,mask).getdata() if p),'mask_sha256':h.digest(path),'method':row['method']}
    h.write(out/'mask-selections.json',selections)
    report=h.candidate(ROOT,out/'gallery',('bandlecity',),selections)
    h.write(out/'receipt.json',{'status':'design proposal','producer_sha256':h.digest(__file__),'traces_sha256':h.digest(BASE/'traces.json'),'states':originals,'count':len(originals),'painting_mutations':0,'click_mutations':0,'selected_recipe_mutations':0,'runtime_observed':False})
    print(out)
if __name__=='__main__':main()
