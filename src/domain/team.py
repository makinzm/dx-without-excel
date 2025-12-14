"""Team domain model."""
import re
from dataclasses import dataclass


@dataclass
class Team:
    """チームエンティティ."""

    id: str
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        """バリデーション."""
        if not self.id:
            msg = "チームIDは必須です"
            raise ValueError(msg)
        if not self.name:
            msg = "チーム名は必須です"
            raise ValueError(msg)
        if not self._is_valid_id(self.id):
            msg = "チームIDは英数字とアンダースコアのみ使用可能です"
            raise ValueError(msg)

    @staticmethod
    def _is_valid_id(team_id: str) -> bool:
        """チームIDの形式チェック."""
        return bool(re.match(r"^[a-zA-Z0-9_]+$", team_id))

    def to_dict(self) -> dict:
        """辞書形式に変換."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Team":
        """辞書から復元."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
        )
