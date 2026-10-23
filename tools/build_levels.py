#!/usr/bin/env python3
from pathlib import Path
import json
from level_data import load_levels, normalized_map
root = Path(__file__).resolve().parents[1]
levels = load_levels(root/'assets/cargo_shift/levels.json')
lines = ['/* Generated from assets/cargo_shift/levels.json. */',
         f'static const char cargo_maps[{len(levels)}][81] = {{']
names = []
dead_masks=[]
box_counts=[]
for level in levels:
    text = normalized_map(level)
    lines.append('    '+json.dumps(text)+',')
    names.append(level['name'])
    floor={i for i,c in enumerate(text) if c!='#'}
    reachable={i for i,c in enumerate(text) if c in '.*+'}
    todo=list(reachable)
    while todo:
        position=todo.pop()
        for delta in (-10,10,-1,1):
            previous=position-delta
            stand=position-2*delta
            if previous in floor and stand in floor and previous not in reachable:
                reachable.add(previous); todo.append(previous)
    mask=[0]*10
    for i in floor-reachable: mask[i>>3] |= 1<<(i&7)
    dead_masks.append(mask)
    box_counts.append(sum(text.count(c) for c in '$*'))
lines += ['};',f'static const char* const cargo_names[{len(levels)}] = {{',
          *('    '+json.dumps(name)+',' for name in names),'};']
lines += [f'static const unsigned short cargo_pars[{len(levels)}] = {{'+','.join(str(l['par']) for l in levels)+'};',
          f'static const unsigned char cargo_box_counts[{len(levels)}] = {{'+','.join(map(str,box_counts))+'};',
          f'static const unsigned char cargo_dead[{len(levels)}][10] = {{',
          *('    {'+','.join(map(str,mask))+'},' for mask in dead_masks),'};']
out = root/'assets/generated'
out.mkdir(parents=True,exist_ok=True)
(out/'cargo_levels.h').write_text('\n'.join(lines)+'\n')
(out/'cargo_config.h').write_text(
    '#ifndef CARGO_CONFIG_H\n#define CARGO_CONFIG_H\n'
    f'#define CARGO_LEVEL_COUNT {len(levels)}\n'
    '#endif\n'
)
