"""Unit tests for the TeamManager class."""


import pytest

from src.presentation.team_manager import TeamManager

# Constants for magic numbers
INITIAL_TEAM_COUNT = 2
AFTER_CREATE_TEAM_COUNT = 3
AFTER_DELETE_TEAM_COUNT = 1


class TestTeamManager:
    """TeamManagerのユニットテスト."""

    @pytest.fixture
    def manager(self) -> TeamManager:
        """Create a TeamManager instance for testing."""
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

