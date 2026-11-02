"""Technical whole-canvas contact sheet of the already painted complete gait."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
from pose_tools import S,P,W,R,sha,png,enc,put,rel
def run():
 receipt=S/'kashuriArmsbearer/gait-candidate-v1/gait-registration-v1.json';rows=json.loads(receipt.read_text())['records'];out=Image.new('RGBA',(1800,810));draw=ImageDraw.Draw(out);deps=[{'path':rel(receipt),'sha256':sha(receipt)},{'path':rel(Path(__file__)),'sha256':sha(Path(__file__))}]
 for row in rows:
  p=P/row['native'];im=Image.open(p).convert('RGBA').crop((105,150,305,285));im=im.resize((600,405),Image.Resampling.NEAREST);f=row['frame'];out.alpha_composite(im,((f%3)*600,(f//3)*405));draw.text(((f%3)*600+4,(f//3)*405+4),f'Painted phase{f}: '+row['intended_contact'],fill='white');deps.append({'path':rel(p),'sha256':sha(p)})
 target=S/'reference-inputs/base-walk-native-guide-v1.png';png(target,out);put(target.with_suffix('.json'),enc({'status':'authored configuration','source_whole_canvas_crop':[105,150,305,285],'reference_display_scale':3,'resampling':'NEAREST','no_perframe_body_fit_warp_or_flip':True,'painted_source_only':True,'image':rel(target),'image_sha256':sha(target),'dependencies':deps,'runtime_verified':False,'release_accepted':False}));print('Wholepaintedgait reference prepared')
if __name__=='__main__':run()
