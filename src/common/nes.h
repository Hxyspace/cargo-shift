#ifndef TUFTY_NES_H
#define TUFTY_NES_H
#include <stdint.h>
#include "tile_ids.h"
#define PAD_A 0x80
#define PAD_B 0x40
#define PAD_SELECT 0x20
#define PAD_START 0x10
#define PAD_UP 0x08
#define PAD_DOWN 0x04
#define PAD_LEFT 0x02
#define PAD_RIGHT 0x01
extern unsigned char oam[256];
extern unsigned char vram_buf[120];
extern volatile unsigned char vram_len, vram_ready, frame;
extern unsigned char pad, pressed, repeat;
extern uint16_t rng_state;
void nes_init(void);
void present(void);
void tick(void);
void screen_clear(void);
void screen_on(void);
void screen_off(void);
void nt_put(unsigned char x, unsigned char y, unsigned char tile);
void nt_text(unsigned char x, unsigned char y, const char* text);
void nt_number(unsigned char x, unsigned char y, uint32_t number, unsigned char width);
void nt_palette(unsigned char x, unsigned char y, unsigned char palette);
void meta(unsigned char x, unsigned char y, unsigned char tile);
void sprites_begin(void);
void sprite(unsigned char x, unsigned char y, unsigned char tile, unsigned char attr);
void sprites_end(void);
void tone(unsigned char kind);
unsigned char random8(void);
void title_draw(const char* title, const char* subtitle);
void title_wait(void);
unsigned char pause_menu(void);
#endif
