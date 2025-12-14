"""計算ルール関連のドメインモデル."""
import ast
import operator
import re
from dataclasses import dataclass
from typing import Any, ClassVar

import pandas as pd


@dataclass
class CalculationRule:
    """計算ルールエンティティ."""

    name: str
    formula: str
    description: str = ""
    group_by: list[str] = None

    def __post_init__(self) -> None:
        """バリデーション."""
        if not self.name:
            msg = "計算ルール名は必須です"
            raise ValueError(msg)
        if not self.formula:
            msg = "計算式は必須です"
            raise ValueError(msg)
        if self.group_by is None:
            self.group_by = []


class CalculationEngine:
    """計算式エンジン."""

    # 安全な演算子のマッピング
    _OPERATORS: ClassVar[dict[type[ast.AST], Any]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # 安全な関数のマッピング
    _FUNCTIONS: ClassVar[dict[str, Any]] = {
        "SUM": pd.Series.sum,
        "MEAN": pd.Series.mean,
        "COUNT": pd.Series.count,
        "MIN": pd.Series.min,
        "MAX": pd.Series.max,
        "STD": pd.Series.std,
        "VAR": pd.Series.var,
    }

    def __init__(self) -> None:
        """計算エンジンを初期化."""

    def validate_formula(self, formula: str) -> bool:
        """計算式の構文をバリデーションする."""
        try:
            # 集約関数の処理
            if self.is_aggregation_formula(formula):
                return self._validate_aggregation_formula(formula)

            # 通常の四則演算の処理
            tree = ast.parse(formula, mode="eval")
            self._validate_ast_node(tree.body)
        except (SyntaxError, ValueError, TypeError):
            return False
        else:
            return True

    def apply_formula(
        self,
        df: pd.DataFrame,
        rule: CalculationRule,
        computed_columns: dict | None = None,
    ) -> pd.Series:
        """DataFrameに計算式を適用する."""
        if computed_columns is None:
            computed_columns = {}

        try:
            if self.is_aggregation_formula(rule.formula):
                return self._apply_aggregation_formula(df, rule)
            return self.apply_arithmetic_formula(df, rule.formula, computed_columns)

        except Exception as e:
            msg = f"計算式の適用に失敗しました: {rule.name} - {e!s}"
            raise ValueError(msg) from e

    def is_aggregation_formula(self, formula: str) -> bool:
        """集約関数を含む式かどうかを判定."""
        aggregation_functions = ["SUM", "MEAN", "COUNT", "MIN", "MAX", "STD", "VAR"]
        formula_upper = formula.upper()
        # 関数呼び出しの形(関数名+括弧)で判定
        return any(f"{func}(" in formula_upper for func in aggregation_functions)

    def _validate_aggregation_formula(self, formula: str) -> bool:
        """集約関数の構文をバリデーション."""
        # 簡単な正規表現でSUM(column)形式をチェック
        pattern = r"^(SUM|MEAN|COUNT|MIN|MAX|STD|VAR)\([a-zA-Z_][a-zA-Z0-9_]*\)$"
        return bool(re.match(pattern, formula.replace(" ", ""), re.IGNORECASE))

    def _apply_aggregation_formula(
        self, df: pd.DataFrame, rule: CalculationRule,
    ) -> pd.Series:
        """集約計算を適用."""
        func_name, column_name = self._parse_aggregation_formula(rule.formula)
        self._validate_aggregation_column(df, column_name)

        if rule.group_by:
            return self._apply_grouped_aggregation(df, rule, func_name, column_name)
        return self._apply_global_aggregation(df, func_name, column_name)

    def _parse_aggregation_formula(self, formula: str) -> tuple[str, str]:
        """集約関数の構文を解析して関数名と列名を返す."""
        cleaned_formula = formula.replace(" ", "")
        pattern = r"^(SUM|MEAN|COUNT|MIN|MAX|STD|VAR)\(([a-zA-Z_][a-zA-Z0-9_]*)\)$"
        match = re.match(pattern, cleaned_formula, re.IGNORECASE)

        if not match:
            msg = f"集約関数の構文が不正です: {formula}"
            raise ValueError(msg)

        func_name, column_name = match.groups()
        return func_name.upper(), column_name

    def _validate_aggregation_column(self, df: pd.DataFrame, column_name: str) -> None:
        """集約対象の列が存在するかを検証."""
        if column_name not in df.columns:
            msg = f"列が存在しません: {column_name}"
            raise ValueError(msg)

    def _apply_grouped_aggregation(
        self, df: pd.DataFrame, rule: CalculationRule, func_name: str, column_name: str,
    ) -> pd.Series:
        """グループ化された集約を適用."""
        group_cols = self._prepare_group_columns(df, rule.group_by)
        grouped = df.groupby(group_cols)[column_name]
        return self._execute_grouped_aggregation(grouped, func_name)

    def _prepare_group_columns(self, df: pd.DataFrame, group_by: list[str]) -> list[str]:
        """グループ化用の列を準備する ex.) 日付変換などを含む."""
        group_cols = []
        for group_col in group_by:
            if "::" in group_col:
                col_name, transform = group_col.split("::")
                if transform == "month" and col_name in df.columns:
                    month_col = pd.to_datetime(df[col_name]).dt.to_period("M")
                    df[f"{col_name}_month"] = month_col
                    group_cols.append(f"{col_name}_month")
                else:
                    group_cols.append(col_name)
            else:
                group_cols.append(group_col)
        return group_cols

    def _execute_grouped_aggregation(self, grouped: pd.core.groupby.SeriesGroupBy, func_name: str) -> pd.Series:
        """SeriesGroupByオブジェクトに対して集約関数を実行."""
        aggregation_methods = {
            "SUM": grouped.sum,
            "MEAN": grouped.mean,
            "COUNT": grouped.count,
            "MIN": grouped.min,
            "MAX": grouped.max,
            "STD": grouped.std,
            "VAR": grouped.var,
        }

        if func_name not in aggregation_methods:
            msg = f"サポートされていない集約関数: {func_name}"
            raise ValueError(msg)

        return aggregation_methods[func_name]()

    def _apply_global_aggregation(self, df: pd.DataFrame, func_name: str, column_name: str) -> pd.Series:
        """全体での集約を適用."""
        func = self._FUNCTIONS[func_name]
        result = func(df[column_name])
        return pd.Series([result], index=[f"{func_name}({column_name})"])

    def apply_arithmetic_formula(
        self,
        df: pd.DataFrame,
        formula: str,
        computed_columns: dict | None = None,
    ) -> pd.Series:
        """四則演算を適用."""
        if computed_columns is None:
            computed_columns = {}

        try:
            tree = ast.parse(formula, mode="eval")
            result = self._evaluate_ast_node(tree.body, df, computed_columns)

            if isinstance(result, (int, float)):
                # スカラー値の場合、DataFrameの行数分のSeriesを作成
                return pd.Series([result] * len(df))
            if isinstance(result, pd.Series):
                return result

            def _raise_type_error() -> None:
                msg = f"計算結果の型が不正です: {type(result)}"
                raise ValueError(msg)

            _raise_type_error()

        except Exception as e:
            msg = f"四則演算の処理に失敗しました: {formula} - {e!s}"
            raise ValueError(msg) from e

    def _validate_ast_node(self, node: ast.AST) -> None:
        """AST/ノードの安全性をバリデーション."""
        if isinstance(node, ast.BinOp):
            if type(node.op) not in self._OPERATORS:
                msg = f"サポートされていない演算子: {type(node.op).__name__}"
                raise ValueError(msg)
            self._validate_ast_node(node.left)
            self._validate_ast_node(node.right)

        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in self._OPERATORS:
                msg = f"サポートされていない単項演算子: {type(node.op).__name__}"
                raise ValueError(msg)
            self._validate_ast_node(node.operand)

        elif isinstance(node, (ast.Constant, ast.Num)):
            # 数値リテラルは安全
            pass

        elif isinstance(node, ast.Name):
            # 変数名(列名)は安全
            pass

        else:
            msg = f"サポートされていないAST要素: {type(node).__name__}"
            raise TypeError(msg)

    def _evaluate_ast_node(
        self,
        node: ast.AST,
        df: pd.DataFrame,
        computed_columns: dict | None = None,
    ) -> float | pd.Series:
        """AST/ノードを評価して値を返す."""
        if computed_columns is None:
            computed_columns = {}

        if isinstance(node, ast.BinOp):
            left = self._evaluate_ast_node(node.left, df, computed_columns)
            right = self._evaluate_ast_node(node.right, df, computed_columns)
            op_func = self._OPERATORS[type(node.op)]
            return op_func(left, right)

        if isinstance(node, ast.UnaryOp):
            operand = self._evaluate_ast_node(node.operand, df, computed_columns)
            op_func = self._OPERATORS[type(node.op)]
            return op_func(operand)

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Num):  # Python 3.7以前の互換性
            return node.n

        if isinstance(node, ast.Name):
            column_name = node.id

            # まず計算済み列をチェック
            if column_name in computed_columns:
                return computed_columns[column_name]

            # 次に元のDataFrame列をチェック
            if column_name in df.columns:
                return df[column_name]

            msg = f"列または計算済み変数が存在しません: {column_name}"
            raise ValueError(msg)

        msg = f"評価できないAST要素: {type(node).__name__}"
        raise ValueError(msg)


    def apply_multiple_rules(
        self, df: pd.DataFrame, rules: list[CalculationRule],
    ) -> pd.DataFrame:
        """複数の計算ルールを順次適用してDataFrameを拡張."""
        result_df = df.copy()
        computed_columns = {}

        for rule in rules:
            try:
                if self.is_aggregation_formula(rule.formula):
                    # 集約処理は別途処理が必要
                    computed_result = self._apply_aggregation_formula(result_df, rule)
                else:
                    computed_result = self.apply_arithmetic_formula(
                        result_df, rule.formula, computed_columns,
                    )

                # 計算結果を保存
                computed_columns[rule.name] = computed_result
                is_series = isinstance(computed_result, pd.Series)
                if is_series and len(computed_result) == len(result_df):
                    result_df[rule.name] = computed_result

            except Exception as e:
                msg = f"計算ルール '{rule.name}' の適用に失敗しました: {e!s}"
                raise ValueError(msg) from e

        return result_df


def parse_calculation_rules(rules_data: list[dict[str, Any]]) -> list[CalculationRule]:
    """YAML設定から計算ルールのリストを生成."""
    rules = []

    for rule_data in rules_data:
        try:
            rule = CalculationRule(
                name=rule_data["name"],
                formula=rule_data["formula"],
                description=rule_data.get("description", ""),
                group_by=rule_data.get("group_by", []),
            )

            # 基本的な構文チェック, 変数参照は実行時にチェック
            if not rule.formula.strip():
                msg = f"計算式が空です: {rule.name}"
                raise ValueError(msg)

            rules.append(rule)

        except KeyError as e:
            msg = f"必須フィールドが不足しています: {e}"
            raise ValueError(msg) from e

    return rules
