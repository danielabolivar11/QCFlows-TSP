import pytest
from fastapi import HTTPException
from qcflows_api.main import KMatrixRequest, health, k_matrix


def test_health_endpoint():
    assert health() == {"status": "ok"}


def test_k_matrix_endpoint_returns_ordered_matrix_with_missing_pairs_as_null():
    payload = k_matrix(
        KMatrixRequest(
            num_qubits=3,
            basis="z",
            rdms=[{
                "qubits": [0, 1],
                "rho": [
                    [0.5, 0.0, 0.0, 0.5],
                    [0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0],
                    [0.5, 0.0, 0.0, 0.5],
                ],
            }],
        ))

    assert payload["matrix"] == [
        [0.0, 1.0, None],
        [1.0, 0.0, None],
        [None, None, 0.0],
    ]


def test_k_matrix_endpoint_accepts_complex_entries():
    payload = k_matrix(
        KMatrixRequest(
            num_qubits=2,
            basis="z",
            rdms=[{
                "qubits": [0, 1],
                "rho": [
                    [[0.5, 0.0], 0.0, 0.0, [0.5, 0.0]],
                    [0.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0],
                    [[0.5, 0.0], 0.0, 0.0, [0.5, 0.0]],
                ],
            }],
        ))

    assert payload["matrix"] == [[0.0, 1.0], [1.0, 0.0]]


def test_k_matrix_endpoint_rejects_bad_matrix_shape():
    request = KMatrixRequest(
        num_qubits=2,
        basis="z",
        rdms=[{
            "qubits": [0, 1],
            "rho": [[1.0]]
        }],
    )

    with pytest.raises(HTTPException) as exc_info:
        k_matrix(request)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "each RDM rho must be a 4x4 matrix"
