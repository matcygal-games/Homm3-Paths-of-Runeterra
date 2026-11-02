"""Copy selected genuine provider outputs into versioned own source closure."""
from pathlib import Path
import hashlib,json,re,shutil
from PIL import Image,ImageOps,ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 records=[]
 for path in sorted(HERE.glob('generation-records-batch-*.json')):records.extend(json.loads(path.read_text()))
 states=[]
 for row in records:
  source=Path(re.search(r' as (C:.*?\.png) by default',row['hint']).group(1))
  folder=HERE/('terrain' if row['state']=='empty-terrain' else 'state-art/'+row['state']);folder.mkdir(parents=True,exist_ok=True)
  destination=folder/'master.png'
  if not destination.exists():shutil.copy2(source,destination)
  elif sha(destination)!=sha(source):raise ValueError('Preserved provider master changed '+row['state'])
  (folder/'prompt.txt').write_text(row['prompt'],encoding='utf-8')
  meta={**row,'master_sha256':sha(destination),'status':'authored configuration','tool':'OpenAI built-in image_gen','native_verified':False,'release_accepted':False}
  (folder/'generation.json').write_text(json.dumps(meta,indent=2)+'\n')
  if row['state']!='empty-terrain':states.append(row['state'])
 columns=4;cell=(280,245);board=Image.new('RGB',(columns*cell[0],((len(states)+columns-1)//columns)*cell[1]),(45,37,35));draw=ImageDraw.Draw(board)
 for i,state in enumerate(states):
  im=Image.open(HERE/'state-art'/state/'master.png').convert('RGBA');alpha=im.getchannel('A');bb=alpha.point(lambda v:255 if v>=8 else 0).getbbox()
  if not bb:raise ValueError('Empty source '+state)
  im=ImageOps.contain(im.crop(bb),(268,215),Image.Resampling.LANCZOS);x=(i%columns)*cell[0]+(cell[0]-im.width)//2;y=(i//columns)*cell[1]+6;board.paste(im,(x,y),im)
  draw.text(((i%columns)*cell[0]+8,(i//columns)*cell[1]+224),state,fill=(245,224,200))
 board.save(REPORT/'all-new-state-provider-review.png')
 (REPORT/'provider-sources.json').write_text(json.dumps({'status':'authored configuration','copied':len(records),'all_transparent_requested':True,'new_state_masters':states,'source_pins':{row['state']:sha(HERE/('terrain' if row['state']=='empty-terrain' else 'state-art/'+row['state'])/'master.png') for row in records},'native_verified':False},indent=2)+'\n')
 print(json.dumps({'provider_outputs_preserved':len(records),'new_state_masters':len(states)}))
if __name__=='__main__':main()
