import contextlib
import copy
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import main


class SimulatorTests(unittest.TestCase):
    def setUp(self):
        self.cross = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
        self.x_shape = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]

    def run_console(self, entered):
        result = subprocess.run(
            [sys.executable, "-B", str(Path(main.__file__).resolve())],
            input=entered, text=True, capture_output=True, encoding="utf-8",
            env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_mac_reference_scores(self):
        self.assertEqual(main.calculate_mac(self.cross, self.cross), 5)
        self.assertEqual(main.calculate_mac(self.cross, self.x_shape), 1)

    def test_epsilon_ties_and_boundary(self):
        for a, b in [(1, 1), (0.9, 0.8999999999999999), (0, main.EPSILON / 2)]:
            self.assertEqual(main.compare_scores(a, b), "UNDECIDED")
        self.assertEqual(main.compare_scores(0, main.EPSILON), "B")
        self.assertEqual(main.compare_scores(5, 1), "A")

    def test_label_aliases(self):
        for label in ["+", "cross", " Cross "]:
            self.assertEqual(main.normalize_label(label), "Cross")
        for label in ["x", " X "]:
            self.assertEqual(main.normalize_label(label), "X")
        with self.assertRaises(ValueError):
            main.normalize_label("circle")

    def test_generator_reference_patterns(self):
        patterns = main.generate_patterns(3)
        self.assertEqual(patterns["Cross"], self.cross)
        self.assertEqual(patterns["X"], self.x_shape)

    def test_generator_required_sizes(self):
        for size in [3, 5, 13, 25]:
            patterns = main.generate_patterns(size)
            for matrix in patterns.values():
                main.validate_matrix(matrix, size)
                self.assertEqual(main.calculate_mac(matrix, matrix), 2 * size - 1)
            self.assertEqual(main.calculate_mac(patterns["Cross"], patterns["X"]), 1)

    def test_generator_edge_sizes_and_independent_rows(self):
        self.assertEqual(main.generate_patterns(1), {"Cross": [[1]], "X": [[1]]})
        patterns = main.generate_patterns(4)
        self.assertEqual(patterns["Cross"][2], [1, 1, 1, 1])
        self.assertEqual(patterns["X"][0], [1, 0, 0, 1])
        patterns["Cross"][0][0] = 9
        self.assertEqual(patterns["Cross"][1][0], 0)
        self.assertEqual(patterns["X"][0][0], 1)

    def test_generator_rejects_invalid_size(self):
        for size in [0, -1, 2.5, "3", True]:
            with self.subTest(size=size), self.assertRaises(ValueError):
                main.generate_patterns(size)

    def test_manual_numeric_retry(self):
        with patch("builtins.input", side_effect=["1 2", "a b c", "0 1 0", "1 1 1", "0 1 0"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main.read_matrix("test"), self.cross)

    def test_timing_repeats_ten_times(self):
        with patch("main.calculate_mac", return_value=5) as calculate:
            self.assertGreaterEqual(main.measure_mac_time(self.cross, self.cross), 0)
        self.assertEqual(calculate.call_count, 10)

    def test_original_json_results(self):
        with contextlib.redirect_stdout(io.StringIO()):
            results = main.analyze_all_patterns(main.load_data())
        self.assertEqual(len(results), 6)
        self.assertEqual(sum(result["passed"] for result in results), 3)
        self.assertEqual(
            [result["case_id"] for result in results if not result["passed"]],
            ["size_5_1", "size_13_2", "size_25_1"],
        )
        self.assertTrue(all(result["predicted"] == "UNDECIDED" for result in results if not result["passed"]))

    def test_invalid_case_does_not_stop_next_case(self):
        dataset = copy.deepcopy(main.load_data())
        dataset["patterns"] = {
            "size_5_1": {"input": [[1]], "expected": "x"},
            "size_5_2": dataset["patterns"]["size_5_2"],
        }
        with contextlib.redirect_stdout(io.StringIO()):
            results = main.analyze_all_patterns(dataset)
        self.assertFalse(results[0]["passed"])
        self.assertTrue(results[1]["passed"])

    def test_normalized_duplicate_filter_is_rejected(self):
        dataset = copy.deepcopy(main.load_data())
        dataset["filters"]["size_5"]["+"] = dataset["filters"]["size_5"]["cross"]
        with self.assertRaises(ValueError):
            main.get_filters(dataset, 5)

    def test_manual_console_with_generated_patterns(self):
        output = self.run_console("1\nCross\nX\nX\n")
        self.assertIn("A 점수: 1.0", output)
        self.assertIn("B 점수: 5.0", output)
        self.assertIn("판정: B", output)

    def test_manual_console_tie(self):
        output = self.run_console("1\nCross\nX\n0 0 0\n0 0 0\n0 0 0\n")
        self.assertIn("판정: UNDECIDED", output)

    def test_json_console(self):
        output = self.run_console("2\n")
        self.assertEqual(output.count("\nPASS\n"), 3)
        self.assertEqual(output.count("\nFAIL -"), 3)
        self.assertIn("총 테스트: 6", output)
        for size in [3, 5, 13, 25]:
            self.assertIn(f"{size}×{size} |", output)

    def test_generator_console_and_size_retry(self):
        output = self.run_console("3\nabc\n0\n5\n")
        self.assertEqual(output.count("입력 오류:"), 2)
        self.assertIn("[5×5 Cross]", output)
        self.assertIn("[5×5 X]", output)
        self.assertIn("판정: Cross", output)
        self.assertIn("판정: X", output)
        self.assertIn("5×5 |", output)


if __name__ == "__main__":
    unittest.main()
