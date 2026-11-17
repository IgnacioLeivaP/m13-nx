#!/usr/bin/env python3
"""Draws the button-icon variants (PlayStation and Switch) for Magic 2013.

The Xbox icons the game ships are replaced with this repository's own drawings: plain geometry and
letters made here, with no third-party art and no system fonts (nothing that cannot be redistributed).

    py -3 -I tools/mtg13_iconos.py --data <game_folder> [--out <output_folder>]

Input: the game folder the installer prepared, with Data_Core.wad and Update_Data_Core.wad (the user's
own). Output: <out>/mtg13_buttons_ps.bin and <out>/mtg13_buttons_switch.bin: the Title Update's
Update_Data_Core.wad with the button textures swapped. The SDK reads the variant the player picks instead
of Update_Data_Core.wad, which is why they live in the game's data folder.

TDX (Xbox 360): 16-byte little-endian header (u16 0x0200, width, height, levels, u32 flags, u32 format)
and then the pixels. Two formats in this game:
  - format 21 (32-bit BGRA, linear): the four XBOX_A/B/X/Y 64x64 textures.
  - 'DXT5' (0x35545844): the SYMBOLS and SYMBOLS_FE 1024x1024 sheets with 11 levels and a 6060-byte block
    after the header. The 11 levels and that block are kept; the levels from 1024 down to 32 are rebuilt and
    the packed tail smaller than 32 stays as it was.
"""
import argparse
import io
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wad  # noqa: E402

TEX = 'DATA_ALL_PLATFORMS/ART_ASSETS/TEXTURES'
FONTS = 'DATA_ALL_PLATFORMS/ART_ASSETS/FONTS'
HOJAS = ('SYMBOLS.TDX', 'SYMBOLS_FE.TDX')
BOTONES = ('A', 'B', 'X', 'Y')

# The Xbox buttons' boxes in SYMBOLS/SYMBOLS_FE (y0, x0, y1, x1), on the 1024x1024 sheet (84 grid).
CASILLAS = {
    'A': (598, 178, 658, 242), 'B': (598, 262, 658, 326),
    'X': (598, 346, 658, 410), 'Y': (598, 430, 658, 494),
    'LB': (514, 848, 578, 916), 'RB': (514, 932, 578, 1000),
    'LT': (598, 8, 662, 76), 'RT': (598, 92, 662, 160),
    'BACK': (598, 596, 662, 664), 'START': (598, 680, 662, 748),
}

# Colors of the drawings (own shapes and letters, not a copy of any glyph).
AZUL = (58, 106, 200, 255)
ROJO = (206, 60, 60, 255)
ROSA = (216, 96, 176, 255)
VERDE = (66, 172, 96, 255)
GRIS = (86, 92, 104, 255)
CLARO = (240, 242, 246, 255)

DXT5 = 0x35545844
BGRA = 21


def leer_tdx(d):
    """(image, levels, flags, format) of a TDX; the image is the largest level."""
    _, w, h, niveles, banderas, fmt = struct.unpack_from('<HHHHII', d, 0)
    offset = 20 + struct.unpack_from('<I', d, 16)[0] if niveles > 1 else 16
    if fmt == BGRA:
        im = Image.frombuffer('RGBA', (w, h), d[offset:offset + w * h * 4], 'raw', 'BGRA', 0, 1).copy()
    elif fmt == DXT5:
        im = Image.open(io.BytesIO(_dds_cabecera(w, h, w * h) + d[offset:offset + w * h])).convert('RGBA')
    else:
        raise SystemExit('unsupported TDX format: %d (%dx%d)' % (fmt, w, h))
    return im, niveles, banderas, fmt


def _dds_cabecera(w, h, lineal, niveles=0):
    """The DDS header (128 bytes) of a DXT5 of that size, made by Pillow (so it need not be written by hand)."""
    buf = io.BytesIO()
    Image.new('RGBA', (w, h)).save(buf, format='DDS', pixel_format='DXT5')
    cab = bytearray(buf.getvalue()[:128])
    struct.pack_into('<I', cab, 20, lineal)     # pitchOrLinearSize
    struct.pack_into('<I', cab, 28, niveles)    # mipmapCount
    return bytes(cab)


def _dxt5(im):
    """The DXT5 bytes of an image (without the DDS header)."""
    buf = io.BytesIO()
    im.convert('RGBA').save(buf, format='DDS', pixel_format='DXT5')
    return buf.getvalue()[128:]


def escribir_tdx(im, banderas=0x5C8):
    """A new format-21 TDX (32-bit BGRA), single level."""
    im = im.convert('RGBA')
    return struct.pack('<HHHHII', 0x0200, im.width, im.height, 1, banderas, BGRA) + im.tobytes('raw', 'BGRA')


