import pytest
from fastapi import HTTPException
from qcflows_api.demo.routes import demo_page, demo_script, demo_styles
from qcflows_api.main import (
    KMatrixRequest,
    app,
    get_circuit,
    get_operations,
    get_state,
    graph_data,
    health,
    k_matrix,
    timeline,
)


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


def test_get_state_endpoint_returns_demo_bell_state():
    payload = get_state()
    nonzero = [
        item for item in payload["amplitudes"]
        if item["magnitude_squared"] > 1e-9
    ]

    assert payload["basis"] == "z"
    assert payload["marker"] == 2
    assert payload["num_qubits"] == 5
    assert [item["basis_state"] for item in nonzero] == ["|00000>", "|00011>"]
    assert [item["magnitude_squared"] for item in nonzero] == [
        pytest.approx(0.5),
        pytest.approx(0.5),
    ]


def test_timeline_endpoint_returns_demo_markers():
    payload = timeline()

    assert payload["current_marker"] == 2
    assert payload["markers"] == [
        {"id": 0, "label": "Input", "operation_count": 0},
        {"id": 1, "label": "After H(0)", "operation_count": 1},
        {"id": 2, "label": "After CX(0,1)", "operation_count": 2},
    ]


def test_get_operations_endpoint_returns_demo_operation_model():
    payload = get_operations()

    assert payload == {
        "num_qubits": 5,
        "operation_count": 2,
        "operations": [
            {
                "id": 1,
                "gate": "h",
                "qubits": [0],
                "params": {},
                "label": "H(0)",
            },
            {
                "id": 2,
                "gate": "cx",
                "qubits": [0, 1],
                "params": {},
                "label": "CX(0,1)",
            },
        ],
    }


def test_get_state_endpoint_can_select_history_marker():
    payload = get_state(marker=1)
    nonzero = [
        item for item in payload["amplitudes"]
        if item["magnitude_squared"] > 1e-9
    ]

    assert payload["marker"] == 1
    assert payload["marker_label"] == "After H(0)"
    assert [item["basis_state"] for item in nonzero] == ["|00000>", "|00001>"]
    assert [item["magnitude_squared"] for item in nonzero] == [
        pytest.approx(0.5),
        pytest.approx(0.5),
    ]


def test_graph_data_endpoint_returns_demo_k_signal():
    payload = graph_data()

    assert payload["metric"] == "k"
    assert payload["metric_label"] == "K_Z"
    assert payload["num_qubits"] == 5
    assert payload["nodes"][0]["prob0"] == pytest.approx(0.5)
    assert payload["nodes"][1]["prob0"] == pytest.approx(0.5)
    assert payload["nodes"][2]["prob0"] == pytest.approx(1.0)
    assert payload["matrix"][0][1] == pytest.approx(1.0)
    assert payload["matrix"][1][0] == pytest.approx(1.0)
    assert payload["edges"] == [{
        "source": 0,
        "target": 1,
        "value": pytest.approx(1.0),
        "directed": False,
    }]


def test_graph_data_endpoint_can_select_pre_correlation_marker():
    payload = graph_data(marker=0)

    assert payload["marker"] == 0
    assert payload["marker_label"] == "Input"
    assert payload["nodes"][0]["prob0"] == pytest.approx(1.0)
    assert payload["nodes"][1]["prob0"] == pytest.approx(1.0)
    assert payload["matrix"][0][1] is None
    assert payload["edges"] == []


def test_get_circuit_endpoint_returns_demo_diagram():
    payload = get_circuit()

    assert payload["marker_label"] == "After CX(0,1)"
    assert payload["num_qubits"] == 5
    assert payload["operation_count"] == 2
    assert [operation["label"] for operation in payload["operations"]] == [
        "H(0)",
        "CX(0,1)",
    ]
    assert "q[0] |0> -H-@-" in payload["circuit_diagram"]
    assert "q[1] |0> ---X-" in payload["circuit_diagram"]


def test_get_circuit_endpoint_can_select_history_marker():
    payload = get_circuit(marker=1)

    assert payload["marker"] == 1
    assert payload["operation_count"] == 1
    assert [operation["label"] for operation in payload["operations"]] == ["H(0)"]
    assert "q[0] |0> -H-" in payload["circuit_diagram"]
    assert "q[1] |0> ---" in payload["circuit_diagram"]
    assert "---X-" not in payload["circuit_diagram"]


def test_history_marker_rejects_unknown_marker():
    with pytest.raises(HTTPException) as exc_info:
        graph_data(marker=9)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "marker must be between 0 and 2"


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
