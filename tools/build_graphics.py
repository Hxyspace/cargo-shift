#!/usr/bin/env python3
"""Build 24px Cargo actors and background crates without scanline crowding."""
from itertools import groupby
import json
from pathlib import Path
from PIL import Image, ImageDraw
from chr_codec import encode
from level_data import centered_map, load_levels, room_offset

ROOT=Path(__file__).resolve().parents[1]
CELL=24
X=8
Y=32
WALL=144
FLOOR=153
GOAL=162
CRATE=171
CRATE_GOAL=180


def rle(data):
    result=[]
    for value,group in groupby(data):
        count=sum(1 for _ in group)
        while count:
            take=min(count,255); result.extend((take,value)); count-=take
    return result+[0]


def text(data,x,y,value):
    for i,c in enumerate(value): data[y*32+x+i]=ord(c)


def block(data,x,y,base):
    for dy in range(3):
        for dx in range(3): data[(y+dy)*32+x+dx]=base+dy*3+dx


def crate_image(docked=False):
    image=Image.new('P',(24,24)); d=ImageDraw.Draw(image)
    # Same four colors in the background and moving-crate sprite palette.
    color=3 if docked else 2
    # A uniform two-pixel frame, with matching corners and no offset shadow.
    d.rectangle((2,2,21,21),fill=color)
    d.rectangle((4,4,19,19),outline=0)
    for x in (9,14): d.line((x,5,x,18),fill=0)
    # Three wooden planks held by a diagonal brace, centered on the cell.
    for y in range(5,19):
        for x in range(5,19):
            distance=abs(x+y-23)
            if distance<=1: d.point((x,y),fill=color)
            elif distance==2: d.point((x,y),fill=0)
    for x,y in ((3,3),(20,3),(3,20),(20,20)): d.point((x,y),fill=0)
    return image


