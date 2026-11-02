"""Original deterministic PCM hextech effects; no sampled or licensed input audio.

Usage: python synthesize.py <unit> <stomper|skimmer|thex> <base|upgrade>
Writes versioned source masters beside this producer. Listening/native playback
approval is deliberately separate from synthesis and structural validation.
"""
from pathlib import Path
import hashlib,json,math,sys,wave
import numpy as np

RATE=48000
ROOT=Path(__file__).resolve().parent
ROLES={'attack':.85,'defend':.60,'killed':1.25,'move':.85,'wince':.38,'shoot':1.05}

def make(kind,role,upgrade):
    duration=ROLES[role]+(.22 if kind=='thex' else 0)
    t=np.arange(round(duration*RATE),dtype=np.float64)/RATE
    seed=int(hashlib.sha256((kind+'/'+role+'/'+str(upgrade)).encode()).hexdigest()[:8],16)
    rng=np.random.default_rng(seed)
    noise=rng.uniform(-1,1,len(t))
    # Cascaded smoothing supplies a restrained low metallic/noise body.
    low=np.convolve(noise,np.ones(41)/41,mode='same')
    base={'stomper':110.,'skimmer':175.,'thex':64.}[kind]*(.83 if upgrade else 1)
    ramp=np.minimum(t/.012,1)*np.minimum((duration-t)/.055,1)
    if role=='shoot':
        charge=np.sin(2*math.pi*(260*t+1400*t*t))*np.minimum(t/.14,1)*np.exp(-t/.16)
        q=np.maximum(t-.14,0);fired=t>=.14
        blast=(.5*np.sin(2*math.pi*(70*q+100*.03*(1-np.exp(-q/.03))))+.35*low*3+.20*np.sin(2*math.pi*(1400*q-600*q*q)))*np.exp(-q/.20)
        out=.22*charge+fired*blast
    elif role=='attack':
        sweep=2*math.pi*(base*t+190*.04*(1-np.exp(-t/.04)))
        body=np.sin(sweep)*np.exp(-t/ .22)
        arc=np.sin(2*math.pi*(880*t-280*t*t))*np.exp(-t/.16)
        impact=noise*np.exp(-t/.035)+low*4*np.exp(-t/.24)
        out=.55*body+.15*arc+.30*impact
    elif role=='defend':
        out=(.43*np.sin(2*math.pi*base*t)+.26*np.sin(2*math.pi*base*2.01*t)+.13*np.sin(2*math.pi*base*3.97*t))*np.exp(-t/.20)+.13*noise*np.exp(-t/.018)
    elif role=='killed':
        phase=2*math.pi*(base*2.4*t-base*.65*t*t/duration)
        out=(.42*np.sin(phase)+.19*np.sin(phase*1.49)+.7*low)*np.exp(-t/.40)
        out+=.10*np.sin(2*math.pi*(1200*t-440*t*t))*np.exp(-t/.18)
    elif role=='move':
        if kind=='skimmer':
            out=(.38*np.sin(2*math.pi*base*t)+.15*np.sin(2*math.pi*base*2.02*t)+low)*(.65+.35*np.sin(2*math.pi*4*t)**2)
        else:
            out=np.zeros(len(t))
            for start in (.05,.43):
                q=np.maximum(t-start,0);mask=t>=start
                out+=mask*(.55*np.sin(2*math.pi*(base*.65*q+base*.08*(1-np.exp(-q/.035))))*np.exp(-q/.10)+low*2.3*np.exp(-q/.07))
            out+=.09*np.sin(2*math.pi*base*3*t)*(np.sin(2*math.pi*2*t)**2)
    else:
        out=(.45*np.sin(2*math.pi*(base*2*t+90*t*t))+.16*noise)*np.exp(-t/.09)
    out*=np.clip(ramp,0,1)
    # Fixed peak ceiling leaves headroom for VCMI's ordinary mixer.
    peak=float(np.max(np.abs(out)))
    if peak:out*=.68/peak
    samples=np.round(out*32767).astype('<i2')
    return samples

def run():
    unit,kind,variant=sys.argv[1:]
    if not unit.isalnum() or kind not in ('stomper','skimmer','thex') or variant not in ('base','upgrade'):
        raise ValueError('Explicit safe unit/kind/variant required')
    folder=ROOT/unit;folder.mkdir(exist_ok=True)
    records={}
    for role in ROLES:
        if role=='shoot' and not (kind=='thex' and variant=='upgrade'):continue
        path=folder/(role+'.wav')
        if path.exists():raise ValueError('Refuse to overwrite an existing source master: '+str(path))
        samples=make(kind,role,variant=='upgrade')
        with wave.open(str(path),'wb') as output:
            output.setnchannels(1);output.setsampwidth(2);output.setframerate(RATE);output.writeframes(samples.tobytes())
        records[role]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'samples':len(samples),'sample_rate':RATE,'channels':1,'bits':16,'peak':float(np.max(np.abs(samples.astype(float))))/32767}
    (folder/'source-record.json').write_text(json.dumps({'unit':unit,'kind':kind,'variant':variant,'method':'Original deterministic oscillators, filtered pseudorandom noise and envelopes; no samples or external audio','producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'status':'authored configuration','audible_approval':False,'files':records},indent=2)+'\n')
    print(json.dumps({'unit':unit,'masters':len(records)}))

if __name__=='__main__':run()
