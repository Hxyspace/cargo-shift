#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/cargo_shift/model.h"
#include "cargo_solutions.h"
#if CARGO_SOLUTION_COUNT != CARGO_LEVEL_COUNT
#error "Regenerate solutions with make solve after changing the level count"
#endif
int main(void)
{
    unsigned i,j,direction;
    int target;
    Cargo initial;
    const char* path;
    for(i=0;i<CARGO_LEVEL_COUNT;++i) {
        cargo_init(i); initial=cargo; path=solutions[i];
        for(j=0;path[j];++j) { assert(cargo_move(path[j]-'0')); assert(!cargo_warning()); }
        assert(cargo.solved && cargo.steps==j);
        assert(cargo_par(i)==j && !cargo_warning());
        assert(cargo_docked()==cargo_boxes(i));
        assert(!cargo_move(0));
        for(unsigned k=0;k<j;++k) assert(cargo_undo());
        assert(!cargo_undo() && !cargo.steps && !cargo.pushes && !cargo.solved);
        assert(cargo.player==initial.player && !memcmp(cargo.board,initial.board,80));
    }
    /* Invalid inputs do not add history. Circular undo retains exactly 128 moves. */
    cargo_init(0);
    assert(!cargo_move(4));
    for(direction=0;direction<4;++direction) {
        target=cargo.player+(direction==0 ? -10 : direction==1 ? 10 : direction==2 ? -1 : 1);
        if(target>=0 && target<80 && !(cargo.board[target]&(WALL|BOX))) break;
    }
    assert(direction<4);
    for(i=0;i<140;++i) { assert(cargo_move(direction)); assert(cargo_move(direction^1)); }
    assert(cargo.count==128 && cargo.steps==280);
    for(i=0;i<128;++i) assert(cargo_undo());
    assert(!cargo_undo() && cargo.steps==152);
    /* Cannot push two adjacent crates or push into a wall. */
    memset(cargo.board,0,sizeof(cargo.board));
    cargo.player=21; cargo.board[22]=BOX; cargo.board[23]=BOX;
    assert(!cargo_move(3));
    cargo.board[23]=WALL; assert(!cargo_move(3));
    cargo_init(0);
    assert(!cargo_warning());
    for(i=0;i<80;++i) cargo.board[i]&=~BOX;
    for(i=0;i<80;++i) if(!(cargo.board[i]&(WALL|GOAL))) {
        cargo.board[i]|=BOX;
        if(cargo_warning()) break;
        cargo.board[i]&=~BOX;
    }
    assert(i<80 && cargo_warning());
    cargo.solved=1;
    assert(!cargo_warning());
    cargo_init(0);
    cargo.board[22]|=BOX; cargo.board[23]|=BOX;
    cargo.board[32]|=BOX; cargo.board[33]|=BOX;
    assert(cargo_warning());
    puts("Cargo Shift: 18 optimal solutions, complete undo, bounded history, blocked pushes and deadlock warnings passed");
    return 0;
}
