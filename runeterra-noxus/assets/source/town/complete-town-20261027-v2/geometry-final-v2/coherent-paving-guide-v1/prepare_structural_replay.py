"""Version private authoring-only consumer harness without shared code edits."""
from pathlib import Path
g=Path(__file__).resolve().parent;old=g.parent
s=(old/'assemble_contract.py').read_text()
s=s.replace("HERE=Path(__file__).resolve().parent;TOWN=HERE.parent;ROOT=HERE.parents[4];REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2'","GUIDE=Path(__file__).resolve().parent;HERE=GUIDE/'structural-contract';TOWN=GUIDE.parents[1];ROOT=GUIDE.parents[5];REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/coherent-paving-guide-v1'")
# All actual selected coast entry pixels are bounded deck/hull frontage.
# Marine support may cover those actual source pixels for visibility; only
# independently traced own horizontal treads carry walking inside the body.
s=s.replace('ImageChops.lighter(roots[state],own_treads[state]),alpha(layers[state],8)','ImageChops.lighter(roots[state],ImageChops.lighter(own_treads[state],door)),alpha(layers[state],8)')
(g/'build_structural_contract.py').write_text(s)
s=(old/'check_consumer.py').read_text()
s=s.replace('HERE=Path(__file__).resolve().parent;TOWN=HERE.parent;ROOT=HERE.parents[4];WORKSPACE=ROOT.parent',"GUIDE=Path(__file__).resolve().parent;HERE=GUIDE/'structural-contract';TOWN=GUIDE.parents[1];ROOT=GUIDE.parents[5];WORKSPACE=ROOT.parent")
s=s.replace("('consumer-'+args.attempt)","('coherent-paving-guide-v1/consumer-'+args.attempt)")
s=s.replace(' if not errors:\n  inspect_negative',' if False: # USER HOLD: authoring structural replay only; final negatives prohibited.\n  inspect_negative')
s=s.replace("'baseline_is_valid_for_negative_attribution':not errors","'baseline_is_valid_for_negative_attribution':False,'authoring_structural_check_only':True,'user_rejected_materials':True,'visual_approval':False,'final_admission_on_hold':True")
s=s.replace("'negative_checks_blocked_reason':None if not errors else 'Actual full-town baseline fails physical admission; mutated failures cannot prove isolated negative attribution.'","'negative_checks_blocked_reason':'User rejected surface appearance; authoring structural replay only. Final negatives and admission held.'")
(g/'check_structural_source.py').write_text(s)
print('Private authoring harness prepared; actual shared compiler/helper unchanged.')
