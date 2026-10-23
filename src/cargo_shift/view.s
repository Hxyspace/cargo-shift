.export _cargo_blit
.export _cargo_room
.importzp ptr1, ptr2, tmp1, tmp2
.segment "CODE"
; fastcall pointer in A/X. Rendering is off; write exactly one full nametable.
_cargo_blit:
    sta ptr1
    stx ptr1+1
    bit $2002
    lda #$20
    sta $2006
    lda #0
    sta $2006
    tay
next:
    lda (ptr1),y
    beq done
    tax
    iny
    bne value
    inc ptr1+1
value:
    lda (ptr1),y
run:
    sta $2007
    dex
    bne run
    iny
    bne next
    inc ptr1+1
    jmp next
done:
    rts

; Expand 10x8 cells to 30x24 background tiles while rendering is off.
; Each cell contains the first of nine consecutive CHR tile IDs.
_cargo_room:
    sta ptr1
    stx ptr1+1
    lda #$81
    sta ptr2
    lda #$20
    sta ptr2+1
    lda #8
    sta tmp1
    bit $2002
room_row:
    lda #0
    sta tmp2
room_line:
    lda ptr2+1
    sta $2006
    lda ptr2
    sta $2006
    ldy #0
room_cell:
    lda (ptr1),y
    clc
    adc tmp2
    sta $2007
    adc #1
    sta $2007
    adc #1
    sta $2007
    iny
    cpy #10
    bne room_cell
    clc
    lda ptr2
    adc #32
    sta ptr2
    bcc :+
    inc ptr2+1
:
    lda tmp2
    clc
    adc #3
    sta tmp2
    cmp #9
    bne room_line
    clc
    lda ptr1
    adc #10
    sta ptr1
    bcc :+
    inc ptr1+1
:
    dec tmp1
    bne room_row
    rts
