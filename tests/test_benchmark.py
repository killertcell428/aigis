"""Tests for the built-in adversarial benchmark suite."""

from aigis.benchmark import ATTACK_CORPUS, SAFE_CORPUS, BenchmarkSuite


class TestBenchmarkCorpus:
    def test_attack_corpus_has_categories(self) -> None:
        assert len(ATTACK_CORPUS) >= 5

    def test_each_category_has_attacks(self) -> None:
        for category, attacks in ATTACK_CORPUS.items():
            assert len(attacks) >= 3, f"Category {category!r} needs at least 3 attacks"

    def test_safe_corpus_non_empty(self) -> None:
        assert len(SAFE_CORPUS) >= 10


class TestBenchmarkSuite:
    def test_run_returns_result(self) -> None:
        suite = BenchmarkSuite()
        result = suite.run()
        assert result is not None
        assert len(result.category_results) > 0

    def test_precision_above_threshold(self) -> None:
        suite = BenchmarkSuite()
        result = suite.run()
        # Overall precision should be at least 70%
        assert result.overall_precision >= 70.0, (
            f"Overall precision {result.overall_precision:.1f}% is too low"
        )

    def test_false_positive_rate_acceptable(self) -> None:
        suite = BenchmarkSuite()
        result = suite.run()
        # False positive rate should be under 15%
        assert result.false_positive_rate <= 15.0, (
            f"False positive rate {result.false_positive_rate:.1f}% is too high: "
            f"{result.false_positive_examples}"
        )

    def test_single_category(self) -> None:
        suite = BenchmarkSuite(categories=["jailbreak"])
        result = suite.run()
        assert len(result.category_results) == 1
        assert result.category_results[0].category == "jailbreak"

    def test_jailbreak_100_percent(self) -> None:
        suite = BenchmarkSuite(categories=["jailbreak"])
        result = suite.run()
        assert result.category_results[0].precision == 100.0

    def test_prompt_injection_100_percent(self) -> None:
        suite = BenchmarkSuite(categories=["prompt_injection"])
        result = suite.run()
        assert result.category_results[0].precision == 100.0

    def test_summary_contains_headers(self) -> None:
        suite = BenchmarkSuite()
        result = suite.run()
        summary = result.summary()
        assert "Precision" in summary
        assert "TOTAL" in summary
        assert "False positive" in summary

    def test_to_dict_structure(self) -> None:
        suite = BenchmarkSuite(categories=["jailbreak"])
        result = suite.run()
        d = result.to_dict()
        assert "categories" in d
        assert "overall_precision" in d
        assert "false_positive_rate" in d
        assert d["categories"][0]["category"] == "jailbreak"

    def test_run_json_valid_json(self) -> None:
        import json

        suite = BenchmarkSuite(categories=["prompt_injection"])
        output = suite.run_json()
        data = json.loads(output)
        assert "overall_precision" in data
