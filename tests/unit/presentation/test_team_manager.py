"""Unit tests for the TeamManager class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.domain.calculation import CalculationRule
from src.domain.team import Team
from src.infrastructure.config.loader import ConfigurationError
from src.presentation.team_manager import TeamManager

# Constants for magic numbers
INITIAL_TEAM_COUNT = 2
AFTER_CREATE_TEAM_COUNT = 3
AFTER_DELETE_TEAM_COUNT = 1


class TestTeamManager:
    """TeamManagerのユニットテスト."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """テスト用の一時設定ディレクトリを作成."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        teams_dir = config_dir / "teams"
        teams_dir.mkdir()

        # テスト用のチーム設定ファイルを作成
        team_a_config = {
            "team": {
                "id": "team_a",
                "name": "営業チームA",
                "description": "サンプルチームA",
            },
            "data_format": {
                "columns": [
                    {"name": "test_col", "type": "string", "required": True},
                ],
            },
            "calculation_rules": [
                {"name": "test_rule", "formula": "a + b", "description": "テストルール"},
            ],
        }

        team_b_config = {
            "team": {
                "id": "team_b",
                "name": "営業チームB",
                "description": "サンプルチームB",
            },
            "data_format": {
                "columns": [
                    {"name": "other_col", "type": "int", "required": False},
                ],
            },
            "calculation_rules": [
                {"name": "other_rule", "formula": "x * y", "description": "その他ルール"},
            ],
        }

        with (teams_dir / "team_a.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(team_a_config, f)
        with (teams_dir / "team_b.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(team_b_config, f)

        return config_dir

    @pytest.fixture
    def manager(self) -> TeamManager:
        """Create a TeamManager instance for testing."""
        with patch("src.presentation.team_manager.TeamConfigManager") as mock_config_manager_class:
            mock_config_manager = Mock()
            mock_config_manager_class.return_value = mock_config_manager

            # Mock the config loading
            mock_config_manager.load_all_teams.return_value = {
                "team_a": Team(id="team_a", name="営業チームA", description="サンプルチームA"),
                "team_b": Team(id="team_b", name="営業チームB", description="サンプルチームB"),
            }

            return TeamManager()

    def test_sample_teams_exist_on_initialization(self, manager: TeamManager) -> None:
        """Test that sample teams exist when TeamManager is initialized."""
        teams = manager.get_all_teams()

        if len(teams) != INITIAL_TEAM_COUNT:
            msg = f"Expected {INITIAL_TEAM_COUNT} teams, got {len(teams)}"
            raise AssertionError(msg)
        if "team_a" not in teams:
            msg = "Expected 'team_a' to be in teams"
            raise AssertionError(msg)
        if "team_b" not in teams:
            msg = "Expected 'team_b' to be in teams"
            raise AssertionError(msg)

    def test_can_get_team(self, manager: TeamManager) -> None:
        """Test that existing team can be retrieved by ID."""
        team = manager.get_team("team_a")

        if team is None:
            msg = "Expected team to not be None"
            raise AssertionError(msg)
        if team.id != "team_a":
            msg = f"Expected team.id to be 'team_a', got {team.id}"
            raise AssertionError(msg)
        if team.name != "営業チームA":
            msg = f"Expected team.name to be '営業チームA', got {team.name}"
            raise AssertionError(msg)

    def test_nonexistent_team_returns_none(self, manager: TeamManager) -> None:
        """Test that getting a nonexistent team returns None."""
        team = manager.get_team("non_existent")

        if team is not None:
            msg = f"Expected team to be None, got {team}"
            raise AssertionError(msg)

    def test_can_create_new_team(self, manager: TeamManager) -> None:
        """Test that a new team can be created successfully."""
        team = manager.create_team("team_c", "チームC", "説明C")

        if team.id != "team_c":
            msg = f"Expected team.id to be 'team_c', got {team.id}"
            raise AssertionError(msg)
        if team.name != "チームC":
            msg = f"Expected team.name to be 'チームC', got {team.name}"
            raise AssertionError(msg)
        if manager.get_team_count() != AFTER_CREATE_TEAM_COUNT:
            count = manager.get_team_count()
            msg = f"Expected team count to be {AFTER_CREATE_TEAM_COUNT}, got {count}"
            raise AssertionError(msg)

    def test_create_team_with_existing_id_raises_error(
        self, manager: TeamManager,
    ) -> None:
        """Test that creating a team with existing ID raises ValueError."""
        with pytest.raises(ValueError, match="既に存在します"):
            manager.create_team("team_a", "新チームA")

    def test_can_delete_team(self, manager: TeamManager) -> None:
        """Test that an existing team can be deleted successfully."""
        result = manager.delete_team("team_a")

        if result is not True:
            msg = f"Expected result to be True, got {result}"
            raise AssertionError(msg)
        if manager.get_team("team_a") is not None:
            msg = "Expected team_a to be deleted (None)"
            raise AssertionError(msg)
        if manager.get_team_count() != AFTER_DELETE_TEAM_COUNT:
            count = manager.get_team_count()
            msg = f"Expected team count to be {AFTER_DELETE_TEAM_COUNT}, got {count}"
            raise AssertionError(msg)

    def test_delete_nonexistent_team_returns_false(self, manager: TeamManager) -> None:
        """Test that deleting a nonexistent team returns False."""
        result = manager.delete_team("non_existent")

        if result is not False:
            msg = f"Expected result to be False, got {result}"
            raise AssertionError(msg)

    def test_check_team_existence(self, manager: TeamManager) -> None:
        """Test team existence checking functionality."""
        if manager.team_exists("team_a") is not True:
            msg = "Expected team_a to exist"
            raise AssertionError(msg)
        if manager.team_exists("non_existent") is not False:
            msg = "Expected non_existent team to not exist"
            raise AssertionError(msg)

    def test_can_get_team_count(self, manager: TeamManager) -> None:
        """Test that team count can be retrieved and changes with operations."""
        if manager.get_team_count() != INITIAL_TEAM_COUNT:
            count = manager.get_team_count()
            msg = f"Expected initial count to be {INITIAL_TEAM_COUNT}, got {count}"
            raise AssertionError(msg)

        manager.create_team("team_c", "チームC")
        if manager.get_team_count() != AFTER_CREATE_TEAM_COUNT:
            count = manager.get_team_count()
            msg = (
                f"Expected count after create to be {AFTER_CREATE_TEAM_COUNT}, "
                f"got {count}"
            )
            raise AssertionError(msg)

        manager.delete_team("team_a")
        if manager.get_team_count() != INITIAL_TEAM_COUNT:
            count = manager.get_team_count()
            msg = f"Expected final count to be {INITIAL_TEAM_COUNT}, got {count}"
            raise AssertionError(msg)

    def test_config_error_handling(self) -> None:
        """設定エラーのハンドリングをテスト."""
        with patch("src.presentation.team_manager.TeamConfigManager") as mock_config_manager_class:
            mock_config_manager = Mock()
            mock_config_manager_class.return_value = mock_config_manager

            # 設定エラーをシミュレート
            mock_config_manager.load_all_teams.side_effect = ConfigurationError("テストエラー")

            manager = TeamManager()

            if not manager.has_config_error():
                msg = "Expected config error to be detected"
                raise AssertionError(msg)

            if manager.get_config_error() != "テストエラー":
                msg = f"Expected error message 'テストエラー', got {manager.get_config_error()}"
                raise AssertionError(msg)

            if manager.get_team_count() != 0:
                msg = f"Expected 0 teams when config error occurs, got {manager.get_team_count()}"
                raise AssertionError(msg)

    def test_reload_config_success(self) -> None:
        """設定ファイルの再読み込み成功テスト."""
        with patch("src.presentation.team_manager.TeamConfigManager") as mock_config_manager_class:
            mock_config_manager = Mock()
            mock_config_manager_class.return_value = mock_config_manager

            # 最初はエラー
            mock_config_manager.load_all_teams.side_effect = ConfigurationError("初回エラー")
            manager = TeamManager()

            if not manager.has_config_error():
                msg = "Expected initial config error"
                raise AssertionError(msg)

            # 再読み込みで成功
            mock_config_manager.load_all_teams.side_effect = None
            mock_config_manager.load_all_teams.return_value = {
                "team_c": Team(id="team_c", name="チームC", description="新チーム"),
            }

            manager.reload_config()

            if manager.has_config_error():
                msg = f"Expected no config error after reload, got {manager.get_config_error()}"
                raise AssertionError(msg)

            if manager.get_team_count() != 1:
                msg = f"Expected 1 team after reload, got {manager.get_team_count()}"
                raise AssertionError(msg)

    def test_get_team_data_format(self) -> None:
        """チームのデータフォーマット設定取得テスト."""
        with patch("src.presentation.team_manager.TeamConfigManager") as mock_config_manager_class:
            mock_config_manager = Mock()
            mock_config_manager_class.return_value = mock_config_manager

            # 正常ケース
            mock_config_manager.load_all_teams.return_value = {}
            mock_config_manager.load_team_data_format.return_value = {
                "columns": [{"name": "test_col", "type": "string"}],
            }

            manager = TeamManager()
            result = manager.get_team_data_format("team_a")

            if result is None:
                msg = "Expected data format to be returned"
                raise AssertionError(msg)

            if "columns" not in result:
                msg = "Expected 'columns' in data format"
                raise AssertionError(msg)

            # エラーケース
            mock_config_manager.load_team_data_format.side_effect = ConfigurationError("テストエラー")
            result = manager.get_team_data_format("team_a")

            if result is not None:
                msg = f"Expected None on error, got {result}"
                raise AssertionError(msg)

    def test_get_team_calculation_rules(self) -> None:
        """チームの計算ルール設定取得テスト."""
        with patch("src.presentation.team_manager.TeamConfigManager") as mock_config_manager_class:
            mock_config_manager = Mock()
            mock_config_manager_class.return_value = mock_config_manager
            mock_rules = [CalculationRule(name="test_rule", formula="a + b", description="テスト")]
            mock_config_manager.load_all_teams.return_value = {}
            mock_config_manager.load_team_calculation_rules.return_value = mock_rules

            manager = TeamManager()
            result = manager.get_team_calculation_rules("team_a")

            if result is None:
                msg = "Expected calculation rules to be returned"
                raise AssertionError(msg)

            if len(result) != 1:
                msg = f"Expected 1 rule, got {len(result)}"
                raise AssertionError(msg)

            if result[0].name != "test_rule":
                msg = f"Expected rule name 'test_rule', got {result[0].name}"
                raise AssertionError(msg)

            # エラーケース
            mock_config_manager.load_team_calculation_rules.side_effect = ConfigurationError("テストエラー")
            result = manager.get_team_calculation_rules("team_a")

            if result is not None:
                msg = f"Expected None on error, got {result}"
                raise AssertionError(msg)

