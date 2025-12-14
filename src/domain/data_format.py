"""データフォーマット関連のドメインモデル."""
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class ColumnDefinition:
    """CSV列定義エンティティ."""

    name: str
    type: str
    required: bool = True
    format: str | None = None
    default: Any | None = None
    description: str = ""

    def __post_init__(self) -> None:
        """バリデーション."""
        if not self.name:
            msg = "列名は必須です"
            raise ValueError(msg)

        valid_types = ["string", "int", "float", "datetime", "bool"]
        if self.type not in valid_types:
            msg = f"サポートされていない型です: {self.type} (有効な型: {valid_types})"
            raise ValueError(msg)


@dataclass
class DataFormat:
    """データフォーマットエンティティ."""

    columns: list[ColumnDefinition]

    def __post_init__(self) -> None:
        """バリデーション."""
        if not self.columns:
            msg = "少なくとも1つの列定義が必要です"
            raise ValueError(msg)

        # 列名の重複チェック
        column_names = [col.name for col in self.columns]
        if len(column_names) != len(set(column_names)):
            msg = "列名が重複しています"
            raise ValueError(msg)

    def get_column_by_name(self, name: str) -> ColumnDefinition | None:
        """列名で列定義を取得."""
        for column in self.columns:
            if column.name == name:
                return column
        return None

    def get_required_columns(self) -> list[ColumnDefinition]:
        """必須列の一覧を取得."""
        return [col for col in self.columns if col.required]


class DataValidator:
    """データ検証クラス."""

    def __init__(self, data_format: DataFormat) -> None:
        """データバリデーターを初期化."""
        self.data_format = data_format

    def validate_dataframe(self, df: pd.DataFrame) -> list[str]:
        """DataFrameを検証してエラーメッセージのリストを返す."""
        errors = []

        # 列の存在チェック
        errors.extend(self._validate_columns_exist(df))

        # 必須列の空値チェック
        errors.extend(self._validate_required_columns(df))

        # データ型チェック i.e. 変換可能性チェック
        errors.extend(self._validate_data_types(df))

        return errors

    def convert_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrameの型を設定に従って変換."""
        df_converted = df.copy()

        for column_def in self.data_format.columns:
            if column_def.name in df_converted.columns:
                try:
                    df_converted[column_def.name] = self._convert_column(
                        df_converted[column_def.name],
                        column_def,
                    )
                except Exception as e:
                    msg = f"列 '{column_def.name}' の型変換に失敗しました: {e!s}"
                    raise ValueError(msg) from e

        return df_converted

    def _validate_columns_exist(self, df: pd.DataFrame) -> list[str]:
        """必須列の存在チェック."""
        errors = []
        required_columns = [col.name for col in self.data_format.get_required_columns()]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            errors.append(f"必須列が不足しています: {', '.join(missing_columns)}")

        return errors

    def _validate_required_columns(self, df: pd.DataFrame) -> list[str]:
        """必須列の空値チェック."""
        errors = []

        for column_def in self.data_format.get_required_columns():
            if column_def.name in df.columns:
                null_count = df[column_def.name].isna().sum()
                if null_count > 0:
                    msg = f"必須列 '{column_def.name}' に {null_count} 個の空値があります"
                    errors.append(msg)

        return errors

    def _validate_data_types(self, df: pd.DataFrame) -> list[str]:
        """データ型の変換可能性チェック."""
        errors = []

        for column_def in self.data_format.columns:
            if column_def.name in df.columns:
                try:
                    # 試しに変換してみる
                    self._convert_column(df[column_def.name], column_def)
                except (ValueError, TypeError) as e:
                    msg = f"列 '{column_def.name}' を {column_def.type} 型に変換できません: {e!s}"
                    errors.append(msg)

        return errors

    def _convert_column(
        self, series: pd.Series, column_def: ColumnDefinition,
    ) -> pd.Series:
        """列を指定された型に変換."""
        # デフォルト値で欠損値を埋める
        if column_def.default is not None:
            series = series.fillna(column_def.default)

        # 型変換のマッピング
        type_converters = {
            "string": lambda s: s.astype(str),
            "int": lambda s: pd.to_numeric(s, errors="raise").astype("Int64"),
            "float": lambda s: pd.to_numeric(s, errors="raise"),
        }

        if column_def.type in type_converters:
            return type_converters[column_def.type](series)

        if column_def.type == "bool":
            return self._convert_to_bool(series)

        if column_def.type == "datetime":
            return self._convert_to_datetime(series, column_def.format)

        msg = f"サポートされていない型: {column_def.type}"
        raise ValueError(msg)

    def _convert_to_bool(self, series: pd.Series) -> pd.Series:
        """ブール型への変換."""
        if series.dtype == "object":
            bool_map = {
                "true": True, "false": False,
                "True": True, "False": False,
                "TRUE": True, "FALSE": False,
                "1": True, "0": False,
                1: True, 0: False,
            }
            return series.map(bool_map).astype(bool)
        return series.astype(bool)

    def _convert_to_datetime(self, series: pd.Series, format_str: str | None) -> pd.Series:
        """日時型への変換."""
        if format_str:
            return pd.to_datetime(series, format=format_str, errors="raise")
        return pd.to_datetime(series, errors="raise")


def parse_data_format(format_data: dict[str, Any]) -> DataFormat:
    """YAML設定からDataFormatオブジェクトを生成."""
    if "columns" not in format_data:
        msg = "データフォーマット設定に 'columns' セクションが必要です"
        raise ValueError(msg)

    columns = []
    for col_data in format_data["columns"]:
        try:
            column = ColumnDefinition(
                name=col_data["name"],
                type=col_data["type"],
                required=col_data.get("required", True),
                format=col_data.get("format"),
                default=col_data.get("default"),
                description=col_data.get("description", ""),
            )
            columns.append(column)

        except KeyError as e:
            msg = f"列定義に必須フィールドが不足しています: {e}"
            raise ValueError(msg) from e

    return DataFormat(columns=columns)
