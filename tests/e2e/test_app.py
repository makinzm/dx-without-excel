"""E2Eテスト用ファイル."""
import os
import re

from playwright.sync_api import Page, expect

# グローバル定数
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8501")


class TestTeamSelectionUI:
    """チーム選択UIのE2Eテスト."""

    def test_ページが正しく表示される(self, page: Page) -> None:  # noqa: N802, PLC2401
        """ページタイトルとヘッダーが表示される."""
        page.goto(BASE_URL)

        # タイトル確認
        expect(page).to_have_title(re.compile("Excel DX 設定管理"))

        # ヘッダー確認
        expect(page.get_by_role("heading", name="📊 Excel DX 設定管理システム")).to_be_visible()

    def test_sidebar_has_team_selection(self, page: Page) -> None:
        """サイドバーにチーム選択UIが表示される."""
        page.goto(BASE_URL)

        # サイドバーのタイトル
        expect(page.get_by_text("🏢 チーム選択")).to_be_visible()

        # セレクトボックスが表示される
        # Streamlitのセレクトボックスは data-testid="stSelectbox" で識別可能
        selectbox = page.locator('[data-testid="stSelectbox"]').first
        expect(selectbox).to_be_visible()

    def test_has_new_team_creation_button(self, page: Page) -> None:
        """新規チーム作成ボタンが表示される."""
        page.goto(BASE_URL)

        create_button = page.get_by_role("button", name="新規チーム作成")
        expect(create_button).to_be_visible()

    def test_four_tabs_are_displayed(self, page: Page) -> None:
        """4つのタブが表示される."""
        page.goto(BASE_URL)

        expect(page.get_by_role("tab", name="📋 チーム設定")).to_be_visible()
        expect(page.get_by_role("tab", name="📊 データフォーマット")).to_be_visible()
        expect(page.get_by_role("tab", name="🧮 計算ルール")).to_be_visible()
        expect(page.get_by_role("tab", name="🔄 Git連携")).to_be_visible()

class TestNewTeamCreationFlow:
    """新規チーム作成のE2Eテスト."""

    def test_new_team_creation_form_displays(self, page: Page) -> None:
        """新規チーム作成ボタンをクリックするとフォームが表示される."""
        page.goto(BASE_URL)

        # 新規作成ボタンをクリック
        page.get_by_role("button", name="新規チーム作成").click()

        # フォームが表示される
        expect(page.get_by_role("heading", name="新規チーム作成")).to_be_visible()

        # 入力フィールドが表示される
        expect(page.get_by_placeholder("team_c")).to_be_visible()
        expect(page.get_by_placeholder("営業チームC")).to_be_visible()
    def test_can_create_team(self, page: Page) -> None:
        """チーム情報を入力して保存できる."""
        page.goto(BASE_URL)

        # 新規作成フォームを開く
        page.get_by_role("button", name="新規チーム作成").click()

        # フォームに入力
        page.get_by_placeholder("team_c").fill("team_test")
        page.get_by_placeholder("営業チームC").fill("テストチーム")
        page.get_by_placeholder("このチームの説明").fill("E2Eテスト用チーム")

        # 保存ボタンをクリック
        page.get_by_role("button", name="💾 保存").click()

        # 成功メッセージが表示される
        success_msg = page.get_by_text("✅ チーム 'テストチーム' を作成しました")
        expect(success_msg).to_be_visible()

    def test_error_when_required_fields_empty(self, page: Page) -> None:
        """チームIDまたは名前が空の場合エラーメッセージが表示される."""
        page.goto(BASE_URL)
        page.get_by_role("button", name="新規チーム作成").click()
        # 何も入力せずに保存
        page.get_by_role("button", name="💾 保存").click()
        # エラーメッセージが表示される
        error_msg = page.get_by_text("チームIDとチーム名は必須です")
        expect(error_msg).to_be_visible()

    def test_cancel_button_closes_form(self, page: Page) -> None:
        """キャンセルボタンでフォームが閉じる."""
        page.goto(BASE_URL)
        page.get_by_role("button", name="新規チーム作成").click()
        # フォームが表示されていることを確認
        form_heading = page.get_by_role("heading", name="新規チーム作成")
        expect(form_heading).to_be_visible()
        # キャンセルボタンをクリック
        page.get_by_role("button", name="❌ キャンセル").click()
        # フォームが閉じる
        expect(form_heading).not_to_be_visible()
class TestTeamDetailDisplay:
    """チーム詳細表示のE2Eテスト."""

    def test_team_details_display_when_selected(self, page: Page) -> None:
        """チームを選択すると詳細が表示される."""
        page.goto(BASE_URL)
        # 初期状態でteam_aが選択されている想定
        # チーム名がヘッダーに表示される
        team_heading = page.get_by_role("heading", name="📋 営業チームA")
        expect(team_heading).to_be_visible()
        # チームIDが表示される
        expect(page.get_by_text("チームID")).to_be_visible()
        expect(page.get_by_text("team_a")).to_be_visible()
class TestTabSwitching:
    """タブ切り替えのE2Eテスト."""

    def test_can_switch_to_data_format_tab(self, page: Page) -> None:
        """データフォーマットタブをクリックすると内容が表示される."""
        page.goto(BASE_URL)

        # データフォーマットタブをクリック
        page.get_by_role("tab", name="📊 データフォーマット").click()
        # タブの内容が表示される
        format_heading = page.get_by_role(
            "heading", name="📊 データフォーマット設定",
        )
        expect(format_heading).to_be_visible()

    def test_can_switch_to_calculation_rules_tab(self, page: Page) -> None:
        """計算ルールタブをクリックすると内容が表示される."""
        page.goto(BASE_URL)
        page.get_by_role("tab", name="🧮 計算ルール").click()
        calc_heading = page.get_by_role("heading", name="🧮 計算ルール設定")
        expect(calc_heading).to_be_visible()
        expect(page.get_by_text("🧮 計算ルール設定")).to_be_visible()

    def test_can_switch_to_git_integration_tab(self, page: Page) -> None:
        """Git連携タブをクリックすると内容が表示される."""
        page.goto(BASE_URL)

        page.get_by_role("tab", name="🔄 Git連携").click()

        git_heading = page.get_by_role("heading", name="🔄 Git連携")
        expect(git_heading).to_be_visible()
        expect(page.get_by_text("TODO: Git連携機能")).to_be_visible()
