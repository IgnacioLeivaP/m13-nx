# mtg13-nx — Magic: The Gathering – Duels of the Planeswalkers 2013 for the Nintendo Switch

<!-- magic-series:start -->
## Other Magic / Duels ports for Nintendo Switch

Each project uses its own game files and installation method. The two 2015 ports are
separate projects; Xbox 360 files cannot be used with the Android port or vice versa.

| Game | Original version | Project and installation guide |
|---|---|---|
| Duels of the Planeswalkers (2009) | Xbox 360 + required PC data | [m09-nx](https://github.com/IgnacioLeivaP/m09-nx#start-here) |
| Magic 2012 | Xbox 360 | [m12-nx](https://github.com/IgnacioLeivaP/m12-nx#start-here) |
| Magic 2013 | Xbox 360 | [m13-nx](https://github.com/IgnacioLeivaP/m13-nx#start-here) |
| Magic 2014 | Android 1.5.0 | [Duels14_nx](https://github.com/IgnacioLeivaP/Duels14_nx#start-here) |
| Magic 2015 | Android 1.4.4959 | [duels_nx](https://github.com/IgnacioLeivaP/duels_nx#start-here) |
| Magic 2015 | Xbox 360 | [m15-nx](https://github.com/IgnacioLeivaP/m15-nx#start-here) |

Otros años: los enlaces llevan a las instrucciones de cada port. Comprueba la versión
de origen antes de preparar los archivos; las versiones Android y Xbox 360 son distintas.
<!-- magic-series:end -->

A **static recompilation** of the Xbox 360 XBLA game *Magic: The Gathering – Duels of the Planeswalkers 2013*
(title `58411213`) to the Nintendo Switch, built with [ReXGlue](https://github.com/rexglue/rexglue-sdk): the game's
PowerPC code is translated to C++ ahead of time and compiled into a native Nintendo Switch program (`.nro`). No
emulator is involved and the console does not run any Xbox code.

**This repository does not contain the game.** Not a single byte of its data, art, audio, video, menu scripts or
translated code is included. You supply your own legally purchased copy; the installer turns it into the folder that
goes on the console's SD card, on your own machine.

---

## Start here

This is a **source release**: build the NRO on Windows from your own game before copying
anything to the Switch. Follow these steps in order:

1. [Check requirements](#step-1--check-requirements), including the exact game and TU.
2. [Prepare original files and dependencies](#step-2--prepare-your-inputs-and-dependencies).
3. [Run the installer](#step-3--build-the-switch-installation) from the repository root.
4. [Copy the generated folder and launch](#step-4--launch-on-the-console) using title takeover.

If a step fails, stop there and read its error; skipping shaders or other required build
stages does not produce a complete installation. Technical details: [docs/BUILD.md](docs/BUILD.md).

## Step 1 — check requirements

A Windows PC (the toolchain is Windows; nothing else is tested):

| What | Why |
|---|---|
| Your own copy of the game | `default.xex`, `Data_Core.wad`, the `Deck_*.WAD` files and the Title Update (`default.xexp`, `Update_Data_Core.wad`, `Update_Data_Decks.wad`). Optional: the DLC packages. |
| Python 3.8 or newer | the installer and the tools, plus `Pillow`, `numpy` and `xxhash` (`py -m pip install Pillow numpy xxhash`) |
| Visual Studio 2022 Build Tools | CMake and Ninja (no MSVC compiler needed) |
| LLVM / clang | to build the ReXGlue code generator |
| [devkitPro](https://devkitpro.org) with the `switch-dev` packages | devkitA64, libnx and deko3d: the console toolchain |
| `git` | to fetch the SDK's large third-party libraries (once) |
| `plume`, `uam`, `imgui`, `reblue-XenosRecomp` | `--thirdparty`; see [THIRD_PARTY.md](THIRD_PARTY.md) |

## Step 2 — prepare your inputs and dependencies

Download and extract this repository's source ZIP, or clone it with Git. Open a Windows
**cmd.exe** terminal in that folder; the examples use `^` for line continuation (not
PowerShell's syntax). Install the tools and Python modules listed in step 1.

Extract your own base game and Title Update into separate input folders. If you have
STFS packages rather than loose files, run the supplied extractor for each package:

```bat
py -3 tools/stfs_extract.py "C:\my-package" "C:\extracted-files"
```

Keep the originals unchanged. Check the required filenames and hashes against the game
profile linked below. Optional DLC can be omitted; the required Title Update cannot.

Fill the SDK dependencies before the first build:

```bat
py -3 install/fetch_thirdparty.py
```

This fetch uses the network. To use an existing SDK checkout with its submodules,
add `--source "C:\local-rexglue-sdk"`. Separately prepare `--thirdparty` with the
port-compatible dependencies listed in [THIRD_PARTY.md](THIRD_PARTY.md). Fetching the
SDK libraries does not supply those application dependencies. Use a new output folder
outside this source repository; keep your source, input game and output folders separate.

## Step 3 — build the Switch installation

```bat
py -3 install\install.py --game mtg13 ^
    --data  "C:\ruta\a\tus\archivos\del\juego" ^
    --dlc   "C:\ruta\a\los\paquetes\dlc" ^
    --tu    "C:\ruta\a\tu\title\update" ^
    --icon  "C:\ruta\a\tu\icono.jpg" ^
    --thirdparty "C:\ruta\a\thirdparty" ^
    --out   "C:\ruta\a\la\salida"
```

`--dlc` and `--icon` are optional. `--tu` can be omitted only when the required TU files
are already available in the supplied data locations. The SDK source is in `sdk/`; prepare its libraries in step 2.

`--data` must contain the game files; `--xex`/`--xexp` can point at them individually if they are elsewhere. Add
`--dry-run` to see every step and command without touching anything. `install\install.py --help` lists the rest.

The NRO's **icon is yours**: `--icon <imagen>` (256x256 JPEG or PNG). Without it the build makes an NRO with no icon;
nothing of the sort is distributed with this repository.

What the installer does, in order:

1. checks Python, CMake, Ninja, clang, devkitPro and the Python modules, and tells you what to install if any is missing;
2. checks the SHA256 of every file you supplied (tables below) and refuses to continue if one does not match;
3. copies the game to a work folder outside the repository;
4. draws the PlayStation and Switch button icon variants from the game's own textures (`tools/mtg13_iconos.py`);
5. builds the menus from *your* copy of the game, on the fly (`install/lua13.py`): the main menu loses the entries that
   need Xbox Live, achievements and the store, the "reloading content" notice stops covering the screen at every start,
   and the Settings menu gains language, button icons and DLC rows. No script text and no bytecode of the game is
   distributed with this repository;
6. translates the game's shaders for the console's GPU (`--skip-shaders` to leave this out);
7. builds the asset pack (`game_root.nxpack` + `.nxidx`);
8. runs the ReXGlue code generator on your `default.xex`;
9. compiles the `.nro` with devkitA64 (with your `--icon`, if given);
10. leaves `switch\mtg13-nx\`, ready for the SD card, next to a `SHA256_mtg13-nx.txt` of everything in it.

Preserve existing saves and settings when updating. Copy only the generated
installation, not the source repository or original Xbox package.

Then copy **that folder** to `sdmc:/switch/` on the console (Hekate's USB mass storage is the most reliable way for
many files; MTP works for single files but its listing went stale in testing — always read back and compare).

### Files you have to provide

| File | Where | SHA256 | Size |
|---|---|---|---|
| `default.xex` | base game (the `58411213` folder of your XBLA copy) | `726e26b408c7cd9078bc60dd3555de6e92c4c55dbb768c03b2e909bf4ace0bc8` | 13 381 632 |
| `default.xexp` | Title Update | `87fda35677d9cfd626123609b52aa4fcb775ca1fca4817247bd5aaff770f8aed` | 907 264 |
| `Data_Core.wad` | base game | `e368c17dcf039e34a8bce361116b35ce749cf664693700f4796971edc56c5bf5` | 477 968 733 |
| `Update_Data_Core.wad` | Title Update | `31db6492020e94cd38e6a165afb8be6bdcc79b9e16aa35fb9c50e0e5fcec610d` | 2 548 730 |
| `Update_Data_Decks.wad` | Title Update | `ff10f9908d730c85e89de90c3c8de7930c3e340d4c09b713489f8d55dcd696e7` | 512 351 |

The Title Update package itself (`TU_1C424GJ_0000004000000.0000000000081`) is checked when you pass `--tu`. Its
SHA256, the 67 `Deck_*.WAD` hashes and the five DLC packages are in
[`install/games/mtg13.json`](install/games/mtg13.json). Without the DLC the base campaign still works.

## Step 4 — launch on the console

Hold **R** while starting any game from the home menu, then open the Homebrew Menu and start `mtg13`. A title takeover
is required: from the Album the applet does not get enough memory.

At its first start the game writes `sdmc:/switch/mtg13-nx/mtg13.toml` with only your options. Everything else is
compiled in.

## What works

- The base game: campaign, single duels, the deck manager and the `Deck_*.WAD` decks of your copy.
- The Title Update: its data WADs are mounted on `update:` (this port carries an SDK fix for that) and the extra cards
  and fixes they contain are the game's own.
- The DLC packages, once they are in `dlc/` (five packs, installed from `dlc/` next to the NRO).
- Languages: the nine the game ships (English, Spanish, French, German, Italian, Japanese, Portuguese, Korean, Russian).
- Button icons: Xbox 360, PlayStation and Nintendo Switch. The installer builds the PlayStation and Switch variants from
  your own textures; the SDK redirects `Update_Data_Core.wad` to the style `update_wad_variant` selects, so all three
  live side by side.
- Settings menu with three rows the original never had: **Language**, **Button icons** and a read-only **DLC** line that
  lists the packs the port found.
- Renders with Renut's Direct3D-level renderer on deko3d, docked and handheld, touch screen as the game's own input.

## Known limitations

Taken from the port's own notes (not everything here could be tested before publishing):

- **Videos are skipped** (the intro and the studio logos); the game goes straight to the menu.
- The main menu keeps the local game, the campaign, the deck manager and the settings; leaderboards, online play,
  achievements and the store are hidden, because there is nothing behind them on a Switch.
- The DLC row reports the packs it found, not what the game actually loaded ("sin verificar").
- Changing the button-icon style takes effect on the next start and the game does not say so.
- Not confirmed on hardware when this repository was prepared: the Switch button icons on screen, a full duel, the DLC
  decks/campaign, the promo of the first start and the "Additional content" entry. Treat those as untested.
- The port's own extra options (frame rate, logging, renderer) are set in `mtg13.toml`, not in a menu.

## What is not in this repository

- `app/thirdparty/` — `plume`, `uam`, `imgui` and `reblue-XenosRecomp`: pass it with `--thirdparty`.
- The **large** third-party libraries of the SDK (`sdk/thirdparty/`): each one has a public repository and its own
  license, so they are fetched instead of copied — `install\fetch_thirdparty.py`. The SDK's own source, its CMake and
  the small dependencies **are** here.
- Any result of running the build: the generated C++ of your game, the asset pack, the shaders, the `.nro`, the button
  icon variants, the patched Lua and the NRO icon.

`docs/BUILD.md` explains what each one is and how to obtain it. Everything else the build needs is here: the port's
own code (`app/`), its configuration (`app/*.toml`), the CMake glue, the toolchain file and the tools.

## Layout

```
app/                the port's own code (C++), its CMake glue and configuration
install/            install.py, lua13.py (the menus), fetch_thirdparty.py and games/mtg13.json
sdk/                the ReXGlue fork this port uses (source and CMake; its big libraries are fetched)
tools/              the tools the installer runs (WAD, Lua, shaders, icons, asset pack) + check_clean.py
docs/BUILD.md       how the pieces fit, step by step
THIRD_PARTY.md      every dependency, its origin and its license
LICENSE               the license of this repository: GNU GPL v3 or later
```

Another game of the saga is installed by adding `install/games/<game>.json` with its own hashes, paths and Lua patches;
the installer is not specific to Magic 2013.

## Credits

This port stands on other people's work: the ReXGlue SDK (Tom Clay, and the Xenia project it derives from), the
Horizon/Switch layer by StevenSND, reNut by masterspike52 and plume by renderbag (the renderer), XenosRecomp by
hedge-dev, uam and deko3d by fincs (devkitPro), and the earlier Magic ports of this saga that share their tools.
See [THIRD_PARTY.md](THIRD_PARTY.md) for the complete list and the licenses.

## Legal notice

This is a **fan project**, made for preservation and personal use on hardware the author owns. It is not affiliated
with, endorsed by or supported by Wizards of the Coast, Hasbro, Stainless Games, Microsoft, Xbox Game Studios or
Nintendo. *Magic: The Gathering* and *Duels of the Planeswalkers* are trademarks of Wizards of the Coast;
*Nintendo Switch* is a trademark of Nintendo; *Xbox 360* is a trademark of Microsoft.

No game data is distributed: you must own the game. Do not redistribute the folder the installer produces, nor any
output of these tools that contains the game's data.

