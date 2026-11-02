"""Add the versioned handoff links to the actual source review page."""
import assemble_packets as common
R=common.REPORT/'heraldry-v1'
p=R/'index.html';s=p.read_text(encoding='utf-8')
s=s.replace(chr(194)+chr(183),' | ').replace(chr(226)+chr(8364)+chr(8221),':')
links='<p><a href="HANDOFF.md">Implementation handoff</a> | <a href="canonical-integration-packet-v3.json">Selective integration packet</a> | <a href="consumer-and-source-checks-v3.json">Executed checks</a> | <a href="graphics-offset-proposal-v1.json">Projectile origin proposal</a></p>'
if links not in s:s=s.replace('<nav>',links+'<nav>',1)
if not s.rstrip().endswith('</html>'):s+='\n</html>\n'
p.write_text(s,encoding='utf-8')
print('Review index links final handoff, guarded packet, checks and offset proposal.')
