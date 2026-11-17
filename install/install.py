#!/usr/bin/env python3
"""Installer of the Magic 2013 port for the Nintendo Switch.

Joins YOUR (purchased) game files with this repository's code and leaves a folder ready to copy to the
console's SD card. It redistributes nothing of the game: the data comes from your copy and is only used on
your own machine.

    py -3 install/install.py --game mtg13 --data <game folder> --dlc <optional folder> --out <folder> \
        [--tu <Title Update folder>] [--icon <image.jpg>] [--thirdparty <folder>]

    py -3 install/install.py --game mtg13 --data ... --out ... --dry-run    # only prints the steps

Steps (each one prints what it does; --dry-run prints the command instead of running it):
    1. check tools               python, cmake, ninja, clang, devkitPro, Pillow, xxhash
    2. check files               SHA256 of default.xex, default.xexp, the WADs, the decks, the Title Update and the DLC
    3. prepare the tree          copies the data to <work>/assets/game_root (outside the repository)
    4. icons                     PlayStation and Switch button variants (tools/mtg13_iconos.py)
    5. lua                       the menus: pulled from the user's WAD and patched here (install/lua13.py)
    6. shaders                   the game's containers for the Renut cache and deko3d_glsl.bin
    7. data package              game_root.nxpack + game_root.nxidx (tools/build_asset_pack.py)
    8. generated code            ReXGlue over your default.xex (the generator is built from the SDK)
    9. NRO                       cmake + Ninja with devkitA64 (icon: --icon; without it the NRO has no icon)
   10. final folder              <out>/switch/mtg13-nx/, ready for sdmc:/switch/

The ReXGlue SDK (the port's branch) lives in sdk/; its large third parties are fetched with
install/fetch_thirdparty.py. The app/thirdparty dependencies are not in this repository (size): pass them with
--thirdparty. See README.md and docs/BUILD.md. The NRO icon is an image of yours: it does not travel in the
repository.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # publico/
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
GAMES_DIR = os.path.join(INSTALL_DIR, 'games')
SDK_DIR = os.path.join(REPO, 'sdk')

# The SDK's large third parties: each has its own repository and is fetched with install/fetch_thirdparty.py.
TERCEROS_GRANDES = ('FFmpeg', 'simde', 'sdl3', 'vulkan-headers', 'glslang', 'spirv-tools', 'tracy', 'vulkan-loader',
                    'catch2', 'imgui', 'xxHash', 'moltenvk', 'tomlplusplus', 'spirv-headers',
                    'vulkan-memory-allocator', 'fmt', 'inja')


class InstallError(Exception):
    pass


def log(msg):
    print(msg, flush=True)


def head(n, total, title):
    log('')
    log('[%d/%d] %s' % (n, total, title))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            piece = f.read(1 << 20)
            if not piece:
                break
            h.update(piece)
    return h.hexdigest()


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return ('%d %s' % (n, unit)) if unit == 'B' else ('%.1f %s' % (n, unit))
        n /= 1024.0


def run(cmd, cwd=None, env=None, dry=False, what=None):
    """Runs a command (or prints it, with --dry-run)."""
    texto = ' '.join('"%s"' % c if ' ' in c else c for c in cmd)
    log('    $ %s%s' % (texto, ('   (%s)' % cwd) if cwd else ''))
    if dry:
        return 0
    entorno = dict(os.environ)
    if env:
        entorno.update(env)
    p = subprocess.run(cmd, cwd=cwd, env=entorno)
    if p.returncode != 0 and what:
        raise InstallError('%s failed (code %d); see the output above' % (what, p.returncode))
    return p.returncode


def tool(name, extra_paths=()):
    """Path of a tool from the PATH (or from the given folders)."""
    p = shutil.which(name)
    if p:
        return p
    for carpeta in extra_paths:
        for ext in ('', '.exe', '.bat'):
            c = os.path.join(carpeta, name + ext)
            if os.path.isfile(c):
                return c
    return None


def load_game(game_id):
    path = os.path.join(GAMES_DIR, game_id + '.json')
    if not os.path.isfile(path):
        disponibles = [os.path.splitext(f)[0] for f in os.listdir(GAMES_DIR) if f.endswith('.json')]
        raise InstallError('unknown game "%s"; available: %s' % (game_id, ', '.join(sorted(disponibles))))
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ----------------------------------------------------------------------------- 1. herramientas

def step_tools(args, juego):
    """Checks what is needed. Returns {name: path or None} and the list of problems."""
    faltan = []
    hay = {}
    hay['python'] = sys.executable
    extra = []
    vs = os.environ.get('MTG13_VSDIR', r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools')
    extra += [os.path.join(vs, 'Common7', 'IDE', 'CommonExtensions', 'Microsoft', 'CMake', 'CMake', 'bin'),
              os.path.join(vs, 'Common7', 'IDE', 'CommonExtensions', 'Microsoft', 'CMake', 'Ninja')]
    devkit = os.environ.get('DEVKITPRO') or os.environ.get('MTG13_DEVKITPRO') or r'C:/devkitPro'
    for nombre in ('cmake', 'ninja'):
        hay[nombre] = tool(nombre, extra)
        if not hay[nombre]:
            faltan.append('%s: install the "Visual Studio 2022 Build Tools" (they bring CMake and Ninja) and start '
                          'from a console that has them on the PATH' % nombre)
    hay['clang'] = tool('clang', ['C:/Program Files/LLVM/bin'])
    if not hay['clang']:
        faltan.append('clang: the code generator is built with clang; install LLVM on the PATH')
    hay['git'] = tool('git')
    # devkitPro (devkitA64 + libnx + deko3d)
    if os.path.isdir(devkit):
        hay['devkitpro'] = devkit
        for sub in ('devkitA64/bin/aarch64-none-elf-g++.exe', 'libnx/lib'):
            if not os.path.exists(os.path.join(devkit, sub.replace('/', os.sep))):
                faltan.append('devkitPro at %s is missing %s: install devkitA64 and libnx with devkitProUpdater' %
                              (devkit, sub))
    else:
        hay['devkitpro'] = None
        faltan.append('devkitPro: install it from https://devkitpro.org (switch-dev packages: devkitA64, libnx, '
                      'deko3d) or point DEVKITPRO at it')
    # Python modules the tools use
    for modulo, pista in (('PIL', 'Pillow (py -m pip install Pillow)'),
                          ('numpy', 'numpy (py -m pip install numpy)'),
                          ('xxhash', 'xxhash (py -m pip install xxhash)')):
        try:
            __import__(modulo)
            hay[modulo] = True
        except ImportError:
            hay[modulo] = None
            faltan.append('Python module %s: %s' % (modulo, pista))
    if not args.sdk:
        faltan.append('the ReXGlue SDK: there is no sdk/ in the repository; pass it with --sdk <folder> (see README)')
    elif not os.path.isfile(os.path.join(args.sdk, 'CMakeLists.txt')):
        faltan.append('--sdk %s does not look like an SDK tree (CMakeLists.txt is missing)' % args.sdk)
    else:
        hay['sdk'] = args.sdk
        sin_terceros = [n for n in TERCEROS_GRANDES
                        if not os.path.isdir(os.path.join(args.sdk, 'thirdparty', n))]
        if sin_terceros:
            faltan.append('the SDK third parties missing in %s (%s): fetch them with '
                          '"py -3 install/fetch_thirdparty.py"'
                          % (os.path.join(args.sdk, 'thirdparty'), ', '.join(sin_terceros)))
    if not args.thirdparty:
        faltan.append('--thirdparty <folder with plume, uam, imgui and reblue-XenosRecomp> (see THIRD_PARTY.md)')
    elif not os.path.isdir(args.thirdparty):
        faltan.append('--thirdparty %s does not exist' % args.thirdparty)
    return hay, faltan


# ----------------------------------------------------------------------------- 2. archivos

def step_verify(args, juego):
    """SHA256 of everything that must be supplied. A different or missing file stops the install."""
    problemas = []
    vistos = {}
    # --xex / --xexp override whatever is in --data (the user may keep them separate).
    sueltos = {}
    for nombre, ruta in (('default.xex', args.xex), ('default.xexp', args.xexp)):
        if ruta:
            sueltos[nombre] = os.path.abspath(ruta)

    def comprueba(entrada, carpeta, tipo):
        nombre = entrada['file']
        ruta = sueltos.get(nombre) or os.path.join(carpeta, nombre)
        if not os.path.isfile(ruta):
            problemas.append('missing %s (%s) in %s' % (nombre, entrada.get('info', ''), carpeta))
            return None
        tam = os.path.getsize(ruta)
        if tam != entrada['size']:
            problemas.append('%s: %s bytes, expected %d (%s)' % (nombre, tam, entrada['size'],
                                                                 entrada.get('info', '')))
            return None
        h = sha256(ruta)
        if h != entrada['sha256']:
            problemas.append('%s: SHA256 %s, expected %s (%s). Is it the %s version?' %
                             (nombre, h[:16] + '...', entrada['sha256'][:16] + '...', entrada.get('info', ''), tipo))
            return None
        log('    OK  %-58s %s' % (nombre, human(tam)))
        vistos[nombre] = ruta
        return ruta

    log('  game data (--data):')
    for entrada in juego['required']:
        comprueba(entrada, args.data, 'base')
    if args.tu and os.path.isdir(args.tu):
        log('  Title Update (--tu):')
        for entrada in juego.get('optional', []):
            comprueba(entrada, args.tu, 'Title Update')
    elif juego.get('optional'):
        log('    (no --tu: the Title Update package that carries default.xexp and the Update_Data_*.wad is not checked)')
    if juego.get('decks'):
        log('  decks (Deck_*.WAD from --data):')
        malos = 0
        for entrada in juego['decks']:
            if not comprueba(entrada, args.data, 'base'):
                malos += 1
        if malos:
            log('    (%d deck(s) do not match: the list is above)' % malos)
    if args.dlc:
        log('  downloadable content (--dlc):')
        for entrada in juego['dlc']:
            ruta = comprueba(entrada, args.dlc, 'DLC')
            if ruta:
                vistos[entrada['file']] = ruta
    for p in problemas:
        log('    !! ' + p)
    if problemas:
        raise InstallError('%d file(s) do not match: nothing is installed' % len(problemas))
    return vistos


# ----------------------------------------------------------------------------- 3. arbol de trabajo

def step_stage(args, juego, archivos):
    """Copies the data to <work>/assets/game_root and the port's code to <work>/app and <work>/tools."""
    work = args.work
    if not os.path.isdir(args.data):
        raise InstallError('--data %s does not exist' % args.data)
    if args.dry_run:
        log('    $ copy %s -> %s (without the mtg13_buttons_* variants)' % (args.data,
                                                                            os.path.join(work, 'assets',
                                                                                         'game_root')))
        log('    $ copy %s/app and %s/tools -> %s' % (REPO, REPO, work))
        log('    $ link %s -> %s/app/thirdparty' % (args.thirdparty or '<--thirdparty>', work))
        return work
    for sub in ('assets/game_root', 'app', 'tools', 'out'):
        os.makedirs(os.path.join(work, sub), exist_ok=True)
    go = os.path.join(work, 'assets', 'game_root')
    copiados = 0
    for nombre in sorted(os.listdir(args.data)):
        origen = os.path.join(args.data, nombre)
        if os.path.isfile(origen):
            # The icon variants are generated here: another install's ones are not copied.
            if nombre.startswith('mtg13_buttons_'):
                continue
            shutil.copy2(origen, os.path.join(go, nombre))
            copiados += 1
        elif os.path.isdir(origen):
            if nombre.lower() in ('cache', 'logs'):
                continue
            shutil.copytree(origen, os.path.join(go, nombre), dirs_exist_ok=True)
            copiados += 1
    for nombre, ruta in (('default.xex', args.xex), ('default.xexp', args.xexp)):
        if ruta:
            shutil.copy2(os.path.abspath(ruta), os.path.join(go, nombre))
    log('    %d entries from %s -> %s (%s)' % (copiados, args.data, go,
                                               human(sum(os.path.getsize(os.path.join(r, f))
                                                         for r, _, fs in os.walk(go) for f in fs))))
    # The port's code: the app and the tools (their cmake relative paths: ../assets, ../out).
    for nombre in ('app', 'tools'):
        destino = os.path.join(work, nombre)
        if os.path.isdir(destino):
            shutil.rmtree(destino)
        shutil.copytree(os.path.join(REPO, nombre), destino)
    log('    app/ and tools/ copied into %s' % work)
    # thirdparty (plume, uam, imgui, reblue-XenosRecomp): linked if possible, copied otherwise.
    tp = os.path.join(work, 'app', 'thirdparty')
    if os.path.isdir(tp):
        shutil.rmtree(tp)
    if not enlaza(args.thirdparty, tp):
        log('    copying thirdparty (this can take a while: hundreds of MB)')
        shutil.copytree(args.thirdparty, tp)
    # The NRO icon is the user's: left where CMake looks for it (out/icon.jpg) before configuring.
    if args.icon:
        if not os.path.isfile(args.icon):
            raise InstallError('--icon %s does not exist' % args.icon)
        os.makedirs(os.path.join(work, 'out'), exist_ok=True)
        shutil.copy2(os.path.abspath(args.icon), os.path.join(work, 'out', 'icon.jpg'))
        log('    NRO icon: %s' % args.icon)
    return work


