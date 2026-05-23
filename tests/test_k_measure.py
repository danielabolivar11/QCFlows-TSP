import numpy as np
import pytest
from qcflows_api.k_measure import compute_k_matrix


def test_product_state_has_zero_k_values():
    rho_00 = np.diag([1.0, 0.0, 0.0, 0.0])

    matrix = compute_k_matrix(2, [((0, 1), rho_00)], basis="z")

    assert matrix == [[0.0, 0.0], [0.0, 0.0]]


def test_bell_state_has_unit_k_in_both_directions():
    rho_bell = np.array([
        [0.5, 0.0, 0.0, 0.5],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.5, 0.0, 0.0, 0.5],
    ])

    matrix = compute_k_matrix(2, [((0, 1), rho_bell)], basis="z")

    assert matrix[0][1] == 1.0
    assert matrix[1][0] == 1.0


def test_w3_pair_rdm_matches_z_basis_paper_example():
    rho_w3_pair = np.array([
        [1 / 3, 0.0, 0.0, 0.0],
        [0.0, 1 / 3, 1 / 3, 0.0],
        [0.0, 1 / 3, 1 / 3, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ])

    matrix = compute_k_matrix(2, [((0, 1), rho_w3_pair)], basis="z")

    assert matrix[0][1] == pytest.approx(4 / 9)
    assert matrix[1][0] == pytest.approx(4 / 9)
