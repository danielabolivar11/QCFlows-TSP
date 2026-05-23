from __future__ import annotations

from typing import Any, Literal

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from qcflows_api.k_measure import compute_k_matrix

app = FastAPI(title="QCFlows API", version="0.1.0")


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
