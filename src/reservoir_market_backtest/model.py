"""Compact, deterministic reconstruction of the historical focal model.

This module exposes the actual simulated Ikeda state update, binary feature
mask, ridge readout, expanding walk-forward schedule, and score transform used
by the project. It is suitable for method inspection and synthetic tests. The
historical production runner used an equivalent native C loop for speed; its
SHA-256 identity is retained in ``evidence/private_artifact_hashes.json``.

Because the source-derived historical feature matrices are intentionally not
distributed, this module does not claim an end-to-end refit of the historical
market experiment from a public checkout.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class IkedaConfiguration:
    virtual_nodes: int = 200
    theta_steps: int = 10
    dt: float = 0.08661933269857963
    feedback_gain_beta: float = 0.3441984642966166
    phase_offset: float = 1.1583611813967833
    input_scale: float = 0.013175730055118363
    auxiliary_delta: float = 0.0
    desynchronization: int = 7
    mask_seed: int = 1234

    def validate(self) -> None:
        if self.virtual_nodes <= 0 or self.theta_steps <= 0:
            raise ValueError("virtual_nodes and theta_steps must be positive")
        if self.dt <= 0.0 or self.input_scale <= 0.0:
            raise ValueError("dt and input_scale must be positive")
        if self.desynchronization < 0:
            raise ValueError("desynchronization must be nonnegative")


FROZEN_IKEDA_CONFIGURATION = IkedaConfiguration()


def binary_input_mask(
    n_features: int,
    configuration: IkedaConfiguration = FROZEN_IKEDA_CONFIGURATION,
) -> np.ndarray:
    """Generate the frozen-seed binary input mask."""

    configuration.validate()
    if n_features <= 0:
        raise ValueError("n_features must be positive")
    rng = np.random.default_rng(configuration.mask_seed)
    return (
        rng.choice(
            (-1.0, 1.0),
            size=(configuration.virtual_nodes, n_features),
        )
        * configuration.input_scale
    )


def ikeda_states(
    features: np.ndarray,
    configuration: IkedaConfiguration = FROZEN_IKEDA_CONFIGURATION,
) -> np.ndarray:
    """Transform a chronological feature matrix with the historical Ikeda loop.

    The discretization is the original semi-explicit Euler update. When
    ``auxiliary_delta`` is zero—as in the selected configuration—the auxiliary
    state does not feed back into the main state. The function therefore calls
    this an Ikeda-type delay loop rather than asserting a band-pass realization.
    """

    configuration.validate()
    inputs = np.asarray(features, dtype=np.float64)
    if inputs.ndim != 2 or inputs.shape[0] == 0 or inputs.shape[1] == 0:
        raise ValueError("features must be a nonempty (time, feature) matrix")
    if not np.isfinite(inputs).all():
        raise ValueError("features contain NaN or infinite values")

    mask = binary_input_mask(inputs.shape[1], configuration)
    held = np.repeat(
        (inputs @ mask.T).reshape(-1),
        configuration.theta_steps,
    )
    delay_length = (
        configuration.virtual_nodes * configuration.theta_steps
        + configuration.desynchronization
    )
    history = np.zeros(delay_length, dtype=np.float64)
    output = np.empty(inputs.shape[0] * configuration.virtual_nodes, dtype=np.float64)
    x_state = 0.1
    y_state = 0.0
    history_index = 0
    drive_index = 0
    output_index = 0

    for _time in range(inputs.shape[0]):
        for _node in range(configuration.virtual_nodes):
            for _step in range(configuration.theta_steps):
                delayed_x = history[history_index]
                forcing = configuration.feedback_gain_beta * np.sin(
                    delayed_x + held[drive_index] + configuration.phase_offset
                ) ** 2
                x_state += configuration.dt * (
                    -x_state - configuration.auxiliary_delta * y_state + forcing
                )
                y_state += configuration.dt * x_state
                history[history_index] = x_state
                history_index = (history_index + 1) % delay_length
                drive_index += 1
            output[output_index] = x_state
            output_index += 1

    states = output.reshape(inputs.shape[0], configuration.virtual_nodes)
    if not np.isfinite(states).all():
        raise FloatingPointError("Ikeda state integration produced non-finite values")
    return states


def fit_ridge_readout(states: np.ndarray, targets: np.ndarray, penalty: float) -> np.ndarray:
    """Fit the historically used ridge readout, including a penalized intercept."""

    design = np.asarray(states, dtype=np.float64)
    response = np.asarray(targets, dtype=np.float64)
    if response.ndim == 1:
        response = response[:, None]
    if design.ndim != 2 or response.ndim != 2 or design.shape[0] != response.shape[0]:
        raise ValueError("states and targets must be aligned two-dimensional arrays")
    if design.shape[0] == 0 or penalty < 0.0:
        raise ValueError("training arrays must be nonempty and penalty nonnegative")
    design_with_intercept = np.column_stack((design, np.ones(design.shape[0])))
    gram = design_with_intercept.T @ design_with_intercept
    return np.linalg.solve(
        gram + penalty * np.eye(gram.shape[0]),
        design_with_intercept.T @ response,
    )


def apply_ridge_readout(states: np.ndarray, weights: np.ndarray) -> np.ndarray:
    design = np.asarray(states, dtype=np.float64)
    if design.ndim != 2:
        raise ValueError("states must be two-dimensional")
    return np.column_stack((design, np.ones(design.shape[0]))) @ np.asarray(weights)


def walk_forward_ridge_scores(
    states: np.ndarray,
    targets: np.ndarray,
    *,
    initial_training_days: int,
    penalty: float = 1.0,
    retrain_every: int = 21,
    embargo: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Run the expanding historical readout schedule without look-ahead."""

    design = np.asarray(states, dtype=np.float64)
    response = np.asarray(targets, dtype=np.float64)
    if response.ndim == 1:
        response = response[:, None]
    if design.ndim != 2 or response.shape != (design.shape[0], 1):
        raise ValueError("expected states (T, D) and one target per row")
    if not 0 < initial_training_days < design.shape[0]:
        raise ValueError("initial_training_days must lie inside the series")
    if retrain_every <= 0 or embargo < 0:
        raise ValueError("retrain_every must be positive and embargo nonnegative")

    predictions = np.full(design.shape[0], np.nan, dtype=np.float64)
    mask = np.zeros(design.shape[0], dtype=bool)
    start = initial_training_days
    while start < design.shape[0]:
        training_end = start - embargo
        if training_end <= 0:
            raise ValueError("embargo leaves no training rows")
        weights = fit_ridge_readout(
            design[:training_end],
            response[:training_end],
            penalty,
        )
        stop = min(start + retrain_every, design.shape[0])
        predictions[start:stop] = apply_ridge_readout(design[start:stop], weights).ravel()
        mask[start:stop] = True
        start = stop
    return predictions, mask


def scores_to_up_values(scores: np.ndarray) -> np.ndarray:
    """Apply the historical fixed sigmoid-like score transform."""

    values = np.asarray(scores, dtype=np.float64)
    return 1.0 / (1.0 + np.exp(-4.0 * values))
