#ifndef CARGO_MODEL_H
#define CARGO_MODEL_H
#include <stdint.h>
#include "cargo_config.h"
#define WALL 1
#define GOAL 2
#define BOX 4
typedef struct {
    uint16_t steps,pushes;
    uint8_t board[80],player,level,solved;
    uint8_t history[128],head,count;
} Cargo;
extern Cargo cargo;
void cargo_init(uint8_t level);
uint8_t cargo_move(uint8_t direction);
uint8_t cargo_undo(void);
const char* cargo_name(uint8_t level);
uint16_t cargo_par(uint8_t level);
uint8_t cargo_boxes(uint8_t level);
uint8_t cargo_docked(void);
uint8_t cargo_warning(void);
uint8_t cargo_initial_cell(uint8_t position);
#endif
