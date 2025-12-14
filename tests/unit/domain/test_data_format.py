"""Unit tests for the data format domain models."""

import pandas as pd
import pytest

from src.domain.data_format import (
    ColumnDefinition,
    DataFormat,
    DataValidator,
    parse_data_format,
)


class TestColumnDefinition:
    """ColumnDefinitionエンティティのユニットテスト."""

    def test_create_column_definition_successfully(self) -> None:
        """Test that ColumnDefinition can be created successfully."""
        col_def = ColumnDefinition(
            name="test_column",
            type="string",
            required=True,
            format=None,
            default="default_value",
            description="Test column",
        )

        if col_def.name != "test_column":
            msg = f"Expected name to be 'test_column', got {col_def.name}"
            raise AssertionError(msg)
        if col_def.type != "string":
            msg = f"Expected type to be 'string', got {col_def.type}"
            raise AssertionError(msg)
        if col_def.required is not True:
            msg = f"Expected required to be True, got {col_def.required}"
            raise AssertionError(msg)

    def test_required_defaults_to_true(self) -> None:
        """Test that required defaults to True."""
        col_def = ColumnDefinition(name="test", type="int")

        if col_def.required is not True:
            msg = f"Expected required to default to True, got {col_def.required}"
            raise AssertionError(msg)

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="列名は必須です"):
            ColumnDefinition(name="", type="string")

    def test_invalid_type_raises_error(self) -> None:
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError, match="サポートされていない型です"):
            ColumnDefinition(name="test", type="invalid_type")

    def test_valid_types_accepted(self) -> None:
        """Test that all valid types are accepted."""
        valid_types = ["string", "int", "float", "datetime", "bool"]

        for valid_type in valid_types:
            col_def = ColumnDefinition(name="test", type=valid_type)
            if col_def.type != valid_type:
                msg = f"Expected type {valid_type} to be valid"
                raise AssertionError(msg)


class TestDataFormat:
    """DataFormatエンティティのユニットテスト."""

    def test_create_data_format_successfully(self) -> None:
        """Test that DataFormat can be created successfully."""
        columns = [
            ColumnDefinition(name="col1", type="string"),
            ColumnDefinition(name="col2", type="int", required=False),
        ]
        data_format = DataFormat(columns=columns)

        if len(data_format.columns) != 2:  # noqa: PLR2004
            msg = f"Expected 2 columns, got {len(data_format.columns)}"
            raise AssertionError(msg)

    def test_empty_columns_raises_error(self) -> None:
        """Test that empty columns list raises ValueError."""
        with pytest.raises(ValueError, match="少なくとも1つの列定義が必要です"):
            DataFormat(columns=[])

    def test_duplicate_column_names_raise_error(self) -> None:
        """Test that duplicate column names raise ValueError."""
        columns = [
            ColumnDefinition(name="duplicate", type="string"),
            ColumnDefinition(name="duplicate", type="int"),
        ]

        with pytest.raises(ValueError, match="列名が重複しています"):
            DataFormat(columns=columns)

    def test_get_column_by_name(self) -> None:
        """Test getting column by name."""
        col1 = ColumnDefinition(name="test_col", type="string")
        col2 = ColumnDefinition(name="other_col", type="int")
        data_format = DataFormat(columns=[col1, col2])

        found_col = data_format.get_column_by_name("test_col")
        if found_col != col1:
            msg = f"Expected to find col1, got {found_col}"
            raise AssertionError(msg)

        not_found = data_format.get_column_by_name("nonexistent")
        if not_found is not None:
            msg = f"Expected None for nonexistent column, got {not_found}"
            raise AssertionError(msg)

    def test_get_required_columns(self) -> None:
        """Test getting required columns."""
        columns = [
            ColumnDefinition(name="required1", type="string", required=True),
            ColumnDefinition(name="optional1", type="int", required=False),
            ColumnDefinition(name="required2", type="float", required=True),
        ]
        data_format = DataFormat(columns=columns)

        required_cols = data_format.get_required_columns()
        required_names = [col.name for col in required_cols]

        expected_required_count = 2
        if len(required_cols) != expected_required_count:
            msg = f"Expected {expected_required_count} required columns, got {len(required_cols)}"
            raise AssertionError(msg)
        if "required1" not in required_names or "required2" not in required_names:
            msg = f"Expected 'required1' and 'required2' in required columns, got {required_names}"
            raise AssertionError(msg)


