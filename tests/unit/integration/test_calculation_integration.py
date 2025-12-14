"""Integration tests for the calculation engine with real config files."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.domain.calculation import CalculationEngine
from src.domain.data_format import DataValidator, parse_data_format
from src.infrastructure.config.loader import (
    ConfigLoader,
    ConfigurationError,
    TeamConfigManager,
)


class TestCalculationEngineIntegration:
    """計算エンジンの統合テスト."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """テスト用の一時設定ディレクトリを作成."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        teams_dir = config_dir / "teams"
        teams_dir.mkdir()

        # テスト用のチーム設定ファイルを作成
        team_config = {
            "team": {
                "id": "test_team",
                "name": "テストチーム",
                "description": "統合テスト用チーム",
            },
            "data_format": {
                "columns": [
                    {"name": "quantity", "type": "int", "required": True},
                    {"name": "unit_price", "type": "float", "required": True},
                    {"name": "discount_rate", "type": "float", "required": False, "default": 0.0},
                ],
            },
            "calculation_rules": [
                {
                    "name": "gross_revenue",
                    "formula": "quantity * unit_price",
                    "description": "粗売上",
                },
                {
                    "name": "discount_amount",
                    "formula": "gross_revenue * discount_rate",
                    "description": "割引金額",
                },
                {
                    "name": "net_revenue",
                    "formula": "gross_revenue - discount_amount",
                    "description": "純売上",
                },
                {
                    "name": "total_revenue",
                    "formula": "SUM(net_revenue)",
                    "description": "売上合計",
                },
            ],
        }

        with (teams_dir / "test_team.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(team_config, f)

        return config_dir

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """サンプルデータを作成."""
        return pd.DataFrame({
            "quantity": [10, 20, 15, 5],
            "unit_price": [100.0, 150.0, 200.0, 80.0],
            "discount_rate": [0.1, 0.05, 0.0, 0.2],
        })

    def test_full_calculation_workflow(
        self, temp_config_dir: Path, sample_data: pd.DataFrame,
    ) -> None:
        """設定ファイルから計算ルールを読み込んで実際に計算を実行する統合テスト."""
        # 設定マネージャーを初期化
        config_loader = ConfigLoader(temp_config_dir)
        team_config_manager = TeamConfigManager(config_loader)

        # 計算ルールを読み込み
        calculation_rules = team_config_manager.load_team_calculation_rules("test_team")

        expected_rules_count = 4
        if len(calculation_rules) != expected_rules_count:
            msg = f"Expected {expected_rules_count} calculation rules, got {len(calculation_rules)}"
            raise AssertionError(msg)

        # 計算エンジンを初期化
        engine = CalculationEngine()

        # 基本計算ルール(集約以外)を適用
        basic_rules = [
            rule for rule in calculation_rules
            if not engine.is_aggregation_formula(rule.formula)
        ]
        result_df = engine.apply_multiple_rules(sample_data, basic_rules)

        # 結果の検証
        expected_rows = 4
        if len(result_df) != expected_rows:
            msg = f"Expected {expected_rows} rows, got {len(result_df)}"
            raise AssertionError(msg)

        # 元の列が保持されているか確認
        original_columns = ["quantity", "unit_price", "discount_rate"]
        if not all(col in result_df.columns for col in original_columns):
            msg = f"Original columns should be preserved: {original_columns}"
            raise AssertionError(msg)

        # 新しい計算列が追加されているか確認
        new_columns = ["gross_revenue", "discount_amount", "net_revenue"]
        if not all(col in result_df.columns for col in new_columns):
            msg = f"New calculated columns should be added: {new_columns}"
            raise AssertionError(msg)

        # 具体的な計算結果の検証
        expected_gross = [1000.0, 3000.0, 3000.0, 400.0]  # quantity * unit_price
        expected_discount = [100.0, 150.0, 0.0, 80.0]     # gross_revenue * discount_rate
        expected_net = [900.0, 2850.0, 3000.0, 320.0]     # gross_revenue - discount_amount

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

    def test_data_format_validation_integration(self, temp_config_dir: Path) -> None:
        """データフォーマット設定と検証の統合テスト."""
        # 設定マネージャーを初期化
        config_loader = ConfigLoader(temp_config_dir)
        team_config_manager = TeamConfigManager(config_loader)

        # データフォーマット設定を読み込み
        data_format_config = team_config_manager.load_team_data_format("test_team")

        if "columns" not in data_format_config:
            msg = "Expected 'columns' in data format config"
            raise AssertionError(msg)

        # データフォーマットオブジェクトを作成
        data_format = parse_data_format(data_format_config)
        validator = DataValidator(data_format)

        # 正常なデータの検証
        valid_df = pd.DataFrame({
            "quantity": [10, 20],
            "unit_price": [100.0, 150.0],
            "discount_rate": [0.1, 0.0],
        })

        errors = validator.validate_dataframe(valid_df)
        if len(errors) > 0:
            msg = f"Expected no errors for valid data, got: {errors}"
            raise AssertionError(msg)

        # 型変換テスト
        string_data_df = pd.DataFrame({
            "quantity": ["10", "20"],
            "unit_price": ["100.0", "150.0"],
            "discount_rate": ["0.1", "0.0"],
        })

        converted_df = validator.convert_dataframe(string_data_df)

        if not pd.api.types.is_integer_dtype(converted_df["quantity"]):
            msg = f"Expected quantity to be integer type, got {converted_df['quantity'].dtype}"
            raise AssertionError(msg)

        if not pd.api.types.is_float_dtype(converted_df["unit_price"]):
            msg = f"Expected unit_price to be float type, got {converted_df['unit_price'].dtype}"
            raise AssertionError(msg)

    def test_config_error_handling(self, tmp_path: Path) -> None:
        """設定エラーのハンドリング統合テスト."""
        # 空の設定ディレクトリ
        empty_config_dir = tmp_path / "empty_config"
        empty_config_dir.mkdir()

        config_loader = ConfigLoader(empty_config_dir)
        team_config_manager = TeamConfigManager(config_loader)

        # チーム一覧の取得でエラーが発生することを確認
        with pytest.raises(ConfigurationError):
            team_config_manager.load_all_teams()

        # 存在しないチームの読み込みでエラーが発生することを確認
        teams_dir = empty_config_dir / "teams"
        teams_dir.mkdir()

        with pytest.raises(ConfigurationError):
            team_config_manager.load_team("nonexistent_team")

    def test_complex_calculation_formula(self, temp_config_dir: Path) -> None:
        """複雑な計算式の統合テスト."""
        # 複雑な計算式を含む設定ファイルを作成
        teams_dir = temp_config_dir / "teams"
        complex_config = {
            "team": {
                "id": "complex_team",
                "name": "複雑計算チーム",
            },
            "calculation_rules": [
                {
                    "name": "base_value",
                    "formula": "quantity * unit_price",
                    "description": "基本値",
                },
                {
                    "name": "tax_amount",
                    "formula": "base_value * tax_rate",
                    "description": "税額",
                },
                {
                    "name": "total_with_tax",
                    "formula": "base_value + tax_amount",
                    "description": "税込み合計",
                },
                {
                    "name": "final_amount",
                    "formula": "total_with_tax - discount_amount",
                    "description": "最終金額",
                },
            ],
        }

        with (teams_dir / "complex_team.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(complex_config, f)

        # 設定を読み込んで計算実行
        config_loader = ConfigLoader(temp_config_dir)
        team_config_manager = TeamConfigManager(config_loader)
        calculation_rules = team_config_manager.load_team_calculation_rules("complex_team")

        engine = CalculationEngine()

        sample_df = pd.DataFrame({
            "quantity": [10, 5],
            "unit_price": [100.0, 200.0],
            "tax_rate": [0.1, 0.08],
            "discount_amount": [50.0, 30.0],
        })

        result_df = engine.apply_multiple_rules(sample_df, calculation_rules)

        # 計算結果の検証
        expected_base = [1000.0, 1000.0]        # quantity * unit_price
        expected_tax = [100.0, 80.0]            # base_value * tax_rate
        expected_total_tax = [1100.0, 1080.0]   # base_value + tax_amount
        expected_final = [1050.0, 1050.0]       # total_with_tax - discount_amount

        pd.testing.assert_series_equal(
            result_df["base_value"],
            pd.Series(expected_base, name="base_value"),
            check_names=False,
        )

        pd.testing.assert_series_equal(
            result_df["final_amount"],
            pd.Series(expected_final, name="final_amount"),
            check_names=False,
        )

        pd.testing.assert_series_equal(
            result_df["tax_amount"],
            pd.Series(expected_tax, name="tax_amount"),
            check_names=False,
        )

        pd.testing.assert_series_equal(
            result_df["total_with_tax"],
            pd.Series(expected_total_tax, name="total_with_tax"),
            check_names=False,
        )
