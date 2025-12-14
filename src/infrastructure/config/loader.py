"""YAML設定ファイルローダー."""
from pathlib import Path
from typing import Any

import yaml

from src.domain.calculation import CalculationRule, parse_calculation_rules
from src.domain.team import Team


class ConfigurationError(Exception):
    """設定関連のエラー."""



class ConfigLoader:
    """設定ファイルローダー."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """設定ローダーを初期化."""
        if config_dir is None:
            # プロジェクトルートのconfigディレクトリを使用
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self._validate_config_directory()

    def _validate_config_directory(self) -> None:
        """設定ディレクトリの存在チェック."""
        if not self.config_dir.exists():
            msg = f"設定ディレクトリが存在しません: {self.config_dir}"
            raise ConfigurationError(msg)

        if not self.config_dir.is_dir():
            msg = f"設定パスがディレクトリではありません: {self.config_dir}"
            raise ConfigurationError(msg)

    def load_app_config(self) -> dict[str, Any]:
        """アプリケーション設定を読み込む."""
        app_config_path = self.config_dir / "app.yaml"
        return self._load_yaml_file(app_config_path, "アプリケーション設定")

    def load_team_config(self, team_id: str) -> dict[str, Any]:
        """チーム設定を読み込む."""
        team_config_path = self.config_dir / "teams" / f"{team_id}.yaml"
        return self._load_yaml_file(team_config_path, f"チーム設定 ({team_id})")

    def get_available_teams(self) -> list[str]:
        """利用可能なチーム一覧を取得."""
        teams_dir = self.config_dir / "teams"

        if not teams_dir.exists():
            msg = f"チーム設定ディレクトリが存在しません: {teams_dir}"
            raise ConfigurationError(msg)

        team_ids = [
            yaml_file.stem
            for yaml_file in teams_dir.glob("*.yaml")
            if yaml_file.is_file()
        ]

        if not team_ids:
            msg = f"チーム設定ファイルが見つかりません: {teams_dir}"
            raise ConfigurationError(msg)

        return sorted(team_ids)

    def _load_yaml_file(self, file_path: Path, description: str) -> dict[str, Any]:
        """YAMLファイルを読み込む."""
        if not file_path.exists():
            msg = f"{description}ファイルが存在しません: {file_path}"
            raise ConfigurationError(msg)

        try:
            with file_path.open("r", encoding="utf-8") as f:
                content = yaml.safe_load(f)

            if content is None:
                def _raise_empty_file_error() -> None:
                    msg = f"{description}ファイルが空または不正です: {file_path}"
                    raise ConfigurationError(msg)
                _raise_empty_file_error()
        except yaml.YAMLError as e:
            msg = f"{description}の YAML 構文エラー: {file_path} - {e!s}"
            raise ConfigurationError(msg) from e
        except Exception as e:
            msg = f"{description}の読み込みに失敗しました: {file_path} - {e!s}"
            raise ConfigurationError(msg) from e
        else:
            return content


class TeamConfigManager:
    """チーム設定管理クラス."""

    def __init__(self, config_loader: ConfigLoader | None = None) -> None:
        """チーム設定マネージャーを初期化."""
        self.config_loader = config_loader or ConfigLoader()

    def load_all_teams(self) -> dict[str, Team]:
        """全チーム設定を読み込んでTeamオブジェクトを生成."""
        try:
            team_ids = self.config_loader.get_available_teams()
            teams = {}

            for team_id in team_ids:
                team = self.load_team(team_id)
                teams[team_id] = team
        except ConfigurationError:
            # 設定エラーは再スロー
            raise
        except Exception as e:
            msg = f"全チーム設定の読み込みに失敗しました: {e!s}"
            raise ConfigurationError(msg) from e
        else:
            return teams

    def load_team(self, team_id: str) -> Team:
        """指定チームの設定を読み込んでTeamオブジェクトを生成."""
        try:
            config = self.config_loader.load_team_config(team_id)

            # 必須フィールドの検証
            self._validate_team_config(config, team_id)

            # Teamオブジェクトの生成
            team_data = config["team"]
            return Team(
                id=team_data["id"],
                name=team_data["name"],
                description=team_data.get("description", ""),
            )

        except ConfigurationError:
            # 設定エラーは再スロー
            raise
        except Exception as e:
            msg = f"チーム設定の読み込みに失敗しました ({team_id}): {e!s}"
            raise ConfigurationError(msg) from e

    def load_team_data_format(self, team_id: str) -> dict[str, Any]:
        """チームのデータフォーマット設定を読み込む."""
        try:
            config = self.config_loader.load_team_config(team_id)

            if "data_format" not in config:
                def _raise_missing_data_format() -> None:
                    msg = f"データフォーマット設定が見つかりません: {team_id}"
                    raise ConfigurationError(msg)
                _raise_missing_data_format()

            return config["data_format"]

        except ConfigurationError:
            raise
        except Exception as e:
            msg = f"データフォーマット設定の読み込みに失敗しました ({team_id}): {e!s}"
            raise ConfigurationError(msg) from e

    def load_team_calculation_rules(self, team_id: str) -> list[CalculationRule]:
        """チームの計算ルール設定を読み込む."""
        try:
            config = self.config_loader.load_team_config(team_id)

            if "calculation_rules" not in config:
                def _raise_missing_calc_rules() -> None:
                    msg = f"計算ルール設定が見つかりません: {team_id}"
                    raise ConfigurationError(msg)
                _raise_missing_calc_rules()

            # 計算ルールオブジェクトに変換
            return parse_calculation_rules(config["calculation_rules"])

        except ConfigurationError:
            raise
        except Exception as e:
            msg = f"計算ルール設定の読み込みに失敗しました ({team_id}): {e!s}"
            raise ConfigurationError(msg) from e

    def _validate_team_config(self, config: dict[str, Any], team_id: str) -> None:
        """チーム設定の必須フィールドを検証."""
        if "team" not in config:
            msg = f"'team' セクションが見つかりません: {team_id}"
            raise ConfigurationError(msg)

        team_data = config["team"]

        required_fields = ["id", "name"]
        for field in required_fields:
            if field not in team_data or not team_data[field]:
                msg = f"必須フィールドが不足または空です: team.{field} ({team_id})"
                raise ConfigurationError(msg)

        # team_idとファイル名の整合性チェック
        if team_data["id"] != team_id:
            msg = f"チームIDとファイル名が一致しません: {team_data['id']} != {team_id}"
            raise ConfigurationError(msg)
