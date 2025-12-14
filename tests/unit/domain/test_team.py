"""Unit tests for the Team entity."""

import pytest

from src.domain.team import Team


class TestTeam:
    """Teamエンティティのユニットテスト."""

    def test_create_team_successfully(self) -> None:
        """Test that Team can be created successfully with all parameters."""
        team = Team(id="team_a", name="チームA", description="説明A")

        if team.id != "team_a":
            msg = f"Expected team.id to be 'team_a', got {team.id}"
            raise AssertionError(msg)
        if team.name != "チームA":
            msg = f"Expected team.name to be 'チームA', got {team.name}"
            raise AssertionError(msg)
        if team.description != "説明A":
            msg = f"Expected team.description to be '説明A', got {team.description}"
            raise AssertionError(msg)

    def test_description_is_optional(self) -> None:
        """Test that description parameter is optional when creating Team."""
        team = Team(id="team_a", name="チームA")

        if team.description != "":
            msg = (
                f"Expected team.description to be empty string, "
                f"got {team.description}"
            )
            raise AssertionError(msg)

    def test_empty_id_raises_error(self) -> None:
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="チームIDは必須です"):
            Team(id="", name="チームA")

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="チーム名は必須です"):
            Team(id="team_a", name="")

    def test_invalid_id_characters_raise_error(self) -> None:
        """Test that invalid characters in ID raise ValueError."""
        with pytest.raises(ValueError, match="英数字とアンダースコアのみ"):
            Team(id="team-a", name="チームA")  # ハイフンは不可

        with pytest.raises(ValueError, match="英数字とアンダースコアのみ"):
            Team(id="チームA", name="チームA")  # 日本語は不可

        with pytest.raises(ValueError, match="英数字とアンダースコアのみ"):
            Team(id="team a", name="チームA")  # スペースは不可

    def test_convert_to_dict(self) -> None:
        """Test that Team can be converted to dictionary."""
        team = Team(id="team_a", name="チームA", description="説明A")
        data = team.to_dict()

        expected_data = {
            "id": "team_a",
            "name": "チームA",
            "description": "説明A",
        }
        if data != expected_data:
            msg = f"Expected {expected_data}, got {data}"
            raise AssertionError(msg)

    def test_restore_from_dict(self) -> None:
        """Test that Team can be restored from dictionary."""
        data = {
            "id": "team_b",
            "name": "チームB",
            "description": "説明B",
        }
        team = Team.from_dict(data)

        if team.id != "team_b":
            msg = f"Expected team.id to be 'team_b', got {team.id}"
            raise AssertionError(msg)
        if team.name != "チームB":
            msg = f"Expected team.name to be 'チームB', got {team.name}"
            raise AssertionError(msg)
        if team.description != "説明B":
            msg = f"Expected team.description to be '説明B', got {team.description}"
            raise AssertionError(msg)

    def test_restore_from_dict_without_description(self) -> None:
        """Test that Team can be restored from dictionary without description."""
        data = {
            "id": "team_c",
            "name": "チームC",
        }
        team = Team.from_dict(data)

        if team.description != "":
            msg = (
                f"Expected team.description to be empty string, "
                f"got {team.description}"
            )
            raise AssertionError(msg)