def releer_niveles(original, im, fmt):
    """The original TDX with the 1024-to-32 levels rebuilt with `im`, in the same format."""
    datos = bytearray(original)
    _, w, h, niveles, _, _ = struct.unpack_from('<HHHHII', datos, 0)
    offset = 20 + struct.unpack_from('<I', datos, 16)[0]
    nivel = im
    while nivel.width >= 32:
        if fmt == BGRA:
            pixeles = nivel.tobytes('raw', 'BGRA')
        else:
            pixeles = _dxt5(nivel)
        datos[offset:offset + len(pixeles)] = pixeles
        offset += len(pixeles)
        nivel = nivel.resize((nivel.width // 2, nivel.height // 2), Image.LANCZOS)
    return bytes(datos)


def _fuente():
    """Pillow's bitmap font: no system font files."""
    return ImageFont.load_default()


def texto(txt, ancho, alto, color):
    """The text, as large as fits in width x height, centered on a canvas of that size."""
    f = _fuente()
    lienzo = Image.new('RGBA', (max(1, ancho), max(1, alto)), (0, 0, 0, 0))
    caja = f.getbbox(txt)
    tw, th = caja[2] - caja[0], caja[3] - caja[1]
    if tw <= 0 or th <= 0:
        return lienzo
    base = Image.new('RGBA', (tw + 2, th + 2), (0, 0, 0, 0))
    ImageDraw.Draw(base).text((1 - caja[0], 1 - caja[1]), txt, font=f, fill=color)
    f2 = min(ancho / base.width, alto / base.height)
    nuevo = base.resize((max(1, round(base.width * f2)), max(1, round(base.height * f2))), Image.LANCZOS)
    lienzo.alpha_composite(nuevo, ((ancho - nuevo.width) // 2, (alto - nuevo.height) // 2))
    return lienzo


def forma(tipo, ancho, alto, color):
    """An own drawing of the requested shape, as large as fits in width x height."""
    esc = 4  # drawn large and shrunk: smooth edges
    W, H = max(1, ancho) * esc, max(1, alto) * esc
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    g = max(2, min(W, H) // 10)
    if tipo == 'cruz':
        w = max(2, (W - 2 * g) // 3)
        d.rectangle((W // 2 - w // 2, g, W // 2 + w // 2, H - g), fill=color)
        d.rectangle((g, H // 2 - w // 2, W - g, H // 2 + w // 2), fill=color)
    elif tipo == 'circulo':
        d.ellipse((g, g, W - g, H - g), outline=color, width=max(2, (W - 2 * g) // 6))
    elif tipo == 'cuadrado':
        d.rectangle((g, g, W - g, H - g), outline=color, width=max(2, (W - 2 * g) // 6))
    elif tipo == 'triangulo':
        d.polygon([(W // 2, g), (W - g, H - g), (g, H - g)], outline=color, width=max(2, (W - 2 * g) // 6))
    elif tipo == 'redondo':  # a key's background: readable over light and dark menus
        d.ellipse((0, 0, W - 1, H - 1), fill=color)
    elif tipo == 'pastilla':
        d.rounded_rectangle((0, 0, W - 1, H - 1), radius=max(2, H // 3), fill=color)
    return im.resize((max(1, ancho), max(1, alto)), Image.LANCZOS)


def tecla(txt, ancho, alto, letra=CLARO, fondo=GRIS, forma_fondo='redondo'):
    im = forma(forma_fondo, ancho, alto, fondo)
    im.alpha_composite(texto(txt, int(ancho * 0.72), int(alto * 0.72), letra),
                       (int(ancho * 0.14), int(alto * 0.14)))
    return im


def tecla_forma(tipo, ancho, alto, color, fondo=GRIS):
    """A key with a shape inside (the PlayStation cross, circle, square or triangle)."""
    im = forma('redondo', ancho, alto, fondo)
    dentro = int(ancho * 0.60)
    im.alpha_composite(forma(tipo, dentro, dentro, color), ((ancho - dentro) // 2, (alto - dentro) // 2))
    return im


def dibujos():
    """{style: {button: image}} with each style's shapes and letters."""
    ps = {
        'A': tecla_forma('cruz', 64, 64, AZUL), 'B': tecla_forma('circulo', 64, 64, ROJO),
        'X': tecla_forma('cuadrado', 64, 64, ROSA), 'Y': tecla_forma('triangulo', 64, 64, VERDE),
        'LB': tecla('L1', 64, 64), 'RB': tecla('R1', 64, 64),
        'LT': tecla('L2', 64, 64, forma_fondo='pastilla'), 'RT': tecla('R2', 64, 64, forma_fondo='pastilla'),
        'BACK': tecla('SEL', 64, 64, forma_fondo='pastilla'), 'START': tecla('STA', 64, 64, forma_fondo='pastilla'),
    }
    switch = {
        'A': tecla('A', 64, 64), 'B': tecla('B', 64, 64),
        'X': tecla('X', 64, 64), 'Y': tecla('Y', 64, 64),
        'LB': tecla('L', 64, 64), 'RB': tecla('R', 64, 64),
        'LT': tecla('ZL', 64, 64, forma_fondo='pastilla'), 'RT': tecla('ZR', 64, 64, forma_fondo='pastilla'),
        'BACK': tecla('-', 64, 64, forma_fondo='pastilla'), 'START': tecla('+', 64, 64, forma_fondo='pastilla'),
    }
    return {'ps': ps, 'switch': switch}


def caja(im):
    """(x0, y0, x1, y1) of what is not transparent."""
    a = np.array(im)[:, :, 3]
    ys, xs = np.nonzero(a > 40)
    if not len(xs):
        return (0, 0, im.width, im.height)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def encajar(icono, w, h):
    """The icon at the largest size that fits in w x h without distortion, centered on a w x h canvas."""
    f = min(w / icono.width, h / icono.height)
    nuevo = icono.resize((max(1, round(icono.width * f)), max(1, round(icono.height * f))), Image.LANCZOS)
    lienzo = Image.new('RGBA', (max(1, w), max(1, h)), (0, 0, 0, 0))
    lienzo.alpha_composite(nuevo, ((w - nuevo.width) // 2, (h - nuevo.height) // 2))
    return lienzo


def variante(estilo, dib, core, update, salida):
    """The user's Update_Data_Core.wad with that style's textures swapped."""
    print('  %s: pulling the textures out of %s' % (estilo, os.path.basename(core)))
    with open(core, 'rb') as f:
        posiciones = wad.posiciones(f)
    queridas = {}
    for i, (nombre, _) in wad.rutas(core).items():
        alto = nombre.upper()
        if alto.startswith('DATA_CORE/'):
            alto = alto[len('DATA_CORE/'):]
        if (alto.startswith(TEX + '/XBOX_') and alto.endswith('.TDX')) or alto in [FONTS + '/' + h for h in HOJAS]:
            queridas[alto] = wad.contenido(core, posiciones[i])
    print('  %s: %d game textures' % (estilo, len(queridas)))

    cambios = {}
    for ruta, datos in queridas.items():
        nombre = ruta.rsplit('/', 1)[1]
        if nombre.startswith('XBOX_') and nombre[5:-4] in dib:
            boton = nombre[5:-4]
            im, niveles, banderas, fmt = leer_tdx(datos)
            if im.size != (64, 64) or niveles != 1:
                continue  # the grey ones are compressed: left as they are
            x0, y0, x1, y1 = caja(im)
            nuevo = Image.new('RGBA', im.size, (0, 0, 0, 0))
            nuevo.alpha_composite(encajar(dib[boton], x1 - x0, y1 - y0), (x0, y0))
            cambios[ruta] = escribir_tdx(nuevo, banderas)
        elif nombre.upper() in HOJAS:
            im, niveles, banderas, fmt = leer_tdx(datos)
            for boton, (y0, x0, y1, x1) in CASILLAS.items():
                # The whole 84-pixel box is cleared (it includes the SELECT/START text and the Xbox button
                # edges) and the new drawing goes into the box the old one occupied.
                cx, cy = (x0 // 84) * 84, (y0 // 84) * 84
                im.paste((0, 0, 0, 0), (cx, cy, min(cx + 84, im.width), min(cy + 84, im.height)))
                im.alpha_composite(encajar(dib[boton], x1 - x0, y1 - y0), (x0, y0))
            cambios[ruta] = releer_niveles(datos, im, fmt)

    with open(update, 'rb') as f:
        posiciones = wad.posiciones(f)
    fs = {}
    for i, (nombre, _) in wad.rutas(update).items():
        fs[nombre] = wad.contenido(update, posiciones[i])
    originales = len(fs)
    for ruta, datos in cambios.items():
        fs['UPDATE_DATA_CORE/' + ruta] = datos
    xml, fecha = wad.cabecera(update)
    n = wad.escribir(fs, salida, fecha, xml)
    print('  %s: %s (%d textures changed out of %d; %d in the WAD)' % (estilo, salida, len(cambios), originales, n))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', required=True, help='prepared game folder (Data_Core.wad, Update_Data_Core.wad)')
    ap.add_argument('--out', help='folder where the variants go (default: the same one)')
    a = ap.parse_args()
    core = os.path.join(a.data, 'Data_Core.wad')
    update = os.path.join(a.data, 'Update_Data_Core.wad')
    for p in (core, update):
        if not os.path.exists(p):
            sys.exit('missing %s' % p)
    salida = a.out or a.data
    os.makedirs(salida, exist_ok=True)
    for estilo, dib in dibujos().items():
        variante(estilo, dib, core, update, os.path.join(salida, 'mtg13_buttons_%s.bin' % estilo))
    print('done: 2 variants in %s' % salida)
    return 0


if __name__ == '__main__':
    sys.exit(main())
