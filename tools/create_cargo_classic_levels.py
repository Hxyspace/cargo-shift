#!/usr/bin/env python3
"""Explicitly reconstruct original classic-style stages from design recipes."""
from collections import deque
from pathlib import Path
import json
import random
TEMPLATES=[
['##########','#   #    #','#        #','## # ##  #','#        #','# #  #   #','#        #','##########'],
['##########','#   ######','#   #    #','#        #','# #  ##  #','#    #   #','###      #','##########'],
['##########','#    #   #','#        #','#  # #   #','# ##   # #','#    #   #','#        #','##########'],
['########','#   ####','# #    #','#   ## #','##     #','#  #   #','#      #','########'],
['#########','#   #   #','#       #','## #  # #','#   #   #','# #   # #','#       #','#########'],
['##########','##   #   #','#  #   # #','#      # #','# # #    #','#   # #  #','###      #','##########'],
['#########','#       #','# # ##  #','#   #   #','###   # #','#  ##   #','#       #','#########'],
['##########','#     ####','# ##     #','#    # # #','## #     #','#    #   #','#  #   ###','##########'],
['##########','#   #    #','# #   #  #','# # #    #','#   ## # #','###      #','###   #  #','##########'],
['##########','#  ##    #','#     #  #','## #  #  #','#    ##  #','#  #     #','#    #   #','##########'],
]
D=(-10,10,-1,1)
def explore(job):
    ti,n,seed=job; rng=random.Random(seed);rows=TEMPLATES[ti]
    text=''.join(row.ljust(10,'#') for row in rows).ljust(80,'#'); floor={i for i,c in enumerate(text) if c!='#'}
    def walk(p,b):
        found={p};todo=[p]
        for p in todo:
            for d in D:
                q=p+d
                if q in floor and q not in b and q not in found: found.add(q);todo.append(q)
        return found
    goals=tuple(sorted(rng.sample(sorted(floor),n))); blocked=set(goals)
    remaining=floor-blocked; roots=[]
    while remaining:
        reachable=walk(min(remaining),blocked);remaining-=reachable
        roots.append((min(reachable),goals))
    todo=deque(roots);dist={s:0 for s in roots}
    while todo and len(dist)<16000:
        state=todo.popleft();p,boxes=state;b=set(boxes);reachable=walk(p,b);depth=dist[state]
        for box in boxes:
            for d in D:
                stand=box+d;back=box+2*d
                if stand not in reachable or back not in reachable: continue
                nb=(b-{box})|{stand};np=min(walk(back,nb));nboxes=tuple(sorted(nb));new=(np,nboxes)
                if new not in dist: dist[new]=depth+1;todo.append(new)
    # Include deepest discovered states, not only fully expanded ones.
    deepest=max(dist.values())
    options=[s for s in dist if dist[s]==deepest and len(set(s[1])-set(goals))>=n-1]
    if not options: return None
    p,boxes=rng.choice(options)
    # Select a reachable starting square; walking does not change the push distance.
    reachable=walk(p,set(boxes));p=rng.choice(sorted(reachable))
    result=list(text)
    for q in goals:result[q]='.'
    for q in boxes:result[q]='*' if q in goals else '$'
    result[p]='+' if p in goals else '@'
    s=''.join(result)
    return dict(name=f'T{ti}-{n}-{seed}',map=[s[i:i+10] for i in range(0,80,10)],min_pushes=deepest,states=len(dist),template=ti,seed=seed)


def main():
    root=Path(__file__).resolve().parents[1]
    designs=json.loads((root/'assets/cargo_shift/classic-design.json').read_text())
    levels=[]
    for design in designs:
        level=explore((design['template'],design['boxes'],design['seed']))
        assert level['min_pushes']==design['minimum_pushes']
        rows=level['map']
        if design['horizontal_flip']:rows=[row[::-1] for row in rows]
        if design['vertical_flip']:rows=rows[::-1]
        cells=[(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c!='#']
        left=min(x for x,y in cells)-1;right=max(x for x,y in cells)+2
        top=min(y for x,y in cells)-1;bottom=max(y for x,y in cells)+2
        rows=[row[left:right] for row in rows[top:bottom]]
        levels.append(dict(name=design['name'],map=rows,par=design['shortest_moves'],
                           min_pushes=design['minimum_pushes'],origin='Original compact puzzle; classic Sokoban design principles',
                           theme=design['theme']))
        print(f"{design['name']}: minimum {design['minimum_pushes']} pushes",flush=True)
    assert len(levels)==18
    (root/'assets/cargo_shift/levels.json').write_text(json.dumps(levels,indent=2)+'\n')


if __name__=='__main__':main()
