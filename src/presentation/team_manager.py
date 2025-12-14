"""Team manager for session state abstraction."""
from src.domain.team import Team


class TeamManager:
    """チーム管理クラス(セッション状態の抽象化)."""

    def __init__(self) -> None:
        """Initialize team manager."""
        self._teams: dict[str, Team] = {}
        self._initialize_sample_teams()

    def _initialize_sample_teams(self) -> None:
        """サンプルチームの初期化."""
        self._teams = {
            "team_a": Team(
                id="team_a", name="営業チームA", description="サンプルチームA",
            ),
            "team_b": Team(
                id="team_b", name="営業チームB", description="サンプルチームB",
            ),
        }

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
