from __future__ import annotations

from typing import Any, Literal

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from qcflows_api.demo.routes import router as demo_router
from qcflows_api.k_measure import compute_k_matrix

app = FastAPI(title="QCFlows API", version="0.1.0")
app.include_router(demo_router)


class RDMInput(BaseModel):
    qubits: tuple[int, int] = Field(
        description="Qubit pair [a, b]. RDM basis order is |a b> = 00, 01, 10, 11.")
    rho: list[list[Any]] = Field(
        description="4x4 density matrix. Entries may be numbers or [real, imag].")


class KMatrixRequest(BaseModel):
    num_qubits: int = Field(ge=1)
    basis: Literal["x", "y", "z"] = "z"
    rdms: list[RDMInput]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v0/k-matrix")
def k_matrix(request: KMatrixRequest) -> dict[str, Any]:
    try:
        rdms = [
            (rdm.qubits, _parse_complex_matrix(rdm.rho))
            for rdm in request.rdms
        ]
        matrix = compute_k_matrix(
            num_qubits=request.num_qubits,
            rdms=rdms,
            basis=request.basis,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "version": "0.1.0",
        "basis": request.basis,
        "num_qubits": request.num_qubits,
        "matrix": matrix,
    }


@app.get("/get_state")
def get_state(basis: Literal["x", "y", "z"] = "z") -> dict[str, Any]:
    state = _demo_statevector(basis)
    return {
        "basis": basis,
        "num_qubits": _DEMO_NUM_QUBITS,
        "amplitudes": [
            {
                "basis_state": f"|{index:0{_DEMO_NUM_QUBITS}b}>",
                "amplitude": _complex_pair(amplitude),
                "magnitude_squared": float(np.abs(amplitude) ** 2),
            }
            for index, amplitude in enumerate(state)
        ],
    }


@app.get("/graph_data")
def graph_data(
    basis: Literal["x", "y", "z"] = "z",
    metric: Literal["k"] = "k",
) -> dict[str, Any]:
    matrix = compute_k_matrix(
        num_qubits=_DEMO_NUM_QUBITS,
        rdms=[((0, 1), _DEMO_BELL_RDM)],
        basis=basis,
    )
    return {
        "basis": basis,
        "metric": metric,
        "metric_label": f"K_{basis.upper()}",
        "metric_max": 1.0,
        "num_qubits": _DEMO_NUM_QUBITS,
        "nodes": _demo_nodes(basis),
        "edges": _matrix_edges(matrix),
        "matrix": matrix,
    }


def _parse_complex_matrix(raw_matrix: list[list[Any]]) -> np.ndarray:
    if len(raw_matrix) != 4 or any(len(row) != 4 for row in raw_matrix):
        raise ValueError("each RDM rho must be a 4x4 matrix")

    return np.array(
        [[_parse_complex_entry(entry) for entry in row] for row in raw_matrix],
        dtype=complex,
    )


def _parse_complex_entry(value: Any) -> complex:
    if isinstance(value, bool):
        raise ValueError("matrix entries must be numbers or [real, imag]")
    if _is_number(value):
        return complex(float(value), 0.0)
    if (isinstance(value, list) and len(value) == 2
            and all(_is_number(component) for component in value)):
        return complex(float(value[0]), float(value[1]))
    raise ValueError("matrix entries must be numbers or [real, imag]")


def _is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


_DEMO_NUM_QUBITS = 5
_DEMO_BELL_STATE = np.zeros(2**_DEMO_NUM_QUBITS, dtype=complex)
_DEMO_BELL_STATE[0] = 1 / np.sqrt(2)
_DEMO_BELL_STATE[3] = 1 / np.sqrt(2)
_DEMO_BELL_RDM = np.array([
    [0.5, 0.0, 0.0, 0.5],
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
    [0.5, 0.0, 0.0, 0.5],
], dtype=complex)


def _demo_statevector(basis: str) -> np.ndarray:
    state = _DEMO_BELL_STATE.copy()
    if basis == "z":
        return state
    rotation = _basis_display_rotation(basis)
    for qubit in range(_DEMO_NUM_QUBITS):
        state = _apply_single_qubit(state, qubit, rotation)
    return state


def _demo_nodes(basis: str) -> list[dict[str, float | int]]:
    state = _demo_statevector(basis)
    probabilities = np.abs(state) ** 2
    nodes: list[dict[str, float | int]] = []
    for qubit in range(_DEMO_NUM_QUBITS):
        mask = 1 << qubit
        prob0 = sum(
            float(probability)
            for index, probability in enumerate(probabilities)
            if not index & mask
        )
        nodes.append({"id": qubit, "prob0": prob0})
    return nodes


def _matrix_edges(matrix: list[list[float | None]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for source in range(len(matrix)):
        for target in range(source + 1, len(matrix)):
            forward = float(matrix[source][target] or 0.0)
            reverse = float(matrix[target][source] or 0.0)
            value = max(forward, reverse)
            if value <= 1e-9:
                continue
            directed = abs(forward - reverse) > 1e-9
            edges.append({
                "source": source if forward >= reverse else target,
                "target": target if forward >= reverse else source,
                "value": value,
                "directed": directed,
            })
    return edges


def _basis_display_rotation(basis: str) -> np.ndarray:
    h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    if basis == "x":
        return h
    return h @ np.array([[1, 0], [0, -1j]], dtype=complex)


def _apply_single_qubit(
    state: np.ndarray,
    qubit: int,
    matrix: np.ndarray,
) -> np.ndarray:
    result = state.copy()
    mask = 1 << qubit
    for base in range(state.size):
        if base & mask:
            continue
        paired = base | mask
        zero = state[base]
        one = state[paired]
        result[base] = matrix[0, 0] * zero + matrix[0, 1] * one
        result[paired] = matrix[1, 0] * zero + matrix[1, 1] * one
    return result


def _complex_pair(value: complex) -> list[float]:
    real = float(np.real(value))
    imag = float(np.imag(value))
    return [
        0.0 if abs(real) < 1e-12 else real,
        0.0 if abs(imag) < 1e-12 else imag,
    ]
