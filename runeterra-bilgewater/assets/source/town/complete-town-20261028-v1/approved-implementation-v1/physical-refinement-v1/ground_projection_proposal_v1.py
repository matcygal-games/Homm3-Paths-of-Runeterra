"""Strict opt-in source-ground projection PROPOSAL, never a canonical helper edit.

Root owns integration. The unchanged consumer remains the default. This module
validates actual source cases and returns conservative ground blockers; it does
not turn a roof into a floor/door or approve any unseen circulation lane.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops


def validate_ground_projection_cases(layout,project,contract,images,physical,bodies,
                                     support,stairs,land,water,dependencies):
    """Return full selected bodies except independently observed floor ribbons.

    Integration points: use returned blockers for own approach/global-path and
    other-building approach intrusion only. Keep original full-body foreground
    doorway and foundation occlusion checks EXACTLY unchanged.
    """
    plan=contract['silhouette_plan']
    records=plan.get('ground_projection_cases',[])
    if not isinstance(records,list):raise ValueError('Ground projection cases must be explicit opt-in records')
    blockers={state:body.copy()for state,body in bodies.items()}
    seen=set();blank=Image.new('L',(800,374));walk=ImageChops.lighter(support,stairs)
    def load(ref,label,empty=False):return layout._binary_mask(project,ref,dependencies,label,empty=empty)
    def own(ref,label):
        path=layout._reference(project,ref,dependencies)
        if not path.is_relative_to((project/'assets/source/town').resolve())or path.stat().st_nlink!=1:
            raise ValueError('Ground projection source must be direct own editable town material: '+label)
        return path
    def outlines(shapes):
        if not isinstance(shapes,list)or not shapes:raise ValueError('A real closed occupied ground contour is required')
        mask=blank.copy();draw=ImageDraw.Draw(mask)
        for points in shapes:
            if not isinstance(points,list)or len(points)<5:raise ValueError('Ground footprint needs an actual source contour, not a sole seam')
            for xy in points:
                if not isinstance(xy,list)or len(xy)!=2 or any(type(v)is not int for v in xy)or not 0<=xy[0]<800 or not 0<=xy[1]<374:
                    raise ValueError('Ground contour leaves native source canvas')
            draw.polygon(list(map(tuple,points)),fill=255)
        return mask
    for row in records:
        expected={'state','projection_type','source_case','occluded_floor_mask','closed_ground_mask','source_floor_mask','own_entry_contacts_mask'}
        if not isinstance(row,dict)or set(row)!=expected:raise ValueError('Ground projection needs its complete strict typed record')
        state=row['state'];kind=row['projection_type']
        if state not in bodies or state in seen or kind not in ('raised-canopy','elevated-facade-back-terrace'):
            raise ValueError('Unknown or duplicate source-ground projection type/state')
        seen.add(state);case_path=own(row['source_case'],'case '+state)
        if case_path.suffix!='.json':raise ValueError('Ground projection case must be own JSON')
        case=layout.fp.read_json(case_path)
        if (not isinstance(case,dict)or case.get('kind')!='source-ground-projection-v1'
            or case.get('state')!=state or case.get('projection_type')!=kind
            or case.get('frame')!=contract['frames'][state]or case.get('background')!=contract['background']
            or any(case.get(k)!=row[k]for k in ('occluded_floor_mask','closed_ground_mask','source_floor_mask','own_entry_contacts_mask'))
            or not isinstance(case.get('reason'),str)or len(case['reason'].strip())<60
            or any(not isinstance(case.get(k),str)or len(case[k].strip())<8 for k in ('occupied_level','behind_floor_level','floor_observation'))
            or case['occupied_level'].strip()==case['behind_floor_level'].strip()):
            raise ValueError('Ground projection case does not bind actual selected sources and distinct levels: '+state)
        # Read the pinned actual source frame/background as dependencies, too.
        layout._image(own(case['frame'],'actual frame'));layout._image(own(case['background'],'actual background'))
        projection=load(row['occluded_floor_mask'],'source-observed occluded floor '+state)
        footprint=load(row['closed_ground_mask'],'closed occupied ground '+state)
        floor=load(row['source_floor_mask'],'actual source-floor continuity '+state)
        entry=load(row['own_entry_contacts_mask'],'own entry soles '+state,True)
        foundation,door,approach=physical[state]
        # Frontage and real bearing material are NEVER waived, even under a
        # repinned facade/canopy source record. Check these before floor type.
        if layout._intersects(projection,door)or layout._intersects(projection,entry):
            raise ValueError('Projected cover may never waive an actual visible frontage/entry: '+state)
        if layout._intersects(projection,foundation):
            raise ValueError('Projected cover may never waive actual bearing material: '+state)
        expected_footprint=ImageChops.multiply(outlines(case.get('closed_ground_contours')),bodies[state])
        if expected_footprint.tobytes()!=footprint.tobytes():
            raise ValueError('Closed occupied footprint differs from its actual source contour/body: '+state)
        if (layout._outside(foundation,footprint)or footprint.tobytes()==foundation.tobytes()
            or footprint.histogram()[255]<foundation.histogram()[255]*3):
            raise ValueError('Closed occupied footprint cannot be replaced by sparse bearing soles: '+state)
        if layout._intersects(projection,footprint):
            raise ValueError('Projected cover intrudes into an actual closed ground wall/footprint: '+state)
        if layout._outside(footprint,land)or layout._intersects(footprint,water):
            raise ValueError('Closed occupied ground cannot float on external water: '+state)
        if (layout._outside(floor,walk)or layout._outside(floor,land)or layout._intersects(floor,water)
            or projection.tobytes()!=ImageChops.multiply(floor,bodies[state]).tobytes()):
            raise ValueError('Projected cover must equal actual source-floor/selected-body intersection: '+state)
        layout._connected(floor,'source-floor continuity '+state)
        outside=ImageChops.subtract(floor,bodies[state])
        witnesses=case.get('visible_floor_witnesses')
        if not isinstance(witnesses,list)or len(witnesses)<2:raise ValueError('Visible floor entry/exit witnesses required: '+state)
        for xy in witnesses:
            if not isinstance(xy,list)or len(xy)!=2 or any(type(v)is not int for v in xy)or not 0<=xy[0]<800 or not 0<=xy[1]<374 or not outside.getpixel(tuple(xy)):
                raise ValueError('Ground continuity witness is not actual unoccluded source floor: '+state)
        evidence=case.get('evidence')
        if not isinstance(evidence,dict)or set(evidence)!={'complete_scene','cover_absent_scene','intersection_overlay'}:
            raise ValueError('Ground projection requires actual full/absent/intersection source evidence')
        selection=case.get('scene_states')
        if (not isinstance(selection,list)or state not in selection or len(selection)!=len(set(selection))
            or any(k not in images for k in selection)):
            raise ValueError('Ground projection source scene is not actual native states')
        scene=layout._image(layout._reference(project,contract['background'],dependencies));absent=scene.copy()
        for key in selection:
            scene=Image.alpha_composite(scene,images[key])
            if key!=state:absent=Image.alpha_composite(absent,images[key])
        if (layout._image(own(evidence['complete_scene'],'complete evidence')).tobytes()!=scene.tobytes()
            or layout._image(own(evidence['cover_absent_scene'],'absence evidence')).tobytes()!=absent.tobytes()):
            raise ValueError('Ground projection full/absent proof differs from actual current composition: '+state)
        layout._image(own(evidence['intersection_overlay'],'intersection proof'))
        blockers[state]=ImageChops.lighter(ImageChops.subtract(bodies[state],projection),footprint)
    return blockers
