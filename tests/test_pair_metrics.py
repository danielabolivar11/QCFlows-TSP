import numpy as np
import pytest

from qcflows_api.pair_metrics import compute_metric_matrix


def test_product_state_has_zero_eof_and_mi():
    rho_00 = np.diag([1.0, 0.0, 0.0, 0.0])

    eof = compute_metric_matrix(2, [((0, 1), rho_00)], metric="eof")
    mi = compute_metric_matrix(2, [((0, 1), rho_00)], metric="mi")

    assert eof == [[0.0, 0.0], [0.0, 0.0]]
    assert mi == [[0.0, 0.0], [0.0, 0.0]]


def test_bell_state_has_unit_eof_and_two_bits_mi():
    rho_bell = np.array([
        [0.5, 0.0, 0.0, 0.5],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.5, 0.0, 0.0, 0.5],
    ])

    eof = compute_metric_matrix(2, [((0, 1), rho_bell)], metric="eof")
    mi = compute_metric_matrix(2, [((0, 1), rho_bell)], metric="mi")

    assert eof[0][1] == pytest.approx(1.0)
    assert eof[1][0] == pytest.approx(1.0)
    assert mi[0][1] == pytest.approx(2.0)
    assert mi[1][0] == pytest.approx(2.0)


def test_classically_correlated_state_has_mi_without_eof():
    rho_classical = np.diag([0.5, 0.0, 0.0, 0.5])

    eof = compute_metric_matrix(2, [((0, 1), rho_classical)], metric="eof")
    mi = compute_metric_matrix(2, [((0, 1), rho_classical)], metric="mi")

    assert eof[0][1] == pytest.approx(0.0)
    assert eof[1][0] == pytest.approx(0.0)
    assert mi[0][1] == pytest.approx(1.0)
    assert mi[1][0] == pytest.approx(1.0)


def test_symmetric_metrics_preserve_missing_pairs_as_null():
    rho_bell = np.array([
        [0.5, 0.0, 0.0, 0.5],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.5, 0.0, 0.0, 0.5],
    ])

    matrix = compute_metric_matrix(3, [((0, 2), rho_bell)], metric="eof")

    assert matrix[0][2] == pytest.approx(1.0)
    assert matrix[2][0] == pytest.approx(1.0)
    assert matrix[0][1] is None
    assert matrix[1][2] is None
