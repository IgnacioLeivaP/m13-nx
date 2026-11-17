// Touch controls: in Bejeweled 3 they called the game's own TouchBegan/Moved/Ended (Bejeweled
// addresses). Xbox Magic 2012 has no such path: for now they do nothing.
// The original version is in ref/bejeweled3-nx/app/src/mtg13_touch.cpp.

#include "mtg13_touch.h"

namespace mtg13::touch {

void OnWindowMouse(MouseKind, float, float) {}

void Dispatch(PPCContext&, uint8_t*) {}

}  // namespace mtg13::touch
