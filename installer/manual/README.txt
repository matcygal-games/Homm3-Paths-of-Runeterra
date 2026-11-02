HEROES III: PATHS OF RUNETERRA V7 - MANUAL ZIP

1. Extract the entire ZIP into a new folder on a local NTFS drive.
   Keep it separate from your original Heroes III installation.
2. Double-click setup.cmd. It finds Heroes III or asks for the folder
   containing Data and Mp3, then checks all 79 required files with SHA-256.
3. When setup succeeds, double-click launch.cmd to play.

Includes the VCMI runtime and V7 Runeterra mods. You must separately own
and install compatible Heroes III data. Original game data and music,
Python, personal profiles and saves are not included. Setup does not
launch the game, install shortcuts or modify original Heroes III files.

Your settings, saves, logs, cache and temporary files stay in this copy's
user folder. Setup links app\Data and app\Mp3 to the original installation;
keep that installation available. No administrator rights are normally
needed. Quick spells, hero information windows and the battle queue start
hidden; existing settings and saves are preserved when setup is rerun.

If you move this extracted folder, rerun setup.cmd before playing.
To use another Heroes III installation, extract a fresh copy of the ZIP.
Do not merge the ZIP into an existing VCMI or Runeterra installation.

Command-line setup (PowerShell 5.1 or later, supplied with Windows):
  .\setup.ps1 -GameDirectory "D:\Games\Heroes III" -NonInteractive
Read-only compatibility check; no folders or links are created:
  .\setup.ps1 -GameDirectory "D:\Games\Heroes III" -ValidateOnly -NonInteractive
HOMM3_PATH may also specify the original Heroes III folder.

If setup reports different game data, select a compatible installation;
do not replace files in your original installation to bypass the check.
Read the included credits and licences for the runtime and mods.
