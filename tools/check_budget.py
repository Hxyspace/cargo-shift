#!/usr/bin/env python3
"""Validate actual linked PRG and internal RAM use; write release budget data."""
import json
from pathlib import Path
import re
import sys
root=Path(__file__).resolve().parents[1]
records=[]
names=sys.argv[1:] or ('cargo_shift',)
for name in names:
    text=(root/f'build/{name}.map').read_text().split('Segment list:',1)[1].split('Exports list',1)[0]
    segments={}
    for line in text.splitlines():
        match=re.match(r'(\w+)\s+([0-9A-F]{6})\s+([0-9A-F]{6})\s+([0-9A-F]{6})',line)
        if match: segments[match[1]]=tuple(int(v,16) for v in match.groups()[1:])
    for segment in ('BSS','DATA'):
        if segment in segments:
            start,end,size=segments[segment]
            if size and not 0x300<=start<=end<0x700: raise ValueError(f'{name}: {segment} outside internal RAM budget')
    prg=sum(segments.get(segment,(0,0,0))[2] for segment in ('STARTUP','LOWCODE','ONCE','CODE','RODATA','DATA','VECTORS'))
    ram=sum(segments.get(segment,(0,0,0))[2] for segment in ('BSS','DATA'))
    if prg>32768: raise ValueError(f'{name}: PRG overflow')
    record=dict(game=name,prg_used=prg,prg_capacity=32768,data_bss=ram,data_bss_capacity=1024,
                c_stack=256,cpu_stack=256,oam=256,chr=8192)
    records.append(record)
    print(f'{name}: PRG {prg}/32768; DATA+BSS {ram}/1024; internal C stack 256; CHR 8192')
(root/('build/cargo-budget.json' if list(names)==['cargo_shift'] else 'build/budgets.json')).write_text(json.dumps(records,indent=2)+'\n')