def enlaza(origen, destino):
    """A directory link if the system allows it (Windows: junction). True if it was made."""
    try:
        subprocess.run(['cmd', '/c', 'mklink', '/J', destino, origen], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        try:
            os.symlink(origen, destino, target_is_directory=True)
            return True
        except Exception:
            return False


# ----------------------------------------------------------------------------- 4. iconos

def step_icons(args, juego, work):
    go = os.path.join(work, 'assets', 'game_root')
    if args.skip_icons:
        log('    (skipped by --skip-icons: the game will use the Xbox icons)')
        return
    run([sys.executable, os.path.join('tools', 'mtg13_iconos.py'), '--data', go, '--out', go],
        cwd=work, dry=args.dry_run, what='the icons')
    for estilo in ('ps', 'switch'):
        p = os.path.join(go, 'mtg13_buttons_%s.bin' % estilo)
        if not args.dry_run and not os.path.isfile(p):
            raise InstallError('%s was not created' % p)


# ----------------------------------------------------------------------------- 5. lua

def step_lua(args, juego, work):
    """The menus, generated here from the .LUA of the user's WAD.

    Each `lua` entry names its module inside the WAD and the install/lua13.py patch applied to it. None of
    this travels in the repository: the game's text is the user's and the operations are ours.
    """
    if not juego.get('lua'):
        return
    destino = os.path.join(work, 'out', 'lua')
    base = os.path.join(work, 'assets', 'game_root')
    if args.dry_run:
        for entrada in juego['lua']:
            log('    $ pull %s from %s and apply the "%s" patch -> out/lua/%s'
                % (entrada['entry'], entrada['wad'], entrada['patch'], entrada['out']))
        return
    sys.path.insert(0, os.path.join(work, 'tools'))
    import wad  # noqa: E402  (the copy of the work tree)
    sys.path.insert(0, INSTALL_DIR)
    import lua13  # noqa: E402
    os.makedirs(destino, exist_ok=True)
    for entrada in juego['lua']:
        ruta_wad = os.path.join(base, entrada['wad'])
        with open(ruta_wad, 'rb') as f:
            posiciones = wad.posiciones(f)
        datos = None
        for indice, (nombre, _) in wad.rutas(ruta_wad).items():
            if nombre.upper() == entrada['entry'].upper():
                datos = wad.contenido(ruta_wad, posiciones[indice])
        if datos is None:
            raise InstallError('%s does not contain %s' % (ruta_wad, entrada['entry']))
        try:
            salida_datos = lua13.apply(entrada['patch'], datos)
        except lua13.PatchError as e:
            raise InstallError('%s: %s' % (entrada['entry'], e))
        salida = os.path.join(destino, entrada['out'])
        with open(salida, 'wb') as f:
            f.write(salida_datos)
        h = lua13.sha256(salida_datos)
        log('    %-46s %s  %s' % (entrada['out'], human(len(salida_datos)), entrada.get('info', '')))
        if entrada.get('sha256') and h != entrada['sha256']:
            log('    (warning) the SHA256 is not the one of the file tested on the console (%s... instead of '
                '%s...): your copy of the game may be another version' % (h[:12], entrada['sha256'][:12]))


# ----------------------------------------------------------------------------- 6. shaders

def step_shaders(args, juego, work):
    go = os.path.join(work, 'assets', 'game_root')
    dump = os.path.join(work, 'out', 'renut_shader_dump')
    wads = [os.path.join(go, nombre) for nombre in
            juego.get('shader_wads', [e['file'] for e in juego['required'] if e['file'].endswith('.wad')])]
    run([sys.executable, os.path.join('tools', 'shaders_wad.py')] + wads + ['--out', dump],
        cwd=work, dry=args.dry_run, what='the game shaders')
    if args.skip_shaders:
        log('    (--skip-shaders: the NRO is left without the game shaders and warns at startup)')
        return
    glsl = os.path.join(work, 'out', 'deko3d_shaders', 'glsl_opt')
    xenos = os.path.join(work, 'out', 'pc', 'xenos_recomp', 'build', 'XenosRecomp', 'XenosRecomp.exe')
    if not args.dry_run:
        faltan = [n for n, p in (('XenosRecomp', xenos),
                                 ('spirv-cross', os.path.join(work, 'out', 'deko3d_tools', 'spirv-cross-build',
                                                              'spirv-cross.exe')),
                                 ('uam', os.path.join(work, 'out', 'deko3d_tools', 'uam-build', 'uam.exe')))
                  if not os.path.isfile(p)]
        if faltan:
            raise InstallError(
                'the PC shader tools are missing: %s. Build them once with '
                'tools/deko3d_build_tools.sh (spirv-cross and uam) and the Renut PC tree (XenosRecomp); '
                'see docs/BUILD.md, step 3. If you do not want them now: --skip-shaders.' % ', '.join(faltan))
    run([xenos, dump, os.path.join(work, 'out', 'deko3d_shaders', 'scratch_cache.cpp'),
         os.path.join('app', 'thirdparty', 'reblue-XenosRecomp', 'XenosRecomp', 'shader_common.h')],
        cwd=work, dry=args.dry_run, what='XenosRecomp',
        env={'BANJO_DEKO3D_SPIRV_DIR': os.path.join(work, 'out', 'deko3d_shaders', 'spirv')})
    run([sys.executable, os.path.join('tools', 'deko3d_shaders.py'), '--spirv',
         os.path.join(work, 'out', 'deko3d_shaders', 'spirv'), '--out', os.path.join(work, 'out', 'deko3d_shaders'),
         '--jobs', str(args.jobs)], cwd=work, dry=args.dry_run, what='deko3d_shaders.py')
    run([sys.executable, os.path.join('tools', 'deko3d_glsl_opt.py'), '--in',
         os.path.join(work, 'out', 'deko3d_shaders', 'glsl'), '--out', glsl, '--check'],
        cwd=work, dry=args.dry_run, what='deko3d_glsl_opt.py')
    run([sys.executable, os.path.join('tools', 'deko3d_shader_package.py'), '--glsl', glsl, '--out',
         os.path.join(work, 'out', 'renut_switch')], cwd=work, dry=args.dry_run, what='deko3d_shader_package.py')
    run([sys.executable, os.path.join('tools', 'renut_switch_shader_cache.py'), '--pc',
         os.path.join(work, 'out', 'pc')], cwd=work, dry=args.dry_run, what='renut_switch_shader_cache.py')
    run([sys.executable, os.path.join('tools', 'renut_release_shaders.py'), '--glsl', glsl],
        cwd=work, dry=args.dry_run, what='renut_release_shaders.py')


# ----------------------------------------------------------------------------- 7. paquete

def step_pack(args, juego, work):
    go = os.path.join(work, 'assets', 'game_root')
    run([sys.executable, os.path.join('tools', 'build_asset_pack.py'), go, '--out-dir',
         os.path.join(work, 'out', 'pack'), '--verify'], cwd=work, dry=args.dry_run, what='the data package')


# ----------------------------------------------------------------------------- 8. codigo generado

def step_codegen(args, juego, work):
    if not args.sdk and not args.dry_run:
        raise InstallError('--sdk is missing (the port\'s ReXGlue SDK tree)')
    sdk = os.path.abspath(args.sdk) if args.sdk else '<--sdk>'
    host = os.path.join(work, 'out', 'host')
    rexglue = os.path.join(host, 'rexglue.exe')
    if args.dry_run or not os.path.isfile(rexglue):
        cmake = shutil.which('cmake') or 'cmake'
        run([cmake, '-S', sdk, '-B', host, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_C_COMPILER=clang', '-DCMAKE_CXX_COMPILER=clang++',
             '-DCMAKE_C_FLAGS=-march=x86-64-v2', '-DCMAKE_CXX_FLAGS=-march=x86-64-v2'],
            dry=args.dry_run, what='the generator configuration')
        run([cmake, '--build', host, '--target', 'rexglue', '-j', str(args.jobs)],
            dry=args.dry_run, what='the generator build')
        log('    (the generator stays in %s)' % host)
    env = dict(juego.get('codegen', {}).get('env', {}))
    env['REXGLUE_DUMP_IMAGE'] = os.path.join(work, 'out', 'default_image.bin')
    app = os.path.join(work, 'app')
    run([rexglue, 'codegen', juego['codegen']['manifest']], cwd=app, env=env, dry=args.dry_run,
        what='the code generator')
    if not args.dry_run:
        perfil = os.path.join(app, 'generated', 'codegen_profile.txt')
        os.makedirs(os.path.dirname(perfil), exist_ok=True)
        with open(perfil, 'w', encoding='ascii') as f:
            f.write(juego['codegen']['profile'])


# ----------------------------------------------------------------------------- 9. NRO

def step_build(args, juego, work):
    devkit = os.environ.get('DEVKITPRO') or os.environ.get('MTG13_DEVKITPRO') or 'C:/devkitPro'
    cmake = shutil.which('cmake') or 'cmake'
    sdk = os.path.abspath(args.sdk) if args.sdk else '<--sdk>'
    toolchain = os.path.join(work, 'tools', 'switch', 'cmake', 'switch-devkitA64.cmake')
    bdir = os.path.join(work, 'out', 'nx')
    cmd = [cmake, '-S', os.path.join(work, 'app'), '-B', bdir, '-G', 'Ninja',
           '-DCMAKE_BUILD_TYPE=Release',
           '-DCMAKE_TOOLCHAIN_FILE=%s' % toolchain,
           '-DREXSDK_DIR=%s' % sdk,
           '-DMTG13_RENUT_RENDERER=ON',
           '-DMTG13_RENUT_PORT_SHADERS=OFF',
           '-DMTG13_SWITCH_LTO=%s' % ('ON' if args.lto else 'OFF'),
           '-DPython3_EXECUTABLE=%s' % sys.executable]
    if args.nvk_sdk:
        cmd.append('-DREXGLUE_SWITCH_NVK_SDK=%s' % os.path.abspath(args.nvk_sdk))
    run(cmd, cwd=work, env={'DEVKITPRO': devkit}, dry=args.dry_run, what='the NRO configuration')
    run([cmake, '--build', bdir, '-j', str(args.jobs)], cwd=work, env={'DEVKITPRO': devkit}, dry=args.dry_run,
        what='the NRO build')


# ----------------------------------------------------------------------------- 10. carpeta final

def step_package(args, juego, work):
    final = os.path.join(args.out, 'switch', juego['sd_folder'])
    os.makedirs(os.path.join(final, 'lua'), exist_ok=True)
    copiado = []

    def pon(origen, nombre, obligatorio=True):
        if args.dry_run:
            log('    $ %s -> %s' % (origen, nombre))
            return
        if not os.path.isfile(origen):
            if obligatorio:
                raise InstallError('%s does not exist (a previous step did not finish)' % origen)
            log('    (warning) %s is missing: %s is not copied' % (origen, nombre))
            return
        shutil.copy2(origen, os.path.join(final, nombre))
        copiado.append((nombre, os.path.getsize(origen)))

    pon(os.path.join(work, 'out', 'nx', juego['nro']), juego['nro'])
    pon(os.path.join(work, 'out', 'pack', juego['pack_name'] + '.nxpack'), juego['pack_name'] + '.nxpack')
    pon(os.path.join(work, 'out', 'pack', juego['pack_name'] + '.nxidx'), juego['pack_name'] + '.nxidx')
    pon(os.path.join(work, 'out', 'renut_switch_release', 'sd', 'deko3d_glsl.bin'), 'deko3d_glsl.bin',
        obligatorio=not args.skip_shaders)
    lua_out = os.path.join(work, 'out', 'lua')
    if os.path.isdir(lua_out):
        for nombre in sorted(os.listdir(lua_out)):
            if nombre.endswith(('.lua', '.luac')):
                if not args.dry_run:
                    shutil.copy2(os.path.join(lua_out, nombre), os.path.join(final, 'lua', nombre))
                    copiado.append(('lua/' + nombre, os.path.getsize(os.path.join(lua_out, nombre))))
    if args.dlc:
        os.makedirs(os.path.join(final, 'dlc'), exist_ok=True)
        for entrada in juego['dlc']:
            origen = os.path.join(args.dlc, entrada['file'])
            if args.dry_run:
                log('    $ %s -> dlc/%s' % (origen, entrada['file']))
            elif os.path.isfile(origen):
                shutil.copy2(origen, os.path.join(final, 'dlc', entrada['file']))
                copiado.append(('dlc/' + entrada['file'], os.path.getsize(origen)))
    log('')
    log('  SD card folder: %s' % final)
    for nombre, tam in copiado:
        log('    %-64s %s' % (nombre, human(tam)))
    if not args.dry_run:
        # The SHA256 table, to check the copy to the console without computing it again.
        tabla = os.path.join(args.out, 'switch', 'SHA256_%s.txt' % juego['sd_folder'])
        with open(tabla, 'w', encoding='ascii', newline='\n') as f:
            for base, _, ficheros in os.walk(final):
                for nombre in sorted(ficheros):
                    ruta = os.path.join(base, nombre)
                    rel = './' + os.path.relpath(ruta, final).replace(os.sep, '/')
                    f.write('%s *%s\n' % (sha256(ruta), rel))
        log('')
        log('  SHA256 of the folder: %s' % tabla)
        log('    py -3 -c "import hashlib,os;[print(hashlib.sha256(open(os.path.join(r,f),\'rb\').read()).hexdigest(), f) for r,d,fs in os.walk(\'%s\') for f in fs]"'
            % juego['sd_folder'])
    log('')
    log('  Copy THAT folder to sdmc:/switch/ on the console (dragging from the PC, or with Hekate/MTP),')
    log('  and on the console start the NRO with a takeover (hold R while opening a game, then the Homebrew Menu):')
    log('  from the Album it does not get enough memory. The first time the game writes its settings')
    log('  (%s.toml) next to the NRO.' % juego['id'])
    return final


# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', default='mtg13', help='game to install (install/games/<game>.json); default mtg13')
    ap.add_argument('--xex', help='default.xex of your copy (usually already in --data)')
    ap.add_argument('--xexp', help='default.xexp of the Title Update (usually already in --data)')
    ap.add_argument('--data', required=True, help='folder with the game data (default.xex, *.wad, Deck_*.WAD)')
    ap.add_argument('--dlc', help='folder with the purchased DLC packages (optional)')
    ap.add_argument('--tu', help='folder with the Title Update package (optional, only to check its SHA256)')
    ap.add_argument('--icon', help='NRO image (a 256x256 JPEG/PNG of yours); without it the NRO has no icon')
    ap.add_argument('--out', required=True, help='folder where switch/<game>-nx/ goes')
    ap.add_argument('--work', help='work folder (default <out>/../<game>_build); outside the repository')
    ap.add_argument('--sdk', help='the ReXGlue SDK tree (default: sdk/ of the repository)')
    ap.add_argument('--thirdparty', help='folder with plume, uam, imgui and reblue-XenosRecomp')
    ap.add_argument('--nvk-sdk', help='Mesa portlibs/switch (only if linking NVK; not needed)')
    ap.add_argument('--jobs', type=int, default=os.cpu_count() or 8, help='parallel jobs (default: CPUs)')
    ap.add_argument('--lto', action='store_true', help='link with LTO (slower; the final NRO uses it)')
    ap.add_argument('--skip-icons', action='store_true', help='do not create the icon variants')
    ap.add_argument('--skip-shaders', action='store_true', help='do not translate the game shaders')
    ap.add_argument('--dry-run', action='store_true', help='print the steps without running anything')
    args = ap.parse_args()

    args.data = os.path.abspath(args.data)
    args.out = os.path.abspath(args.out)
    args.work = os.path.abspath(args.work or os.path.join(os.path.dirname(args.out), args.game + '_build'))
    args.sdk = os.path.abspath(args.sdk) if args.sdk else (SDK_DIR if os.path.isdir(SDK_DIR) else None)
    args.thirdparty = os.path.abspath(args.thirdparty) if args.thirdparty else None
    t0 = time.time()
    log('installer for %s (%s)' % (args.game, 'simulation, nothing runs' if args.dry_run else 'for real'))
    log('  data:   %s' % args.data)
    log('  output: %s' % args.out)
    log('  work:   %s' % args.work)

    try:
        juego = load_game(args.game)
        total = 10
        head(1, total, 'tools')
        hay, faltan = step_tools(args, juego)
        for nombre, p in sorted(hay.items()):
            if p:
                log('    OK  %s' % nombre)
        if faltan:
            log('')
            log('  Missing to be able to install:')
            for f in faltan:
                log('    - %s' % f)
            if not args.dry_run:
                raise InstallError('tools are missing (above); nothing is touched')
            log('  (--dry-run: the steps are printed anyway)')
        head(2, total, 'game files')
        step_verify(args, juego)
        head(3, total, 'work tree')
        step_stage(args, juego, None)
        head(4, total, 'button icons')
        step_icons(args, juego, args.work)
        head(5, total, 'Lua menus')
        step_lua(args, juego, args.work)
        head(6, total, 'shaders')
        step_shaders(args, juego, args.work)
        head(7, total, 'data package')
        step_pack(args, juego, args.work)
        head(8, total, 'generated code (ReXGlue)')
        step_codegen(args, juego, args.work)
        head(9, total, 'NRO')
        step_build(args, juego, args.work)
        head(10, total, 'final folder')
        final = step_package(args, juego, args.work)
    except InstallError as e:
        log('')
        log('ERROR: %s' % e)
        return 1
    except KeyboardInterrupt:
        log('')
        log('interrupted')
        return 130
    log('')
    log('done in %d s (%s)' % (time.time() - t0, final))
    return 0


if __name__ == '__main__':
    sys.exit(main())
