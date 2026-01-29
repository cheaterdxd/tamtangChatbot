import itertools
import time
from src.chat_bot_in_API_mode import config

class KeyManager:
    def __init__(self):
        self.keys = config.GOOGLE_API_KEYS
        if not self.keys:
            raise ValueError("No API keys available.")
        
        self._key_cycle = itertools.cycle(self.keys)
        self.current_key = next(self._key_cycle)
        self.key_usage = {k: 0 for k in self.keys}

    def get_current_key(self):
        return self.current_key

    def switch_key(self):
        """Rotates to the next available API key."""
        old_key = self.current_key
        self.current_key = next(self._key_cycle)
        print(f"⚠️ Switching API Key: ...{old_key[-4:]} -> ...{self.current_key[-4:]}")
        # Optional: Add a small delay to ensure the new key isn't hit immediately in a tight loop
        time.sleep(1)
        return self.current_key

    def report_usage(self):
        self.key_usage[self.current_key] += 1

key_manager = KeyManager()
