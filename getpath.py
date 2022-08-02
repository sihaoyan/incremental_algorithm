from __future__ import annotations
from collections import namedtuple
import itertools
import sys
from typing import Any
import time
import platform
Vertex=Any
Edge=namedtuple('Edge', ('source','destination'))
IntPath=namedtuple('IntPath',('iteration','source','destination'))
Path=namedtuple('Path', ('source', 'destination'))
Fact=Edge or IntPath or Path

def getPaths(edges:set[Edge]):
    paths=set()
    for i in itertools.count(0):
        newPaths=paths | \
        {Path(i,v) for u, v in edges} | \
        {Path(u,x) for u, v in paths for w, x in edges if v==w}
        if paths == newPaths: break
        else: paths = newPaths
    return paths

InputGate = namedtuple('InputGate', ('name', 'sinks'))
AndGate=namedtuple('AndGate', ('sources', 'sinks'))
OrGate=namedtuple('OrGate', ('name', 'sources', 'sinks'))
Gate=InputGate or AndGate or OrGate
    
def getPathsInstr(edges: set[tuple[Any, Any]]):
    edgeInputMap: dict[Edge, int]={}
    gates: list[Gate]=[]
    
    for e in edges:
        u, v,= e
        edgeInputMap[e]=len(gates)
        gates.append(InputGate(e,set()))
        
    paths: set[IntPath]=set()
    projPaths: set[Path]=set()
    pathGateMap: dict[IntPath, int]={}
    for i in itertools.count(1):
        newPaths = set()
        newPathGateMap: dict[IntPath, OrGate]={}
        
        for p in paths:
            _, u, v = p
            np = IntPath(i,u,v)
            newPaths.add(np)
            if np not in newPathGateMap:
                k=len(gates)
                newPathGateMap[np]=k
                gates.append(OrGate(np, set(), set()))
            else:
                assert False
                k=newPathGateMap[np]
            gates[k].sources.add(pathGateMap[p])
            gates[pathGateMap[p]].sinks.add(k)
        for e in edges:
            u, v = e
            np=IntPath(i, u, v)
            newPaths.add(np)
            if np not in newPathGateMap:
                k=len(gates)
                newPathGateMap[np]=k
                gates.append(OrGate(np, set(), set()))
            else:
                k=newPathGateMap[np]
            gates[k].sources.add(edgeInputMap[e])
            gates[edgeInputMap[e]].sinks.add(k)
            
        for p in paths:
            _, u, v = p
            for e in edges:
                w, x=e
                if v==w:
                    np=IntPath(i,u,x)
                    newPaths.add(np)
                    g=len(gates)
                    gates.append(AndGate({pathGateMap[p], edgeInputMap[e]}, set()))
                    gates[pathGateMap[p]].sinks.add(g)
                    gates[edgeInputMap[e]].sinks.add(g)
                    
                    if np not in newPathGateMap:
                        k=len(gates)
                        newPathGateMap[np]=k
                        gates.append(OrGate(np, set(), set()))
                    else:
                        k=newPathGateMap[np]
                    gates[k].sources.add(g)
                    gates[g].sinks.add(k)
        
        newProjPaths={Path(u,v) for _,u, v in newPaths}
        toBreak = projPaths == newProjPaths
        paths=newPaths
        pathGateMap=newPathGateMap
        projPaths=newProjPaths
        
        if toBreak: break
    
    gateOutputMap: dict[Gate, Path]={}
    return projPaths, gates, pathGateMap, newPathGateMap, edgeInputMap

def tupleToStr(t: Fact):
    if isinstance(t, Edge):
        u, v = t
        return f'E{u}{v}'
    elif isinstance(t, IntPath):
        i, u, v =t
        return f'P-{i}-{u}{v}'
    elif isinstance(t, Path):
        u, v = t
        return f'P{u}{v}'
    else: assert False
def remove_edge(e: Edge, gates: list[Gate]):
    removed=[]
    e_name=tupleToStr(e)
    removed.append(e_name)
    for g in gates:
        if isinstance(g, OrGate):
            removed=helper(g, gates, removed)
    return removed
