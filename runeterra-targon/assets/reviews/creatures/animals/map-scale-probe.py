"""Bounded animal mesh projection/pixel experiment; not a production selection."""
import bpy
import json
import math
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view

scene=bpy.context.scene
camera=scene.camera
scene.render.resolution_x=scene.render.resolution_y=64
camera.data.shift_x=-.25
camera.data.shift_y=.4375
timeline=json.loads(scene['action_timeline'])
pivot=bpy.data.objects['Unanimated_facing_pivot']
rows=[]
for scale in (9,10,10.5,11,11.5,12):
    camera.data.ortho_scale=scale
    for group,index in ((2,0),(2,2),(12,3)):
        scene.frame_set(next(n for n,g,f in timeline if g==group and f==index))
        for facing,angle in (('right',0),('left',math.pi)):
            pivot.rotation_euler.z=angle
            bpy.context.view_layer.update()
            points=[world_to_camera_view(scene,camera,ob.matrix_world@v.co)
                    for ob in bpy.data.objects if ob.type=='MESH' and not ob.is_shadow_catcher
                    for v in ob.data.vertices]
            rows.append({'scale':scale,'group':group,'frame':index,'facing':facing,
                         'projected_mesh_bounds':[round(min(p.x for p in points)*64,3),
                             round((1-max(p.y for p in points))*64,3),
                             round(max(p.x for p in points)*64,3),
                             round((1-min(p.y for p in points))*64,3)]})
result={'status':'authored configuration','scene':Path(bpy.data.filepath).name,
        'root':[48,60],'canvas':[64,64],'rows':rows,
        'limits':'Actual mesh projection, excluding shadow catcher; includes all source vertices. PNG antialias/pixel verification still required.'}
Path(__file__).with_name('map-scale-projection-'+scene['unit']+'.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result))
camera.data.ortho_scale=11.5
folder=Path(__file__).parent/('map-scale-11_5-'+scene['unit'])
folder.mkdir(parents=True,exist_ok=True)
scene.render.threads_mode='FIXED'
scene.render.threads=4
for group,index in ((2,0),(2,2),(12,3)):
    scene.frame_set(next(n for n,g,f in timeline if g==group and f==index))
    for facing,angle in (('right',0),('left',math.pi)):
        pivot.rotation_euler.z=angle
        bpy.context.view_layer.update()
        scene.render.filepath=str(folder/(f'{facing}-g{group:02d}-f{index:03d}.png'))
        bpy.ops.render.render(write_still=True)
