.text
.globl _sidebar_hook
_sidebar_hook:
    stp x29, x30, [sp, #-64]!
    mov x29, sp
    stp x0, x1, [sp, #16]
    str x2, [sp, #32]
    ldr x0, [sp, #32]
.globl _load_eq1
_load_eq1: nop
.globl _complete
_complete: nop
.globl _call_eq1
_call_eq1: nop
    cbnz w0, L1
    ldr x0, [sp, #32]
.globl _load_eq2
_load_eq2: nop
.globl _incomplete
_incomplete: nop
.globl _call_eq2
_call_eq2: nop
    cbnz w0, L2
    ldr x0, [sp, #32]
.globl _load_eq3
_load_eq3: nop
.globl _all
_all: nop
.globl _call_eq3
_call_eq3: nop
    cbnz w0, L3
    ldr x0, [sp, #32]
.globl _load_eq4
_load_eq4: nop
.globl _video
_video: nop
.globl _call_eq4
_call_eq4: nop
    cbnz w0, L4
    ldr x0, [sp, #32]
.globl _load_eq5
_load_eq5: nop
.globl _audio
_audio: nop
.globl _call_eq5
_call_eq5: nop
    cbnz w0, L5
    ldr x0, [sp, #32]
.globl _load_eq6
_load_eq6: nop
.globl _compressed
_compressed: nop
.globl _call_eq6
_call_eq6: nop
    cbnz w0, L6
    ldr x0, [sp, #32]
.globl _load_eq7
_load_eq7: nop
.globl _document
_document: nop
.globl _call_eq7
_call_eq7: nop
    cbnz w0, L7
    ldr x0, [sp, #32]
.globl _load_eq8
_load_eq8: nop
.globl _misc
_misc: nop
.globl _call_eq8
_call_eq8: nop
    cbnz w0, L8
    ldr x2, [sp, #32]
    b LSet
L1:
    adr x2, LText1
    b LMake
L2:
    adr x2, LText2
    b LMake
L3:
    adr x2, LText3
    b LMake
L4:
    adr x2, LText4
    b LMake
L5:
    adr x2, LText5
    b LMake
L6:
    adr x2, LText6
    b LMake
L7:
    adr x2, LText7
    b LMake
L8:
    adr x2, LText8
    b LMake
LMake:
.globl _load_nsstring
_load_nsstring: nop
.globl _load_utf8
_load_utf8: nop
.globl _call_make
_call_make: nop
    mov x2, x0
LSet:
    ldp x0, x1, [sp, #16]
    ldp x29, x30, [sp], #64
.globl _tail_send
_tail_send: nop
LText1:
    .asciz "已完成"
LText2:
    .asciz "未完成"
LText3:
    .asciz "全部下载"
LText4:
    .asciz "视频"
LText5:
    .asciz "音频"
LText6:
    .asciz "压缩包"
LText7:
    .asciz "文档"
LText8:
    .asciz "其他"
