# Windows installer

The Inno Setup installer in `installer/windows/paths-v7.iss` packages the V7 VCMI runtime and mod files. It does not include original Heroes III game data or a personal profile. It detects common GOG and Steam installations and allows the player to select another folder. The selected installation must match the 79 SHA-256 checks in the V7 game-data contract.

The installer creates a separate profile, Start menu shortcuts, an optional desktop shortcut and an uninstaller. The quick spell panel, hero statistics windows and battle queue are hidden by default. Game data is accessed through junctions; uninstalling removes those junctions without following them and preserves saved games.

The installer is unsigned. Public distribution still requires the [rights review](RIGHTS_AND_RELEASE.md).

## Build

Install Inno Setup 7 and Python, then provide the V7 profile, reviewed application payload and game-data contract:

```powershell
.\installer\windows\build.ps1 -V7Profile "<V7 profile>" -ReviewedPayload "<reviewed staging>\Payload\app" -GameContract "<reviewed staging>\Installer\homm3-source-contract.json"
```

The build checks the V7 manifest, compares included mod files by hash, checks the omission list, scans text for personal paths and rejects game archives. Thirteen metadata/readme files are excluded because they are not runtime content and some contain personal paths. Three credits files omitted from the older payload are restored after a privacy check.

## Compare the payload

To compare the packaged mod files with the source profile:

```powershell
python -m dev.audit_installer_payload --source "<V7 profile>\app\Mods" --payload "<installer staging>\Payload\app\Mods"
```

This is a development installer. Gameplay, clean-machine installation and redistribution approval require their own checks; a matching file inventory does not complete those checks.

## Manual ZIP

The manual package includes the V7 mods and VCMI runtime, with setup and launch scripts. Players need their own compatible **Heroes of Might and Magic III: Complete** installation. Original game data, music, personal settings and saved games are excluded from the ZIP.

1. Extract the entire ZIP into a new folder on a local NTFS drive, outside the original game folder.
2. Run `setup.cmd` and select the Heroes III folder if it is not detected.
3. Run `launch.cmd` after setup succeeds.

Setup checks the 79 required game files before creating links to `Data` and `Mp3`. Settings and saves belong to the extracted copy's `user/` folder. Quick spells, hero information windows and the battle queue start hidden. Rerunning setup preserves existing settings and saves; rerun it after moving the extracted folder.

Build a new ZIP with Python from the source checkout:

```powershell
python installer/manual/build.py --profile "<V7 profile>" --payload "<reviewed staging>\Payload\app" --game-contract "<reviewed staging>\Installer\homm3-source-contract.json" --output "build\manual\Paths-of-Runeterra-V7-Manual.zip"
```

The builder uses `installer/manual/payload.lock.json` to check the reviewed file inventory. It restores the three credits files, includes license notices and known engine patches, then verifies every ZIP member against its SHA-256 manifest. The ZIP is finalized only after those checks pass. Its companion `.SHA256SUMS` file records the archive checksum. Python is needed to build the package, not to set it up or play.
