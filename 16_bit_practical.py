from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit, transpile
from qiskit_aer import Aer

q = QuantumRegister(16, 'q')
c = ClassicalRegister(16, 'c')
circuit = QuantumCircuit(q, c)

circuit.h(q)

circuit.measure(q, c)

circuit.draw()

backend = Aer.get_backend('qasm_simulator')

t_circuit = transpile(circuit, backend)

job = backend.run(t_circuit, shots=1)

result = job.result()
counts = result.get_counts()
print('Result:', counts)
