from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from collections import deque
import math

backend = AerSimulator()

def qrng_int(M):
    n = math.ceil(math.log2(M))
    qc = QuantumCircuit(n, n)
    qc.h(range(n)); qc.measure(range(n), range(n))
    job = backend.run(transpile(qc, backend), shots=1)
    bitstr = next(iter(job.result().get_counts().keys()))
    return int(bitstr, 2) % M

def index_to_perm(i, n):
    items=list(range(n)); p=[]
    for k in range(n-1,-1,-1):
        f=math.factorial(k); pos=i//f; i%=f
        p.append(items.pop(pos))
    return p

def solvable(p):
    a=[x for x in p if x!=0]
    inv=sum(a[i]>a[j] for i in range(len(a)) for j in range(i+1,len(a)))
    return inv%2==0

def solve_bfs(start):
    goal=(0,1,2,3); start=tuple(start)
    if start==goal: return [start]
    neigh={0:[1,2],1:[0,3],2:[0,3],3:[1,2]}
    q=deque([start]); parent={start:None}
    while q:
        s=q.popleft(); z=s.index(0)
        for nb in neigh[z]:
            t=list(s); t[z],t[nb]=t[nb],t[z]; t=tuple(t)
            if t not in parent:
                parent[t]=s; q.append(t)
                if t==goal:
                    path=[t]
                    while parent[path[-1]] is not None: path.append(parent[path[-1]])
                    return list(reversed(path))
    return None

# Generate quantum-random solvable puzzle and solve
M = math.factorial(4)
while True:
    perm = index_to_perm(qrng_int(M), 4)
    if solvable(perm):
        path = solve_bfs(perm)
        if path: break  # ensure solvable and path exists
        
print("Quantum-random start (0 = blank):", perm)
print("Number of moves to goal:", len(path) - 1)
for i, st in enumerate(path):
    print(f"Step {i}: {st[0]} {st[1]}  /  {st[2]} {st[3]}")
    
