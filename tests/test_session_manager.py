import pytest
from unittest.mock import Mock, patch
from session_manager import (
    get_session_with_retry,
    refresh_cookies,
    get_session,
    verify_login,
)


class TestSessionManager:
    """Test cases for session management functionality."""

    def test_get_session_with_retry_config(self):
        """Test that session is configured with retry strategy."""
        session = get_session_with_retry()

        # Check that session has proper configuration
        assert session is not None
        assert len(session.adapters) > 0  # Should have adapters configured

        # Check headers are set
        assert "User-Agent" in session.headers

    @patch("session_manager.sync_playwright")
    @patch("session_manager.config")
    def test_refresh_cookies_basic(self, mock_config, mock_playwright):
        """Test basic cookie refresh functionality."""
        # Mock config to disable encryption
        mock_config.ENCRYPT_COOKIES = False
        mock_config.SECRET_KEY = ""
        mock_config.LOGIN_URL = "https://example.com/login"
        mock_config.PLAYWRIGHT_TIMEOUT = 5000
        mock_config.COOKIES_FILE = "cookies.json"

        # Mock playwright components
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()
        mock_cookies = [
            {"name": "session_id", "value": "abc123", "domain": "example.com"}
        ]

        mock_context.cookies.return_value = mock_cookies
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_p = Mock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_p

        with patch("session_manager.save_json") as mock_save:
            refresh_cookies()

            # Verify playwright interactions
            mock_p.chromium.launch.assert_called_once_with(headless=False)
            mock_context.new_page.assert_called_once()
            mock_page.goto.assert_called_once()
            mock_page.wait_for_timeout.assert_called_once()

            # Verify cookies were saved
            mock_save.assert_called_once_with("cookies.json", mock_cookies)

    @patch("session_manager.os.path.exists")
    @patch("session_manager.load_json")
    def test_get_session_existing_cookies(self, mock_load, mock_exists):
        """Test getting session with existing cookies."""
        mock_exists.return_value = True
        mock_cookies = [
            {"name": "session_id", "value": "abc123", "domain": "example.com"}
        ]
        mock_load.return_value = mock_cookies

        session = get_session()

        # Verify cookies were loaded and set
        assert session is not None
        # Check that cookies were set
        # (this would require more detailed mocking)

    @patch("session_manager.os.path.exists")
    def test_get_session_no_cookies_triggers_refresh(self, mock_exists):
        """Test that missing cookies triggers refresh."""
        mock_exists.return_value = False

        with patch("session_manager.refresh_cookies") as mock_refresh:
            with patch("session_manager.load_json") as mock_load:
                mock_load.return_value = []

                # Call get_session which should trigger refresh
                # when no cookies exist
                get_session()

                # Verify refresh was called
                mock_refresh.assert_called_once()

    def test_verify_login_success(self):
        """Test successful login verification."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = "Welcome back! Dashboard content here"
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        result = verify_login(mock_session)
        assert result is True

    def test_verify_login_not_logged_in(self):
        """Test login verification when not logged in."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = "Please Sign In to continue"
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response

        result = verify_login(mock_session)
        assert result is False

    def test_verify_login_request_failure(self):
        """Test login verification with network errors."""
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Network error")

        result = verify_login(mock_session)
        assert result is False

    @patch("session_manager.config")
    def test_encryption_enabled_validation(self, mock_config):
        """Test that encryption validation works."""
        mock_config.ENCRYPT_COOKIES = True
        mock_config.SECRET_KEY = ""

        with pytest.raises(ValueError, match="SHIFT_SECRET_KEY"):
            refresh_cookies()

    @patch("session_manager.config")
    def test_encryption_validation(self, mock_config):
        """Test that encryption validation works."""
        mock_config.ENCRYPT_COOKIES = True
        mock_config.SECRET_KEY = ""

        with pytest.raises(ValueError, match="SHIFT_SECRET_KEY"):
            refresh_cookies()
