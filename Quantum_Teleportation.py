from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
from IPython.display import display

shots = 1024
backend = AerSimulator()

q = QuantumRegister(3, 'q')
c = ClassicalRegister(3, 'c')

qc = QuantumCircuit(q, c) 

qc.x(q[0])

qc.h(q[1])
qc.cx(q[1], q[2])

qc.cx(q[0], q[1])
qc.h(q[0])

qc.measure(q[0], c[0])
qc.measure(q[1], c[0])

qc.x(q[2])
last = qc.data[-1]
instr = last.operation
qargs = last.qubits
cargs = last.clbits
mutable_instr = instr.to_mutable()
mutable_instr.condition = (c, 2)   # c[1] == 1 -> integer value 2 (binary 010)
qc.data[-1] = (mutable_instr, qargs, cargs)

qc.z(q[2])
last = qc.data[-1]
instr = last.operation
qargs = last.qubits
cargs = last.clbits
mutable_instr = instr.to_mutable()
mutable_instr.condition = (c, 1)   # c[0] == 1 -> integer value 1 (binary 001)
qc.data[-1] = (mutable_instr, qargs, cargs)

qc.measure(q[2], c[2])

qc_compiled = transpile(qc, backend)
job = backend.run(qc_compiled, shots=shots)
result = job.result()
counts = result.get_counts(qc_compiled)

print("\nCounts:", counts)
print("Bitstring order [c2 c1 c0], c2 = Bob's measurement\n")

display(plot_histogram(counts))

print("\nCircuit (text):")
print(qc.draw(output='text'))
