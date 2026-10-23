#include "nes.h"
#include "model.h"
#include "cargo_view.h"
#define REG(a) (*(volatile unsigned char*)(a))
#define NONE 255
#define ANIM_FRAMES 6
void __fastcall__ cargo_blit(const unsigned char* data);
void __fastcall__ cargo_room(const unsigned char* data);
unsigned char mode;
static unsigned char clear_wait,input_lock,anim,anim_from,anim_to,box_from,box_to;
static unsigned char facing,queued,held,held_ticks;
static const signed char deltas[4]={-10,10,-1,1};
static const unsigned char key_bits[5]={PAD_UP,PAD_DOWN,PAD_LEFT,PAD_RIGHT,PAD_B};
static const unsigned char cargo_colors[32]={
    0x0f,0x0c,0x27,0x2a, 0x0f,0x07,0x17,0x27,
    0x0f,0x0b,0x1a,0x2a, 0x0f,0x0c,0x1c,0x30,
    0x0f,0x0c,0x27,0x2a, 0x0f,0x07,0x17,0x27,
    0x0f,0x0b,0x1a,0x2a, 0x0f,0x06,0x16,0x30
};

static void sound(unsigned char kind)
{
    tone(kind);
    REG(0x4000)=kind==0 ? 0x92 : kind==4 ? 0x94 : 0x98;
}
static unsigned char pixel(unsigned char from,unsigned char to,unsigned char vertical)
{
    unsigned char a,b,distance;
    a=vertical ? CARGO_Y+(from/10)*CARGO_CELL : CARGO_X+cargo_room_x[cargo.level]+(from%10)*CARGO_CELL;
    b=vertical ? CARGO_Y+(to/10)*CARGO_CELL : CARGO_X+cargo_room_x[cargo.level]+(to%10)*CARGO_CELL;
    if(a==b) return a;
    distance=(ANIM_FRAMES-anim)*4;
    return b>a ? a+distance : a-distance;
}
static void actor(unsigned char x,unsigned char y,unsigned char tile,unsigned char palette)
{
    unsigned char row;
    for(row=0;row<3;++row) {
        sprite(x,y,tile++,palette); sprite(x+8,y,tile++,palette);
        sprite(x+16,y,tile++,palette); y+=8;
    }
}
static void cell(unsigned char position)
{
    unsigned char x,y,tile,row,column,value;
    value=cargo.board[position];
    if(value&BOX) tile=(value&GOAL) ? CARGO_BG_CRATE_GOAL : CARGO_BG_CRATE;
    else tile=(value&GOAL) ? CARGO_BG_GOAL : CARGO_BG_FLOOR;
    x=CARGO_X/8+cargo_room_x[cargo.level]/8+(position%10)*3;
    y=CARGO_Y/8+(position/10)*3;
    for(row=0;row<3;++row)
        for(column=0;column<3;++column) nt_put(x+column,y+row,tile++);
}
static void actors(void)
{
    unsigned char x,y,tile;
    sprites_begin();
    x=pixel(anim ? anim_from : cargo.player,cargo.player,0);
    y=pixel(anim ? anim_from : cargo.player,cargo.player,1);
    tile=CARGO_SPR_WORKER+facing*9;
    if(anim&1) tile+=36;
    actor(x,y,tile,1);
    if(anim && box_to!=NONE)
        actor(pixel(box_from,box_to,0),pixel(box_from,box_to,1),CARGO_SPR_CRATE,0);
    sprites_end();
}
static void background(void)
{
    unsigned char i;
    screen_off(); cargo_blit(cargo_room_scene);
    nt_put(18,2,'0'+(cargo.level+1)/10); nt_put(19,2,'0'+(cargo.level+1)%10);
    cargo_room(cargo_room_maps[cargo.level]);
    for(i=0;i<80;++i) if(cargo.board[i]&BOX) cell(i);
    actors(); screen_on();
}
static void static_screen(const unsigned char* scene)
{
    screen_off(); cargo_blit(scene); sprites_begin(); sprites_end(); screen_on();
}
static void reset_view(void)
{
    clear_wait=anim=0;
    box_to=queued=held=NONE; held_ticks=0; facing=1;
}
static void title(void)
{
    unsigned char clock;
    clock=0; static_screen(cargo_title_scene);
    sprites_begin();
    actor(104,136,CARGO_SPR_WORKER+27,1);
    actor(128,136,CARGO_SPR_CRATE,0);
    sprites_end();
    for(;;) {
        tick(); random8(); ++clock;
        if(!(clock&31)) nt_text(10,24,(clock&32) ? "           " : "PRESS START");
        if(pressed&PAD_START) { sound(0); return; }
    }
}
static unsigned char request(void)
{
    unsigned char key,i;
    key=NONE;
    if(pressed&PAD_B) key=4;
    else for(i=0;i<4;++i) if(pressed&key_bits[i]) { key=i; break; }
    if(key==NONE && held<5 && (pad&key_bits[held])) key=held;
    if(key==NONE) for(i=0;i<5;++i) if(pad&key_bits[i]) { key=i; break; }
    if(key==NONE) { held=NONE; held_ticks=0; return NONE; }
    if(key!=held) { held=key; held_ticks=key==4 ? 14 : 12; return key; }
    if(held_ticks && --held_ticks) return NONE;
    held_ticks=key==4 ? 4 : 6;
    return key;
}
static void act(unsigned char key)
{
    unsigned char before,record,direction,changed,pushed;
    before=cargo.player; pushed=0; direction=0; box_to=NONE;
    if(key==4) {
        if(!cargo.count) { if(pressed&PAD_B) sound(4); return; }
        record=cargo.history[(cargo.head-1)&127]; direction=record&3;
        if(record&4) { box_from=before+deltas[direction]; box_to=before; pushed=1; }
        changed=cargo_undo(); facing=direction^1;
    } else {
        direction=key; facing=key;
        changed=cargo_move(key);
        if(changed && (cargo.history[(cargo.head-1)&127]&4)) {
            box_from=before+deltas[key]; box_to=box_from+deltas[key]; pushed=1;
        }
    }
    if(!changed) { if(pressed&key_bits[key]) sound(4); actors(); return; }
    anim_from=before; anim_to=cargo.player; anim=ANIM_FRAMES;
    if(pushed) cell(box_from);
    clear_wait=cargo.solved ? 45 : 0;
    if(key==4) sound(0);
    else sound(cargo.solved ? 2 : pushed ? 1 : 0);
    actors();
}
static unsigned char menu(const unsigned char* scene,unsigned char count,unsigned char x,unsigned char y)
{
    unsigned char choice,before;
    choice=0; static_screen(scene);
    for(;;) {
        tick(); before=choice;
        if(pressed&PAD_SELECT || repeat&PAD_DOWN) choice=choice==count-1 ? 0 : choice+1;
        else if(repeat&PAD_UP) choice=choice ? choice-1 : count-1;
        if(choice!=before) {
            nt_put(x,y+before*3,' '); nt_put(x,y+choice*3,'>'); sound(0);
        }
        if(pressed&PAD_B) return 0;
        if(pressed&PAD_START) return choice;
    }
}
static void complete(void)
{
    static_screen(cargo_complete_scene);
    do { tick(); } while(!(pressed&PAD_START));
}
void main(void)
{
    unsigned char action,key,i;
    nes_init();
    REG(0x2006)=0x3f; REG(0x2006)=0;
    for(i=0;i<32;++i) REG(0x2007)=cargo_colors[i];
    for(;;) {
        mode=0; title(); cargo_init(0); reset_view(); input_lock=1;
        background(); mode=1;
        while(mode) {
            tick();
            if(pressed&PAD_START) {
                anim=0; queued=held=NONE;
                mode=2; action=menu(cargo_pause_scene,3,9,12);
                if(action==2) { mode=0; break; }
                if(action==1) { cargo_init(cargo.level); reset_view(); }
                background(); input_lock=cargo.solved ? 0 : 1; mode=cargo.solved?3:1;
                continue;
            }
            if(input_lock) {
                if(!pad) input_lock=0;
                continue;
            }
            key=request();
            if(anim) {
                if(key==4 || queued==NONE) queued=key;
                --anim;
                if(!anim && box_to!=NONE) cell(box_to);
                actors();
                continue;
            }
            if(queued!=NONE) { key=queued; queued=NONE; }
            if(key==4) act(key);
            else if(cargo.solved) {
                if(clear_wait && --clear_wait) continue;
                if(cargo.level==CARGO_LEVEL_COUNT-1) {
                    mode=4; complete(); mode=0; break;
                }
                cargo_init(cargo.level+1); reset_view(); input_lock=1; background(); mode=1;
            } else if(pressed&PAD_A) {
                queued=held=NONE; mode=5;
                action=menu(cargo_retry_scene,2,10,13);
                if(action) { cargo_init(cargo.level); reset_view(); }
                background(); input_lock=1;
            } else if(key<4) act(key);
            mode=cargo.solved?3:1;
        }
    }
}
