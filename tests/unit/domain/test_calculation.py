"""Unit tests for the calculation domain models."""

import numpy as np
import pandas as pd
import pytest

from src.domain.calculation import (
    CalculationEngine,
    CalculationRule,
    parse_calculation_rules,
)


class TestCalculationRule:
    """CalculationRuleエンティティのユニットテスト."""

    def test_create_calculation_rule_successfully(self) -> None:
        """Test that CalculationRule can be created successfully."""
        rule = CalculationRule(
            name="test_rule",
            formula="a + b",
            description="Test calculation",
            group_by=["category"],
        )

        if rule.name != "test_rule":
            msg = f"Expected rule.name to be 'test_rule', got {rule.name}"
            raise AssertionError(msg)
        if rule.formula != "a + b":
            msg = f"Expected rule.formula to be 'a + b', got {rule.formula}"
            raise AssertionError(msg)
        if rule.description != "Test calculation":
            msg = f"Expected rule.description to be 'Test calculation', got {rule.description}"
            raise AssertionError(msg)
        if rule.group_by != ["category"]:
            msg = f"Expected rule.group_by to be ['category'], got {rule.group_by}"
            raise AssertionError(msg)

    def test_group_by_defaults_to_empty_list(self) -> None:
        """Test that group_by defaults to empty list."""
        rule = CalculationRule(name="test", formula="a + b")

        if rule.group_by != []:
            msg = f"Expected rule.group_by to be [], got {rule.group_by}"
            raise AssertionError(msg)

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="計算ルール名は必須です"):
            CalculationRule(name="", formula="a + b")

    def test_empty_formula_raises_error(self) -> None:
        """Test that empty formula raises ValueError."""
        with pytest.raises(ValueError, match="計算式は必須です"):
            CalculationRule(name="test", formula="")


