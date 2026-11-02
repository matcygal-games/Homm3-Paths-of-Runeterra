# Hunter walking candidates — 21 October 2026

Status: **authored configuration**. Both six-pose cohorts remain unselected.
No recipe, production selection, manifest, stage or native runtime was changed.

The earlier full-body reference attempts repeatedly restored the old leading
leg. This experiment instead constructed an actual costumed 3D guide with
separate hip/knee/ankle chains, a matched orthographic camera, a hood, short cape,
quiver and low carried bow. Its near shin has three pale straps; its far shin is
plain. Only a leg-free upper-body painting crop supplies identity. The guide is
an editable pose input, never final game art. No original-game mesh/pixel or
another faction's rig/pixel was used.

The first actual built-in image-generation call produced an opposite contact:
the visible camera-near upper thigh connects to the rear/left three-strapped
shin and boot, while the far plain boot leads right. The coordinator separately
inspected this source and its 74-pixel native comparison and found it promising.
This establishes one painted anatomical phase, not complete motion acceptance.

Six actual costumed guide phases then fixed the same anatomical leg identities:

| Zero-based phase | Near leg (three straps) | Far leg (plain) |
| --- | --- | --- |
| 0 | Forward/right contact | Trailing/left |
| 1 | Supporting | Bent passing |
| 2 | Rear push-off | Reaching forward |
| 3 | Trailing/left | Forward/right contact |
| 4 | Bent passing | Supporting |
| 5 | Reaching forward | Rear push-off |

A second actual built-in call painted all six base Hunter poses over that
guide. A third painted the Veteran equipment onto those exact articulated
poses. Inspection of the source and native crops shows opposite contact order
between phases 0 and 3, and different passing support between 1 and 4. These are
genuine painted leg articulations, not translated idle, mirrored whole figures,
warped limbs or repeated stills. All twelve new native frames have unique hashes.

Technical assembly takes six fixed 512×512 cells from each 1536×1024 painted
atlas and applies one fixed 0.172 scale and one fixed placement. Every output is
RGBA 450×400 with pivot 197,266. It never recenters, rescales or stretches a
phase individually. Head/torso placement is stable. The lower footprint varies
about three pixels as the near and far feet take contact in the elevated camera;
this requires native shadow/ground review rather than a per-frame pixel shift.
The diagnostic loop is a lossless WebP of the actual six exported frames, not
a substitute for native animation playback.

Identity concerns remain for independent review: the new camera reads slightly
more side-on, the body reads slimmer, and the base's upper-arm material is more
covered leather than the old selected cohort. The Veteran adds a broader brighter
fur mantle/cape, reinforced silver bodice/shoulders and bow end fittings, but
the upgrade difference is modest at native scale. Do not trade the corrected
stride for unreviewed identity drift or declare every Hunter action repaired.
The existing aimed shooting, standing, hit, death, turn, portrait and map sources
remain selected and untouched.

Actual commands and source pins are captured in `checks.json` and the generation
records. The helper uses Blender 4.5.9 LTS (hash 8bf95cbd38d1) only to create
guides. The provider is the built-in OpenAI image-generation tool; the callable
tool exposed no model identifier. Generated originals were preserved under
the returned default directory and copied into versioned project sources.
Redistribution remains unresolved. All art acceptance and native all-action
playback remain pending.
