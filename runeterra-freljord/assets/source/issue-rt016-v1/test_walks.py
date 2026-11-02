"""Executed candidate checks; analytical geometry is never native acceptance."""
from pathlib import Path
import copy
import json
import sys
import unittest
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image
import author_walks as current

OLD=current.OLD
sys.path.insert(0,str(OLD.parent))
sys.path.insert(0,str(OLD.parent/'equipment-sculpt-pass'))
import verify_gait
import verify_pass


def ids(mesh, part):
    return sorted({i for face,name in zip(mesh.faces,mesh.parts) if name==part for i in face})


def surfaces(mesh,joints):
    vertices=np.asarray(mesh.vertices)
    failures=[]
    for side in ('near','far'):
        feet=ids(mesh,side+'_sculpt_foot')
        legs=sorted({i for face,name in zip(mesh.faces,mesh.parts) if name.startswith(side+'_sculpt_') for i in face})
        if verify_pass.surface_failure(vertices,feet,legs,joints['legs'][side]):
            failures.append(side+' actual sole/contact/clearance')
        actual=np.array(joints['sculpt_surface_contacts'][side]['actual_sole_toe_vertex'])
        if np.linalg.norm(vertices[feet]-actual,axis=1).min()>1e-8:
            failures.append(side+' declared toe absent from actual sole')
    caps=ids(mesh,'finished_bound_grip')[-2:]
    if np.linalg.norm(np.mean(vertices[caps],axis=0)-joints['arms']['far']['wrist'])>1e-8:
        failures.append('real surfaced grip detached')
    return failures


def visible_rgba(image):
    pixels=np.asarray(image).copy()
    pixels[pixels[:,:,3]==0,:3]=0
    return pixels


class WalkChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measurements={}
        cls.poses={}
        for unit in current.UNITS:
            cls.poses[unit]=[current.author(i/6,unit) for i in range(6)]

    def test_real_support_contact_clearance_fixed_chains_and_loop(self):
        for unit in current.UNITS:
            dense=[];world={'near':[],'far':[]};first=None;uv0=None
            for sample in range(61):
                mesh,joints=current.author(sample/60,unit)
                self.assertEqual(surfaces(mesh,joints),[],(unit,sample))
                vertices=np.asarray(mesh.vertices)
                self.assertGreaterEqual(vertices[:,2].min(),-.001)
                triuv=np.asarray(mesh.uv)[np.asarray(mesh.faces)]
                if sample==0:first=vertices.copy();uv0=triuv.copy()
                self.assertLess(np.abs(triuv-uv0).max(),1e-12)
                if sample==60:self.assertLess(np.abs(vertices-first).max(),1e-8)
                for side,start in (('near',0),('far',30)):
                    if start<=sample<start+30:
                        toe=np.array(joints['sculpt_surface_contacts'][side]['actual_sole_toe_vertex'])
                        toe[0]+=joints['reference_root_world_x'];world[side].append(toe)
                oldmesh,oldjoints=current.previous.author(sample/60,unit)
                self.assertEqual(joints['legs'],oldjoints['legs'])
                self.assertEqual(joints['arms'],oldjoints['arms'])
                # Actual ordered triangle geometry and UV for all non-equipment
                # parts remains identical, independent of vertex renumbering.
                for attr in ('vertices','uv'):
                    a=np.asarray(getattr(mesh,attr))[np.asarray(mesh.faces)]
                    b=np.asarray(getattr(oldmesh,attr))[np.asarray(oldmesh.faces)]
                    keep=np.array([not name.startswith('finished_feather_') for name in mesh.parts])
                    self.assertEqual(mesh.parts,oldmesh.parts)
                    self.assertLess(np.abs(a[keep]-b[keep]).max(),1e-12)
                dense.append({'sample':sample,'minimum_z':float(vertices[:,2].min())})
            slip={side:float(np.ptp(points,axis=0).max()) for side,points in world.items()}
            self.assertTrue(all(value<1e-8 for value in slip.values()))
            records=[j for _,j in self.poses[unit]]
            self.assertEqual(verify_gait.geometry_checks(records),[])
            self.measurements[unit]={'dense_samples':dense,'actual_stance_slip_world':slip,
                 'whole_mesh_loop_max_vertex_error':float(np.abs(vertices-first).max()),
                 'fixed_uv_max_error':float(np.abs(triuv-uv0).max())}

    def test_actual_geometry_and_phase_negative_controls(self):
        for unit in current.UNITS:
            mesh,joints=self.poses[unit][0]
            for defect in ('floating','penetrating','detached_grip'):
                bad=copy.deepcopy(mesh)
                indices=ids(bad,'finished_bound_grip' if defect=='detached_grip' else 'near_sculpt_foot')
                for i in indices:bad.vertices[i][2]+=.05 if defect!='penetrating' else -.05
                self.assertTrue(surfaces(bad,joints),(unit,defect))
            records=[j for _,j in self.poses[unit]]
            repeated=[copy.deepcopy(records[0]) for _ in records]
            wrong=[records[i] for i in (0,2,1,5,4,3)]
            clear=copy.deepcopy(records);clear[1]['legs']['far']['sole_lift']=0
            for bad in (repeated,wrong,clear):self.assertTrue(verify_gait.geometry_checks(bad))

    def test_render_registration_hashes_atlas_and_mirror(self):
        for unit in current.UNITS:
            root=current.HERE/'candidates'/unit
            receipt=json.loads((root/'receipt.json').read_text())
            atlas=Image.new('RGBA',(2700,400))
            frames=[]
            for phase in range(6):
                path=root/f'composite-g00-f{phase:03}.png'
                frame=Image.open(path).convert('RGBA')
                self.assertEqual(frame.size,(450,400))
                self.assertEqual(current.sha(path),receipt['frames'][phase]['composite_sha256'])
                alpha=np.asarray(frame)[:,:,3]
                y,x=np.where(alpha>0)
                self.assertGreater(x.min(),0);self.assertLess(x.max(),449)
                self.assertGreater(y.min(),0);self.assertLess(y.max(),399)
                self.assertFalse(alpha[:,0].any() or alpha[:,-1].any())
                self.assertTrue(np.array_equal(visible_rgba(current.mirror(current.mirror(frame))),visible_rgba(frame)))
                # Transparent hidden RGB does not affect appearance; a real
                # visible-pixel mutation must still fail the comparison.
                changed=frame.copy()
                opaque=np.argwhere(np.asarray(frame)[:,:,3]>128)[0]
                xx,yy=int(opaque[1]),int(opaque[0])
                red,green,blue,alpha=changed.getpixel((xx,yy))
                changed.putpixel((xx,yy),(red^255,green,blue,alpha))
                self.assertFalse(np.array_equal(visible_rgba(frame),visible_rgba(changed)))
                atlas.paste(frame,(450*phase,0));frames.append(frame)
            for phase,frame in enumerate(frames):
                self.assertTrue(np.array_equal(np.asarray(atlas.crop((phase*450,0,(phase+1)*450,400))),np.asarray(frame)))
            self.assertEqual(len({row['surface_sha256'] for row in receipt['frames']}),6)
            self.assertEqual(receipt['camera'],current.previous.contract(unit)['camera'])

    def test_editable_objs_match_checked_pose(self):
        for unit in current.UNITS:
            for phase,(mesh,joints) in enumerate(self.poses[unit]):
                path=current.HERE/'candidates'/unit/f'phase{phase}.obj'
                vertices=np.array([[float(x) for x in line.split()[1:]] for line in path.read_text().splitlines() if line.startswith('v ')])
                self.assertLessEqual(np.abs(vertices-np.asarray(mesh.vertices)).max(),5.000001e-8)
                self.assertIn('mtllib materials.mtl',path.read_text())

    def test_real_shadow_projection_and_composite(self):
        for unit in current.UNITS:
            for phase,(mesh,joints) in enumerate(self.poses[unit]):
                root=current.HERE/'candidates'/unit
                saved=Image.open(root/f'shadow-g00-f{phase:03}.png').convert('RGBA')
                self.assertTrue(np.array_equal(np.asarray(saved),np.asarray(current.shadow(mesh))))
                self.assertGreater(np.count_nonzero(np.asarray(saved)[:,:,3]),100)
                body=Image.open(root/f'surface-g00-f{phase:03}.png').convert('RGBA')
                savedcomposite=Image.open(root/f'composite-g00-f{phase:03}.png').convert('RGBA')
                self.assertTrue(np.array_equal(np.asarray(savedcomposite),np.asarray(Image.alpha_composite(saved,body))))

    def test_selected_and_dependency_closure_unchanged(self):
        for filename in ('selected-before.json','dependency-pins.json'):
            pins=json.loads((current.REPORT/filename).read_text())
            self.assertGreater(len(pins),20)
            self.assertEqual([name for name,value in pins.items() if current.sha(current.PROJECT/name)!=value],[])
        for unit in current.UNITS:
            root=current.HERE/'candidates'/unit
            receipt=json.loads((root/'receipt.json').read_text())
            self.assertEqual(receipt['source_dependencies'],json.loads((current.REPORT/'dependency-pins.json').read_text()))
            provenance=json.loads((root/'materials/paint-provenance.json').read_text())
            for name,row in provenance.items():
                self.assertEqual(current.sha(root/'materials'/(name+'.png')),row['output_sha256'])
                self.assertEqual(current.sha(current.PROJECT/row['source']),row['source_sha256'])

    @classmethod
    def tearDownClass(cls):
        current.write_json(current.REPORT/'geometry-measurements-v2.json',cls.measurements)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(WalkChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    current.write_json(current.REPORT/'candidate-tests-v2.json',{'tests_run':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'ok':result.wasSuccessful(),'scope':'candidate-only source/geometry/raster; no native, selection, art approval'})
    sys.exit(0 if result.wasSuccessful() else 1)
