#!/usr/bin/env python3
"""Find shortest move solutions with push A*; generate ROM inputs and host fixtures."""
from collections import deque
from functools import lru_cache
import heapq
from itertools import count
import json
from pathlib import Path
from level_data import load_levels

ROOT = Path(__file__).resolve().parents[1]
DIRECTIONS = [(-10,'UP'),(10,'DOWN'),(-1,'LEFT'),(1,'RIGHT')]


def minimum_pushes(level,max_states=500000):
    """Independent forward BFS with free walking; certify the push lower bound."""
    text=''.join(row.ljust(10,'#') for row in level['map']).ljust(80,'#')
    floor={i for i,c in enumerate(text) if c!='#'}
    goals=frozenset(i for i,c in enumerate(text) if c in '.*+')
    boxes=frozenset(i for i,c in enumerate(text) if c in '$*')
    player=next(i for i,c in enumerate(text) if c in '@+')
    live=set(goals);todo=list(live)
    for position in todo:
        for delta,_ in DIRECTIONS:
            if position-delta in floor and position-2*delta in floor and position-delta not in live:
                live.add(position-delta);todo.append(position-delta)
    def walk(player,boxes):
        reachable={player};todo=[player]
        for p in todo:
            for delta,_ in DIRECTIONS:
                q=p+delta
                if q in floor and q not in boxes and q not in reachable:
                    reachable.add(q);todo.append(q)
        return reachable
    initial=(min(walk(player,boxes)),boxes)
    todo=deque([(initial,0)]);seen={initial}
    while todo:
        (player,boxes),depth=todo.popleft()
        if boxes==goals:return depth,len(seen)
        reachable=walk(player,boxes)
        for box in sorted(boxes):
            for delta,_ in DIRECTIONS:
                target=box+delta
                if box-delta not in reachable or target not in live or target in boxes:continue
                new_boxes=(boxes-{box})|{target}
                state=(min(walk(box,new_boxes)),new_boxes)
                if state not in seen:
                    seen.add(state);todo.append((state,depth+1))
        if len(seen)>max_states:raise RuntimeError('push BFS state budget exceeded')
    raise RuntimeError('push BFS found no solution')


def solve(level, max_states=300000):
    text=''.join(row.ljust(10,'#') for row in level['map']).ljust(80,'#')
    walls={i for i,c in enumerate(text) if c=='#'}
    goals={i for i,c in enumerate(text) if c in '.*+'}
    initial=(next(i for i,c in enumerate(text) if c in '@+'),tuple(i for i,c in enumerate(text) if c in '$*'))
    floor=set(range(80))-walls
    if len(initial[1])!=len(goals): raise RuntimeError('box and goal counts differ')
    # Reverse-push distances exclude squares from which no goal can be reached.
    distances=[]
    for goal in sorted(goals):
        distance={goal:0}; todo=deque([goal])
        while todo:
            position=todo.popleft()
            for delta,_ in DIRECTIONS:
                previous=position-delta
                if previous in floor and position-2*delta in floor and previous not in distance:
                    distance[previous]=distance[position]+1; todo.append(previous)
        distances.append(distance)
    live=set().union(*(set(d) for d in distances))
    @lru_cache(maxsize=100000)
    def heuristic(boxes):
        # Minimum one-to-one assignment is admissible for the move-count cost.
        costs={0:0}
        for box in boxes:
            next_costs={}
            for mask,cost in costs.items():
                for g,distance in enumerate(distances):
                    if mask&(1<<g) or box not in distance: continue
                    next_mask=mask|(1<<g); value=cost+distance[box]
                    if value<next_costs.get(next_mask,10**9): next_costs[next_mask]=value
            costs=next_costs
        return costs.get((1<<len(boxes))-1,10**9)
    serial=count()
    queue=[(heuristic(initial[1]),0,next(serial),initial)]
    parents={initial:None}; costs={initial:0}
    while queue:
        _,cost,_,state=heapq.heappop(queue)
        if cost!=costs[state]: continue
        player,boxes=state
        if set(boxes)==goals:
            result=[]
            while parents[state] is not None:
                state,path=parents[state]
                result.append(path)
            return [direction for path in reversed(result) for direction in path],len(parents)
        blocked=set(boxes)
        walks={player:()}; todo=deque([player])
        while todo:
            position=todo.popleft()
            for direction,(delta,_) in enumerate(DIRECTIONS):
                target=position+delta
                if target in floor and target not in blocked and target not in walks:
                    walks[target]=walks[position]+(direction,); todo.append(target)
        for box in boxes:
            for direction,(delta,_) in enumerate(DIRECTIONS):
                beyond=box+delta; stand=box-delta
                if stand not in walks or beyond not in live or beyond in blocked: continue
                next_boxes=tuple(sorted((blocked-{box})|{beyond}))
                estimate=heuristic(next_boxes)
                if estimate>=10**9: continue
                next_state=(box,next_boxes)
                path=walks[stand]+(direction,); next_cost=cost+len(path)
                if next_cost<costs.get(next_state,10**9):
                    costs[next_state]=next_cost; parents[next_state]=(state,path)
                    heapq.heappush(queue,(next_cost+estimate,next_cost,next(serial),next_state))
        if len(parents)>max_states: raise RuntimeError('solver state budget exceeded')
    raise RuntimeError(f'unsolvable map: {level["name"]}')


def main():
    levels=load_levels(ROOT/'assets/cargo_shift/levels.json')
    fixtures=[]
    for index,level in enumerate(levels,1):
        directions,states=solve(level)
        pushes,push_states=minimum_pushes(level)
        if len(directions)!=level['par']:
            raise RuntimeError(f"{level['name']}: shortest move count changed")
        if pushes!=level['min_pushes']:
            raise RuntimeError(f"{level['name']}: minimum push count changed")
        fixtures.append(''.join(str(d) for d in directions))
        print(f"{index:02}. {level['name']}: {len(directions)} moves, {pushes} pushes",flush=True)
    destination=ROOT/'tests/fixtures/cargo_solutions.h'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(f'#define CARGO_SOLUTION_COUNT {len(levels)}\n'
                           f'static const char* solutions[{len(levels)}] = {{\n'+
                           ''.join('    '+json.dumps(s)+',\n' for s in fixtures)+'};\n')


if __name__=='__main__': main()
