from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.circuit.library import QFTGate
from qiskit.visualization import plot_histogram, circuit_drawer
import matplotlib.pyplot as plt

%matplotlib inline

# backend and shots
backend = AerSimulator()
shots = 1024

# build circuit: prepare |10101> by X on qubits 0,2,4 (indices 0..4)
qc = QuantumCircuit(5, 5)
qc.x([0, 2, 4]) 

# append 5-qubit QFT (modern QFTGate avoids deprecation warning)
qc.append(QFTGate(5), range(5))

# measure all qubits
qc.measure(range(5), range(5))

# draw circuit (matplotlib)
circuit_drawer(qc, output="mpl")

# transpile, run and get results
qc_t = transpile(qc, backend=backend)
job = backend.run(qc_t, shots=shots)
counts = job.result().get_counts()

# print and plot
print("Counts:", counts)

fig = plot_histogram(counts)
plt.show()  # <-- ensure histogram displays