"""Asterisk: decision analysis over possible world states."""

from .core import (
    JsonValue,
    Objective,
    Operation,
    Outcome,
    delta,
    expected_improvement,
    improvement,
    numeric_pointer,
    observe,
    pareto_frontier,
    scenario_improvements,
)

__all__ = [
    "JsonValue",
    "Objective",
    "Operation",
    "Outcome",
    "delta",
    "expected_improvement",
    "improvement",
    "numeric_pointer",
    "observe",
    "pareto_frontier",
    "scenario_improvements",
]

__version__ = "0.1.0.dev0"
