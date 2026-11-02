"""Technical crop of the new own Rampager portrait for Jayce's army specialty."""
from pathlib import Path
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent
P=next(p for p in HERE.parents if p.name=='runeterra-piltover')
MASTER='assets/source/creatures/painted-hextech-v2/hextechRampager/portrait-v1-master.png'
MASTER_SHA='fe1eef891f3a6018ff76356c76c8587ef68ff6c17fa05ba61e59abc35f5ad297'
CROP=[450,569,1196,1315]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    master=P/MASTER
    if sha(master)!=MASTER_SHA:raise ValueError('Rampager portrait master changed')
    out=HERE/'jayce';out.mkdir(exist_ok=True)
    with Image.open(master) as opened:
        im=opened.convert('RGBA')
    if im.size!=(1196,1315):raise ValueError('Measured portrait dimensions changed')
    records=[]
    for role,size in [('specialtyLarge',44),('specialtySmall',32)]:
        path=out/(role+'.png');image=im.crop(tuple(CROP)).resize((size,size),Image.Resampling.LANCZOS)
        image.save(path)
        recipe={'recipe_type':'raster','production_status':'painted-master-complete-unapproved','canvas':[size,size],
            'output_path':f'Content/Sprites/runeterra/piltover/heroes/jayce/{role}.png','source':path.relative_to(P).as_posix(),
            'source_sha256':sha(path),'source_canvas':[size,size],'fit':'exact',
            'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen inherited own Rampager portrait','model':'not exposed by tool',
                'prompt':'No new imagegen call. Fixed square head/horns crop from own original Hextech Rampager portrait, resized to native specialty size. Jayce army-engineering specialty is a gameplay adaptation, not personal invention or transformation.',
                'painted_master':MASTER,'painted_master_sha256':MASTER_SHA,'source_crop':CROP},
            'production_inputs':[{'path':MASTER,'sha256':MASTER_SHA},{'path':Path(__file__).relative_to(P).as_posix(),'sha256':sha(Path(__file__))}]}
        target=out/(role+'.recipe.json');target.write_text(json.dumps(recipe,indent=2)+'\n')
        records.append({'path':target.relative_to(P).as_posix(),'sha256':sha(target),'output_path':recipe['output_path']})
    (HERE/'candidate-selection-v1.json').write_text(json.dumps({'status':'authored configuration','recipes':records,'source_crop':CROP,'runtime_verified':False,'visual_approval_granted':False},indent=2)+'\n')
    print(json.dumps({'outputs':len(records),'new_image_generation':False}))
if __name__=='__main__':main()
