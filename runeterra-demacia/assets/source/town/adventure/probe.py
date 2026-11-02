"""Isolated native owner-color art diagnostic; never Demacia gameplay acceptance.

Registers own flaggable objects, without overriding original entity definitions.
The diagnostic mod exists only in a project-owned copied runtime sandbox.
"""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
import json
import shutil
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT / "scripts"))
from common import VCMI, json_bytes, read_json, sha256, write_json, zip_files
from discovery import discover
from maps import ordinary_core_heroes
from runtime import prepare_sandbox, diagnostics

MOD = "demacia-adventure-probe"
STATES = ("village", "fort", "citadel", "castle", "capitol")
REPORT = PROJECT / "build/reports/runtime/adventure-ownership-probe-v10"


def prepare():
    info = discover(PROJECT.parent)
    environment = prepare_sandbox(Path(info["runtime"]["client"]), Path(info["runtime"]["server"]),
                                  [Path(item["path"]) for item in info["archives"]],
                                  include_mod=False, name="runtime-adventure-art-sandbox")
    app, user = Path(environment["app"]), Path(environment["user"])
    mod = user / "Mods" / MOD
    write_json(mod / "mod.json", {"name": "Demacia adventure sprite ownership diagnostic", "version": "0.0.1",
        "author": "Runeterra Demacia project", "description": "Own flaggable art probes only; no Demacia mechanics and no core entity overrides.",
        "modType": "Graphical", "objects": ["config/objects.json"], "compatibility": {"min": "1.8.0"}})
    types, objects, resource_hashes = {}, [], {}
    for state in STATES:
        recipe = PROJECT / "assets/recipes" / f"adventure-{state}-animation.json"
        from animation import assemble
        assembled = assemble(PROJECT, recipe, resume=True)
        for item in assembled["outputs"]:
            source = PROJECT / "assets/generated" / item["output_path"]
            target = mod / item["output_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            resource_hashes[item["output_path"]] = sha256(target)
        template = {"animation": f"runeterra/demacia/town/map/{state}.json", "mask": ["VVVVVV", "VVVVVV", "VVVVVV", "VVBBBV", "VBBABB"],
                    "visitableFrom": ["---", "---", "+++"]}
        types[state] = {"name": state + " candidate", "templates": {"ownArt": template},
                        "message": "Art ownership probe; not a recruitable town.", "bonuses": {}, "dailyIncome": {}}
    write_json(mod / "Content/config/objects.json", {"adventureOwnershipProbe": {
        "name": "Demacia art ownership diagnostic", "handler": "flaggable", "types": types}})
    for row, owner in enumerate(("red", "blue", None)):
        for column, state in enumerate(STATES):
            options = {"owner": owner} if owner else {}
            objects.append({"instanceName": "art" + (owner or "neutral").title() + state.title() + "_" + str(len(objects)),
                "type": MOD + ":adventureOwnershipProbe", "subtype": MOD + ":" + state,
                "x": 5 + column * 6, "y": 5 + row * 6, "l": 0,
                "template": types[state]["templates"]["ownArt"], "options": options})
    for owner, x in (("red", 17), ("blue", 34)):
        objects.append({"instanceName": "original" + owner.title() + "Castle_" + str(len(objects)),
            "type": "town", "subtype": "core:castle", "x": x, "y": 22, "l": 0,
            "template": {"animation": "AVCCASX0.DEF", "mask": ["VVVVV", "VBBBB", "VBBBB", "VBABB"], "visitableFrom": ["---", "-+-", "+++"]},
            "options": {"owner": owner, "buildings": {"allOf": ["villageHall", "fort"]}}})
        objects.append({"instanceName": "original" + owner.title() + "Hero_" + str(len(objects)),
            "type": "hero", "subtype": "core:knight", "x": x, "y": 23, "l": 0,
            "template": {"animation": "AH00_.def", "mask": ["A"], "visitableFrom": ["+++", "+-+", "+++"]},
            "options": {"owner": owner, "type": "core:orrin" if owner == "red" else "core:valeska", "experience": 0}})
    header = {"versionMajor": 3, "versionMinor": 0, "name": "Demacia ownership ART DIAGNOSTIC", "author": "Runeterra Demacia project",
        "description": "Five own art states in red/blue/neutral rows using a scoped flaggable object. No Demacia town mechanics, troops or core overrides.",
        "difficulty": "NORMAL", "mods": [{"modId": MOD, "name": "Demacia art diagnostic", "version": "0.0.1"}],
        "mapLevels": {"surface": {"width": 36, "height": 24, "index": 0, "layer": "core:surface"}},
        "players": {owner: {"canPlay": "PlayerOrAI", "allowedFactions": {"anyOf": ["core:castle"]}, "randomFaction": False,
                             "mainTown": {"x": x, "y": 22, "l": 0, "generateHero": False}} for owner, x in (("red", 17), ("blue", 34))},
        "allowedHeroes": {"anyOf": ordinary_core_heroes()},
        "triggeredEvents": {"victory": {"condition": ["standardWin"], "effect": {"type": "victory"}},
                            "loss": {"condition": ["daysWithoutTown", {"value": 7}], "effect": {"type": "defeat"}}}}
    output = user / "Maps/adventure-ownership-probe.vmap"
    zip_files(output, {"header.json": json_bytes(header), "objects.json": json_bytes(objects),
                       "surface_terrain.json": json_bytes([["gr0_" for _ in range(36)] for _ in range(24)])})
    presets = {"activePreset": "art-probe", "presets": {"art-probe": {"mods": ["vcmi", MOD]}}}
    for name in ("modSettings.json", "testModSettings.json"):
        write_json(user / "config" / name, presets)
    write_json(user / "config/settings.json", {"mods": {"validation": "full"},
        "logging": {"loggers": [{"domain": "global", "level": "info"}, {"domain": "rng", "level": "info"}]},
        "ai": {"adventureAlliedAI": "EmptyAI", "adventureEnemyAI": "EmptyAI"},
        "video": {"fullscreen": False, "resolution": {"width": 1280, "height": 800, "scaling": 100}},
        "general": {"saveFrequency": 1000000}})
    result = {"environment": environment, "resource_sha256": resource_hashes, "map": str(output), "map_sha256": sha256(output),
              "diagnostic_only": True, "scope": "Own flaggable objects use the same native owner-overlay rendering path; not actual Demacia town gameplay.",
              "no_core_config_override": True, "owners": ["red", "blue", "neutral"], "state_columns": list(STATES)}
    write_json(REPORT / "environment.json", result)
    return result


def capture(environment):
    if sys.platform != "win32":
        raise ValueError("The desktop capture helper requires Windows")
    from PIL import Image, ImageGrab
    from owner_overlay import compare_owner_atlas
    app = Path(environment["environment"]["app"])
    user = Path(environment["environment"]["user"])
    log_path = REPORT / "stdout.log"
    REPORT.mkdir(parents=True, exist_ok=True)
    command = [str(app / "VCMI_client.exe"), "--testmap", "Maps/adventure-ownership-probe.vmap", "--spectate",
               "--spectate-ignore-hero", "--nointro", "--disable-video", "--savefrequency", "1000000"]
    metadata = {"command": command, "diagnostic_only": True, "visual_approval_granted": False,
                "purpose": environment["scope"], "images": []}
    api = ctypes.windll.user32
    try:
        api.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        pass
    api.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    api.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    api.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    api.SetForegroundWindow.argtypes = [wintypes.HWND]
    api.GetForegroundWindow.restype = wintypes.HWND
    api.IsWindowVisible.argtypes = [wintypes.HWND]
    api.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    api.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    api.WindowFromPoint.argtypes = [wintypes.POINT]
    api.WindowFromPoint.restype = wintypes.HWND
    api.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    api.GetAncestor.restype = wintypes.HWND
    api.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    api.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    original_cursor = wintypes.POINT()
    api.GetCursorPos(ctypes.byref(original_cursor))
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    api.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]

    def own_windows():
        found = []
        def visit(window, parameter):
            pid = wintypes.DWORD()
            api.GetWindowThreadProcessId(window, ctypes.byref(pid))
            rect = wintypes.RECT()
            valid = api.GetClientRect(window, ctypes.byref(rect))
            if valid and pid.value == process.pid and api.IsWindowVisible(window) and rect.right >= 800 and rect.bottom >= 600:
                found.append({"handle": window, "width": rect.right, "height": rect.bottom})
            return True
        api.EnumWindows(callback_type(visit), 0)
        return found
    with log_path.open("wb") as stream:
        process = subprocess.Popen(command, cwd=app, stdin=subprocess.PIPE, stdout=stream, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        metadata["pid"] = process.pid
        write_json(REPORT / "process.json", metadata)
        try:
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline and process.poll() is None:
                windows = own_windows()
                text_path = user / "logs/VCMI_Client_log.txt"
                text = ""
                if text_path.is_file():
                    with text_path.open("rb") as log:
                        text = log.read(2_000_000).decode("utf-8", "replace")
                if windows and "Creating adventure AI EmptyAI" in text:
                    # Native developer console takes over this isolated AI
                    # player, stopping rapid EmptyAI months during art review.
                    process.stdin.write(b"controlai red\n")
                    process.stdin.flush()
                    metadata["native_console_command"] = "controlai red"
                    break
                time.sleep(0.2)
            if process.poll() is not None:
                metadata["process_exit_code"] = process.returncode
                raise RuntimeError("Art-probe client exited before capture; inspect the engine log")
            time.sleep(1)
            windows = own_windows()
            metadata["window_candidates"] = windows
            if not windows:
                raise RuntimeError("No current visible window belonging to the owned probe client")
            window = windows[-1]["handle"]
            api.ShowWindow(window, 9)
            api.SetForegroundWindow(window)
            # A temporary topmost position makes this owned client visible even
            # if Windows refuses foreground activation. It ends when the owned
            # process is closed; no other window's placement is changed.
            api.SetWindowPos(window, wintypes.HWND(-1), 0, 0, 0, 0, 1 | 2 | 16 | 64)
            time.sleep(0.3)
            # Native SDL consumes the physical cursor position. Posted mouse
            # messages alone may act on a stale hover target, so use a real
            # scoped click in this verified, owned topmost window.
            origin = wintypes.POINT()
            api.ClientToScreen(window, ctypes.byref(origin))
            click = wintypes.POINT(origin.x + 1120, origin.y + 40)
            clicked_window = api.WindowFromPoint(click)
            if api.GetAncestor(clicked_window, 2) != window:
                raise RuntimeError("Owned minimap is obscured; refusing a desktop click")
            api.SetCursorPos(click.x, click.y)
            time.sleep(0.15)
            api.mouse_event(0x0002, 0, 0, 0, 0)
            api.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(1)
            if api.GetForegroundWindow() == window:
                api.keybd_event(0x10, 0, 0, 0)
                time.sleep(0.1)
                api.keybd_event(0x72, 0, 0, 0)
                time.sleep(0.1)
                api.keybd_event(0x72, 0, 2, 0)
                time.sleep(0.1)
                api.keybd_event(0x10, 0, 2, 0)
                metadata["native_export_shortcut"] = "Shift+F3"
                time.sleep(0.5)
            rect, point = wintypes.RECT(), wintypes.POINT()
            if not api.GetClientRect(window, ctypes.byref(rect)) or not api.ClientToScreen(window, ctypes.byref(point)):
                raise RuntimeError("Owned client window changed again before capture")
            if rect.right <= 0 or rect.bottom <= 0:
                raise RuntimeError("Owned client is not a nonempty capture target")
            bbox = (point.x, point.y, point.x + rect.right, point.y + rect.bottom)
            metadata["foreground_window"] = api.GetForegroundWindow()
            center_window = api.WindowFromPoint(wintypes.POINT((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2))
            visible_root = api.GetAncestor(center_window, 2)
            metadata["visible_center_root"] = visible_root
            if visible_root == window:
                image = ImageGrab.grab(bbox=bbox)
                method = "Own topmost visible client-area ImageGrab, verified by WindowFromPoint; no resizing"
            else:
                # GPU-backed SDL can return black here. Keep that as a failed
                # capture, never as a rendered-art acceptance image.
                image = ImageGrab.grab(window=window)
                method = "Own HWND ImageGrab/PrintWindow; no resizing"
            if all(low == high == 0 for low, high in image.getextrema()):
                image.save(REPORT / "capture-black.png")
                raise RuntimeError("GPU-backed HWND capture was black; no visual rendering evidence")
            destination = PROJECT / "references/in-game" / ("demacia-adventure-ownership-" + REPORT.name + ".png")
            destination.parent.mkdir(parents=True, exist_ok=True)
            image.save(destination)
            metadata["images"].append({"path": str(destination), "sha256": sha256(destination), "bbox": list(bbox),
                                       "size": list(image.size), "method": method, "visually_inspected": False})
            for exported in (user / "cache/extracted/screenshots").glob("screenshot-map-*.png"):
                destination = PROJECT / "references/in-game" / ("demacia-ownership-native-map-" + exported.name)
                shutil.copyfile(exported, destination)
                metadata["images"].append({"path": str(destination), "sha256": sha256(destination),
                    "method": "Native VCMI whole-map export shortcut; no resizing", "visually_inspected": False})
                atlas = Image.open(destination).convert("RGB")
                masks = {state: Image.open(PROJECT / f"assets/source/town/adventure/{state}/ownership-overlay-v1.png").convert("RGBA")
                         for state in STATES}
                comparison = compare_owner_atlas(atlas, masks)
                comparison.update({"native_image": str(destination), "native_sha256": sha256(destination),
                    "native_dimensions": list(atlas.size), "scope": environment["scope"],
                    "method": "Compare the three native owner rows; no pixel rescaling or simulated rendering."})
                write_json(REPORT / "ownership-pixel-comparison.json", comparison)
                metadata["native_owner_pixel_comparison"] = comparison["all_owner_differences_confined_to_authored_cloth"]
        except Exception as error:
            metadata["capture_error"] = str(error)
        finally:
            cleanup = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True,
                                     text=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            metadata["cleanup"] = {"exit_code": cleanup.returncode, "output": cleanup.stdout + cleanup.stderr}
            api.SetCursorPos(original_cursor.x, original_cursor.y)
            for log in (user / "logs").glob("*.txt"):
                shutil.copyfile(log, REPORT / log.name)
            texts = [(REPORT / "stdout.log").read_text(encoding="utf-8", errors="replace")]
            texts.extend(log.read_text(encoding="utf-8", errors="replace") for log in REPORT.glob("VCMI*.txt"))
            found = diagnostics(texts)
            metadata["runtime_diagnostics_count"] = len(found)
            metadata["runtime_diagnostics"] = found[:30]
            metadata["original_inputs_unchanged"] = all(sha256(Path(path)) == value for path, value in environment["environment"]["archives_sha256"].items())
            write_json(REPORT / "capture.json", metadata)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    environment = prepare()
    result = capture(environment) if args.capture else environment
    print(json.dumps({"report": str(REPORT), "images": result.get("images", []), "capture_error": result.get("capture_error"),
                      "runtime_diagnostics_count": result.get("runtime_diagnostics_count"), "original_inputs_unchanged": result.get("original_inputs_unchanged")}))
