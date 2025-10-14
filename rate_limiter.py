import time
import random


class RateLimiter:
    def __init__(self, min_delay=2.0, max_delay=30.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.delay = min_delay

    def wait(self):
        jitter = random.uniform(0, 0.3 * self.delay)
        time.sleep(self.delay + jitter)

    def increase(self):
        self.delay = min(self.delay * 2, self.max_delay)

    def reset(self):
        self.delay = self.min_delay
