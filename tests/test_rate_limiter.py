from unittest.mock import patch
from rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for rate limiting functionality."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with correct defaults."""
        limiter = RateLimiter()
        assert limiter.min_delay == 2.0
        assert limiter.max_delay == 30.0
        assert limiter.delay == 2.0

    def test_rate_limiter_custom_values(self):
        """Test rate limiter with custom values."""
        limiter = RateLimiter(min_delay=1.0, max_delay=10.0)
        assert limiter.min_delay == 1.0
        assert limiter.max_delay == 10.0
        assert limiter.delay == 1.0

    @patch("time.sleep")
    def test_wait_function(self, mock_sleep):
        """Test that wait function sleeps for correct duration."""
        limiter = RateLimiter(min_delay=5.0, max_delay=10.0)

        limiter.wait()

        # Should sleep for delay ± jitter
        mock_sleep.assert_called_once()
        sleep_time = mock_sleep.call_args[0][0]
        assert 5.0 <= sleep_time <= 5.0 * 1.3  # Allow for 30% jitter

    def test_increase_delay(self):
        """Test that delay increases when rate limited."""
        limiter = RateLimiter(min_delay=1.0, max_delay=10.0)

        initial_delay = limiter.delay
        limiter.increase()
        assert limiter.delay == min(initial_delay * 2, limiter.max_delay)

    def test_increase_respects_max_delay(self):
        """Test that delay doesn't exceed maximum."""
        limiter = RateLimiter(min_delay=5.0, max_delay=8.0)

        # Increase multiple times
        limiter.increase()  # 10.0, but capped at 8.0
        assert limiter.delay == 8.0

        limiter.increase()  # Should stay at 8.0
        assert limiter.delay == 8.0

    def test_reset_delay(self):
        """Test that reset returns delay to minimum."""
        limiter = RateLimiter(min_delay=1.0, max_delay=10.0)

        limiter.increase()
        assert limiter.delay > 1.0

        limiter.reset()
        assert limiter.delay == 1.0

    def test_exponential_backoff_pattern(self):
        """Test the exponential backoff pattern works correctly."""
        limiter = RateLimiter(min_delay=1.0, max_delay=16.0)

        delays = []
        for _ in range(5):
            delays.append(limiter.delay)
            limiter.increase()

        expected_delays = [1.0, 2.0, 4.0, 8.0, 16.0]
        assert delays == expected_delays

    @patch("time.sleep")
    def test_wait_with_jitter(self, mock_sleep):
        """Test that wait includes random jitter."""
        limiter = RateLimiter(min_delay=10.0, max_delay=20.0)

        # Run multiple times to check jitter variation
        sleep_times = []
        for _ in range(10):
            limiter.wait()
            sleep_times.append(mock_sleep.call_args[0][0])
            mock_sleep.reset_mock()

        # Should have some variation (jitter)
        unique_times = set(sleep_times)
        assert len(unique_times) > 1, "Jitter should create variation in sleep times"

        # All times should be within expected range
        for sleep_time in sleep_times:
            assert 10.0 <= sleep_time <= 10.0 * 1.3
