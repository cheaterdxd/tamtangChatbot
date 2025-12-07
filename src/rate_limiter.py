import time
import functools
from src import config

class RateLimiter:
    def __init__(self, rpm=config.RPM_LIMIT, tpm=config.TPM_LIMIT):
        self.rpm = rpm
        self.tpm = tpm
        
        self.request_timestamps = []
        self.token_timestamps = [] # List of (timestamp, token_count)

    def _cleanup_old_timestamps(self):
        now = time.time()
        # Keep only timestamps within the last 60 seconds
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]
        self.token_timestamps = [(t, c) for t, c in self.token_timestamps if now - t < 60]

    def wait_if_needed(self, estimated_tokens=0):
        """Pauses execution if limits are reached."""
        while True:
            self._cleanup_old_timestamps()
            
            # Check RPM
            if len(self.request_timestamps) >= self.rpm:
                sleep_time = 1.0 # Simple wait logic
                print(f"⏳ Rate Limit (RPM): Waiting {sleep_time}s...")
                time.sleep(sleep_time)
                continue
            
            # Check TPM
            current_tokens = sum(c for _, c in self.token_timestamps)
            if current_tokens + estimated_tokens > self.tpm:
                sleep_time = 1.0
                print(f"⏳ Rate Limit (TPM): Waiting {sleep_time}s...")
                time.sleep(sleep_time)
                continue
                
            break
            
    def record_request(self, tokens=0):
        now = time.time()
        self.request_timestamps.append(now)
        self.token_timestamps.append((now, tokens))

rate_limiter = RateLimiter()

def limit_rate(estimated_tokens=0):
    """Decorator to apply rate limiting."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            rate_limiter.wait_if_needed(estimated_tokens)
            result = func(*args, **kwargs)
            # Roughly estimate tokens if not provided or refine after call?
            # For simplicity, we record the estimated tokens upfront or 0.
            rate_limiter.record_request(estimated_tokens)
            return result
        return wrapper
    return decorator
