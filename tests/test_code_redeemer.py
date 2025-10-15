from unittest.mock import Mock, patch
from code_redeemer import redeem_code


class TestCodeRedeemer:
    """Test cases for SHiFT code redemption functionality."""

    def test_redeem_code_success(self):
        """Test successful code redemption."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = "Congratulations! Code redeemed successfully!"
        mock_session.post.return_value = mock_response

        result = redeem_code(mock_session, "TEST123")
        assert result == "redeemed"
        mock_session.post.assert_called_once()

    def test_redeem_code_used(self):
        """Test redemption of already used code."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = "This code has already been used."
        mock_session.post.return_value = mock_response

        result = redeem_code(mock_session, "USED123")
        assert result == "used"

    def test_redeem_code_invalid(self):
        """Test redemption of invalid code."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = "Invalid code provided."
        mock_session.post.return_value = mock_response

        result = redeem_code(mock_session, "INVALID")
        assert result == "invalid"

    def test_redeem_code_expired(self):
        """Test redemption of expired code."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = "This code has expired."
        mock_session.post.return_value = mock_response

        result = redeem_code(mock_session, "EXPIRED123")
        assert result == "expired"

    def test_redeem_code_network_error(self):
        """Test handling of network/request errors."""
        mock_session = Mock()
        mock_session.post.side_effect = Exception("Network timeout")

        result = redeem_code(mock_session, "TEST123")
        assert result == "failed"

    def test_redeem_code_unexpected_response(self):
        """Test handling of unexpected server responses."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = "Some unexpected response from server"
        mock_session.post.return_value = mock_response

        result = redeem_code(mock_session, "TEST123")
        assert result == "unknown"

    @patch("code_redeemer.logger")
    def test_redeem_code_logs_errors(self, mock_logger):
        """Test that errors are properly logged."""
        mock_session = Mock()
        mock_session.post.side_effect = Exception("Connection failed")

        result = redeem_code(mock_session, "TEST123")

        assert result == "failed"
        mock_logger.error.assert_called_once()

    def test_redeem_code_case_insensitive_matching(self):
        """Test that response matching is case insensitive."""
        test_cases = [
            ("SUCCESS! CODE REDEEMED", "redeemed"),
            ("Code has been USED", "used"),
            ("Code has EXPIRED", "expired"),
            ("INVALID code entered", "invalid"),
        ]

        for response_text, expected_result in test_cases:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.text = response_text
            mock_session.post.return_value = mock_response

            result = redeem_code(mock_session, "TEST123")
            assert result == expected_result, f"Failed for response: {response_text}"
