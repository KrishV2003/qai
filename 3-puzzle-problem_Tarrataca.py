import math
import numpy as np
from itertools import permutations
from collections import Counter
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import UnitaryGate
from qiskit_aer import AerSimulator

# ----------------------------
# STEP 1: Define puzzle encoding
# ----------------------------
# 2x2 puzzle -> 4 tiles (0 = empty)
# We can arrange them in 4! = 24 different ways.
# We'll represent each arrangement as a unique number (index 0–23).

perms = list(permutations([0, 1, 2, 3]))  # all valid board states

# Convert puzzle configuration to an integer index
def perm_to_index(p):
    idx = 0
    elems = list(p)
    n = 4
    for i in range(n):
        smaller = sum(1 for j in range(i + 1, n) if elems[j] < elems[i])
        idx += smaller * math.factorial(n - i - 1)
    return idx

# Convert index back to puzzle configuration
def index_to_perm(idx):
    elems = list(range(4))
    perm = []
    for i in range(3, -1, -1):
        f = math.factorial(i)
        pos = idx // f
        idx = idx % f
        perm.append(elems.pop(pos))
    return tuple(perm)

# ----------------------------
# STEP 2: Define production rules (swaps)
# ----------------------------
# Rules represent legal moves of the empty tile
# Each rule is a SWAP between two positions
swap_rules = [(0, 1), (0, 2), (1, 3), (2, 3)]  # all valid neighbor swaps
n_state_q = 5  # 2^5 = 32 >= 24 states

# Build a reversible (unitary) matrix for each swap rule
def build_swap_unitary(a, b):
    dim = 2**n_state_q
    U = np.eye(dim, dtype=complex)
    for p in perms:
        i = perm_to_index(p)
        pos = p.index(0)  # where is the empty tile?
        # If empty tile is at one of the swap positions, perform the swap
        if pos == a or pos == b:
            new = list(p)
            new[a], new[b] = new[b], new[a]
            j = perm_to_index(tuple(new))
            U[j, i] = 1
            U[i, i] = 0
    return U

# Create 4 unitary swap gates
rule_gates = [UnitaryGate(build_swap_unitary(a, b), label=f"R{k}") for k, (a, b) in enumerate(swap_rules)]

# ----------------------------
# STEP 3: Build the Tarrataca circuit
# ----------------------------
def build_tarrataca(start, goal, depth=2):
    start_idx = perm_to_index(start)
    goal_idx = perm_to_index(goal)

    # Each rule step is encoded in 2 qubits (since we have 4 rules)
    bits_per_rule = 2
    total_rule_bits = bits_per_rule * depth
    total_qubits = n_state_q + total_rule_bits

    qc = QuantumCircuit(total_qubits, total_qubits)
    state_qs = list(range(n_state_q))
    rule_qs = [n_state_q + i for i in range(total_rule_bits)]

    # ---- Initialize the puzzle to the start configuration
    start_bits = format(start_idx, f'0{n_state_q}b')[::-1]
    for q, b in enumerate(start_bits):
        if b == '1':
            qc.x(state_qs[q])

    # ---- Put rule qubits in superposition (try all rule sequences)
    for q in rule_qs:
        qc.h(q)

    # ---- Function: Apply rules controlled by the rule qubits
    def apply_rules(forward=True):
        steps = range(depth) if forward else reversed(range(depth))
        for s in steps:
            ctrl = rule_qs[s*bits_per_rule:(s+1)*bits_per_rule]
            gates = rule_gates if forward else reversed(rule_gates)
            for val, gate in enumerate(gates):
                pattern = format(val, f'0{bits_per_rule}b')[::-1]
                g = gate.control(bits_per_rule, ctrl_state=pattern)
                qc.append(g, ctrl + state_qs)

    # ---- Oracle: Mark (phase-flip) the goal state
    def oracle():
        goal_bits = format(goal_idx, f'0{n_state_q}b')[::-1]
        for i, b in enumerate(goal_bits):
            if b == '0':
                qc.x(state_qs[i])
        last = state_qs[-1]
        qc.h(last)
        qc.mcx(state_qs[:-1], last)
        qc.h(last)
        for i, b in enumerate(goal_bits):
            if b == '0':
                qc.x(state_qs[i])

    # ---- Diffusion operator on rule qubits (Grover step)
    def diffusion():
        for q in rule_qs:
            qc.h(q); qc.x(q)
        last = rule_qs[-1]
        qc.h(last)
        qc.mcx(rule_qs[:-1], last)
        qc.h(last)
        for q in rule_qs:
            qc.x(q); qc.h(q)

    # ---- Grover loop (apply sequence → oracle → undo → diffusion)
    num_rules = len(rule_gates)
    S = num_rules ** depth
    iterations = max(1, int(round((math.pi / 4) * math.sqrt(S))))

    for _ in range(iterations):
        apply_rules(True)
        oracle()
        apply_rules(False)
        diffusion()

    # ---- Apply rules one last time to get final puzzle state
    apply_rules(True)
    qc.measure(range(total_qubits), range(total_qubits))
    return qc

# ----------------------------
# STEP 4: Run the simulation
# ----------------------------
start = (1, 2, 3, 0)  # initial puzzle
goal = (1, 2, 0, 3)   # goal puzzle
qc = build_tarrataca(start, goal, depth=2)

sim = AerSimulator()
result = sim.run(transpile(qc, sim), shots=512).result()
counts = result.get_counts()

# ----------------------------
# STEP 5: Decode and show results
# ----------------------------
bits_per_rule = 2
total_rule_bits = bits_per_rule * 2
mapped = Counter()

for bits, c in counts.items():
    bits = bits[::-1]  # LSB-first
    state_idx = int(bits[:n_state_q][::-1], 2)
    rule_idx = int(bits[n_state_q:n_state_q+total_rule_bits][::-1], 2)
    seq = [(rule_idx >> (s * bits_per_rule)) & 3 for s in range(2)]
    mapped[(index_to_perm(state_idx), tuple(seq))] += c

print("\n🧠 Top results (Final puzzle state, Rule sequence, Frequency):")
for (perm, seq), cnt in mapped.most_common(6):
    print(f"{perm}  <-- by applying rules {seq} ({cnt} counts)")
