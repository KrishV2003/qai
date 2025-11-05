from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt

shots = 2048
p1, p2 = 0.01, 0.02
noise = NoiseModel()
noise.add_all_qubit_quantum_error(depolarizing_error(p1,1), ['h','x','u1','u2','u3','rz','sx'])
noise.add_all_qubit_quantum_error(depolarizing_error(p2,2), ['cx'])
backend = AerSimulator()

# Bare circuit (start in |0>, measure) — logical error = measuring '1'
circ_bare = QuantumCircuit(1,1)
circ_bare.measure(0,0)
circ_bare = transpile(circ_bare, backend=backend)

# Encoded 3-qubit repetition code for |0> (|000>), measure all 3 physical qubits
qc_enc = QuantumCircuit(3,3)
qc_enc.cx(0,1)
qc_enc.cx(0,2)
qc_enc.measure([0,1,2],[0,1,2])
qc_enc = transpile(qc_enc, backend=backend)

# Run
cnt_bare = backend.run(circ_bare, shots=shots, noise_model=noise).result().get_counts()
cnt_enc  = backend.run(qc_enc,    shots=shots, noise_model=noise).result().get_counts()

# Majority decode
def majority_decode(counts3):
    out = {'0':0,'1':0}
    for bits,c in counts3.items():
        out['1' if bits.count('1')>=2 else '0'] += c
    return out

dec_enc = majority_decode(cnt_enc)

# Logical error rates (we started in |0>, so '1' is error)
bare_err = cnt_bare.get('1',0)/sum(cnt_bare.values())
enc_err  = dec_enc.get('1',0)/sum(dec_enc.values())
impr_pct = (bare_err - enc_err)/bare_err*100 if bare_err>0 else 0.0

# Output
print(f"Shots: {shots}")
print("Bare counts:", cnt_bare)
print("Encoded physical counts:", cnt_enc)
print("Encoded decoded counts:", dec_enc)
print(f"Bare logical error rate: {bare_err:.6f}")
print(f"Encoded logical error rate: {enc_err:.6f}")
print(f"Percent improvement: {impr_pct:.2f}%")

# Quick visual (optional)
fig, axes = plt.subplots(1,2,figsize=(10,4))
plot_histogram({'0': cnt_bare.get('0',0), '1': cnt_bare.get('1',0)}, ax=axes[0], title="Bare")
plot_histogram(dec_enc, ax=axes[1], title="Encoded (majority decode)")
plt.tight_layout(); plt.show()

