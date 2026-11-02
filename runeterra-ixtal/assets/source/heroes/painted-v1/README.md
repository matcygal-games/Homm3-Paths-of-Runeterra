# Ixtal painted hero sources

Fifteen portrait paintings and fifteen specialty paintings were produced individually with the OpenAI built-in imagegen tool. No Blender, substitute 3D render, original portrait recolor, code-painted figure or API fallback was used. The provider did not expose its model identifier. Exact issued prompts are retained in each `generation-request.json` and `specialty-generation-request.json`. Original provider PNGs are the editable bitmap masters; deterministic cropping/resize is in `derive_native.py`.

Seven League identities use actually inspected official Riot appearance references: Qiyana, Nidalee, Neeko, Milio, revised Primordial Sovereign Skarner, Malphite and Zyra. Eight supporting people have **original project interpretations of their exact faces**: Inessa, Mara, Lupé, Luné, Aliay Qunlan, Mivasim, Chiuqeslan and Bayal. Their sourced identity, sex, age where established, institutional role and specific prose cues are retained; unsourced face, hairstyle, skin-color, costume, chair or beard details are not advertised as canon. Shared Ixtali clothing/background details are project art direction.

Inessa is seated and remains permanently unable to walk; a close portrait cannot verify mobility, and no cure is depicted or implied. Lupé and Luné are distinct elder twins rather than recolored copies. Luné's portrait retains a confined setting without inventing an escape. Aliay is male. Mivasim is an older woman with jade-like eyes and dark robes. Chiuqeslan is an older bald man with green eyes and broad black-robed shoulders; his beard is an original design choice. Bayal's presentation stays modest rather than a canonical army officer. Milio remains a twelve-year-old support character. Nonhuman portraits depict actual nonhuman heads rather than targetable hero troops.

The actual original Castle portrait board was inspected at native 58×64 and 48×32. The actual native specialty comparison and the UN44/UN32 hero/exchange consumers establish 44×44 and 32×32 specialty surfaces. Private official/source reference images and provider output-path receipts remain outside the asset source tree, under the coordinator's private implementation reports; they are not release assets. Their byte receipts and reading coverage are preserved there.

Every large/small pair uses its own painted master. Large portraits retain painted environmental context; small portraits use a separate fixed face crop rather than shrinking the whole large surface. Specialty subjects follow the frozen native mechanics, not a different MOBA ability. `native-output-index.json` enumerates all sixty native candidates and their SHA-256 pins. Each adjacent raster recipe produces only `Content/Sprites/runeterra/ixtal/heroes/<id>/<role>.png`.

Replay from the implementation root:

```powershell
..\runeterra-demacia\.venv\Scripts\python.exe assets/source/heroes/painted-v1/derive_native.py
```

The script performs only technical whole-image crops, color-mode conversion and LANCZOS resizing, with no anatomy repaint, visual filter or procedural artwork. `paint_jobs_v1.py` writes missing request records only; it does not call a generator or recreate an existing painting.

Status: painted-master-complete-unapproved. These are real authored candidates with technical/source verification, not final human visual, native graphical, rights or release acceptance. No asset selection, stage publication or native desktop action belongs to this worker handoff. Regional scenery is an interpreted compressed portrait backdrop, not an authenticated Ixaocan street map. Final comparisons and actual in-game crop/readability checks remain required.
