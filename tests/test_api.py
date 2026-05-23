import pytest
from fastapi import HTTPException
from qcflows_api.demo.routes import demo_page, demo_script, demo_styles
from qcflows_api.main import KMatrixRequest, app, health, k_matrix


def test_health_endpoint():
    assert health() == {"status": "ok"}


def test_demo_page_is_served_with_live_k_matrix_endpoint():
    response = demo_page()
    body = response.body.decode()

    assert response.status_code == 200
    assert "QCFlows K-matrix Demo" in body
    assert '<link rel="stylesheet" href="/demo.css">' in body
    assert '<script src="/demo.js" defer></script>' in body


def test_demo_assets_are_served():
    css_response = demo_styles()
    js_response = demo_script()

    assert css_response.media_type == "text/css"
    assert "grid-template-columns" in css_response.body.decode()
    assert js_response.media_type == "application/javascript"
    assert 'fetch("/v0/k-matrix"' in js_response.body.decode()


def test_demo_router_is_registered_on_app():
    paths = {route.path for route in app.routes}

    assert "/" in paths
    assert "/demo.css" in paths
    assert "/demo.js" in paths


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
