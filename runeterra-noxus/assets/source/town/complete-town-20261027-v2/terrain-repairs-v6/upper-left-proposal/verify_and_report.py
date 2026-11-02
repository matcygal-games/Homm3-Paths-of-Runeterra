"""Executed preservation and native comparison evidence for an isolated proposal."""
from pathlib import Path
import hashlib,json,subprocess,sys,argparse
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent
TOWN=HERE.parents[1];ROOT=TOWN.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2/terrain-repairs-v6/upper-left-proposal'
BOX=(0,104,398,178)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',type=int,choices=(4,5),default=5);v=ap.parse_args().version
    source=TOWN/'terrain/final-native-v5.png';s=json.loads((TOWN/'candidate-final-v5/selection.json').read_text())
    assert sha(source)=='d068f192b852110ee774592541855527e91904027b38f3733fe93eaf4f126017'
    bg=Image.open(source).convert('RGB');proposal=Image.open(HERE/f'terrain-recomposed-v{v}.png').convert('RGB')
    d=ImageChops.difference(bg,proposal)
    outside=d.copy();ImageDraw.Draw(outside).rectangle((BOX[0],BOX[1],BOX[2]-1,BOX[3]-1),fill=(0,0,0))
    assert outside.getbbox() is None
    patch=Image.open(HERE/f'patch-native-v{v}.png').convert('RGBA');assert patch.getchannel('A').getextrema()==(255,255)
    layers=[];masters=[]
    for state in s['states']:
        layer=ROOT/state['native_layer'];master=ROOT/state['master']
        assert sha(layer)==state['native_layer_sha256'];assert sha(master)==state['master_sha256']
        layers.append(ref(layer));masters.append(ref(master))
    before=sha(HERE/f'terrain-recomposed-v{v}.png')
    subprocess.run([sys.executable,str(HERE/'compose_proposal.py'),'--version',str(v)],check=True,capture_output=True)
    assert sha(HERE/f'terrain-recomposed-v{v}.png')==before
    original=ROOT/'build/reports/complete-town-20261027-v2/final-v3/extracted-original-castle-source-assembly.png'
    original_im=Image.open(original).convert('RGB');assert original_im.size==(800,374)
    board=Image.new('RGB',(1600,394),(16,16,16));board.paste(original_im,(0,20));board.paste(Image.open(REPORT/f'full-native-v{v}.png').convert('RGB'),(800,20))
    draw=ImageDraw.Draw(board);draw.text((3,3),'Actual extracted original HoMM3 Castle source assembly; no runtime claim',fill='white');draw.text((803,3),f'Noxus isolated painted upper-left proposal V{v}; no runtime acceptance',fill='white');board.save(REPORT/f'actual-original-native-comparison-v{v}.png')
    attempts=[]
    for version,name in [(1,'generated-master-v1.png'),(2,'generated-master-v2.png'),(3,'college-right-master-v3.png'),(4,'college-material-master-v4.png'),(5,'academy-left-master-v5.png')][:v]:
        attempts.append({'version':version,'master':ref(HERE/name),'prompt':ref(HERE/f'prompt-v{version}.txt'),'provider':'OpenAI built-in image_gen','model':'Not exposed by built-in tool','status':'rejected for integration' if version==1 else ('superseded by V4' if version in (2,3) else 'design proposal')})
    provenance={'status':'design proposal','tool':'OpenAI built-in image_gen','generated_masters':attempts,'base':ref(source),'original_rendering_control':ref(original),'composition_script':ref(HERE/'compose_proposal.py'),'patch':ref(HERE/f'patch-native-v{v}.png'),'full_recomposition':ref(HERE/f'terrain-recomposed-v{v}.png'),'native_patch_box':BOX,'native_patch_alpha_extrema':patch.getchannel('A').getextrema(),'outside_patch_pixel_difference_bbox':outside.getbbox(),'unchanged_native_layers':layers,'unchanged_painted_building_masters':masters,'deterministic_repeat_sha256':before,'actual_checks':{'base_hash_pin':True,'all_pixels_outside_rectangle_exact':True,'all36_layer_pins_exact':len(layers)==36,'all36_painted_master_pins_exact':len(masters)==36,'repeat_conversion_identical':True,'opaque_native_patch':True,'native800x374_original_comparison_saved':True},'incomplete':['Independent final floor/root/route tracing and artist review','Coordinator integration into a final combined terrain candidate','Current-build native town construction/click/runtime observations','External visual/rights release acceptance'],'geometry_pass_claimed':False,'runtime_verified':False,'release_accepted':False}
    (HERE/f'provenance-v{v}.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (REPORT/f'preservation-checks-v{v}.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'checks':provenance['actual_checks'],'terrain_sha256':before,'patch_sha256':sha(HERE/f'patch-native-v{v}.png')}))
if __name__=='__main__':main()
