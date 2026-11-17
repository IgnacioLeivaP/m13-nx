# How the build fits together

For first-time installation, follow the [numbered README steps](../README.md#start-here).
Prepare original files and dependencies first, build next, then copy only the generated
installation to the SD card. Commands with `^` use Windows **cmd.exe**, not PowerShell.
Other Xbox 360 years are linked in the [series index](../README.md#other-magic--duels-ports-for-nintendo-switch).

`install/install.py` runs these steps for you. This page is the explanation, for when a step fails or when you want to
run them by hand.

```
install/install.py
  |-- 1  tools             python, cmake, ninja, clang, devkitPro, Pillow, numpy, xxhash
  |-- 2  SHA256            default.xex, default.xexp, the Title Update WADs, the 67 decks, the TU and the DLC
  |-- 3  tree              <work>/assets/game_root  +  <work>/app  +  <work>/tools  (+ out/icon.jpg)
  |-- 4  icons             tools/mtg13_iconos.py        -> mtg13_buttons_{ps,switch}.bin
  |-- 5  lua               install/lua13.py             -> out/lua/<modulo>.lua
  |-- 6  shaders           tools/shaders_wad.py, XenosRecomp, tools/deko3d_*.py
  |-- 7  pack              tools/build_asset_pack.py    -> game_root.nxpack/.nxidx
  |-- 8  codegen           rexglue codegen              -> app/generated/
  |-- 9  NRO               cmake + Ninja (devkitA64)    -> mtg13.nro
  `-- 10 final folder      <out>/switch/mtg13-nx/ + SHA256_mtg13-nx.txt
```

The work folder mirrors the layout the CMake files expect (`app/`, `tools/`, `assets/`, `out/` side by side), which is
why the relative paths inside `app/CMakeLists.txt` and `app/cmake/*.cmake` need no changes.

## What you have to supply

### The SDK (`sdk/`, or `--sdk <folder>`)

The ReXGlue fork this port builds against. It contains the code generator (`rexglue codegen`), the Xbox 360 kernel and
runtime, the Horizon (Switch) layer, and the third-party sources the runtime links (FFmpeg for XMA audio, glslang,
SPIRV-Tools, fmt, spdlog, xxHash, toml++…). Its own source and CMake are in `sdk/`; the **large** third parties are
not copied there — fetch them once with `py -3 install/fetch_thirdparty.py` (`--help` explains it; `--source` uses a
local checkout and touches no network).

`--sdk` exists for a tree kept somewhere else; when it is left out, `sdk/` of this repository is used. Build the
generator once with (the installer does this when `<work>/out/host/rexglue.exe` is missing):

```bat
cmake -S <sdk> -B <work>\out\host -G Ninja -DCMAKE_BUILD_TYPE=Release ^
      -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ ^
      -DCMAKE_C_FLAGS=-march=x86-64-v2 -DCMAKE_CXX_FLAGS=-march=x86-64-v2
cmake --build <work>\out\host --target rexglue
```

`-march=x86-64-v2` is required (the SDK uses SSSE3 intrinsics).

This port carries one fix of its own in the SDK: the game looks for its Title Update only on `update:`, so the runtime
mounts it there even when the install has no separate update folder (`sdk/src/system/runtime.cpp`).

### `--thirdparty <folder>`

A folder with the four trees `app/thirdparty/` needs: `plume` (MIT), `uam` (zlib/MIT), `imgui` (MIT) and
`reblue-XenosRecomp` (MIT, Renut's version). The installer junction/copies it into `<work>/app/thirdparty`.

### The NRO icon (`--icon <image>`)

A 256x256 JPEG or PNG of yours. The installer copies it to `<work>/out/icon.jpg`, which is where `app/CMakeLists.txt`
looks for it before configuring the NRO. Without `--icon` (and with no `app/icon.jpg` in the tree) the NRO is built
with no icon. It is never distributed with this repository.

### The PC-side shader tools (step 6)

Translating the game's shaders for the console needs three host programs, built once:

| Program | Where it goes | How |
|---|---|---|
| `spirv-cross.exe` | `<work>/out/deko3d_tools/spirv-cross-build/` | `bash tools/deko3d_build_tools.sh` (SPIRV-Cross sources, Apache-2.0) |
| `uam.exe` | `<work>/out/deko3d_tools/uam-build/` | same script (uam, zlib/MIT) |
| `XenosRecomp.exe` | `<work>/out/pc/xenos_recomp/build/XenosRecomp/` | built by a PC configure of `app/` (`thirdparty/reblue-XenosRecomp` is an ExternalProject) |

`--skip-shaders` leaves them out. The NRO then has no translated game shaders, `deko3d_glsl.bin` is not created and
the renderer logs a warning; the game will not draw correctly, so this is only for checking the rest of the pipeline.

## Step details

**Icons (4).** `mtg13_iconos.py` reads the four `XBOX_A/B/X/Y.TDX` (64x64, BGRA) and the two symbol sheets
`SYMBOLS.TDX` / `SYMBOLS_FE.TDX` (1024x1024, DXT5, 11 mip levels) out of your `Data_Core.wad` with `tools/wad.py`,
draws the PlayStation and Switch glyphs itself (plain geometry and Pillow's built-in bitmap font — no external art and
no font file from the system), and writes `Update_Data_Core.wad` once per style with the six textures replaced: your
147 Title Update entries stay byte for byte as they are. The two resulting WADs go into the game folder, because the
SDK redirects `Update_Data_Core.wad` to the one `update_wad_variant` selects.

**Lua (5).** Three scripts, all built from *your* copy of the game — no script text and no bytecode of the game is
distributed with this repository. Magic 2013 keeps its menus as Lua **text** inside `Data_Core.wad` (next to the
compiled `.LOB` the game loads), so this port patches the text, not the bytecode. Each entry of `lua` in
`install/games/mtg13.json` names its entry inside the WAD and the patch of `install/lua13.py` to apply:

- `carousel` deletes the five statements that add *Leaderboards*, *Multiplayer*, *Achievements* and *Download content*
  to the main menu.
- `enumeration` replaces one function of the "reloading content" notice, so that it stays invisible instead of covering
  the screen for five seconds at every start; the rest of the notice is the game's own.
- `settings` inserts the port's own Lua (language, button icons, DLC state) plus its three rows into the Settings menu,
  and moves the rows it already had so everything fits.

Each patch states how many times every pattern has to match: if your copy of the game is a different build, the
installer stops and says which operation did not match rather than leaving a half-patched menu. It also compares the
SHA256 of what it produced with the file that was tested on the console, and warns when it differs.

**Shaders (6).** `shaders_wad.py` pulls the shader containers (magic `0x102A11xx`) out of the game's WADs into
`out/renut_shader_dump`, named by XXH3 of the container, which is how the renderer looks them up. Then XenosRecomp
translates them to SPIR-V, `deko3d_shaders.py` turns each into uam GLSL and a DKSH, `deko3d_glsl_opt.py` optimises it,
`deko3d_shader_package.py` makes the package, `renut_switch_shader_cache.py` writes the Switch shader table, and
`renut_release_shaders.py` assembles `out/renut_switch_release/` — the file `sd/deko3d_glsl.bin` from there is what
goes on the SD card.

**Code generation (8).** `rexglue codegen mtg13_manifest.toml` runs inside `<work>/app` with
`REX_MAX_JUMP_TABLE_ENTRIES=4096` and `REXGLUE_DUMP_IMAGE=<work>/out/default_image.bin`; it writes `app/generated/`
(the game translated to C++, never committed) and the CMake glue. `app/generated/codegen_profile.txt` records which
profile was used.

**NRO (9).** `cmake -S app -B out/nx -G Ninja` with `tools/switch/cmake/switch-devkitA64.cmake` as the toolchain file,
`-DREXSDK_DIR=<sdk>`, `-DMTG13_RENUT_RENDERER=ON`, `-DMTG13_RENUT_PORT_SHADERS=OFF`. `--lto` adds
`-DMTG13_SWITCH_LTO=ON` for the release link (much slower). The output is `out/nx/mtg13.nro`, whose homebrew-menu
entry says "Magic 2013" by "Nispero". The hand-written native copies of hot guest functions that other ports of this
saga carry (`MTG13_HOT_SOURCES`) are not part of this repository: the build uses the code generator's own output.

**Package (10).** `mtg13.nro`, `game_root.nxpack` + `.nxidx`, `deko3d_glsl.bin`, `lua/` and (optionally) `dlc/` in
`<out>/switch/mtg13-nx/`, plus `SHA256_mtg13-nx.txt` beside it. The game writes its own `mtg13.toml` there on the first
start; there is no settings file to ship.

## Adding another game of the saga

Copy `install/games/mtg13.json`, change the id, the file names, the SHA256 tables, the manifest name and the `lua`
entries (their WAD, entry and patch); add the CMake tree of that game under a folder of its own. `install.py` takes
`--game <id>` and reads everything game-specific from that file.

