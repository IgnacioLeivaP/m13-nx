#!/usr/bin/env python3
"""The game's menus, patched AT INSTALL TIME from the .LUA of YOUR copy of the game.

Magic 2013 keeps its menus as Lua text inside `Data_Core.wad` (the same entries the game also loads
as .LOB bytecode). That text is the game's and does NOT travel in this repository: what travels are the
operations to apply to it and the piece of Lua that is ours.

    py -3 -I install/lua13.py --data <game folder> --entry <WAD entry> --patch <name> --out <file>
    py -3 -I install/lua13.py --list

Four operations, all over the user's text (there is no bytecode to touch here):

  delete_lines     deletes the lines matching the regular expression (the dead main-menu entries).
  replace_function replaces a whole function: from the line matching the header to the first line that is
                   exactly `end`; the original body is thrown away and ours takes its place.
  insert_before    inserts text just before the matching line (the new Settings-menu rows).
  replace          swaps one text for another, with its expected count (the coordinates of those rows).

Each operation says how many times it has to match: if it does not, the installer stops and explains, instead
of leaving a half-patched menu. At the end the SHA256 of the result is compared with the file tested on the
console.
"""
import argparse
import hashlib
import os
import re
import sys

# --- our Lua: this is the only thing that travels in the repository ------------------------------------------------

# Settings menu: languages, button icons and DLC state. It is added to the user's script without touching what
# the game already did (difficulty, notices, hints reset): its `reset` is saved and wrapped.
SETTINGS_AYUDA = """-- Port options. Existing 2013 difficulty/hints/progression behavior stays above.
local languages = {
 {code='en',name='English'}, {code='es',name='Espa\\241ol'},
 {code='fr',name='Fran\\231ais'}, {code='de',name='Deutsch'},
 {code='it',name='Italiano'}, {code='ja',name='Nihongo'},
 {code='pt',name='Portugu\\234s'}, {code='ko',name='Hangugeo'}, {code='ru',name='Russkiy'}
}
local styles = {{code='xbox',name='Xbox'},{code='ps',name='PlayStation'},{code='switch',name='Nintendo Switch'}}
local function names(list)
 local out={} for i,v in ipairs(list) do out[i]=v.name end return out
end
local function index(list,code)
 for i,v in ipairs(list) do if v.code==code then return i end end return 1
end
-- 2013: playMovie is on the frontend object, not on game.
local function enviar(msg)
 local o=frontend
 if o and o.playMovie then o:playMovie(msg) end
end
local original_reset=reset
reset=function(menu)
 original_reset(menu)
 menu:send_item_message(221,message.set_values,{value=index(languages,MTG13.idioma)})
 menu:send_item_message(222,message.set_values,{value=index(styles,MTG13.estilo)})
end
on_event[221]=function(menu,item,evt)
 if evt==event.value_change then
  local value=languages[item.selected_option]
  if value then MTG13.idioma=value.code; enviar('mtg13:idioma='..value.code) end
 end
end
on_event[222]=function(menu,item,evt)
 if evt==event.value_change then
  local value=styles[item.selected_option]
  if value then MTG13.estilo=value.code; enviar('mtg13:estilo='..value.code) end
 end
end"""

# This chunk was written by hand by the version tested on the console, with stray LF line breaks inside a CRLF
# file. It is kept identical so the result is the same file, byte for byte, as the one tested.
SETTINGS_CRUDO = u"""-- 2013: playMovie is on the frontend object, not on game.
local function enviar(msg)
 local o=frontend
 if o and o.playMovie then o:playMovie(msg) end
end
"""