class TestDataValidator:
    """DataValidatorのユニットテスト."""

    @pytest.fixture
    def sample_data_format(self) -> DataFormat:
        """サンプルDataFormatを作成."""
        return DataFormat(columns=[
            ColumnDefinition(name="name", type="string", required=True),
            ColumnDefinition(name="age", type="int", required=True),
            ColumnDefinition(name="salary", type="float", required=False, default=0.0),
            ColumnDefinition(name="active", type="bool", required=False, default=True),
        ])

    @pytest.fixture
    def validator(self, sample_data_format: DataFormat) -> DataValidator:
        """DataValidatorインスタンスを作成."""
        return DataValidator(sample_data_format)

    def test_validate_valid_dataframe(self, validator: DataValidator) -> None:
        """正常なDataFrameのバリデーションテスト."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "salary": [50000.0, 60000.0, 70000.0],
            "active": [True, False, True],
        })

        errors = validator.validate_dataframe(df)

        if len(errors) != 0:
            msg = f"Expected no errors for valid DataFrame, got: {errors}"
            raise AssertionError(msg)

    def test_validate_missing_required_columns(self, validator: DataValidator) -> None:
        """必須列が不足している場合のバリデーションテスト."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            # age列が不足
            "salary": [50000.0, 60000.0],
        })

        errors = validator.validate_dataframe(df)

        if len(errors) == 0:
            msg = "Expected errors for missing required column"
            raise AssertionError(msg)

        error_text = " ".join(errors)
        if "必須列が不足しています" not in error_text:
            msg = f"Expected missing column error, got: {errors}"
            raise AssertionError(msg)

    def test_validate_null_values_in_required_columns(
        self, validator: DataValidator,
    ) -> None:
        """必須列に空値がある場合のバリデーションテスト."""
        df = pd.DataFrame({
            "name": ["Alice", None, "Charlie"],
            "age": [25, 30, None],
            "salary": [50000.0, 60000.0, 70000.0],
        })

        errors = validator.validate_dataframe(df)

        if len(errors) == 0:
            msg = "Expected errors for null values in required columns"
            raise AssertionError(msg)

        error_text = " ".join(errors)
        if "空値があります" not in error_text:
            msg = f"Expected null value error, got: {errors}"
            raise AssertionError(msg)

    def test_convert_dataframe_types(self, validator: DataValidator) -> None:
        """DataFrameの型変換テスト."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": ["25", "30", "35"],  # 文字列として入力
            "salary": ["50000.0", "60000.0", None],  # 文字列とNull
            "active": ["true", "false", "1"],  # 文字列のboolean
        })

        converted_df = validator.convert_dataframe(df)

        # 型の確認
        if converted_df["name"].dtype != "object":
            msg = f"Expected name column to be string type, got {converted_df['name'].dtype}"
            raise AssertionError(msg)

        if not pd.api.types.is_integer_dtype(converted_df["age"]):
            msg = f"Expected age column to be integer type, got {converted_df['age'].dtype}"
            raise AssertionError(msg)

        if not pd.api.types.is_float_dtype(converted_df["salary"]):
            msg = f"Expected salary column to be float type, got {converted_df['salary'].dtype}"
            raise AssertionError(msg)

        # 値の確認
        expected_ages = [25, 30, 35]
        if not all(converted_df["age"].to_numpy() == expected_ages):
            msg = f"Expected ages {expected_ages}, got {converted_df['age'].to_numpy()}"
            raise AssertionError(msg)

        # デフォルト値の確認
        if converted_df["salary"].iloc[2] != 0.0:
            msg = f"Expected default salary 0.0, got {converted_df['salary'].iloc[2]}"
            raise AssertionError(msg)


class TestParseDataFormat:
    """parse_data_format関数のユニットテスト."""

    def test_parse_valid_data_format(self) -> None:
        """正常な設定データからDataFormatをパースできることをテスト."""
        format_data = {
            "columns": [
                {
                    "name": "test_col",
                    "type": "string",
                    "required": True,
                    "description": "Test column",
                },
                {
                    "name": "num_col",
                    "type": "int",
                    "required": False,
                    "default": 0,
                },
            ],
        }

        data_format = parse_data_format(format_data)

        expected_columns = 2
        if len(data_format.columns) != expected_columns:
            msg = f"Expected {expected_columns} columns, got {len(data_format.columns)}"
            raise AssertionError(msg)

        first_col = data_format.columns[0]
        if first_col.name != "test_col":
            msg = f"Expected first column name 'test_col', got {first_col.name}"
            raise AssertionError(msg)
        if first_col.type != "string":
            msg = f"Expected first column type 'string', got {first_col.type}"
            raise AssertionError(msg)

    def test_parse_missing_columns_section(self) -> None:
        """Columns セクションが不足している場合にエラーが発生することをテスト."""
        format_data = {
            "other_section": {},
            # columns が不足
        }

        with pytest.raises(ValueError, match="'columns' セクションが必要です"):
            parse_data_format(format_data)

    def test_parse_column_missing_required_field(self) -> None:
        """列定義に必須フィールドが不足している場合にエラーが発生することをテスト."""
        format_data = {
            "columns": [
                {
                    "name": "test_col",
                    # type が不足
                    "required": True,
                },
            ],
        }

        with pytest.raises(ValueError, match="列定義に必須フィールドが不足しています"):
            parse_data_format(format_data)
