.text
.globl _sidebar_hook
_sidebar_hook:
    subq $40, %rsp
    movq %rdi, 0(%rsp)
    movq %rsi, 8(%rsp)
    movq %rdx, 16(%rsp)
    movq 16(%rsp), %rdi
.globl _load_eq1
_load_eq1: movq 0(%rip), %rsi
.globl _complete
_complete: leaq 0(%rip), %rdx
.globl _call_eq1
_call_eq1: callq *0(%rip)
    testb %al, %al
    jne L1
    movq 16(%rsp), %rdi
.globl _load_eq2
_load_eq2: movq 0(%rip), %rsi
.globl _incomplete
_incomplete: leaq 0(%rip), %rdx
.globl _call_eq2
_call_eq2: callq *0(%rip)
    testb %al, %al
    jne L2
    movq 16(%rsp), %rdi
.globl _load_eq3
_load_eq3: movq 0(%rip), %rsi
.globl _all
_all: leaq 0(%rip), %rdx
.globl _call_eq3
_call_eq3: callq *0(%rip)
    testb %al, %al
    jne L3
    movq 16(%rsp), %rdi
.globl _load_eq4
_load_eq4: movq 0(%rip), %rsi
.globl _video
_video: leaq 0(%rip), %rdx
.globl _call_eq4
_call_eq4: callq *0(%rip)
    testb %al, %al
    jne L4
    movq 16(%rsp), %rdi
.globl _load_eq5
_load_eq5: movq 0(%rip), %rsi
.globl _audio
_audio: leaq 0(%rip), %rdx
.globl _call_eq5
_call_eq5: callq *0(%rip)
    testb %al, %al
    jne L5
    movq 16(%rsp), %rdi
.globl _load_eq6
_load_eq6: movq 0(%rip), %rsi
.globl _compressed
_compressed: leaq 0(%rip), %rdx
.globl _call_eq6
_call_eq6: callq *0(%rip)
    testb %al, %al
    jne L6
    movq 16(%rsp), %rdi
.globl _load_eq7
_load_eq7: movq 0(%rip), %rsi
.globl _document
_document: leaq 0(%rip), %rdx
.globl _call_eq7
_call_eq7: callq *0(%rip)
    testb %al, %al
    jne L7
    movq 16(%rsp), %rdi
.globl _load_eq8
_load_eq8: movq 0(%rip), %rsi
.globl _misc
_misc: leaq 0(%rip), %rdx
.globl _call_eq8
_call_eq8: callq *0(%rip)
    testb %al, %al
    jne L8
    movq 16(%rsp), %rdx
    jmp LSet
L1:
    leaq LText1(%rip), %rdx
    jmp LMake
L2:
    leaq LText2(%rip), %rdx
    jmp LMake
L3:
    leaq LText3(%rip), %rdx
    jmp LMake
L4:
    leaq LText4(%rip), %rdx
    jmp LMake
L5:
    leaq LText5(%rip), %rdx
    jmp LMake
L6:
    leaq LText6(%rip), %rdx
    jmp LMake
L7:
    leaq LText7(%rip), %rdx
    jmp LMake
L8:
    leaq LText8(%rip), %rdx
    jmp LMake
LMake:
.globl _load_nsstring
_load_nsstring: movq 0(%rip), %rdi
.globl _load_utf8
_load_utf8: movq 0(%rip), %rsi
.globl _call_make
_call_make: callq *0(%rip)
    movq %rax, %rdx
LSet:
    movq 0(%rsp), %rdi
    movq 8(%rsp), %rsi
    addq $40, %rsp
.globl _tail_send
_tail_send: jmpq *0(%rip)
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
