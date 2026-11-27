"""Small, dependency-free decision kernel for Asterisk.

The kernel deliberately does not define a universal structural difference
between arbitrary JSON values. Decisions care about semantic differences:
changes in declared observables/objectives.

Given a vector-valued observation function G and states s0, s1,

    delta_G(s0, s1) = G(s1) - G(s0)

is well-defined even when the surrounding JSON structures contain large
amounts of irrelevant or incomparable information.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from typing import Callable, Iterable, Literal, Mapping, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
Measure: TypeAlias = Callable[[JsonValue], float]
Transition: TypeAlias = Callable[[JsonValue], Iterable["Outcome"]]
Sense: TypeAlias = Literal["maximize", "minimize"]


@dataclass(frozen=True, slots=True)
class Objective:
    """A goal-relevant scalar observable.

    sense only orients preference. delta remains a raw measurement change,
    while improvement is positive when the objective gets better.
    """

    name: str
    measure: Measure
    sense: Sense = "maximize"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("objective name must not be empty")
        if self.sense not in ("maximize", "minimize"):
            raise ValueError("sense must be 'maximize' or 'minimize'")

    def value(self, state: JsonValue) -> float:
        value = float(self.measure(state))
        if not isfinite(value):
            raise ValueError(f"objective {self.name!r} produced a non-finite value")
        return value

    def improvement(self, before: JsonValue, after: JsonValue) -> float:
        raw_delta = self.value(after) - self.value(before)
        return raw_delta if self.sense == "maximize" else -raw_delta


@dataclass(frozen=True, slots=True)
class Outcome:
    """One possible post-state of an operation.

    probability=None is intentionally distinct from an equiprobable outcome.
    Unknown probabilities should not silently become known ones.
    """

    state: JsonValue
    probability: float | None = None

    def __post_init__(self) -> None:
        if self.probability is not None and not 0.0 <= self.probability <= 1.0:
            raise ValueError("outcome probability must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class Operation:
    """A state transition that may have multiple possible outcomes."""

    name: str
    transition: Transition

    def outcomes(self, state: JsonValue) -> tuple[Outcome, ...]:
        outcomes = tuple(self.transition(state))
        if not outcomes:
            raise ValueError(f"operation {self.name!r} produced no outcomes")
        return outcomes


def _objective_tuple(objectives: Iterable[Objective]) -> tuple[Objective, ...]:
    result = tuple(objectives)
    names = [objective.name for objective in result]
    if len(names) != len(set(names)):
        raise ValueError("objective names must be unique")
    return result


def observe(state: JsonValue, objectives: Iterable[Objective]) -> dict[str, float]:
    """Project a state into its goal-relevant observable vector."""

    objs = _objective_tuple(objectives)
    return {objective.name: objective.value(state) for objective in objs}


def delta(
    before: JsonValue,
    after: JsonValue,
    objectives: Iterable[Objective],
) -> dict[str, float]:
    """Return raw observable change: after minus before."""

    objs = _objective_tuple(objectives)
    return {
        objective.name: objective.value(after) - objective.value(before)
        for objective in objs
    }


def improvement(
    before: JsonValue,
    after: JsonValue,
    objectives: Iterable[Objective],
) -> dict[str, float]:
    """Return preference-oriented change; positive means better."""

    objs = _objective_tuple(objectives)
    return {
        objective.name: objective.improvement(before, after)
        for objective in objs
    }


def scenario_improvements(
    operation: Operation,
    state: JsonValue,
    objectives: Iterable[Objective],
) -> tuple[dict[str, float], ...]:
    """Evaluate every possible outcome without assuming probabilities."""

    objs = _objective_tuple(objectives)
    return tuple(
        improvement(state, outcome.state, objs)
        for outcome in operation.outcomes(state)
    )


def expected_improvement(
    operation: Operation,
    state: JsonValue,
    objectives: Iterable[Objective],
) -> dict[str, float]:
    """Return the probability-weighted improvement vector.

    This function refuses to invent probabilities. Every outcome must carry
    one, and the probabilities must sum to one.
    """

    objs = _objective_tuple(objectives)
    outcomes = operation.outcomes(state)

    if any(outcome.probability is None for outcome in outcomes):
        raise ValueError("expected improvement requires probabilities for all outcomes")

    probabilities = [float(outcome.probability) for outcome in outcomes]
    if not isclose(sum(probabilities), 1.0, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("outcome probabilities must sum to 1")

    total = {objective.name: 0.0 for objective in objs}
    for outcome, probability in zip(outcomes, probabilities):
        vector = improvement(state, outcome.state, objs)
        for name, value in vector.items():
            total[name] += probability * value
    return total


def dominates(
    left: Mapping[str, float],
    right: Mapping[str, float],
    *,
    epsilon: float = 0.0,
) -> bool:
    """Whether left Pareto-dominates right.

    Inputs are assumed to be preference-oriented, i.e. larger is better.
    """

    if left.keys() != right.keys():
        raise ValueError("vectors must contain the same objectives")

    no_worse = all(left[key] >= right[key] - epsilon for key in left)
    strictly_better = any(left[key] > right[key] + epsilon for key in left)
    return no_worse and strictly_better


def pareto_frontier(
    alternatives: Mapping[str, Mapping[str, float]],
    *,
    epsilon: float = 0.0,
) -> list[str]:
    """Return non-dominated alternatives, preserving input order."""

    names = list(alternatives)
    frontier: list[str] = []
    for candidate in names:
        vector = alternatives[candidate]
        if not any(
            other != candidate
            and dominates(alternatives[other], vector, epsilon=epsilon)
            for other in names
        ):
            frontier.append(candidate)
    return frontier


def numeric_pointer(pointer: str) -> Measure:
    """Build a numeric measure from an RFC-6901-style JSON Pointer.

    Dictionaries and arrays are supported. The selected value must be a
    finite number; booleans are rejected even though Python subclasses bool
    from int.
    """

    if pointer == "":
        tokens: tuple[str, ...] = ()
    else:
        if not pointer.startswith("/"):
            raise ValueError("JSON Pointer must be empty or start with '/'")
        tokens = tuple(
            token.replace("~1", "/").replace("~0", "~")
            for token in pointer[1:].split("/")
        )

    def measure(state: JsonValue) -> float:
        current: JsonValue = state

        for token in tokens:
            if isinstance(current, dict):
                current = current[token]
            elif isinstance(current, list):
                try:
                    index = int(token)
                except ValueError as exc:
                    raise KeyError(f"array index is not an integer: {token!r}") from exc
                current = current[index]
            else:
                raise KeyError(f"cannot descend through scalar at {token!r}")

        if isinstance(current, bool) or not isinstance(current, (int, float)):
            raise TypeError(f"JSON Pointer {pointer!r} does not select a number")

        value = float(current)
        if not isfinite(value):
            raise ValueError(f"JSON Pointer {pointer!r} selected a non-finite number")
        return value

    return measure
