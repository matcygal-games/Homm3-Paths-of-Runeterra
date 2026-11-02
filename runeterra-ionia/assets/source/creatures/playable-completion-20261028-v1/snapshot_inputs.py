"""Explicit authoring snapshot for this versioned candidate only."""
from pathlib import Path
import hashlib,json
S=Path(__file__).resolve().parent;P=S.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=['ionianDisciple','enlightenedWarrior','kinkouInitiate','kinkouAdept','kashuriArmsbearer','kashuriMarksman','resistanceBlade','resistanceVeteran']
files=[S/'death-ground-registration.json',S/'public-source-lineage.json',S/'REPRODUCE.txt']
files += [P/e['public_source']for e in json.loads((S/'public-source-lineage.json').read_text())['sources']]
for n in names:
    files.extend([S/n/('motion-v2-prompt.txt'if n=='resistanceVeteran'else'motion-prompt.txt'),S/n/('combat-v2-prompt.txt'if n=='ionianDisciple'else'combat-prompt.txt'),S/n/'near-walk-prompt.txt',S/n/'far-walk-prompt.txt',S/n/('adventure-v3-prompt.txt'if n=='enlightenedWarrior'else('adventure-v2-prompt.txt'if n=='resistanceVeteran'else'adventure-prompt.txt'))])
files.extend([S/'projectile/prompt.txt',S/'resistanceVeteran/motion-prompt.txt',S/'resistanceVeteran/adventure-prompt.txt'])
old=P/'assets/source/creatures/painted-20261025-revision-v1'
files+=list((old/'t3/candidates').glob('*.json'))+list((old/'t5-t7/recipes-v2').glob('*.json'))
for n,v in [('resistanceBlade','v1'),('resistanceVeteran','v2')]:
    files.append(old/'t6'/n/f'identity-prompt-{v}.txt')
files.extend([P/'assets/source/town/landscape-v2/master.png',P/'assets/source/town/landscape-v2/prompt.txt',P/'assets/source/town/landscape-v1/master.png',P/'assets/source/town/landscape-v1/prompt.txt',old/'t5-t7/portrait-scene-lineage-v1.json'])
data={'status':'authored configuration','scope':'Explicit delivered painted sources and source ancestry. Private official/native style references are hash-only controls, not redistributed.',
      'input_sha256':{p.relative_to(P).as_posix():sha(p)for p in sorted(files)},
      'official_ionia_crest_reference_sha256':'c8df47b7021ed103cf646b72fdb2275211a97846cd921923893f0a756659c535',
      'excluded_study':'Disciple combat-v1 has a duplicate staff in one preparation pose; preserved unselected. No old3D sources are adopted.'}
(S/'inputs.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
print(json.dumps({'pinned_inputs':len(data['input_sha256'])}))