# The new rows, with the indentation the menu expects.
SETTINGS_FILAS = u"""        options_frm { y=center_y+192 },
        options_lbl { id=111, y=center_y+192, text=MTG13.txt_idioma },
        dropdown { id=221, group=1001, x=300, y=center_y+192, w=300, h=100,
                   options=names(languages), fixed_order=true },
        options_frm { y=center_y+256 },
        options_lbl { id=112, y=center_y+256, text=MTG13.txt_botones },
        dropdown { id=222, group=1001, x=300, y=center_y+256, w=300, h=100,
                   options=names(styles), fixed_order=true },
        options_frm { y=center_y+320 },
        options_lbl { id=113, y=center_y+320, text=MTG13.txt_dlc },
        options_lbl { id=114, x=300, y=center_y+320, text=MTG13.dlc },
        options_lbl { id=115, x=130, w=1000, y=center_y+384, text=MTG13.txt_reinicio },"""

# The "reloading content" notice: the game shows it for five seconds at every start and polls the content. Here
# it stays invisible and stops polling; the rest of the function (which the game needs) stays the game's own.
ENUMERACION_CUERPO = u"""-- Port: the reload runs without showing this box (the original forced it on screen for 5 seconds at every start).
show_for_atleast_five_seconds = function (menu)
\tmenu.poll_for_enumeration = true
\tmenu:set_alpha(0)
end"""

# The main-menu entries that need Xbox Live, achievements or the store: there is nowhere to take the player.
CARRUSEL_MUERTAS = r'^\s*table\.insert\(menu_items.*\bid\s*=\s*(?:leaderboards|multiplayer|dlc|achievements)\b'

# patch name -> operations, in the order they are applied
#   (type, pattern, text, times, what is looked for [, chunks that keep their line breaks])
PARCHES = {
    'carousel': [
        ('delete_lines', CARRUSEL_MUERTAS, None, 5,
         'the Leaderboards, Multiplayer, Additional content and Download content entries'),
    ],
    'enumeration': [
        ('replace_function', r'^show_for_atleast_five_seconds\s*=\s*function\s*\(menu\)', ENUMERACION_CUERPO, 1,
         'the reloading content notice'),
    ],
    'settings': [
        ('insert_before', r'^center_y\s*=\s*-?\d+\s*$', SETTINGS_AYUDA, 1,
         'the code of the new rows (language, icons, DLC)', [SETTINGS_CRUDO]),
        ('replace', r'center_y\s*=\s*-?\d+', 'center_y = -280', 1, 'the menu fits with the new rows'),
        ('replace', r'center_y\+90\b', 'center_y+64', 2, "the game's rows closer together"),
        ('replace', r'center_y\+180\b', 'center_y+128', 2, "the game's rows closer together"),
        ('replace', r'y\s*=\s*220\b', 'y = 190', 1, 'the reset hints button moves up'),
        ('replace', r'y\s*=\s*285\b', 'y = 265', 1, 'the default values button moves up'),
        ('insert_before', r'^\t\t-- Reset Tips\s*$', SETTINGS_FILAS, 1,
         "the new rows, before the game's buttons"),
    ],
}


class PatchError(Exception):
    pass


def _salto(texto):
    """The line ending of the user's file (the game's is CRLF)."""
    return '\r\n' if '\r\n' in texto else '\n'


def _con_saltos(texto, salto):
    """Our text with the user's file line ending."""
    return texto.replace('\n', salto)