class TestCalculationEngine:
    """CalculationEngineのユニットテスト."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """サンプルDataFrameを作成."""
        return pd.DataFrame({
            "quantity": [10, 20, 15],
            "unit_price": [100.0, 150.0, 200.0],
            "discount_rate": [0.1, 0.05, 0.0],
        })

    @pytest.fixture
    def engine(self) -> CalculationEngine:
        """CalculationEngineインスタンスを作成."""
        return CalculationEngine()

    def test_basic_arithmetic_operations(
        self, engine: CalculationEngine, sample_dataframe: pd.DataFrame,
    ) -> None:
        """基本的な四則演算のテスト."""
        rule = CalculationRule(name="gross_revenue", formula="quantity * unit_price")

        result = engine.apply_formula(sample_dataframe, rule)
        expected = pd.Series([1000.0, 3000.0, 3000.0], name="gross_revenue")

        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_formula_with_computed_columns(
        self, engine: CalculationEngine, sample_dataframe: pd.DataFrame,
    ) -> None:
        """計算済み列を参照する式のテスト."""
        # まず最初の計算を実行
        rule1 = CalculationRule(name="gross_revenue", formula="quantity * unit_price")
        computed_columns = {}

        result1 = engine.apply_arithmetic_formula(
            sample_dataframe,
            rule1.formula,
            computed_columns,
        )
        computed_columns["gross_revenue"] = result1

        # 計算済み列を参照する次の計算
        rule2 = CalculationRule(name="discount_amount", formula="gross_revenue * discount_rate")
        result2 = engine.apply_arithmetic_formula(
            sample_dataframe,
            rule2.formula,
            computed_columns,
        )

        expected = pd.Series([100.0, 150.0, 0.0], name="discount_amount")
        pd.testing.assert_series_equal(result2, expected, check_names=False)

    def test_multiple_rules_application(
        self, engine: CalculationEngine, sample_dataframe: pd.DataFrame,
    ) -> None:
        """複数ルールの順次適用テスト."""
        rules = [
            CalculationRule(name="gross_revenue", formula="quantity * unit_price"),
            CalculationRule(name="discount_amount", formula="gross_revenue * discount_rate"),
            CalculationRule(name="net_revenue", formula="gross_revenue - discount_amount"),
        ]

        result_df = engine.apply_multiple_rules(sample_dataframe, rules)

        # 元の列が保持されていることを確認
        if not all(col in result_df.columns for col in sample_dataframe.columns):
            msg = "Original columns should be preserved"
            raise AssertionError(msg)

        # 新しい計算列が追加されていることを確認
        expected_new_columns = ["gross_revenue", "discount_amount", "net_revenue"]
        if not all(col in result_df.columns for col in expected_new_columns):
            msg = f"Expected new columns {expected_new_columns} to be added"
            raise AssertionError(msg)

        # 計算結果の検証
        expected_gross = [1000.0, 3000.0, 3000.0]
        expected_discount = [100.0, 150.0, 0.0]
        expected_net = [900.0, 2850.0, 3000.0]

        pd.testing.assert_series_equal(
            result_df["gross_revenue"],
            pd.Series(expected_gross, name="gross_revenue"),
            check_names=False,
        )
        pd.testing.assert_series_equal(
            result_df["discount_amount"],
            pd.Series(expected_discount, name="discount_amount"),
            check_names=False,
        )
        pd.testing.assert_series_equal(
            result_df["net_revenue"],
            pd.Series(expected_net, name="net_revenue"),
            check_names=False,
        )

    def test_aggregation_formula_detection(self, engine: CalculationEngine) -> None:
        """集約関数の検出テスト."""
        # 集約関数を含む式
        if not engine.is_aggregation_formula("SUM(revenue)"):
            msg = "Should detect SUM as aggregation function"
            raise AssertionError(msg)

        if not engine.is_aggregation_formula("MEAN(price)"):
            msg = "Should detect MEAN as aggregation function"
            raise AssertionError(msg)

        # 通常の四則演算
        if engine.is_aggregation_formula("quantity * unit_price"):
            msg = "Should not detect arithmetic as aggregation function"
            raise AssertionError(msg)

        # 集約関数名が含まれているが関数呼び出しではない
        if engine.is_aggregation_formula("SUM_column * rate"):
            msg = "Should not detect SUM_column as aggregation function"
            raise AssertionError(msg)

    def test_invalid_formula_raises_error(
        self, engine: CalculationEngine, sample_dataframe: pd.DataFrame,
    ) -> None:
        """不正な計算式でエラーが発生することをテスト."""
        rule = CalculationRule(name="invalid", formula="nonexistent_column * 2")

        with pytest.raises(ValueError, match="列または計算済み変数が存在しません"):
            engine.apply_formula(sample_dataframe, rule)


class TestParseCalculationRules:
    """parse_calculation_rules関数のユニットテスト."""

    def test_parse_valid_rules(self) -> None:
        """正常な設定データからルールをパースできることをテスト."""
        rules_data = [
            {
                "name": "gross_revenue",
                "formula": "quantity * unit_price",
                "description": "粗売上",
            },
            {
                "name": "net_revenue",
                "formula": "gross_revenue - discount",
                "description": "純売上",
                "group_by": ["month"],
            },
        ]

        rules = parse_calculation_rules(rules_data)

        expected_rule_count = 2
        if len(rules) != expected_rule_count:
            msg = f"Expected {expected_rule_count} rules, got {len(rules)}"
            raise AssertionError(msg)

        rule1, rule2 = rules

        if rule1.name != "gross_revenue":
            msg = f"Expected first rule name to be 'gross_revenue', got {rule1.name}"
            raise AssertionError(msg)
        if rule1.formula != "quantity * unit_price":
            msg = f"Expected first rule formula to be 'quantity * unit_price', got {rule1.formula}"
            raise AssertionError(msg)

        if rule2.group_by != ["month"]:
            msg = f"Expected second rule group_by to be ['month'], got {rule2.group_by}"
            raise AssertionError(msg)

    def test_parse_rules_missing_required_field(self) -> None:
        """必須フィールドが不足している場合にエラーが発生することをテスト."""
        rules_data = [
            {
                "name": "test_rule",
                # formula が不足
                "description": "Test",
            },
        ]

        with pytest.raises(ValueError, match="必須フィールドが不足しています"):
            parse_calculation_rules(rules_data)

    def test_parse_rules_empty_formula(self) -> None:
        """空の計算式でエラーが発生することをテスト."""
        rules_data = [
            {
                "name": "test_rule",
                "formula": "",  # 空の計算式
                "description": "Test",
            },
        ]

        with pytest.raises(ValueError, match="計算式は必須です"):
            parse_calculation_rules(rules_data)


class TestCalculationEngineValidation:
    """CalculationEngine validation tests."""

    @pytest.fixture
    def engine(self) -> CalculationEngine:
        """CalculationEngineインスタンスを作成."""
        return CalculationEngine()

    def test_validate_formula_arithmetic(self, engine: CalculationEngine) -> None:
        """四則演算の計算式検証テスト."""
        valid_formulas = [
            "a + b",
            "quantity * unit_price",
            "(a + b) * c",
            "-x + y",
            "a / b - c",
            "x ** 2",
            "a % b",
        ]

        for formula in valid_formulas:
            if not engine.validate_formula(formula):
                msg = f"Valid formula should pass validation: {formula}"
                raise AssertionError(msg)

    def test_validate_formula_aggregation(self, engine: CalculationEngine) -> None:
        """集約関数の計算式検証テスト."""
        valid_formulas = [
            "SUM(revenue)",
            "MEAN(price)",
            "COUNT(items)",
            "MIN(value)",
            "MAX(amount)",
            "STD(scores)",
            "VAR(measurements)",
        ]

        for formula in valid_formulas:
            if not engine.validate_formula(formula):
                msg = f"Valid aggregation formula should pass validation: {formula}"
                raise AssertionError(msg)

    def test_validate_formula_invalid_syntax(self, engine: CalculationEngine) -> None:
        """不正な構文の計算式検証テスト."""
        invalid_formulas = [
            "a +",
            "* b",
            "SUM(",
            "UNKNOWN_FUNC(x)",
            "import os",
            "exec('print')",
        ]

        for formula in invalid_formulas:
            if engine.validate_formula(formula):
                msg = f"Invalid formula should fail validation: {formula}"
                raise AssertionError(msg)

        if engine.validate_formula("a + + b"):
            # この式は技術的には有効（a + (+b)と解釈される）なので、バリデーションを通す
            pass
        else:
            msg = "Formula 'a + + b' should pass validation as valid syntax"
            raise AssertionError(msg)

    def test_validate_formula_aggregation_invalid(self, engine: CalculationEngine) -> None:
        """不正な集約関数の計算式検証テスト."""
        invalid_formulas = [
            "SUM()",
            "MEAN(a, b)",
            "COUNT(123)",
            "SUM a",
            "INVALID(column)",
        ]

        for formula in invalid_formulas:
            if engine.validate_formula(formula):
                msg = f"Invalid aggregation formula should fail validation: {formula}"
                raise AssertionError(msg)


class TestCalculationEngineAggregation:
    """CalculationEngine aggregation tests."""

    @pytest.fixture
    def sample_sales_data(self) -> pd.DataFrame:
        """売上データのサンプル."""
        return pd.DataFrame({
            "product": ["A", "B", "A", "C", "B"],
            "region": ["North", "North", "South", "South", "North"],
            "revenue": [100, 200, 150, 300, 250],
            "quantity": [10, 5, 15, 8, 12],
            "date": pd.to_datetime(["2024-01-15", "2024-01-20", "2024-02-10", "2024-02-15", "2024-03-05"]),
        })

    @pytest.fixture
    def engine(self) -> CalculationEngine:
        """CalculationEngineインスタンスを作成."""
        return CalculationEngine()

    def test_aggregation_sum_without_groupby(
        self, engine: CalculationEngine, sample_sales_data: pd.DataFrame,
    ) -> None:
        """グループ化なしのSUM集約テスト."""
        rule = CalculationRule(name="total_revenue", formula="SUM(revenue)")

        result = engine.apply_formula(sample_sales_data, rule)
        expected_value = 1000  # 100 + 200 + 150 + 300 + 250

        if len(result) != 1:
            msg = f"Expected single result, got {len(result)}"
            raise AssertionError(msg)
        if result.iloc[0] != expected_value:
            msg = f"Expected {expected_value}, got {result.iloc[0]}"
            raise AssertionError(msg)

    def test_aggregation_with_groupby(
        self, engine: CalculationEngine, sample_sales_data: pd.DataFrame,
    ) -> None:
        """グループ化ありのMEAN集約テスト."""
        rule = CalculationRule(
            name="avg_revenue_by_region",
            formula="MEAN(revenue)",
            group_by=["region"],
        )

        result = engine.apply_formula(sample_sales_data, rule)

        # North: (100 + 200 + 250) / 3 = 183.33, South: (150 + 300) / 2 = 225
        expected_len = 2
        if len(result) != expected_len:
            msg = f"Expected {expected_len} groups, got {len(result)}"
            raise AssertionError(msg)

        # 結果の値を検証（順序は保証されないので、値の存在だけ確認）
        expected_values = {183.33333333333334, 225.0}
        result_values = set(result.values)

        if result_values != expected_values:
            msg = f"Expected values {expected_values}, got {result_values}"
            raise AssertionError(msg)

    def test_aggregation_date_month_groupby(
        self, engine: CalculationEngine, sample_sales_data: pd.DataFrame,
    ) -> None:
        """日付の月次グループ化テスト."""
        rule = CalculationRule(
            name="monthly_revenue",
            formula="SUM(revenue)",
            group_by=["date::month"],
        )

        result = engine.apply_formula(sample_sales_data, rule)

        # 2024-01: 300, 2024-02: 450, 2024-03: 250
        expected_len = 3
        if len(result) != expected_len:
            msg = f"Expected {expected_len} months, got {len(result)}"
            raise AssertionError(msg)

        # 月次の売上総額を確認
        expected_values = {300.0, 450.0, 250.0}
        result_values = set(result.values)

        if result_values != expected_values:
            msg = f"Expected monthly values {expected_values}, got {result_values}"
            raise AssertionError(msg)

    def test_aggregation_count_function(
        self, engine: CalculationEngine, sample_sales_data: pd.DataFrame,
    ) -> None:
        """COUNT集約関数のテスト."""
        rule = CalculationRule(
            name="product_count",
            formula="COUNT(product)",
            group_by=["region"],
        )

        result = engine.apply_formula(sample_sales_data, rule)

        # North: 3件, South: 2件
        expected_values = {2, 3}
        result_values = set(result.values)

        if result_values != expected_values:
            msg = f"Expected count values {expected_values}, got {result_values}"
            raise AssertionError(msg)

    def test_aggregation_min_max_functions(
        self, engine: CalculationEngine, sample_sales_data: pd.DataFrame,
    ) -> None:
        """MIN/MAX集約関数のテスト."""
        min_rule = CalculationRule(name="min_revenue", formula="MIN(revenue)")
        max_rule = CalculationRule(name="max_revenue", formula="MAX(revenue)")

        min_result = engine.apply_formula(sample_sales_data, min_rule)
        max_result = engine.apply_formula(sample_sales_data, max_rule)

        if min_result.iloc[0] != 100:  # noqa: PLR2004
            msg = f"Expected min revenue 100, got {min_result.iloc[0]}"
            raise AssertionError(msg)
        if max_result.iloc[0] != 300:  # noqa: PLR2004
            msg = f"Expected max revenue 300, got {max_result.iloc[0]}"
            raise AssertionError(msg)

    def test_aggregation_invalid_column(
        self, engine: CalculationEngine, sample_sales_data: pd.DataFrame,
    ) -> None:
        """存在しない列での集約エラーテスト."""
        rule = CalculationRule(name="invalid", formula="SUM(nonexistent_column)")

        with pytest.raises(ValueError, match="列が存在しません"):
            engine.apply_formula(sample_sales_data, rule)

    def test_aggregation_invalid_formula_syntax(
        self, engine: CalculationEngine, sample_sales_data: pd.DataFrame,
    ) -> None:
        """不正な集約関数の構文エラーテスト."""
        rule = CalculationRule(name="invalid", formula="SUM()")

        with pytest.raises(ValueError, match="集約関数の構文が不正です"):
            engine.apply_formula(sample_sales_data, rule)


class TestCalculationEngineMultipleRulesWithAggregation:
    """Multiple rules with aggregation tests."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """テストデータ."""
        return pd.DataFrame({
            "quantity": [10, 20, 15],
            "unit_price": [100.0, 150.0, 200.0],
            "category": ["A", "B", "A"],
        })

    @pytest.fixture
    def engine(self) -> CalculationEngine:
        """CalculationEngineインスタンスを作成."""
        return CalculationEngine()

    def test_multiple_rules_with_arithmetic_and_aggregation(
        self, engine: CalculationEngine, sample_data: pd.DataFrame,
    ) -> None:
        """四則演算と集約が混在する複数ルールのテスト."""
        rules = [
            CalculationRule(name="total_value", formula="quantity * unit_price"),
            CalculationRule(name="avg_quantity", formula="MEAN(quantity)"),
            CalculationRule(name="total_by_category", formula="SUM(total_value)", group_by=["category"]),
        ]

        # 最初の2つのルールのみ適用可能（3番目は集約でDataFrameに追加できない）
        result_df = engine.apply_multiple_rules(sample_data, rules[:2])

        # 元の列が保持されていることを確認
        original_columns = ["quantity", "unit_price", "category"]
        if not all(col in result_df.columns for col in original_columns):
            msg = "Original columns should be preserved"
            raise AssertionError(msg)

        # 計算列が追加されていることを確認
        if "total_value" not in result_df.columns:
            msg = "total_value column should be added"
            raise AssertionError(msg)

        # total_valueの計算結果確認
        expected_total_value = [1000.0, 3000.0, 3000.0]
        pd.testing.assert_series_equal(
            result_df["total_value"],
            pd.Series(expected_total_value, name="total_value"),
            check_names=False,
        )


class TestCalculationEngineErrorCases:
    """CalculationEngine error handling tests."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """サンプルDataFrameを作成."""
        return pd.DataFrame({
            "quantity": [10, 20, 15],
            "unit_price": [100.0, 150.0, 200.0],
        })

    @pytest.fixture
    def engine(self) -> CalculationEngine:
        """CalculationEngineインスタンスを作成."""
        return CalculationEngine()

    def test_unsupported_ast_node_error(self, engine: CalculationEngine) -> None:
        """サポートされていないAST要素のエラーテスト."""
        # _validate_ast_node を直接テストすることは困難なので、
        # 不正な式での評価エラーをテスト
        sample_df = pd.DataFrame({"x": [1, 2, 3]})

        # 比較演算子（サポートされていない）
        rule = CalculationRule(name="invalid", formula="x > 5")

        with pytest.raises(ValueError, match="計算式の適用に失敗しました"):
            engine.apply_formula(sample_df, rule)

    def test_division_by_zero_handling(
        self, engine: CalculationEngine, sample_dataframe: pd.DataFrame,
    ) -> None:
        """ゼロ除算の処理テスト."""
        # ゼロ除算はPandasで処理されるため、inf になる
        zero_df = sample_dataframe.copy()
        zero_df["zero_col"] = 0

        rule = CalculationRule(name="division", formula="quantity / zero_col")
        result = engine.apply_formula(zero_df, rule)

        # 結果は inf になることを確認
        expected_inf_count = len(result)
        actual_inf_count = sum(val == np.inf for val in result)

        if actual_inf_count != expected_inf_count:
            msg = f"Expected {expected_inf_count} inf values, got {actual_inf_count}. Result: {result.tolist()}"
            raise AssertionError(msg)

    def test_ast_evaluation_error_propagation(
        self, engine: CalculationEngine, sample_dataframe: pd.DataFrame,
    ) -> None:
        """AST評価でのエラー伝播テスト."""
        rule = CalculationRule(name="error", formula="undefined_function(quantity)")

        with pytest.raises(ValueError, match="計算式の適用に失敗しました"):
            engine.apply_formula(sample_dataframe, rule)
