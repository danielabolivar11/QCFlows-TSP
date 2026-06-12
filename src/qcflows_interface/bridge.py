import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, partial_trace

_SINGLE_QUBIT_GATES = {"h", "x", "y", "z", "s", "t", "sdg", "tdg", "sx"}
_SINGLE_QUBIT_ROT = {"rx", "ry", "rz"}
_TWO_QUBIT_GATES = {"cx", "cz", "swap"}
_CONTROLLED_ROT = {"crx", "cry", "crz"}


# Switch endianess of the RDMs fom qiskit format |j i> to qcflow format |i j>. swap the order of the qubits leads to the permutation below:
_PERM = [0, 2, 1, 3]



def _angle(params: dict) -> float:
    if not params:
        return np.pi / 2
    for key in ("angle", "theta"):
        if key in params:
            return float(params[key])
    return float(next(iter(params.values())))


def build_circuit(num_qubits: int, operations: list[dict]) -> QuantumCircuit:
    qc = QuantumCircuit(num_qubits)

    for op in operations:
        gate = str(op["gate"]).lower()
        qubits = [int(q) for q in op["qubits"]]
        params = op.get("params", {})

        if gate in _SINGLE_QUBIT_GATES:
            getattr(qc, gate)(qubits[0])
        elif gate in _SINGLE_QUBIT_ROT:
            getattr(qc, gate)(_angle(params), qubits[0])
        elif gate in _TWO_QUBIT_GATES:
            getattr(qc, gate)(qubits[0], qubits[1])
        elif gate in _CONTROLLED_ROT:
            getattr(qc, gate)(_angle(params), qubits[0], qubits[1])
        else:
            raise ValueError(f"Unsupported gate: {gate!r}")

    return qc




def _pack(m: np.ndarray) -> list:
    return [[[float(v.real), float(v.imag)] for v in row] for row in m]

def _pair_rdm(state: Statevector, n: int, i: int, j: int) -> np.ndarray:
    dm = partial_trace(state, [q for q in range(n) if q not in (i, j)]).data
    return dm[np.ix_(_PERM, _PERM)]

def _single_rdm(state: Statevector, n: int, i: int) -> np.ndarray:
    dm = partial_trace(state, [q for q in range(n) if q != i]).data
    return dm[np.ix_([0, 1], [0, 1])]


def simulate_marker(num_qubits: int, operations: list[dict]) -> dict:
    state = Statevector.from_instruction(build_circuit(num_qubits, operations))

    rdms = [
            {"qubits": [i, j], "rho": _pack(_pair_rdm(state, num_qubits, i, j))}
            for i in range(num_qubits) for j in range(i + 1, num_qubits)
        ]
    marginals = [
            {"qubit": q, "rho": _pack(_single_rdm(state, num_qubits, q))}
            for q in range(num_qubits)
        ]
    statevector = [[float(v.real), float(v.imag)] for v in state.data]

    return {"rdms": rdms, "marginals": marginals, "statevector": statevector}
