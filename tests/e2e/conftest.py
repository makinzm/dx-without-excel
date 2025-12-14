"""E2Eテスト用の設定ファイル."""
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Browser:
    """ブラウザセッションを開始."""
    return playwright.chromium.launch()


@pytest.fixture(scope="session")
def context(browser: Browser) -> BrowserContext:
    """ブラウザコンテキストを作成."""
    return browser.new_context()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    """ページを作成."""
    return context.new_page()
