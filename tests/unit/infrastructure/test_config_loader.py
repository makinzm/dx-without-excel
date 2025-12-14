"""Unit tests for the configuration loader."""

from pathlib import Path

import pytest
import yaml

from src.infrastructure.config.loader import (
    ConfigLoader,
    ConfigurationError,
    TeamConfigManager,
)


class TestConfigLoader:
    """ConfigLoaderのユニットテスト."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """テスト用の一時設定ディレクトリを作成."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # teams ディレクトリを作成
        teams_dir = config_dir / "teams"
        teams_dir.mkdir()

        return config_dir

    @pytest.fixture
    def config_loader(self, temp_config_dir: Path) -> ConfigLoader:
        """ConfigLoaderインスタンスを作成."""
        return ConfigLoader(temp_config_dir)

    def test_create_config_loader_with_existing_directory(self, temp_config_dir: Path) -> None:
        """既存のディレクトリでConfigLoaderが正常に作成できることをテスト."""
        loader = ConfigLoader(temp_config_dir)

        if loader.config_dir != temp_config_dir:
            msg = f"Expected config_dir to be {temp_config_dir}, got {loader.config_dir}"
            raise AssertionError(msg)

    def test_create_config_loader_with_nonexistent_directory(self) -> None:
        """存在しないディレクトリでエラーが発生することをテスト."""
        nonexistent_path = Path("/nonexistent/path")

        with pytest.raises(ConfigurationError, match="設定ディレクトリが存在しません"):
            ConfigLoader(nonexistent_path)

    def test_load_app_config_success(self, config_loader: ConfigLoader, temp_config_dir: Path) -> None:
        """アプリケーション設定の正常読み込みテスト."""
        # app.yamlファイルを作成
        app_config_content = {
            "app": {
                "name": "Test App",
                "version": "1.0.0",
            },
        }
        app_config_path = temp_config_dir / "app.yaml"
        with app_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(app_config_content, f)

        config = config_loader.load_app_config()

        if config["app"]["name"] != "Test App":
            msg = f"Expected app name 'Test App', got {config['app']['name']}"
            raise AssertionError(msg)

    def test_load_app_config_file_not_found(self, config_loader: ConfigLoader) -> None:
        """app.yamlが存在しない場合のエラーテスト."""
        with pytest.raises(ConfigurationError, match="アプリケーション設定ファイルが存在しません"):
            config_loader.load_app_config()

    def test_load_team_config_success(self, config_loader: ConfigLoader, temp_config_dir: Path) -> None:
        """チーム設定の正常読み込みテスト."""
        # team_a.yamlファイルを作成
        team_config_content = {
            "team": {
                "id": "team_a",
                "name": "Team A",
                "description": "Test team",
            },
        }
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "team_a.yaml"
        with team_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_config_content, f)

        config = config_loader.load_team_config("team_a")

        if config["team"]["id"] != "team_a":
            msg = f"Expected team id 'team_a', got {config['team']['id']}"
            raise AssertionError(msg)

    def test_get_available_teams(self, config_loader: ConfigLoader, temp_config_dir: Path) -> None:
        """利用可能チーム一覧の取得テスト."""
        teams_dir = temp_config_dir / "teams"

        # 複数のチーム設定ファイルを作成
        for team_id in ["team_a", "team_b", "team_c"]:
            team_config_path = teams_dir / f"{team_id}.yaml"
            team_config_content = {"team": {"id": team_id, "name": f"Team {team_id.upper()}"}}
            with team_config_path.open("w", encoding="utf-8") as f:
                yaml.dump(team_config_content, f)

        team_ids = config_loader.get_available_teams()

        expected_teams = ["team_a", "team_b", "team_c"]
        if sorted(team_ids) != sorted(expected_teams):
            msg = f"Expected teams {expected_teams}, got {team_ids}"
            raise AssertionError(msg)

    def test_get_available_teams_empty_directory(self, config_loader: ConfigLoader) -> None:
        """チーム設定ファイルが存在しない場合のエラーテスト."""
        with pytest.raises(ConfigurationError, match="チーム設定ファイルが見つかりません"):
            config_loader.get_available_teams()

    def test_load_yaml_file_with_invalid_syntax(self, config_loader: ConfigLoader, temp_config_dir: Path) -> None:
        """不正なYAML構文の場合のエラーテスト."""
        # 不正なYAMLファイルを作成
        invalid_yaml_path = temp_config_dir / "app.yaml"
        with invalid_yaml_path.open("w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(ConfigurationError, match="YAML 構文エラー"):
            config_loader.load_app_config()


class TestTeamConfigManager:
    """TeamConfigManagerのユニットテスト."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """テスト用の一時設定ディレクトリを作成."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        teams_dir = config_dir / "teams"
        teams_dir.mkdir()

        return config_dir

    @pytest.fixture
    def team_config_manager(self, temp_config_dir: Path) -> TeamConfigManager:
        """TeamConfigManagerインスタンスを作成."""
        config_loader = ConfigLoader(temp_config_dir)
        return TeamConfigManager(config_loader)

    def test_load_team_success(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """チーム設定の正常読み込みとTeamオブジェクト生成テスト."""
        # team_a.yamlファイルを作成
        team_config_content = {
            "team": {
                "id": "team_a",
                "name": "営業チームA",
                "description": "テスト用チーム",
            },
        }
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "team_a.yaml"
        with team_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_config_content, f)

        team = team_config_manager.load_team("team_a")

        if team.id != "team_a":
            msg = f"Expected team id 'team_a', got {team.id}"
            raise AssertionError(msg)
        if team.name != "営業チームA":
            msg = f"Expected team name '営業チームA', got {team.name}"
            raise AssertionError(msg)
        if team.description != "テスト用チーム":
            msg = f"Expected team description 'テスト用チーム', got {team.description}"
            raise AssertionError(msg)

    def test_load_team_missing_team_section(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """teamセクションが不足している場合のエラーテスト."""
        # teamセクションのないYAMLファイルを作成
        team_config_content = {
            "other_section": {
                "data": "value",
            },
        }
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "team_a.yaml"
        with team_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_config_content, f)

        with pytest.raises(ConfigurationError, match="'team' セクションが見つかりません"):
            team_config_manager.load_team("team_a")

    def test_load_team_id_mismatch(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """チームIDとファイル名が一致しない場合のエラーテスト."""
        # team_a.yamlにteam_bの設定を記述
        team_config_content = {
            "team": {
                "id": "team_b",  # ファイル名と異なる
                "name": "チームB",
            },
        }
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "team_a.yaml"
        with team_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_config_content, f)

        with pytest.raises(ConfigurationError, match="チームIDとファイル名が一致しません"):
            team_config_manager.load_team("team_a")

    def test_load_team_data_format_success(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """データフォーマット設定の正常読み込みテスト."""
        team_config_content = {
            "team": {
                "id": "team_a",
                "name": "チームA",
            },
            "data_format": {
                "columns": [
                    {"name": "col1", "type": "string", "required": True},
                ],
            },
        }
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "team_a.yaml"
        with team_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_config_content, f)

        data_format = team_config_manager.load_team_data_format("team_a")

        if "columns" not in data_format:
            msg = "Expected 'columns' in data_format"
            raise AssertionError(msg)
        if len(data_format["columns"]) != 1:
            msg = f"Expected 1 column, got {len(data_format['columns'])}"
            raise AssertionError(msg)

    def test_load_team_calculation_rules_success(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """計算ルール設定の正常読み込みテスト."""
        team_config_content = {
            "team": {
                "id": "team_a",
                "name": "チームA",
            },
            "calculation_rules": [
                {
                    "name": "test_rule",
                    "formula": "a + b",
                    "description": "テストルール",
                },
            ],
        }
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "team_a.yaml"
        with team_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_config_content, f)

        rules = team_config_manager.load_team_calculation_rules("team_a")

        if len(rules) != 1:
            msg = f"Expected 1 rule, got {len(rules)}"
            raise AssertionError(msg)
        if rules[0].name != "test_rule":
            msg = f"Expected rule name 'test_rule', got {rules[0].name}"
            raise AssertionError(msg)

    def test_load_team_missing_data_format(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """データフォーマット設定が不足している場合のエラーテスト."""
        team_config_content = {
            "team": {
                "id": "team_a",
                "name": "チームA",
            },
            # data_format セクションなし
        }
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "team_a.yaml"
        with team_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_config_content, f)

        with pytest.raises(ConfigurationError, match="データフォーマット設定が見つかりません"):
            team_config_manager.load_team_data_format("team_a")

    def test_load_team_missing_calculation_rules(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """計算ルール設定が不足している場合のエラーテスト."""
        team_config_content = {
            "team": {
                "id": "team_a",
                "name": "チームA",
            },
            # calculation_rules セクションなし
        }
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "team_a.yaml"
        with team_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_config_content, f)

        with pytest.raises(ConfigurationError, match="計算ルール設定が見つかりません"):
            team_config_manager.load_team_calculation_rules("team_a")

    def test_load_all_teams_success(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """全チーム設定の正常読み込みテスト."""
        teams_dir = temp_config_dir / "teams"

        # 複数のチーム設定ファイルを作成
        teams_data = {
            "team_a": {"id": "team_a", "name": "チームA", "description": "説明A"},
            "team_b": {"id": "team_b", "name": "チームB", "description": "説明B"},
        }

        for team_id, team_data in teams_data.items():
            team_config_content = {"team": team_data}
            team_config_path = teams_dir / f"{team_id}.yaml"
            with team_config_path.open("w", encoding="utf-8") as f:
                yaml.dump(team_config_content, f)

        teams = team_config_manager.load_all_teams()

        expected_team_count = 2
        if len(teams) != expected_team_count:
            msg = f"Expected {expected_team_count} teams, got {len(teams)}"
            raise AssertionError(msg)

        for team_id in ["team_a", "team_b"]:
            if team_id not in teams:
                msg = f"Expected team {team_id} to be loaded"
                raise AssertionError(msg)
            if teams[team_id].id != team_id:
                msg = f"Expected team id {team_id}, got {teams[team_id].id}"
                raise AssertionError(msg)

    def test_load_team_missing_required_fields(self, team_config_manager: TeamConfigManager, temp_config_dir: Path) -> None:
        """必須フィールドが不足している場合のエラーテスト."""
        test_cases = [
            # id フィールド不足
            {
                "config": {"team": {"name": "チームA"}},
                "error_pattern": "必須フィールドが不足または空です: team.id",
            },
            # name フィールド不足
            {
                "config": {"team": {"id": "team_a"}},
                "error_pattern": "必須フィールドが不足または空です: team.name",
            },
            # id が空文字
            {
                "config": {"team": {"id": "", "name": "チームA"}},
                "error_pattern": "必須フィールドが不足または空です: team.id",
            },
            # name が空文字
            {
                "config": {"team": {"id": "team_a", "name": ""}},
                "error_pattern": "必須フィールドが不足または空です: team.name",
            },
        ]

        teams_dir = temp_config_dir / "teams"

        for i, test_case in enumerate(test_cases):
            team_config_path = teams_dir / f"test_team_{i}.yaml"
            with team_config_path.open("w", encoding="utf-8") as f:
                yaml.dump(test_case["config"], f)

            with pytest.raises(ConfigurationError, match=test_case["error_pattern"]):
                team_config_manager.load_team(f"test_team_{i}")

            # テストファイルをクリーンアップ
            team_config_path.unlink()


class TestConfigLoaderErrorHandling:
    """ConfigLoader error handling tests."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """テスト用の一時設定ディレクトリを作成."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir

    def test_config_loader_with_file_as_config_dir(self, tmp_path: Path) -> None:
        """設定パスがファイルの場合のエラーテスト."""
        # ファイルを作成
        file_path = tmp_path / "not_a_directory.txt"
        file_path.write_text("test content")

        with pytest.raises(ConfigurationError, match="設定パスがディレクトリではありません"):
            ConfigLoader(file_path)

    def test_load_empty_yaml_file(self, tmp_path: Path) -> None:
        """空のYAMLファイルの場合のエラーテスト."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # 空のファイルを作成
        app_config_path = config_dir / "app.yaml"
        app_config_path.write_text("")

        config_loader = ConfigLoader(config_dir)

        with pytest.raises(ConfigurationError, match="ファイルが空または不正です"):
            config_loader.load_app_config()

    def test_load_yaml_file_read_permission_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """ファイル読み込み権限エラーのテスト."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        app_config_path = config_dir / "app.yaml"
        app_config_path.write_text("test: value")

        config_loader = ConfigLoader(config_dir)

        # Path.open をモックしてIOErrorを発生させる
        original_open = Path.open
        def mock_open(self: Path, *args: tuple, **kwargs: dict) -> None:
            if "app.yaml" in str(self):
                msg = "Permission denied"
                raise OSError(msg)
            return original_open(self, *args, **kwargs)

        monkeypatch.setattr(Path, "open", mock_open)

        with pytest.raises(ConfigurationError, match="読み込みに失敗しました"):
            config_loader.load_app_config()

    def test_teams_directory_not_exists(self, tmp_path: Path) -> None:
        """teamsディレクトリが存在しない場合のエラーテスト."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        # teams ディレクトリを作成しない

        config_loader = ConfigLoader(config_dir)

        with pytest.raises(ConfigurationError, match="チーム設定ディレクトリが存在しません"):
            config_loader.get_available_teams()


class TestTeamConfigManagerErrorHandling:
    """TeamConfigManager error handling tests."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """テスト用の一時設定ディレクトリを作成."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        teams_dir = config_dir / "teams"
        teams_dir.mkdir()
        return config_dir

    def test_load_team_config_file_not_found(self, temp_config_dir: Path) -> None:
        """存在しないチーム設定ファイルの読み込みエラーテスト."""
        config_loader = ConfigLoader(temp_config_dir)
        team_config_manager = TeamConfigManager(config_loader)

        with pytest.raises(ConfigurationError, match="ファイルが存在しません"):
            team_config_manager.load_team("nonexistent_team")

    def test_load_team_yaml_syntax_error(self, temp_config_dir: Path) -> None:
        """YAMLファイルの構文エラーテスト."""
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "broken_team.yaml"

        # 不正なYAMLを書き込み
        team_config_path.write_text("invalid: yaml: [broken")

        config_loader = ConfigLoader(temp_config_dir)
        team_config_manager = TeamConfigManager(config_loader)

        with pytest.raises(ConfigurationError, match="YAML 構文エラー"):
            team_config_manager.load_team("broken_team")

    def test_load_all_teams_configuration_error_propagation(self, temp_config_dir: Path) -> None:
        """load_all_teamsでの設定エラー伝播テスト."""
        teams_dir = temp_config_dir / "teams"

        # 正常なチーム設定
        team_a_config = {"team": {"id": "team_a", "name": "チームA"}}
        team_a_path = teams_dir / "team_a.yaml"
        with team_a_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_a_config, f)

        # 不正なチーム設定（必須フィールド不足）
        team_b_config = {"team": {"id": "team_b"}}  # name フィールド不足
        team_b_path = teams_dir / "team_b.yaml"
        with team_b_path.open("w", encoding="utf-8") as f:
            yaml.dump(team_b_config, f)

        config_loader = ConfigLoader(temp_config_dir)
        team_config_manager = TeamConfigManager(config_loader)

        # 不正な設定により全体の読み込みがエラーになることを確認
        with pytest.raises(ConfigurationError, match="必須フィールドが不足または空です"):
            team_config_manager.load_all_teams()

    def test_load_team_data_format_configuration_error_propagation(self, temp_config_dir: Path) -> None:
        """データフォーマット読み込みでの設定エラー伝播テスト."""
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "error_team.yaml"

        # 不正なYAMLファイルを作成
        team_config_path.write_text("invalid yaml content: [")

        config_loader = ConfigLoader(temp_config_dir)
        team_config_manager = TeamConfigManager(config_loader)

        with pytest.raises(ConfigurationError, match="YAML 構文エラー"):
            team_config_manager.load_team_data_format("error_team")

    def test_load_team_calculation_rules_configuration_error_propagation(self, temp_config_dir: Path) -> None:
        """計算ルール読み込みでの設定エラー伝播テスト."""
        teams_dir = temp_config_dir / "teams"
        team_config_path = teams_dir / "error_team.yaml"

        # 不正なYAMLファイルを作成
        team_config_path.write_text("invalid yaml content: [")

        config_loader = ConfigLoader(temp_config_dir)
        team_config_manager = TeamConfigManager(config_loader)

        with pytest.raises(ConfigurationError, match="YAML 構文エラー"):
            team_config_manager.load_team_calculation_rules("error_team")

    def test_team_config_manager_default_config_loader(self) -> None:
        """デフォルトのConfigLoaderでのTeamConfigManager初期化テスト."""
        # デフォルトコンストラクタでConfigLoaderが作成されることを確認
        team_config_manager = TeamConfigManager()

        if team_config_manager.config_loader is None:
            msg = "Expected config_loader to be created"
            raise AssertionError(msg)
        if not isinstance(team_config_manager.config_loader, ConfigLoader):
            msg = f"Expected ConfigLoader instance, got {type(team_config_manager.config_loader)}"
            raise AssertionError(msg)  # noqa: TRY004
