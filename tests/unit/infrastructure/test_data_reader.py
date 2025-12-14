"""DataReaderのユニットテスト."""
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.infrastructure.data.reader import DataReader, DataSourceError


@pytest.fixture
def temp_csv(tmp_path: Path) -> Path:
    """一時的なCSVファイルを作成."""
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("name,age,score\nAlice,25,85.5\nBob,30,90.0\n")
    return csv_path


@pytest.fixture
def mock_config_loader() -> Mock:
    """ConfigLoaderのモック."""
    with patch("src.infrastructure.data.reader.ConfigLoader") as mock:
        yield mock


class TestDataReader:
    """DataReaderクラスのテスト."""

    def test_init_default_project_root(self) -> None:
        """デフォルトのproject_rootが正しく設定される."""
        reader = DataReader()
        assert reader.project_root.exists()
        assert reader.project_root.is_dir()

    def test_init_custom_project_root(self, tmp_path: Path) -> None:
        """カスタムproject_rootが正しく設定される."""
        reader = DataReader(project_root=tmp_path)
        assert reader.project_root == tmp_path

    def test_resolve_path_absolute(self, tmp_path: Path) -> None:
        """絶対パスがそのまま返される."""
        reader = DataReader(project_root=tmp_path)
        abs_path = "/absolute/path/file.csv"
        result = reader._resolve_path(abs_path)  # noqa: SLF001
        assert result == Path(abs_path)

    def test_resolve_path_relative(self, tmp_path: Path) -> None:
        """相対パスがproject_rootを基準に解決される."""
        reader = DataReader(project_root=tmp_path)
        rel_path = "data/test.csv"
        result = reader._resolve_path(rel_path)  # noqa: SLF001
        expected = (tmp_path / rel_path).resolve()
        assert result == expected

    def test_validate_and_get_data_source_missing(self) -> None:
        """data_sourceセクションが無い場合にエラー."""
        reader = DataReader()
        config = {}
        with pytest.raises(DataSourceError, match="data_source セクションが見つかりません"):
            reader._validate_and_get_data_source(config, "team_x")  # noqa: SLF001

    def test_validate_and_get_data_source_success(self) -> None:
        """data_sourceが正しく返される."""
        reader = DataReader()
        config = {"data_source": {"kind": "local_csv", "path": "data.csv"}}
        result = reader._validate_and_get_data_source(config, "team_x")  # noqa: SLF001
        assert result == {"kind": "local_csv", "path": "data.csv"}

    def test_load_by_kind_unsupported(self) -> None:
        """未対応のkindでエラー."""
        reader = DataReader()
        data_source = {"kind": "unknown"}
        with pytest.raises(DataSourceError, match="未対応のデータソース種類"):
            reader._load_by_kind(data_source)  # noqa: SLF001

    def test_get_csv_path_missing_path(self) -> None:
        """pathが未設定の場合にエラー."""
        reader = DataReader()
        data_source = {"kind": "local_csv"}
        with pytest.raises(DataSourceError, match="data_source.path が未設定です"):
            reader._get_csv_path(data_source)  # noqa: SLF001

    def test_get_csv_path_not_exists(self, tmp_path: Path) -> None:
        """CSVファイルが存在しない場合にエラー."""
        reader = DataReader(project_root=tmp_path)
        data_source = {"path": "nonexistent.csv"}
        with pytest.raises(DataSourceError, match="CSVファイルが存在しません"):
            reader._get_csv_path(data_source)  # noqa: SLF001

    def test_get_csv_path_success(self, tmp_path: Path, temp_csv: Path) -> None:
        """CSVパスが正しく返される."""
        reader = DataReader(project_root=tmp_path)
        data_source = {"path": str(temp_csv)}
        result = reader._get_csv_path(data_source)  # noqa: SLF001
        assert result == temp_csv

    def test_read_csv_success(self, temp_csv: Path) -> None:
        """CSVが正しく読み込まれる."""
        reader = DataReader()
        df = reader._read_csv(temp_csv, {})  # noqa: SLF001
        assert len(df) == 2
        assert list(df.columns) == ["name", "age", "score"]
        assert df.iloc[0]["name"] == "Alice"

    def test_read_csv_with_options(self, tmp_path: Path) -> None:
        """CSV読み込みオプションが適用される."""
        csv_path = tmp_path / "data.csv"
        csv_path.write_text("Alice,25\nBob,30\n", encoding="utf-8")
        reader = DataReader()
        df = reader._read_csv(csv_path, {"header": False})  # noqa: SLF001
        assert len(df) == 2
        assert 0 in df.columns  # ヘッダー無しなので数値列名

    def test_read_csv_invalid_encoding(self, tmp_path: Path) -> None:
        """エンコーディングエラーでDataSourceErrorが発生."""
        invalid_csv = tmp_path / "invalid.csv"
        # UTF-8として不正なバイト列を書き込む
        invalid_csv.write_bytes(b"name,value\n\xff\xfe\x00invalid")
        reader = DataReader()
        with pytest.raises(DataSourceError, match="CSV読み込みに失敗しました"):
            reader._read_csv(invalid_csv, {"encoding": "utf-8"})  # noqa: SLF001

    def test_apply_type_conversions_none_format(self) -> None:
        """data_formatがNoneの場合、変換なし."""
        reader = DataReader()
        df = pd.DataFrame({"a": ["1", "2"]})
        reader._apply_type_conversions(df, None)  # noqa: SLF001
        assert df["a"].dtype == object

    def test_apply_type_conversions_no_columns(self) -> None:
        """data_formatにcolumnsが無い場合、変換なし."""
        reader = DataReader()
        df = pd.DataFrame({"a": ["1", "2"]})
        reader._apply_type_conversions(df, {})  # noqa: SLF001
        assert df["a"].dtype == object

    def test_convert_column_type_int(self) -> None:
        """int型変換が正しく動作."""
        reader = DataReader()
        df = pd.DataFrame({"num": ["1", "2", "3"]})
        reader._convert_column_type(df, "num", "int", {})  # noqa: SLF001
        assert df["num"].dtype.name == "Int64"
        assert df["num"].iloc[0] == 1

    def test_convert_column_type_float(self) -> None:
        """float型変換が正しく動作."""
        reader = DataReader()
        df = pd.DataFrame({"val": ["1.5", "2.7"]})
        reader._convert_column_type(df, "val", "float", {})  # noqa: SLF001
        assert df["val"].dtype == float
        assert df["val"].iloc[0] == 1.5

    def test_convert_column_type_datetime(self) -> None:
        """datetime型変換が正しく動作."""
        reader = DataReader()
        df = pd.DataFrame({"date": ["2025-01-01", "2025-12-31"]})
        reader._convert_column_type(df, "date", "datetime", {"format": "%Y-%m-%d"})  # noqa: SLF001
        assert pd.api.types.is_datetime64_any_dtype(df["date"])

    def test_convert_column_type_string(self) -> None:
        """string型変換が正しく動作."""
        reader = DataReader()
        df = pd.DataFrame({"text": [1, 2, 3]})
        reader._convert_column_type(df, "text", "string", {})  # noqa: SLF001
        assert df["text"].dtype.name == "string"

    def test_load_local_csv_success(self, tmp_path: Path, temp_csv: Path) -> None:
        """ローカルCSVの読み込みが成功."""
        reader = DataReader(project_root=tmp_path)
        data_source = {"path": str(temp_csv), "options": {"encoding": "utf-8"}}
        df = reader._load_local_csv(data_source)  # noqa: SLF001
        assert len(df) == 2
        assert "name" in df.columns

    def test_load_team_dataframe_integration(self, tmp_path: Path, mock_config_loader: Mock) -> None:
        """load_team_dataframeの統合テスト."""
        # CSVファイル作成
        csv_path = tmp_path / "team.csv"
        csv_path.write_text("date,value\n2025-01-01,100\n2025-01-02,200\n")

        # Configモック
        mock_loader_instance = mock_config_loader.return_value
        mock_loader_instance.load_team_config.return_value = {
            "data_source": {
                "kind": "local_csv",
                "path": str(csv_path),
                "options": {"encoding": "utf-8"},
            },
        }

        reader = DataReader(project_root=tmp_path)
        data_format = {
            "columns": [
                {"name": "date", "type": "datetime", "format": "%Y-%m-%d"},
                {"name": "value", "type": "int"},
            ],
        }

        df = reader.load_team_dataframe("test_team", data_format)
        assert len(df) == 2
        assert pd.api.types.is_datetime64_any_dtype(df["date"])
        assert df["value"].dtype.name == "Int64"
        assert df["value"].iloc[0] == 100
