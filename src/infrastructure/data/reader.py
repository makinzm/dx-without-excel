"""データソースから実データを読み込むリーダー."""
from pathlib import Path
from typing import Any

import pandas as pd

from src.infrastructure.config.loader import ConfigLoader


class DataSourceError(Exception):
    """データソース関連のエラー."""


class DataReader:
    """チームごとのデータ読み込みクラス."""

    def __init__(self, project_root: Path | None = None) -> None:  # noqa: D107
        if project_root is None:
            # src/infrastructure/data/reader.py から4階層上がプロジェクトルート
            project_root = Path(__file__).parent.parent.parent.parent
        self.project_root = project_root
        self._config_loader = ConfigLoader()

    def _resolve_path(self, rel_or_abs_path: str) -> Path:
        p = Path(rel_or_abs_path)
        if p.is_absolute():
            return p
        return (self.project_root / p).resolve()

    def load_team_dataframe(self, team_id: str, data_format: dict[str, Any] | None = None) -> pd.DataFrame:
        """チーム設定に基づきデータを読み込む.

        現在は kind=local_csv に対応し、`path` のCSVを読み込む。
        data_format が与えられた場合、型変換や日付パースを試みる。
        """
        config = self._config_loader.load_team_config(team_id)
        data_source = self._validate_and_get_data_source(config, team_id)
        df = self._load_by_kind(data_source)
        self._apply_type_conversions(df, data_format)
        return df

    def _validate_and_get_data_source(self, config: dict[str, Any], team_id: str) -> dict[str, Any]:
        """データソース設定を検証して返す."""
        if "data_source" not in config:
            msg = f"data_source セクションが見つかりません: {team_id}"
            raise DataSourceError(msg)
        return config["data_source"]

    def _load_by_kind(self, data_source: dict[str, Any]) -> pd.DataFrame:
        """データソースの種類に応じて読み込み処理を振り分ける."""
        kind = data_source.get("kind")
        if kind == "local_csv":
            return self._load_local_csv(data_source)
        # 将来的な拡張例として、S3やデータベースからの読み込みもここで振り分け可能
        msg = f"未対応のデータソース種類: {kind}"
        raise DataSourceError(msg)

    def _load_local_csv(self, data_source: dict[str, Any]) -> pd.DataFrame:
        """ローカルCSVファイルを読み込む."""
        csv_path = self._get_csv_path(data_source)
        return self._read_csv(csv_path, data_source.get("options", {}))

    def _get_csv_path(self, data_source: dict[str, Any]) -> Path:
        """CSVファイルのパスを取得して検証."""
        path_str = data_source.get("path")
        if not path_str:
            msg = "data_source.path が未設定です"
            raise DataSourceError(msg)

        csv_path = self._resolve_path(path_str)
        if not csv_path.exists():
            msg = f"CSVファイルが存在しません: {csv_path}"
            raise DataSourceError(msg)

        return csv_path

    def _read_csv(self, csv_path: Path, options: dict[str, Any]) -> pd.DataFrame:
        """CSVファイルを読み込む."""
        encoding = options.get("encoding", "utf-8")
        header = 0 if options.get("header", True) else None

        try:
            return pd.read_csv(csv_path, encoding=encoding, header=header)
        except Exception as e:
            msg = f"CSV読み込みに失敗しました: {csv_path} - {e!s}"
            raise DataSourceError(msg) from e

    def _apply_type_conversions(self, df: pd.DataFrame, data_format: dict[str, Any] | None) -> None:
        """data_formatに従って型変換を適用."""
        if not data_format or "columns" not in data_format:
            return

        for col_def in data_format["columns"]:
            name = col_def.get("name")
            col_type = col_def.get("type")
            if name in df.columns and col_type:
                self._convert_column_type(df, name, col_type, col_def)

    def _convert_column_type(
        self, df: pd.DataFrame, name: str, col_type: str, col_def: dict[str, Any],
    ) -> None:
        """単一列の型変換を実行."""
        try:
            if col_type == "int":
                df[name] = pd.to_numeric(df[name], errors="coerce").astype("Int64")
            elif col_type == "float":
                df[name] = pd.to_numeric(df[name], errors="coerce")
            elif col_type == "datetime":
                fmt = col_def.get("format")
                df[name] = pd.to_datetime(df[name], format=fmt, errors="coerce")
            elif col_type == "string":
                df[name] = df[name].astype("string")
        except Exception:  # noqa: BLE001, S110
            # 型変換失敗時はcoerce結果をそのまま利用
            pass
