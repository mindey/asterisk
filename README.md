# Asterisk

**Decision analysis over possible world states.**

Asterisk began in 2016 as an attempt to make quantitative decision and risk
tools useful for arbitrary personal and machine goals: represent reality,
represent desired states, describe possible actions, and compare what those
actions may produce.

The modernization keeps that purpose while making the core much smaller.

## The central idea

A possible state may be any JSON-compatible value. Asterisk does **not** try
to define one universal semantic subtraction operation over arbitrary JSON.
Instead, a decision declares the observables that matter.

\[
\Delta_G(s_0,s_1)=G(s_1)-G(s_0)
\]

where \(G\) is a vector of goal-relevant measurements.

This means that a large structural difference can be irrelevant to a decision,
while a one-number change can be decisive.

~~~python
from asterisk import Objective, improvement, numeric_pointer

before = {
    "project": {"knowledge": 2},
    "resources": {"cost": 10},
    "private_notes": "anything",
}

after = {
    "project": {"knowledge": 5},
    "resources": {"cost": 12},
    "private_notes": "structurally unrelated changes are allowed",
}

goals = [
    Objective("knowledge", numeric_pointer("/project/knowledge"), "maximize"),
    Objective("cost", numeric_pointer("/resources/cost"), "minimize"),
]

assert improvement(before, after, goals) == {
    "knowledge": 3.0,
    "cost": -2.0,
}
~~~

## Operations and uncertainty

An operation maps a state to possible post-states.

~~~python
from asterisk import Operation, Outcome

trade = Operation(
    "uncertain trade",
    lambda state: (
        Outcome({"wealth": 16}, probability=0.7),
        Outcome({"wealth": 4}, probability=0.3),
    ),
)
~~~

If probabilities are absent, Asterisk keeps them unknown and exposes the
scenarios instead of silently assuming equiprobability.

## Choice without premature scalarization

The initial kernel supports vector-valued improvements and Pareto frontiers.
A single weighted utility function is therefore optional rather than built into
the ontology.

## Status

The modern kernel is intentionally tiny and experimental. It currently
contains:

- JSON-compatible world states;
- scalar observables/objectives;
- raw deltas and preference-oriented improvements;
- operations with multiple possible outcomes;
- expected improvement when probabilities are explicit;
- Pareto-frontier selection;
- RFC-6901-style numeric JSON Pointer observables.

See docs/2026-11-27_modernization.md for the design rationale and near frontier.

The historical 2016 design notes remain under docs/.
