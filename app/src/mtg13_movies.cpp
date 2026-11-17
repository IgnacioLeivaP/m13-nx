// Videos (WMV/XMV) of Magic 2012.
//
// With the Renut renderer, the first video (the WotC logo, ~frame 58) makes the Vulkan
// device get lost ("device lost") and nothing else draws (2026-11-08, unresolved: see
// BITACORA "Renut draws Magic on PC"). Meanwhile, with Renut the videos are skipped: the
// game asks for them from Lua with playMovie (Lua function table at 0x82CAAB60:
// playMovie -> sub_82B8C620, isMoviePlaying -> sub_82B849E8, stopMovie -> sub_82B849C0).
// playMovie reads the name, calls sub_82B8C428 (builds the path and starts the video with
// sub_823685E0) and returns its true/false to Lua. sub_82B8C428 is intercepted so that it
// answers false ("could not"): the Lua part stays intact. (Intercepting the whole playMovie
// and returning nothing ended in a kernel DbgBreak.)
// With the emulated GPU the videos work and always play.

#include <cstdint>
#include <string>

#include <rex/cvar.h>
#include <rex/hook.h>
#include <rex/logging.h>
#include <rex/system/kernel_state.h>

#include "mtg13_opciones.h"

#if MTG13_RENUT_RENDERER
#include "renut_engine/gpu/banjo_renut_select.h"
#endif

REXCVAR_DEFINE_BOOL(mtg13_movies_renut, false, "Mtg13",
                    "Renut's renderer: play the game's videos (false = skip them; they lose the Vulkan "
                    "device for now). The emulated GPU always plays them");

namespace {
// An MSVC std::string of the game (32-bit): the text in place when its capacity (+0x14) is under 16, else a pointer at
// +0; its size at +0x10.
std::string GuestString(uint32_t address) {
  auto* memory = rex::system::kernel_state()->memory();
  const uint8_t* s = address ? memory->TranslateVirtual<const uint8_t*>(address) : nullptr;
  if (!s) return {};
  auto be32 = [](const uint8_t* p) { return uint32_t(p[0]) << 24 | uint32_t(p[1]) << 16 | uint32_t(p[2]) << 8 | p[3]; };
  const uint32_t size = be32(s + 0x10), capacity = be32(s + 0x14);
  if (size > 256) return {};
  const uint8_t* text = capacity < 16 ? s : memory->TranslateVirtual<const uint8_t*>(be32(s));
  return text ? std::string(reinterpret_cast<const char*>(text), size) : std::string();
}

bool SaltarVideos() {
#if MTG13_RENUT_RENDERER
  return ::banjo::renut_gpu::Active() && !REXCVAR_GET(mtg13_movies_renut);
#else
  return false;
#endif
}
}  // namespace

extern "C" REX_FUNC(__imp__sub_82B21D50);
REX_HOOK_RAW(sub_82B21D50) {  // bool (const std::string* nombre)
  // Our Settings menu's messages (mtg13_opciones.h): game:playMovie("mtg13:estilo=ps").
  if (mtg13::opciones::HandleMessage(GuestString(ctx.r3.u32))) {
    ctx.r3.u64 = 0;
    return;
  }
  if (SaltarVideos()) {
    static bool avisado = false;
    if (!avisado) {
      avisado = true;
      REXLOG_INFO("[movies] Renut: los videos se saltan (mtg13_movies_renut = false)");
    }
    ctx.r3.u64 = 0;  // false: el video no arranco
    return;
  }
  __imp__sub_82B21D50(ctx, base);
}