def paste_actor(atlas,image,base):
    for q in range(9):
        tile=base+q
        atlas.paste(image.crop((q%3*8,q//3*8,q%3*8+8,q//3*8+8)),(tile%16*8,tile//16*8))


def make_sprites():
    sprite=Image.open(ROOT/'assets/cargo_shift/sprites.png').copy()
    # Keep the original four-direction art, enlarged to match a full room cell.
    source=sprite.copy()
    worker=json.loads((ROOT/'assets/cargo_shift/tiles.json').read_text())['CARGO_SPR_WORKER']
    for phase in range(2):
        for direction in range(4):
            actor=Image.new('P',(16,16))
            for q in range(4):
                tile=worker+direction*4+phase*16+q
                actor.paste(source.crop((tile%16*8,tile//16*8,tile%16*8+8,tile//16*8+8)),(q%2*8,q//2*8))
            paste_actor(sprite,actor.resize((24,24),Image.Resampling.NEAREST),64+phase*36+direction*9)
    paste_actor(sprite,crate_image(),136)
    paste_actor(sprite,crate_image(True),145)
    return sprite


def menu_scene(entries):
    data=[0]*960+[255]*64
    for x,y,value in entries: text(data,x,y,value)
    return rle(data)


def make_background():
    source=Image.open(ROOT/'assets/cargo_shift/background.png')
    bg=source.copy()
    for base,kind in ((WALL,'wall'),(FLOOR,'floor'),(GOAL,'goal'),(CRATE,'crate'),(CRATE_GOAL,'crate_goal')):
        image=Image.new('P',(24,24)); d=ImageDraw.Draw(image)
        if kind=='wall':
            d.rectangle((1,1,22,22),fill=1)
            d.rectangle((3,3,20,20),outline=0)
            d.point((4,4),fill=0); d.point((19,19),fill=0)
        elif kind.startswith('crate'):
            image=crate_image(kind=='crate_goal')
        else:
            d.point((4,4),fill=1); d.point((18,18),fill=1)
            if kind=='goal':
                d.rectangle((8,8,15,15),outline=3)
                d.rectangle((11,11,12,12),fill=3)
        for q in range(9):
            tile=base+q
            bg.paste(image.crop((q%3*8,q//3*8,q%3*8+8,q//3*8+8)),(tile%16*8,tile//16*8))
    # Large lettering reuses the existing pixel font. Deduplicate its 8x8 tiles.
    logo=Image.new('P',(256,120))
    for word,y in (('CARGO',32),('SHIFT',72)):
        for i,c in enumerate(word):
            tile=ord(c)
            glyph=source.crop((tile%16*8,tile//16*8,tile%16*8+8,tile//16*8+8))
            glyph=glyph.resize((32,32),Image.Resampling.NEAREST)
            logo.paste(glyph,(48+i*32,y))
    data=[0]*960+[255]*64
    lookup={bytes(64):0}
    available=iter(range(189,256))
    for y in range(15):
        for x in range(32):
            tile=logo.crop((x*8,y*8,x*8+8,y*8+8)); key=tile.tobytes()
            if key not in lookup:
                try: index=next(available)
                except StopIteration: raise ValueError('Title exceeds CHR budget')
                lookup[key]=index; bg.paste(tile,(index%16*8,index//16*8))
            data[y*32+x]=lookup[key]
    # A small warehouse vignette anchors the title without gameplay instructions.
    for x,base in ((7,WALL),(10,FLOOR),(13,FLOOR),(16,GOAL),(19,FLOOR),(22,WALL)):
        block(data,x,17,base)
    for x in range(7,25): data[20*32+x]=129
    # Vignette goals use the green room palette.
    for ay in (4,):
        for ax in range(1,7): data[960+ay*8+ax]=0
    text(data,10,24,'PRESS START')
    return bg,data


def main():
    out=ROOT/'assets/generated'; out.mkdir(parents=True,exist_ok=True)
    bg,title=make_background()
    sprites=make_sprites()
    chr_data=bytes(encode(bg))+bytes(encode(sprites))
    assert len(chr_data)==8192
    (out/'cargo_tiles.chr').write_bytes(chr_data)
    ids=dict(CARGO_SPR_WORKER=64,CARGO_SPR_CRATE=136,CARGO_SPR_CRATE_GOAL=145)
    lines=['/* Generated Cargo Shift assets. */']
    lines += [f'#define {key} {value}' for key,value in ids.items()]
    lines += [f'#define CARGO_CELL {CELL}',f'#define CARGO_X {X}',f'#define CARGO_Y {Y}']
    lines += [f'#define CARGO_BG_{name} {tile}' for name,tile in (('FLOOR',FLOOR),('GOAL',GOAL),('CRATE',CRATE),('CRATE_GOAL',CRATE_GOAL))]
    levels=load_levels(ROOT/'assets/cargo_shift/levels.json')
    # Store each room once as 80 metatile IDs rather than 960 expanded tiles.
    # This keeps all 18 rooms within Mapper 0 even with larger 24px cells.
    lines.append(f'static const unsigned char cargo_room_maps[{len(levels)}][80] = {{')
    for level in levels:
        layout=centered_map(level)
        values=[WALL if c=='#' else GOAL if c in '.*+' else FLOOR for c in layout]
        lines.append('{'+','.join(map(str,values))+'},')
    lines.append('};')
    lines.append('static const unsigned char cargo_room_x[] = {'+','.join(str(room_offset(level)*CELL) for level in levels)+'};')
    room=[0]*960+[255]*8+[0]*56
    text(room,12,2,'STAGE 00')
    for name,packed in (
        ('title',rle(title)),
        ('room',rle(room)),
        ('pause',menu_scene([(13,8,'PAUSE'),(9,12,'>'),(11,12,'CONTINUE'),(11,15,'RETRY'),(11,18,'TITLE')])),
        ('retry',menu_scene([(10,8,'RETRY STAGE?'),(10,13,'>'),(12,13,'NO'),(12,16,'YES')])),
        ('complete',menu_scene([(11,9,'ALL CLEAR'),(10,14,f'{len(levels):02} STAGES'),(10,22,'PRESS START')]))):
        lines.append(f'static const unsigned char cargo_{name}_scene[] = {{'+','.join(map(str,packed))+'};')
    (out/'cargo_view.h').write_text('\n'.join(lines)+'\n')
    print(f'Cargo CHR 8192 bytes; {len(levels)} rooms, {len(levels)*80} bytes of metatiles')


if __name__=='__main__': main()
