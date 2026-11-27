# Asterisk modernization: semantic differences over possible states

Asterisk started from a simple question: how can we reason quantitatively about
actions, plans, assets, risks, and goals outside the narrow domains where such
tools are normally used?

The first modernization step keeps that question and discards an unnecessary
requirement: Asterisk does **not** need to know how to subtract every possible
pair of JSON documents.

## State

For the core, a possible world state is any JSON-compatible value:

\[
s \in S.
\]

JSON is deliberately only the carrier. Asterisk does not assume that every
field is commensurable, meaningful to every decision, or even worth comparing.

## Goal-relevant observation

A decision supplies observables/objectives

\[
G = (g_1, \ldots, g_k), \qquad g_i : S \rightarrow \mathbb{R}.
\]

The semantic difference between two states relative to those observables is

\[
\Delta_G(s_0, s_1) = G(s_1) - G(s_0).
\]

This means two structurally different JSON states can be decision-equivalent:

\[
s_a \sim_G s_b \iff G(s_a)=G(s_b).
\]

That equivalence is useful. It lets Asterisk ignore irrelevant state details
without pretending that a universal structural JSON diff is a universal
semantic diff.

Objectives additionally declare a preference direction (maximize/minimize).
A raw delta remains descriptive; an *improvement* vector orients every
component so that positive means better.

## Operation

An operation is initially modeled as a transition from a state to one or more
possible post-states:

\[
T : S \rightarrow \mathcal{P}(S).
\]

When probabilities are explicitly known, this can be treated as a finite
distribution and expected improvement can be computed. When probabilities are
unknown, Asterisk preserves that fact and returns scenario-wise improvements
instead of silently assuming equiprobability.

This distinction is intentional.

## Multi-objective choice

The first kernel does not collapse every objective into one scalar utility.
Improvement vectors can be compared by Pareto dominance. Scalarization,
constraints, risk measures, lexicographic preferences, satisficing, and other
choice rules can be layered on later.

## Relation to the 2016 design

The old distinction between *reality* and *desirity* already contained the
essential idea: compare the actual world with a desired one and reason about
the increment.

The modernization changes where the subtraction lives. Rather than requiring
arbitrary world objects themselves to support subtraction, goal-relevant
observables provide the coordinate system in which subtraction is meaningful.

## Deliberate non-goals of the first kernel

- no universal structural JSON diff;
- no mandatory ontology or Wikidata dependency;
- no assumption that unknown outcomes are equiprobable;
- no single universal utility function;
- no autonomous action execution.

These can be added as explicit layers rather than hidden assumptions.

## Near frontier

The next useful layers are likely:

1. constraints and desired regions, not merely maximize/minimize objectives;
2. richer uncertainty (intervals, samples, distributions, ambiguity sets);
3. operation composition into plans;
4. risk measures and tail/downside summaries;
5. reversible/irreversible action metadata and option value;
6. adapters from JSON Schema, Wikidata, MCP/tool descriptions, and historical
   Asterisk/StepIO/PlanDF representations;
7. optional structural/provenance-aware JSON differencing for explanation.

The core should remain small enough that each of these semantics stays visible.