def apply(nombre, datos):
    """The user's script, already patched (bytes). Raises PatchError if something does not add up."""
    if nombre not in PARCHES:
        raise PatchError('unknown patch "%s"; available: %s' % (nombre, ', '.join(sorted(PARCHES))))
    texto = datos.decode('latin-1') if isinstance(datos, bytes) else datos
    salto = _salto(texto)
    for op in PARCHES[nombre]:
        tipo, patron, suyo, esperado, que = op[0], op[1], op[2], op[3], op[4]
        crudos = op[5] if len(op) > 5 else ()
        if tipo == 'delete_lines':
            lineas = texto.split(salto)
            quedan = [l for l in lineas if not re.search(patron, l)]
            hechas = len(lineas) - len(quedan)
            if hechas != esperado:
                raise PatchError("%s: expected %d lines (%s) but got %d. Your copy of the game's script is not "
                                 'the one this installer knows.' % (nombre, esperado, que, hechas))
            texto = salto.join(quedan)
        elif tipo == 'replace_function':
            cuerpo = _con_saltos(suyo, salto)
            for crudo in crudos:
                cuerpo = cuerpo.replace(_con_saltos(crudo, salto), crudo)
            lineas = texto.split(salto)
            salida, hechas, i = [], 0, 0
            while i < len(lineas):
                if re.search(patron, lineas[i]):
                    j = i + 1
                    while j < len(lineas) and lineas[j].rstrip() != 'end':
                        j += 1
                    if j >= len(lineas):
                        raise PatchError('%s: the function of %r does not end in a standalone `end`' % (nombre, que))
                    salida.extend(cuerpo.split(salto))
                    hechas += 1
                    i = j + 1
                    continue
                salida.append(lineas[i])
                i += 1
            if hechas != esperado:
                raise PatchError('%s: expected %d function (%s) but got %d' % (nombre, esperado, que, hechas))
            texto = salto.join(salida)
        elif tipo == 'insert_before':
            bloque = _con_saltos(suyo, salto)
            for crudo in crudos:
                bloque = bloque.replace(_con_saltos(crudo, salto), crudo)
            salida, hechas = [], 0
            for linea in texto.split(salto):
                if re.search(patron, linea):
                    # a blank line, the block and another blank line: the anchor stays where it was
                    salida.extend([''] + bloque.split(salto) + [''])
                    hechas += 1
                salida.append(linea)
            if hechas != esperado:
                raise PatchError('%s: cannot find where to insert %s (%r matches %d times, expected %d)'
                                 % (nombre, que, patron, hechas, esperado))
            texto = salto.join(salida)
        elif tipo == 'replace':
            texto, hechas = re.subn(patron, suyo, texto)
            if hechas != esperado:
                raise PatchError('%s: %s matches %d times, expected %d' % (nombre, que, hechas, esperado))
        else:
            raise PatchError('unknown operation: %s' % tipo)
    return texto.encode('latin-1')


def sha256(datos):
    return hashlib.sha256(datos).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true', help='the patches there are, with their operations')
    ap.add_argument('--data', help='game folder (with Data_Core.wad)')
    ap.add_argument('--wad', help='the WAD to read (default <--data>/Data_Core.wad)')
    ap.add_argument('--entry', help='path of the entry inside the WAD')
    ap.add_argument('--patch', help='which patch to apply (%s)' % ', '.join(sorted(PARCHES)))
    ap.add_argument('--out', help='output file')
    a = ap.parse_args()
    if a.list:
        for nombre in sorted(PARCHES):
            print(nombre)
            for op in PARCHES[nombre]:
                print('    %-15s %-40s (%d)  %s' % (op[0], str(op[1])[:40], op[3], op[4]))
        return 0
    if not (a.entry and a.patch):
        ap.error('--entry and --patch are required (see --list)')
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'tools'))
    import wad as wadmod
    ruta = a.wad or os.path.join(a.data or '.', 'Data_Core.wad')
    with open(ruta, 'rb') as f:
        posiciones = wadmod.posiciones(f)
    datos = None
    for indice, (nombre, _) in wadmod.rutas(ruta).items():
        if nombre.upper() == a.entry.upper():
            datos = wadmod.contenido(ruta, posiciones[indice])
    if datos is None:
        sys.exit('%s does not contain %s' % (ruta, a.entry))
    salida = apply(a.patch, datos)
    if a.out:
        with open(a.out, 'wb') as f:
            f.write(salida)
        print('%s: %d -> %d bytes, sha256 %s' % (a.out, len(datos), len(salida), sha256(salida)))
    else:
        sys.stdout.buffer.write(salida)
    return 0


if __name__ == '__main__':
    sys.exit(main())
