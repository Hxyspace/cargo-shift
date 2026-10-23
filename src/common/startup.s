.export __STARTUP__ : absolute = 1
.export _exit, _oam := $0200
.import _main, zerobss, copydata
.import __CSTACK_START__, __CSTACK_SIZE__
.importzp sp
.import _vram_ready, _vram_buf, _vram_len, _frame

.segment "HEADER"
.byte "NES", $1A, 2, 1, 0, 0
.byte 0,0,0,0,0,0,0,0

.segment "STARTUP"
reset:
    sei
    cld
    ldx #$ff
    txs
    inx
    stx $2000
    stx $2001
    stx $4010
    stx $4015
    lda #$40
    sta $4017
    bit $2002
first:
    bit $2002
    bpl first
    lda #0
clear:
    sta $0000,x
    sta $0100,x
    sta $0200,x
    sta $0300,x
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
    inx
    bne clear
second:
    bit $2002
    bpl second
    ; Bottom-of-stack canaries are checked by the headless regression runner.
    lda #$a5
    ldx #0
stack_fill:
    sta $0700,x
    sta $0100,x
    inx
    bne stack_fill
    lda #<(__CSTACK_START__ + __CSTACK_SIZE__)
    sta sp
    lda #>(__CSTACK_START__ + __CSTACK_SIZE__)
    sta sp+1
    jsr zerobss
    jsr copydata
    jsr _main
_exit:
    jmp _exit

nmi:
    pha
    txa
    pha
    tya
    pha
    inc _frame
    lda _vram_ready
    beq done
    bit $2002
    ldx #0
    cpx _vram_len
    beq dma
flush:
    lda _vram_buf,x
    sta $2006
    inx
    lda _vram_buf,x
    sta $2006
    inx
    lda _vram_buf,x
    sta $2007
    inx
    cpx _vram_len
    bne flush
dma:
    lda #0
    sta $2003
    lda #2
    sta $4014
    lda #0
    sta $2005
    sta $2005
    sta _vram_len
    sta _vram_ready
done:
    pla
    tay
    pla
    tax
    pla
irq:
    rti
.segment "VECTORS"
.word nmi, reset, irq