def helper(gate: Gate, gates: list[Gate], removed):
    if isinstance(gate, InputGate):
        return tupleToStr(gate.name)
    elif isinstance(gate, AndGate):
        sources=gate.sources
        sources={tupleToStr(gates[s].name) for s in sources}
        for name in sources:
            if name in removed:
                return False
        return True
    elif isinstance(gate, OrGate):
        sources=gate.sources
        sources=[(tupleToStr(gates[k].name) not in removed) if not isinstance(gates[k], AndGate) else helper(gates[k], gates, removed)\
                 for k in sources]
        if True not in sources:
            removed.append(tupleToStr(gate.name))
        return removed
    else: assert False, gate
    
    
def toStr(gate: Gate, gates: list[Gate]):
    if isinstance(gate, InputGate):
        return tupleToStr(gate.name)
    elif isinstance(gate, AndGate):
        sources=gate.sources
        sources={tupleToStr(gate.name) for s in sources}
        sources= ' and '.join(sources)
        return sources
    elif isinstance(gate, OrGate):
        sources=gate.sources
        sources=[tupleToStr(gates[k].name) if not isinstance(gates[k], AndGate) else toStr(gates[k], gates)\
                 for k in sources]
        sources= ' or '.join(sources)
        ans=f'{tupleToStr(gate.name)}={sources}'
        return ans
    else: assert False, gate 

edges ={('a','b'), ('b','c'), ('c','a')}
edges= {Edge(u,v) for u, v in edges}    
e = Edge('a','b')
# for u, v in getPaths(edges):
#          print(f'{u}, {v}')

paths, gates, pathGateMap, newPathGateMap, edgeInputMap=getPathsInstr(edges)

t1=time.perf_counter()
print("path removing result using naive incremental algorithm: ", remove_edge(e, gates))
t2=time.perf_counter()
print("naive incremental use: "+str((t2-t1)*1000)+"ms")
print()
# print(newPathGateMap)

t1=time.perf_counter()
affected=[]
sinks=[]
sink=edgeInputMap[e]
sinks.append(sink)
count=1
while 1==1:
    newsinks=[]
    newaffected=[]
    #print(count)
    for s in sinks:
        if isinstance(gates[s], InputGate):
            #print(s, gates[s])
            newsinks+=gates[s].sinks
            newaffected.append(s)
            #print(affected)
        elif isinstance(gates[s], AndGate):
            #print(s, gates[s])
            newsinks+=gates[s].sinks
            newaffected.append(s)
        elif isinstance(gates[s], OrGate):
            #print(s, gates[s])
            sources=gates[s].sources
            affectsource=[source for source in sources if source not in affected]
            if not affectsource:
                newsinks+=gates[s].sinks
                newaffected.append(s)
            #newsinks+=gates[s].sinks
    if not newaffected:
        break
    affected+=newaffected
    affected.sort()
    sinks=newsinks
    sinks=[*set(sinks)]
    sinks.sort()
    count+=1
t2=time.perf_counter()
affectedstr=[tupleToStr(gates[k].name) for k in affected if not isinstance(gates[k], AndGate)]
# affectedstr=list(set(affectedstr))
affectedstr=sorted(set(affectedstr), key=lambda x: affectedstr.index(x))
print("path removing result using naive incremental algorithm: ", affectedstr)
print("advanced incremental use: "+str((t2-t1)*1000)+"ms")
print()

edges ={('b','c'), ('c','a')}
edges= {Edge(u,v) for u, v in edges}
t1=time.perf_counter()
paths, gates, pathGateMap, newPathGateMap, edgeInputMap=getPathsInstr(edges)
t2=time.perf_counter()
print("rerunning uses: "+str((t2-t1)*1000)+"ms")
# newaffectedstr=[]
# for a in affectedstr:
#     if isinstance(a, IntPath):
#         a=a._replace(iteration=0)
#     newaffectedstr.append(a)
