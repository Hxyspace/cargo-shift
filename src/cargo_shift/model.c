#include "model.h"
#include <string.h>
#include "cargo_levels.h"
Cargo cargo;
static const int8_t deltas[4] = {-10,10,-1,1};
const char* cargo_name(uint8_t level) { return cargo_names[level%CARGO_LEVEL_COUNT]; }
uint16_t cargo_par(uint8_t level) { return cargo_pars[level%CARGO_LEVEL_COUNT]; }
uint8_t cargo_boxes(uint8_t level) { return cargo_box_counts[level%CARGO_LEVEL_COUNT]; }
uint8_t cargo_initial_cell(uint8_t position)
{
    char c;
    c=cargo_maps[cargo.level][position];
    if(c=='#') return WALL;
    if(c=='.' || c=='+') return GOAL;
    if(c=='$') return BOX;
    if(c=='*') return BOX|GOAL;
    return 0;
}
uint8_t cargo_docked(void)
{
    uint8_t i,count;
    count=0;
    for(i=0;i<80;++i) if((cargo.board[i]&(BOX|GOAL))==(BOX|GOAL)) ++count;
    return count;
}
uint8_t cargo_warning(void)
{
    uint8_t i,a,b,c,d;
    if(cargo.solved) return 0;
    for(i=0;i<80;++i) if((cargo.board[i]&BOX) &&
        (cargo_dead[cargo.level][i>>3] & (1<<(i&7)))) return 1;
    /* A full 2x2 of walls/crates cannot be opened by pushing. */
    for(i=0;i<69;++i) if(i%10<9) {
        a=cargo.board[i]; b=cargo.board[i+1];
        c=cargo.board[i+10]; d=cargo.board[i+11];
        if((a&(WALL|BOX)) && (b&(WALL|BOX)) && (c&(WALL|BOX)) && (d&(WALL|BOX)) &&
           (((a&(BOX|GOAL))==BOX) || ((b&(BOX|GOAL))==BOX) ||
            ((c&(BOX|GOAL))==BOX) || ((d&(BOX|GOAL))==BOX))) return 1;
    }
    return 0;
}
static uint8_t solved(void)
{
    uint8_t i;
    for(i=0;i<80;++i) if((cargo.board[i] & (BOX|GOAL))==BOX) return 0;
    return 1;
}
void cargo_init(uint8_t level)
{
    uint8_t i;
    char c;
    memset(&cargo,0,sizeof(cargo));
    cargo.level=level%CARGO_LEVEL_COUNT;
    for(i=0;i<80;++i) {
        c=cargo_maps[cargo.level][i];
        /* Keep this explicit: cc65 V2.19 miscompiles a nested ternary here at -Oirs. */
        cargo.board[i]=cargo_initial_cell(i);
        if(c=='@' || c=='+') cargo.player=i;
    }
    cargo.solved=solved();
}
static int16_t neighbor(uint8_t position,uint8_t direction)
{
    int16_t next;
    if((direction==2 && position%10==0) || (direction==3 && position%10==9)) return -1;
    next=(int16_t)position+deltas[direction];
    return next<0 || next>=80 ? -1 : next;
}
uint8_t cargo_move(uint8_t direction)
{
    int16_t target,beyond;
    uint8_t pushed;
    if(direction>3 || cargo.solved || cargo.steps==65535U) return 0;
    target=neighbor(cargo.player,direction);
    if(target<0 || (cargo.board[target]&WALL)) return 0;
    pushed=0;
    if(cargo.board[target]&BOX) {
        beyond=neighbor(target,direction);
        if(beyond<0 || (cargo.board[beyond]&(WALL|BOX))) return 0;
        cargo.board[beyond]|=BOX;
        cargo.board[target]&=~BOX;
        pushed=1;
        if(cargo.pushes<65535U) ++cargo.pushes;
    }
    cargo.player=target;
    if(cargo.steps<65535U) ++cargo.steps;
    cargo.history[cargo.head]=direction | (pushed?4:0);
    cargo.head=(cargo.head+1)&127;
    if(cargo.count<128) ++cargo.count;
    cargo.solved=solved();
    return 1;
}
uint8_t cargo_undo(void)
{
    uint8_t record,direction;
    int16_t beyond;
    if(!cargo.count) return 0;
    cargo.head=(cargo.head-1)&127;
    record=cargo.history[cargo.head];
    direction=record&3;
    if(record&4) {
        beyond=neighbor(cargo.player,direction);
        cargo.board[beyond]&=~BOX;
        cargo.board[cargo.player]|=BOX;
        if(cargo.pushes) --cargo.pushes;
    }
    cargo.player-=deltas[direction];
    if(cargo.steps) --cargo.steps;
    --cargo.count;
    cargo.solved=solved();
    return 1;
}
