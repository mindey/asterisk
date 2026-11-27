import unittest

from asterisk import (
    Objective,
    Operation,
    Outcome,
    delta,
    expected_improvement,
    improvement,
    numeric_pointer,
    pareto_frontier,
    scenario_improvements,
)


class TestGoalRelativeDifference(unittest.TestCase):
    def setUp(self):
        self.objectives = (
            Objective("knowledge", numeric_pointer("/project/knowledge"), "maximize"),
            Objective("cost", numeric_pointer("/resources/cost"), "minimize"),
        )

    def test_irrelevant_json_differences_do_not_change_semantic_delta(self):
        before = {
            "project": {"knowledge": 2},
            "resources": {"cost": 10},
            "notes": {"private": "old"},
        }
        after_a = {
            "project": {"knowledge": 5},
            "resources": {"cost": 12},
            "notes": {"private": "new"},
        }
        after_b = {
            "project": {"knowledge": 5},
            "resources": {"cost": 12},
            "notes": {
                "private": "completely different",
                "nested": [1, 2, {"anything": True}],
            },
        }

        self.assertEqual(
            delta(before, after_a, self.objectives),
            {"knowledge": 3.0, "cost": 2.0},
        )
        self.assertEqual(
            improvement(before, after_a, self.objectives),
            {"knowledge": 3.0, "cost": -2.0},
        )
        self.assertEqual(
            improvement(before, after_a, self.objectives),
            improvement(before, after_b, self.objectives),
        )


class TestOperations(unittest.TestCase):
    def test_scenarios_work_without_probabilities(self):
        state = {"wealth": 10}
        objective = Objective("wealth", numeric_pointer("/wealth"))

        operation = Operation(
            "uncertain trade",
            lambda _: (
                Outcome({"wealth": 16}),
                Outcome({"wealth": 4}),
            ),
        )

        self.assertEqual(
            scenario_improvements(operation, state, [objective]),
            ({"wealth": 6.0}, {"wealth": -6.0}),
        )

        with self.assertRaises(ValueError):
            expected_improvement(operation, state, [objective])

    def test_expected_improvement_requires_explicit_distribution(self):
        state = {"wealth": 10}
        objective = Objective("wealth", numeric_pointer("/wealth"))

        operation = Operation(
            "uncertain trade",
            lambda _: (
                Outcome({"wealth": 16}, probability=0.7),
                Outcome({"wealth": 4}, probability=0.3),
            ),
        )

        result = expected_improvement(operation, state, [objective])
        self.assertAlmostEqual(result["wealth"], 2.4)


class TestParetoFrontier(unittest.TestCase):
    def test_returns_only_non_dominated_alternatives(self):
        alternatives = {
            "safe": {"value": 2.0, "reversibility": 5.0},
            "fast": {"value": 5.0, "reversibility": 1.0},
            "worse-safe": {"value": 1.0, "reversibility": 4.0},
        }

        self.assertEqual(pareto_frontier(alternatives), ["safe", "fast"])


class TestJsonPointer(unittest.TestCase):
    def test_arrays_and_escaping(self):
        state = {"a/b": [{"~x": 3}]}
        measure = numeric_pointer("/a~1b/0/~0x")
        self.assertEqual(measure(state), 3.0)


if __name__ == "__main__":
    unittest.main()
