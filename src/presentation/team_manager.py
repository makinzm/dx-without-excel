"""Team manager for session state abstraction."""
from src.domain.team import Team
from src.infrastructure.config.loader import ConfigurationError, TeamConfigManager


class TeamManager:
    """チーム管理クラス(セッション状態の抽象化)."""

    def __init__(self) -> None:
        """Initialize team manager."""
        self._teams: dict[str, Team] = {}
        self._config_manager = TeamConfigManager()
        self._config_error: str | None = None
        self._load_teams_from_config()

    def _load_teams_from_config(self) -> None:
        """設定ファイルからチームを読み込む."""
        try:
            self._teams = self._config_manager.load_all_teams()
            self._config_error = None
        except ConfigurationError as e:
            self._config_error = str(e)
            self._teams = {}

    def get_all_teams(self) -> dict[str, Team]:
        """全チームを取得."""
        return self._teams.copy()

    def get_team(self, team_id: str) -> Team | None:
        """指定したチームを取得."""
        return self._teams.get(team_id)

    def create_team(self, team_id: str, name: str, description: str = "") -> Team:
        """新規チームを作成."""
        if team_id in self._teams:
            msg = f"チームID '{team_id}' は既に存在します"
            raise ValueError(msg)

        team = Team(id=team_id, name=name, description=description)
        self._teams[team_id] = team
        return team

    def delete_team(self, team_id: str) -> bool:
        """チームを削除."""
        if team_id in self._teams:
            del self._teams[team_id]
            return True
        return False

    def team_exists(self, team_id: str) -> bool:
        """チームが存在するか確認."""
        return team_id in self._teams

    def get_team_count(self) -> int:
        """チーム数を取得."""
        return len(self._teams)

    def get_config_error(self) -> str | None:
        """設定エラーメッセージを取得."""
        return self._config_error

    def has_config_error(self) -> bool:
        """設定エラーがあるかどうか."""
        return self._config_error is not None

    def reload_config(self) -> None:
        """設定ファイルを再読み込み."""
        self._load_teams_from_config()

    def get_team_data_format(self, team_id: str) -> dict | None:
        """チームのデータフォーマット設定を取得."""
        try:
            return self._config_manager.load_team_data_format(team_id)
        except ConfigurationError:
            return None

    def get_team_calculation_rules(self, team_id: str) -> list | None:
        """チームの計算ルール設定を取得."""
        try:
            return self._config_manager.load_team_calculation_rules(team_id)
        except ConfigurationError:
            return None
