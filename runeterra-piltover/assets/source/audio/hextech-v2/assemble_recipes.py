"""Bind original PCM masters to scoped audio-copy recipes, without editing content."""
from pathlib import Path
import hashlib,json,wave

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-piltover')
UNITS=('armoredStomper','prismaticStomper','hextechRotorwing','hextechStormwing','hextechRampager','hextechDreadnought')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(p):return p.relative_to(PROJECT).as_posix()

def main():
    out=HERE/'candidate-recipes-v1';out.mkdir(exist_ok=True)
    records=[]
    for unit in UNITS:
        record=HERE/unit/'source-record.json'
        data=json.loads(record.read_text())
        if data['producer_sha256']!=sha(HERE/'synthesize.py'):raise ValueError('Producer changed since synthesis')
        for role,meta in data['files'].items():
            source=HERE/unit/(role+'.wav')
            if sha(source)!=meta['sha256']:raise ValueError('Audio source changed')
            with wave.open(str(source),'rb') as w:
                if w.getparams()[:4]!=(1,2,48000,meta['samples']) or w.getcomptype()!='NONE':raise ValueError('PCM format mismatch')
            output=f'Content/Sounds/runeterra/piltover/creatures/{unit}/{role}.wav'
            recipe={'recipe_type':'pcm_wav_copy','production_status':'audio-master-complete-unapproved',
                'source':relative(source),'source_sha256':sha(source),'output_path':output,
                'generation':{'image_generation_used':False,'method':'Original deterministic oscillators, filtered pseudorandom noise and envelopes; no sampled, licensed or external audio. Source authoring is separate from audible/native approval.'},
                'production_inputs':[{'path':relative(p),'sha256':sha(p)} for p in (HERE/'synthesize.py',HERE/'assemble_recipes.py',record)]}
            path=out/(unit+'-'+role+'.json')
            encoded=(json.dumps(recipe,indent=2,sort_keys=True)+'\n').encode()
            if path.exists() and path.read_bytes()!=encoded:raise ValueError('Refuse to replace changed candidate')
            path.write_bytes(encoded)
            records.append({'path':relative(path),'sha256':sha(path),'output_path':output})
    summary={'status':'authored configuration','recipes':records,'image_generation_used':False,'audible_approval':False,'runtime_verified':False,'release_accepted':False}
    (HERE/'candidate-selection-v1.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'recipes':len(records),'selected':False}))

if __name__=='__main__':main()
