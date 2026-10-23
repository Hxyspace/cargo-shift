#include "nes.h"
#define REG(a) (*(volatile unsigned char*)(a))
unsigned char vram_buf[120];
volatile unsigned char vram_len, vram_ready, frame;
unsigned char pad, pressed, repeat;
uint16_t rng_state = 0xACE1;
unsigned char rendering;
static unsigned char previous, held_frames, sprite_count, sound_time;
static unsigned char attributes[64];
static const unsigned char colors[32] = {
    0x0f,0x12,0x21,0x30, 0x0f,0x17,0x27,0x30,
    0x0f,0x0b,0x2a,0x30, 0x0f,0x14,0x24,0x30,
    0x0f,0x12,0x21,0x30, 0x0f,0x17,0x27,0x30,
    0x0f,0x0b,0x2a,0x30, 0x0f,0x14,0x24,0x30
};

static void write_byte(uint16_t address, unsigned char value)
{
    if (rendering) {
        if (vram_len >= sizeof(vram_buf)) present();
        vram_buf[vram_len++] = address >> 8;
        vram_buf[vram_len++] = address;
        vram_buf[vram_len++] = value;
    } else {
        REG(0x2006) = address >> 8;
        REG(0x2006) = address;
        REG(0x2007) = value;
    }
}

void present(void)
{
    if (!rendering) return;
    vram_ready = 1;
    while (vram_ready) {}
}

void tick(void)
{
    unsigned char i, value;
    present();
    previous = pad;
    REG(0x4016) = 1;
    REG(0x4016) = 0;
    value = 0;
    for (i = 0; i != 8; ++i) value = (value << 1) | (REG(0x4016) & 1);
    pad = value;
    pressed = pad & ~previous;
    if (pad != previous || !pad) held_frames = 0;
    else if (held_frames != 255) ++held_frames;
    repeat = pressed;
    if (held_frames >= 18 && !(held_frames & 7)) repeat |= pad & 15;
    if (sound_time && !--sound_time) REG(0x4015) = 0;
}

void screen_off(void)
{
    present();
    REG(0x2000) = 0;
    REG(0x2001) = 0;
    rendering = 0;
}

void screen_clear(void)
{
    uint16_t i;
    screen_off();
    REG(0x2006) = 0x20;
    REG(0x2006) = 0;
    for (i = 0; i != 1024; ++i) REG(0x2007) = 0;
    for (i = 0; i != 64; ++i) attributes[i] = 0;
    sprites_begin();
    sprites_end();
}

void screen_on(void)
{
    REG(0x2003) = 0;
    REG(0x4014) = 2;
    REG(0x2005) = 0;
    REG(0x2005) = 0;
    rendering = 1;
    REG(0x2000) = 0x88;
    REG(0x2001) = 0x1e;
}

void nes_init(void)
{
    unsigned char i;
    screen_clear();
    REG(0x2006) = 0x3f;
    REG(0x2006) = 0;
    for (i = 0; i != 32; ++i) REG(0x2007) = colors[i];
}

void nt_put(unsigned char x, unsigned char y, unsigned char tile)
{
    write_byte(0x2000 + (uint16_t)y * 32 + x, tile);
}

void nt_text(unsigned char x, unsigned char y, const char* text)
{
    while (*text) nt_put(x++, y, *text++);
}

void nt_number(unsigned char x, unsigned char y, uint32_t number, unsigned char width)
{
    unsigned char digit;
    while (width) {
        --width;
        digit = number % 10;
        number /= 10;
        nt_put(x + width, y, '0' + digit);
    }
}

void nt_palette(unsigned char x, unsigned char y, unsigned char palette)
{
    unsigned char index, shift, value;
    index = (y >> 2) * 8 + (x >> 2);
    shift = ((y & 2) << 1) | (x & 2);
    value = (attributes[index] & ~(3 << shift)) | (palette << shift);
    if (value != attributes[index]) {
        attributes[index] = value;
        write_byte(0x23c0 + index, value);
    }
}

void meta(unsigned char x, unsigned char y, unsigned char tile)
{
    nt_put(x, y, tile);
    nt_put(x + 1, y, tile + 1);
    nt_put(x, y + 1, tile + 2);
    nt_put(x + 1, y + 1, tile + 3);
}

void sprites_begin(void) { sprite_count = 0; }
void sprite(unsigned char x, unsigned char y, unsigned char tile, unsigned char attr)
{
    unsigned char index;
    if (sprite_count >= 64) return;
    index = sprite_count++ << 2;
    oam[index] = y - 1;
    oam[index + 1] = tile;
    oam[index + 2] = attr;
    oam[index + 3] = x;
}
void sprites_end(void)
{
    unsigned char i;
    for (i = sprite_count; i < 64; ++i) oam[(unsigned char)(i << 2)] = 0xf0;
}

void tone(unsigned char kind)
{
    static const uint16_t periods[5] = {380,190,100,600,250};
    uint16_t period;
    period = periods[kind % 5];
    REG(0x4015) = 1;
    REG(0x4000) = 0x9a;
    REG(0x4001) = 0x08;
    REG(0x4002) = period;
    REG(0x4003) = period >> 8;
    sound_time = 7;
}

unsigned char random8(void)
{
    rng_state = (rng_state >> 1) ^ ((rng_state & 1) ? 0xb400 : 0);
    return rng_state ^ (rng_state >> 8);
}

void title_draw(const char* title, const char* subtitle)
{
    unsigned char x, y;
    screen_clear();
    for (x = 2; x < 30; ++x) {
        nt_put(x, 6, TILE_BORDER);
        nt_put(x, 24, TILE_BORDER);
    }
    for (y = 6; y <= 24; y += 2)
        for (x = 2; x < 30; x += 2) nt_palette(x, y, 1);
    nt_text(4, 9, title);
    nt_text(4, 12, subtitle);
    nt_text(4, 20, "START / A TO PLAY");
    nt_text(4, 22, "ONE PLAYER  -  NO SAVE");
}

void title_wait(void)
{
    screen_on();
    do { tick(); random8(); } while (!(pressed & (PAD_A | PAD_START)));
    tone(1);
}

unsigned char pause_menu(void)
{
    unsigned char choice, old;
    choice = 0;
    screen_clear();
    nt_text(12, 8, "PAUSED");
    nt_text(9, 12, "RESUME");
    nt_text(9, 15, "RESTART");
    nt_text(9, 18, "TITLE");
    nt_text(5, 24, "UP/DOWN  A TO SELECT");
    nt_put(7, 12, '>');
    screen_on();
    for (;;) {
        tick();
        old = choice;
        if (repeat & PAD_UP) choice = choice ? choice - 1 : 2;
        if (repeat & PAD_DOWN) choice = choice == 2 ? 0 : choice + 1;
        if (choice != old) {
            nt_put(7, 12 + old * 3, 0);
            nt_put(7, 12 + choice * 3, '>');
            tone(0);
        }
        if (pressed & PAD_START) return 0;
        if (pressed & PAD_A) return choice;
    }
}
