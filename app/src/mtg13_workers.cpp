// The game's match-worker loop (sub_82A40030 in the Title Update), translated by the generator, with one change of
// this port: the loop that waits for a job to appear sleeps a little after 64 empty polls instead of spinning at full
// speed on one core (mtg13_worker_idle_us; 0 turns the fix off). The ready byte the loop watches lives in the worker
// structure, at +0xE110 of the object it points to at +76. Every shutdown and job path is the game's own.
#include "generated/default/mtg13_init.h"
#include <chrono>
#include <thread>
#include <rex/cvar.h>
REXCVAR_DEFINE_INT32(mtg13_worker_idle_us, 100, "Mtg13", "Sleep after 64 empty worker polls; 0 disables")
    .range(0, 5000);
extern "C" REX_FUNC(sub_82A40030) {
	REX_FUNC_PROLOGUE();
    uint32_t idle_polls = 0;
    const int idle_us = REXCVAR_GET(mtg13_worker_idle_us);
	PPCRegister ctr{};
	PPCXERRegister xer{};
	PPCRegister reserved{};
	PPCCRRegister cr0{};
	PPCCRRegister cr6{};
	PPCRegister r15{};
	PPCRegister r16{};
	PPCRegister r17{};
	PPCRegister r18{};
	PPCRegister r19{};
	PPCRegister r20{};
	PPCRegister r21{};
	PPCRegister r22{};
	PPCRegister r23{};
	PPCRegister r24{};
	PPCRegister r25{};
	PPCRegister r26{};
	PPCRegister r27{};
	PPCRegister r28{};
	PPCRegister r29{};
	PPCRegister r30{};
	PPCRegister r31{};
	PPCRegister f31{};
	PPCRegister temp{};
	uint32_t ea{};
	ctx.r12.u64 = ctx.lr;
	ctx.lr = 0x82A40038;
	REX_STORE_D_U64(ctx.r1.u32, -152, f31.u64);
	ea = -240 + ctx.r1.u32;
	REX_STORE_U32(ea, ctx.r1.u32);
	ctx.r1.u32 = ea;
	ctx.r11.s64 = -2112421888;
	ctx.r10.s64 = 0;
	ctx.r9.s64 = ctx.r11.s64 + -12016;
	ctx.r8.s64 = 6356992;
	ctx.r7.s64 = 0;
	ctx.r6.s64 = 0;
	ctx.r5.s64 = 0;
	ctx.fpscr.disableFlushMode();
	temp.u32 = REX_LOAD_D_U32(ctx.r9.u32, 344);
	f31.f64 = double(temp.f32);
	r31.u64 = ctx.r3.u64;
	r25.s64 = 0;
	r27.s64 = 1;
	r16.u64 = ctx.r10.u64 | 57616;
	r17.u64 = ctx.r8.u64 | 16704;
	r28.u64 = ctx.r7.u64 | 57784;
	r19.s64 = -2099576832;
	r22.s64 = 3;
	r15.u64 = ctx.r6.u64 | 34316;
	r18.u64 = ctx.r5.u64 | 34468;
	r20.s64 = 2;
	r26.s64 = -2099576832;
loc_82A40090:
	ctx.r11.u64 = REX_LOAD_D_U8(r31.u32, 65);
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (!cr6.eq) goto loc_82A400AC;
	ctx.r11.u64 = REX_LOAD_D_U32(r26.u32, -25268);
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	ctx.r11.u64 = r25.u64;
	if (!cr6.eq) goto loc_82A400B0;
loc_82A400AC:
	ctx.r11.u64 = r27.u64;
loc_82A400B0:
	ctx.r11.u64 = ctx.r11.u32 & 0xFF;
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (!cr6.eq) goto loc_82A404D4;
	ctx.r3.u64 = REX_LOAD_D_U32(r31.u32, 76);
	ctx.r11.u64 = REX_LOAD_U8(ctx.r3.u32 + r16.u32);
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (cr6.eq) {
        if (idle_us > 0 && ++idle_polls >= 64) {
            std::this_thread::sleep_for(std::chrono::microseconds(idle_us));
            idle_polls = 0;
        }
        goto loc_82A40090;
    }
    idle_polls = 0;
	ctx.r11.u64 = REX_LOAD_U8(r31.u32 + r17.u32);
	r24.u64 = r31.u64 + r17.u64;
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (cr6.eq) goto loc_82A40134;
	ctx.r6.s64 = 0;
	ctx.r5.s64 = 1;
	ctx.r4.s64 = 1;
	ctx.lr = 0x82A400EC;
	sub_82A08D50(ctx, base);
	ctx.r11.u64 = ctx.r3.u32 & 0xFF;
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (!cr6.eq) goto loc_82A40134;
	ctx.r11.u64 = REX_LOAD_D_U32(r26.u32, -25268);
	ctx.r8.u64 = REX_LOAD_D_U32(r31.u32, 48);
	ctx.r6.u64 = ctx.r8.u8 & 0x20 ? 0 : (r27.u32 << (ctx.r8.u8 & 0x3F));
	ctx.r11.u64 = REX_LOAD_U32(ctx.r11.u32 + r28.u32);
	ctx.r5.u64 = ~ctx.r6.u64;
	ctx.r4.s64 = ctx.r11.s64 + 44;
loc_82A40110:
	// mfmsr r7
	// mtmsrd r13,1
	ea = ctx.r4.u32;
	reserved.u32 = *(uint32_t*)REX_RAW_ADDR(ea);
	ctx.r10.u64 = __builtin_bswap32(reserved.u32);
	ctx.r9.u64 = ctx.r5.u64 & ctx.r10.u64;
	// stwcx. r9,0,r4
	ea = ctx.r4.u32;
	cr0.lt = 0;
	cr0.gt = 0;
	cr0.eq = __sync_bool_compare_and_swap(reinterpret_cast<uint32_t*>(REX_RAW_ADDR(ea)), reserved.s32, __builtin_bswap32(ctx.r9.s32));
	cr0.so = xer.so;
	// mtmsrd r7,1
	if (!cr0.eq) goto loc_82A40110;
	REX_STORE_D_U32(r31.u32, 52, r22.u32);
	REX_STORE_D_U8(r24.u32, 0, r25.u8);
loc_82A40134:
	ctx.r11.u64 = REX_LOAD_D_U32(r31.u32, 48);
	cr6.compare<int32_t>(ctx.r11.s32, 0, xer);
	if (!cr6.eq) goto loc_82A40164;
	ctx.r11.u64 = REX_LOAD_D_U32(r26.u32, -25268);
	ctx.r11.u64 = ctx.r11.u64 + r28.u64;
	ctx.r10.u64 = REX_LOAD_D_U32(ctx.r11.u32, 0);
	ctx.r9.u64 = REX_LOAD_D_U32(ctx.r10.u32, 48);
	cr6.compare<uint32_t>(ctx.r9.u32, 0, xer);
	if (cr6.eq) goto loc_82A40164;
	ctx.r11.u64 = REX_LOAD_D_U32(ctx.r11.u32, 0);
	ctx.r3.u64 = REX_LOAD_D_U32(ctx.r11.u32, 48);
	ctx.lr = 0x82A40164;
	sub_82A4A360(ctx, base);
loc_82A40164:
	ctx.r11.u64 = REX_LOAD_D_U8(r31.u32, 56);
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (cr6.eq) goto loc_82A401D8;
	ctx.r6.s64 = 0;
	ctx.r3.u64 = REX_LOAD_D_U32(r31.u32, 76);
	ctx.r5.s64 = 1;
	ctx.r4.s64 = 0;
	ctx.lr = 0x82A40184;
	sub_82A08D50(ctx, base);
	ctx.r11.u64 = ctx.r3.u32 & 0xFF;
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (!cr6.eq) goto loc_82A401B0;
	ctx.r11.u64 = REX_LOAD_D_U32(r31.u32, 76);
	ctx.r3.u64 = ctx.r11.u64 + r15.u64;
	ctx.lr = 0x82A4019C;
	sub_82A040C0(ctx, base);
	ctx.r10.u64 = ctx.r3.u32 & 0xFF;
	cr6.compare<uint32_t>(ctx.r10.u32, 0, xer);
	if (!cr6.eq) goto loc_82A401B0;
	REX_STORE_D_U8(r31.u32, 56, r25.u8);
	goto loc_82A401D4;
loc_82A401B0:
	ctx.lr = 0x82A401B4;
	sub_82972238(ctx, base);
	ctx.fpscr.disableFlushMode();
	temp.u32 = REX_LOAD_D_U32(r31.u32, 60);
	ctx.f0.f64 = double(temp.f32);
	ctx.f13.f64 = double(float(ctx.f1.f64 - ctx.f0.f64));
	cr6.compare(ctx.f13.f64, f31.f64);
	if (!cr6.gt) goto loc_82A401D8;
	REX_STORE_D_U8(r31.u32, 56, r25.u8);
	ctx.r11.u64 = REX_LOAD_D_U32(r31.u32, 76);
	ctx.r3.u64 = ctx.r11.u64 + r18.u64;
	ctx.lr = 0x82A401D4;
	sub_82255798(ctx, base);
loc_82A401D4:
	REX_STORE_D_U32(r31.u32, 52, r27.u32);
loc_82A401D8:
	r21.u64 = r25.u64;
loc_82A401DC:
	r23.u64 = REX_LOAD_D_U32(r31.u32, 52);
	ctx.r11.u64 = REX_LOAD_D_U32(r31.u32, 52);
	ctx.r11.s64 = ctx.r11.s64 + -1;
	cr6.compare<uint32_t>(ctx.r11.u32, 9, xer);
	if (cr6.gt) goto loc_82A404B8;
	ctx.r12.s64 = -2103181312;
	ctx.r0.u64 = ((uint32_t)(ctx.r11.u32 << 2));
	ctx.r12.s64 = ctx.r12.s64 + 520;
	ctx.r0.u64 = REX_LOAD_U32(ctx.r12.u32 + ctx.r0.u32);
	ctr.u64 = ctx.r0.u64;
	switch (ctx.r11.u32) {
	case 0:
		goto loc_82A40230;
	case 1:
		goto loc_82A40298;
	case 2:
		goto loc_82A4028C;
	case 3:
		goto loc_82A4044C;
	case 4:
		goto loc_82A40460;
	case 5:
		goto loc_82A40474;
	case 6:
		goto loc_82A4047C;
	case 7:
		goto loc_82A40490;
	case 8:
		goto loc_82A404A4;
	case 9:
		goto loc_82A404AC;
	default:
		__builtin_trap(); // Switch case out of range
	}
loc_82A40230:
	ctx.r11.u64 = REX_LOAD_D_U8(r31.u32, 5);
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (!cr6.eq) goto loc_82A4028C;
	ctx.r3.u64 = REX_LOAD_D_U32(r19.u32, -1788);
	ctx.lr = 0x82A40244;
	sub_82B54E60(ctx, base);
	ctx.r11.u64 = ctx.r3.u32 & 0xFF;
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (!cr6.eq) goto loc_82A4028C;
	REX_STORE_D_U8(r24.u32, 0, r25.u8);
	ctx.r8.u64 = REX_LOAD_D_U32(r26.u32, -25268);
	ctx.r6.u64 = REX_LOAD_D_U32(r31.u32, 48);
	ctx.r5.u64 = ctx.r6.u8 & 0x20 ? 0 : (r27.u32 << (ctx.r6.u8 & 0x3F));
	ctx.r11.u64 = REX_LOAD_U32(ctx.r8.u32 + r28.u32);
	ctx.r4.s64 = ctx.r11.s64 + 44;
loc_82A40268:
	// mfmsr r7
	// mtmsrd r13,1
	ea = ctx.r4.u32;
	reserved.u32 = *(uint32_t*)REX_RAW_ADDR(ea);
	ctx.r10.u64 = __builtin_bswap32(reserved.u32);
	ctx.r9.u64 = ctx.r5.u64 | ctx.r10.u64;
	// stwcx. r9,0,r4
	ea = ctx.r4.u32;
	cr0.lt = 0;
	cr0.gt = 0;
	cr0.eq = __sync_bool_compare_and_swap(reinterpret_cast<uint32_t*>(REX_RAW_ADDR(ea)), reserved.s32, __builtin_bswap32(ctx.r9.s32));
	cr0.so = xer.so;
	// mtmsrd r7,1
	if (!cr0.eq) goto loc_82A40268;
	REX_STORE_D_U32(r31.u32, 52, r20.u32);
	goto loc_82A404B8;
loc_82A4028C:
	ctx.r3.s64 = 1;
	ctx.lr = 0x82A40294;
	sub_8230D990(ctx, base);
	goto loc_82A404B8;
loc_82A40298:
	ctx.r11.u64 = REX_LOAD_D_U32(r26.u32, -25268);
	ctx.r7.u64 = REX_LOAD_D_U32(r31.u32, 48);
	ctx.r6.u64 = ctx.r7.u8 & 0x20 ? 0 : (r27.u32 << (ctx.r7.u8 & 0x3F));
	ctx.r11.u64 = REX_LOAD_U32(ctx.r11.u32 + r28.u32);
	ctx.r5.s64 = ctx.r11.s64 + 44;
loc_82A402AC:
	// mfmsr r8
	// mtmsrd r13,1
	ea = ctx.r5.u32;
	reserved.u32 = *(uint32_t*)REX_RAW_ADDR(ea);
	ctx.r10.u64 = __builtin_bswap32(reserved.u32);
	ctx.r9.u64 = ctx.r6.u64 | ctx.r10.u64;
	// stwcx. r9,0,r5
	ea = ctx.r5.u32;
	cr0.lt = 0;
	cr0.gt = 0;
	cr0.eq = __sync_bool_compare_and_swap(reinterpret_cast<uint32_t*>(REX_RAW_ADDR(ea)), reserved.s32, __builtin_bswap32(ctx.r9.s32));
	cr0.so = xer.so;
	// mtmsrd r8,1
	if (!cr0.eq) goto loc_82A402AC;
	ctx.r11.u64 = REX_LOAD_D_U32(r26.u32, -25268);
	ctx.r11.u64 = ctx.r11.u64 + r28.u64;
	ctx.r4.u64 = REX_LOAD_D_U32(ctx.r11.u32, 0);
	ctx.r3.u64 = REX_LOAD_D_U8(ctx.r4.u32, 40);
	cr6.compare<uint32_t>(ctx.r3.u32, 0, xer);
	if (!cr6.eq) goto loc_82A40314;
	ctx.r10.u64 = REX_LOAD_D_U32(r31.u32, 48);
	ctx.r11.u64 = REX_LOAD_D_U32(ctx.r11.u32, 0);
	ctx.r6.u64 = ctx.r10.u8 & 0x20 ? 0 : (r27.u32 << (ctx.r10.u8 & 0x3F));
	ctx.r5.u64 = ~ctx.r6.u64;
	ctx.r4.s64 = ctx.r11.s64 + 44;
loc_82A402F4:
	// mfmsr r7
	// mtmsrd r13,1
	ea = ctx.r4.u32;
	reserved.u32 = *(uint32_t*)REX_RAW_ADDR(ea);
	ctx.r9.u64 = __builtin_bswap32(reserved.u32);
	ctx.r8.u64 = ctx.r5.u64 & ctx.r9.u64;
	// stwcx. r8,0,r4
	ea = ctx.r4.u32;
	cr0.lt = 0;
	cr0.gt = 0;
	cr0.eq = __sync_bool_compare_and_swap(reinterpret_cast<uint32_t*>(REX_RAW_ADDR(ea)), reserved.s32, __builtin_bswap32(ctx.r8.s32));
	cr0.so = xer.so;
	// mtmsrd r7,1
	if (!cr0.eq) goto loc_82A402F4;
	goto loc_82A404B8;
loc_82A40314:
	ctx.r3.u64 = r31.u64;
	ctx.lr = 0x82A4031C;
	sub_82A3FAB8(ctx, base);
	ctx.r11.u64 = ctx.r3.u32 & 0xFF;
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	ctx.r11.u64 = REX_LOAD_D_U32(r26.u32, -25268);
	ctx.r11.u64 = REX_LOAD_U32(ctx.r11.u32 + r28.u32);
	ctx.r4.s64 = ctx.r11.s64 + 44;
	if (!cr6.eq) goto loc_82A40360;
	ctx.r8.u64 = REX_LOAD_D_U32(r31.u32, 48);
	ctx.r6.u64 = ctx.r8.u8 & 0x20 ? 0 : (r27.u32 << (ctx.r8.u8 & 0x3F));
	ctx.r5.u64 = ~ctx.r6.u64;
loc_82A40340:
	// mfmsr r7
	// mtmsrd r13,1
	ea = ctx.r4.u32;
	reserved.u32 = *(uint32_t*)REX_RAW_ADDR(ea);
	ctx.r10.u64 = __builtin_bswap32(reserved.u32);
	ctx.r9.u64 = ctx.r5.u64 & ctx.r10.u64;
	// stwcx. r9,0,r4
	ea = ctx.r4.u32;
	cr0.lt = 0;
	cr0.gt = 0;
	cr0.eq = __sync_bool_compare_and_swap(reinterpret_cast<uint32_t*>(REX_RAW_ADDR(ea)), reserved.s32, __builtin_bswap32(ctx.r9.s32));
	cr0.so = xer.so;
	// mtmsrd r7,1
	if (!cr0.eq) goto loc_82A40340;
	goto loc_82A404B8;
loc_82A40360:
	ctx.r7.u64 = REX_LOAD_D_U32(r31.u32, 48);
	ctx.r6.u64 = ctx.r7.u8 & 0x20 ? 0 : (r27.u32 << (ctx.r7.u8 & 0x3F));
	ctx.r5.u64 = ~ctx.r6.u64;
loc_82A4036C:
	// mfmsr r8
	// mtmsrd r13,1
	ea = ctx.r4.u32;
	reserved.u32 = *(uint32_t*)REX_RAW_ADDR(ea);
	ctx.r10.u64 = __builtin_bswap32(reserved.u32);
	ctx.r9.u64 = ctx.r5.u64 & ctx.r10.u64;
	// stwcx. r9,0,r4
	ea = ctx.r4.u32;
	cr0.lt = 0;
	cr0.gt = 0;
	cr0.eq = __sync_bool_compare_and_swap(reinterpret_cast<uint32_t*>(REX_RAW_ADDR(ea)), reserved.s32, __builtin_bswap32(ctx.r9.s32));
	cr0.so = xer.so;
	// mtmsrd r8,1
	if (!cr0.eq) goto loc_82A4036C;
	REX_STORE_D_U32(r31.u32, 52, r22.u32);
	ctx.r4.s64 = 0;
	REX_STORE_D_U8(r24.u32, 0, r25.u8);
	ctx.r3.u64 = REX_LOAD_D_U32(r31.u32, 76);
	ctx.lr = 0x82A4039C;
	sub_82A075F0(ctx, base);
	r30.u64 = ctx.r3.u64;
loc_82A403A0:
	ctx.r10.u64 = REX_LOAD_D_U32(r30.u32, 4);
	ctx.r11.u64 = REX_LOAD_D_U32(r30.u32, 8);
	cr6.compare<uint32_t>(ctx.r10.u32, 0, xer);
	if (cr6.eq) goto loc_82A403C8;
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (!cr6.eq) goto loc_82A403C0;
	ctx.r11.u64 = REX_LOAD_D_U32(ctx.r10.u32, 44);
	goto loc_82A403E4;
loc_82A403C0:
	ctx.r11.u64 = REX_LOAD_D_U32(ctx.r11.u32, 12);
	goto loc_82A403E4;
loc_82A403C8:
	cr6.compare<uint32_t>(ctx.r11.u32, 0, xer);
	if (!cr6.eq) goto loc_82A403E0;
	ctx.r11.u64 = REX_LOAD_D_U32(r30.u32, 0);
	ctx.r10.u64 = REX_LOAD_D_U32(ctx.r11.u32, 16);
	REX_STORE_D_U32(r30.u32, 8, ctx.r10.u32);
	goto loc_82A403E8;
loc_82A403E0:
	ctx.r11.u64 = REX_LOAD_D_U32(ctx.r11.u32, 8);
loc_82A403E4:
	REX_STORE_D_U32(r30.u32, 8, ctx.r11.u32);
loc_82A403E8:
	r29.u64 = REX_LOAD_D_U32(r30.u32, 8);
	cr6.compare<uint32_t>(r29.u32, 0, xer);
	if (cr6.eq) goto loc_82A40440;
	ctx.r11.u64 = REX_LOAD_D_U32(r29.u32, 52);
	ctx.r10.u64 = REX_LOAD_D_U32(r29.u32, 48);
	cr6.compare<int32_t>(ctx.r11.s32, ctx.r10.s32, xer);
	if (cr6.eq) goto loc_82A403A0;
	cr6.compare<int32_t>(ctx.r11.s32, 2, xer);
	if (!cr6.eq) goto loc_82A40424;
	ctx.r4.s64 = 0;
	ctx.r3.u64 = r29.u64;
	ctx.lr = 0x82A40418;
	sub_829E7078(ctx, base);
	ctx.r11.u64 = REX_LOAD_D_U32(r29.u32, 48);
	REX_STORE_D_U32(r29.u32, 52, ctx.r11.u32);
	goto loc_82A403A0;
loc_82A40424:
	cr6.compare<int32_t>(ctx.r11.s32, 0, xer);
	if (!cr6.eq) goto loc_82A40434;
	ctx.r3.u64 = r29.u64;
	ctx.lr = 0x82A40434;
	sub_829E2988(ctx, base);
loc_82A40434:
	ctx.r11.u64 = REX_LOAD_D_U32(r29.u32, 48);
	REX_STORE_D_U32(r29.u32, 52, ctx.r11.u32);
	goto loc_82A403A0;
loc_82A40440:
	REX_STORE_D_U32(r30.u32, 8, r25.u32);
	REX_STORE_D_U32(r30.u32, 0, r25.u32);
	goto loc_82A404B8;
loc_82A4044C:
	ctx.r5.s64 = 0;
	ctx.r4.s64 = 0;
	ctx.r3.u64 = r31.u64;
	ctx.lr = 0x82A4045C;
	sub_82A3F428(ctx, base);
	goto loc_82A404B8;
loc_82A40460:
	ctx.r5.s64 = 2;
	ctx.r4.s64 = 0;
	ctx.r3.u64 = r31.u64;
	ctx.lr = 0x82A40470;
	sub_82A3F428(ctx, base);
	goto loc_82A404B8;
loc_82A40474:
	ctx.r4.s64 = 0;
	goto loc_82A404B0;
loc_82A4047C:
	ctx.r5.s64 = 0;
	ctx.r4.s64 = 1;
	ctx.r3.u64 = r31.u64;
	ctx.lr = 0x82A4048C;
	sub_82A3F428(ctx, base);
	goto loc_82A404B8;
loc_82A40490:
	ctx.r5.s64 = 2;
	ctx.r4.s64 = 2;
	ctx.r3.u64 = r31.u64;
	ctx.lr = 0x82A404A0;
	sub_82A3F428(ctx, base);
	goto loc_82A404B8;
loc_82A404A4:
	ctx.r4.s64 = 1;
	goto loc_82A404B0;
loc_82A404AC:
	ctx.r4.s64 = 2;
loc_82A404B0:
	ctx.r3.u64 = r31.u64;
	ctx.lr = 0x82A404B8;
	sub_82A3FCE8(ctx, base);
loc_82A404B8:
	ctx.r11.u64 = REX_LOAD_D_U32(r31.u32, 52);
	cr6.compare<int32_t>(ctx.r11.s32, r23.s32, xer);
	if (cr6.eq) goto loc_82A40090;
	cr6.compare<int32_t>(r21.s32, 5, xer);
	if (cr6.gt) goto loc_82A40090;
	r21.s64 = r21.s64 + 1;
	goto loc_82A401DC;
loc_82A404D4:
	ctx.r1.s64 = ctx.r1.s64 + 240;
	f31.u64 = REX_LOAD_D_U64(ctx.r1.u32, -152);
	return;
}
