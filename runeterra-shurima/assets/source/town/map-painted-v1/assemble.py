"""Technical registration of genuine painted map objects; never paints artwork."""
from pathlib import Path
from io import BytesIO
import hashlib, json, sys
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
WORKSPACE = PROJECT.parent
REPORT = PROJECT / 'build/reports/town-map-painted-20261024-v1'
sys.path.insert(0, str(WORKSPACE / 'scripts'))
from faction_art_compile import create_compiler
compiler = create_compiler('shurima')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
def relative(path): return path.relative_to(PROJECT).as_posix()

# Authored stair/visit landmarks. Static-object registration, not opaque-bbox fit.
# Every source and old version is preserved. Native visual acceptance stays open.
STATES = [('village', 2, .14, (770, 1120)), ('fort', 1, .14, (770, 1120)),
          ('citadel', 1, .14, (770, 1140)), ('castle', 1, .13, (750, 1170)),
          ('capitol', 1, .12, (790, 1220))]
records, outputs = [], {}
board = Image.new('RGB', (5 * 192, 222), (56, 49, 42))
draw = ImageDraw.Draw(board)
for column, (state, version, scale, contact) in enumerate(STATES):
    master = HERE / f'{state}-master-v{version}.png'
    provenance = HERE / f'{state}-generation-v{version}.json'
    generation = json.loads(provenance.read_text())
    with Image.open(master) as image:
        image.load()
        assert image.mode == 'RGBA' and image.size == (1254, 1254)
        # Built-in output is1254-square, independently measured. Apply the SAME
        # whole-canvas logical1280 calibration to every state; never fit alpha.
        factor = image.width / 1280
        matrix = tuple(v * factor for v in
                       (1/scale, 0, contact[0]-110/scale, 0, 1/scale, contact[1]-177/scale))
        frame = image.transform((192,192), Image.Transform.AFFINE, matrix, Image.Resampling.BICUBIC)
        # A larger technical canvas independently checks that visible alpha is not clipped.
        expanded_matrix = tuple(v * factor for v in
                                (1/scale,0,contact[0]-142/scale,0,1/scale,contact[1]-209/scale))
        expanded = image.transform((256,256),Image.Transform.AFFINE,expanded_matrix,Image.Resampling.BICUBIC)
        outside = expanded.copy(); outside.paste((0,0,0,0), (32,32,224,224))
        assert outside.getchannel('A').getextrema()[1] <= 4, (state, 'visible source clipped')
        target = HERE / 'native' / f'{state}-000.png'
        target.parent.mkdir(exist_ok=True)
        frame.save(target)
        board.paste(frame, (column*192, 24), frame)
        draw.text((column*192+6, 5), state + ' - unapproved', fill='white')
    recipe = {'recipe_type':'vcmi_animation','production_status':'painted-master-complete-unapproved',
        'status':'authored configuration','role':'town-adventure-animation',
        'output_path':f'Content/Sprites/runeterra/shurima/town/map/{state}.json',
        'canvas':[192,192], 'pivot':{'x':110,'y':177}, 'generateOverlay':0,'generateShadow':0,
        'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen',
            'model':'not exposed by built-in tool','prompt':generation['prompt'],
            'painted_master':relative(master),'painted_master_sha256':sha(master),
            'provenance':relative(provenance),'producer':relative(Path(__file__)),
            'method':'Fixed authored stair-anchor registration and uniform state scale; no artistic pixel repaint.'},
        'groups':[{'group':0,'frames':[{'source':relative(target),'source_canvas':[192,192],
            'source_sha256':sha(target)}]}],
        'credits':{'author':'Project-directed built-in imagegen; technical2D registration',
            'license':None,'redistribution':'unresolved; release prohibited'},
        'visual_approval_granted':False,'acceptance':'Native map scale/visit/flags and state progression pending.'}
    path = PROJECT / 'assets/recipes/town/map-painted-v1' / (state+'.json')
    write(path, recipe)
    first, receipt = compiler.plan(PROJECT, path)
    second, _ = compiler.plan(PROJECT, path)
    assert first == second and len(first) == 2
    for name, data in first.items():
        assert name not in outputs
        outputs[name] = hashlib.sha256(data).hexdigest()
        destination = REPORT / 'compiled' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    decoded = Image.open(BytesIO(first[next(name for name in first if name.endswith('.png'))]))
    assert decoded.convert('RGBA').tobytes() == frame.tobytes()
    records.append({'state':state,'source':relative(master),'source_sha256':sha(master),
        'recipe':relative(path),'recipe_sha256':sha(path),'scale':scale,
        'authored_source_stair_contact':list(contact),'native_visit_contact':[110,177],
        'source_canvas':[1254,1254],'logical_registration_canvas':[1280,1280],
        'native_canvas':[192,192],
        'outside_alpha_max':outside.getchannel('A').getextrema()[1],
        'repeat_compile_byte_exact':True,'native_png_pixel_exact':True})
board.save(REPORT / 'states-native-1x.png')
write(HERE/'registration.json',{'states':records,'native_visual_acceptance':'pending',
    'scale_caveat':'Static-state authored registration; door scale and progression require pixel/game review.',
    'original_references':'Private original Castle192x192 resources measured in report, excluded from release.'})
write(REPORT/'conversion.json',{'status':'authored configuration','required_outputs':5,
    'expanded_files':len(outputs),'output_sha256':outputs,'states':records,
    'native_execution':False,'release_accepted':False,'visual_approval_granted':False})
print(json.dumps({'compiled_states':len(records),'expanded_files':len(outputs)}))
