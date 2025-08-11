import time, asyncio, random, collections

class RateLimitedEndpoint:
    def __init__(self, api_name: str, capacity_per_second: int, latency_jitter=(0.02, 0.06)):
        self.api_name = api_name
        self.capacity_per_second = capacity_per_second
        self.request_timestamps = collections.deque()
        self.concurrent_lock = asyncio.Lock()
        self.latency_jitter = latency_jitter
        self.reject_count = 0
        self.accept_count = 0

    async def call(self, agent_id: str, payload: dict):
        """Return (ok, payload). ok=False on rate limit or internal error.
        Internal errors do NOT consume capacity in the current window.
        """
        async with self.concurrent_lock:
            now = time.time()
            while self.request_timestamps and now - self.request_timestamps[0] > 1.0:
                self.request_timestamps.popleft()
            if len(self.request_timestamps) >= self.capacity_per_second:
                self.reject_count += 1
                return False, {"error": "rate_limited", "api": self.api_name}
            self.request_timestamps.append(now)
        try:
            await asyncio.sleep(random.uniform(*self.latency_jitter))
            # attempt to hash payload; be robust to unhashable
            try:
                result_hash = hash((agent_id, frozenset(payload.items())))
            except Exception:
                result_hash = hash((agent_id, str(payload)))
            self.accept_count += 1
            return True, {"ok": True, "api": self.api_name, "result": result_hash}
        except Exception as e:
            # internal error path: do not increase accept_count, return structured error
            return False, {"error": "internal_error", "api": self.api_name, "message": str(e)}

class Environment:
    def __init__(self):
        self.apis = {
            "otp": RateLimitedEndpoint("otp", capacity_per_second=2),
            "cibil": RateLimitedEndpoint("cibil", capacity_per_second=1),
            "itr": RateLimitedEndpoint("itr", capacity_per_second=1),
            "vehicle": RateLimitedEndpoint("vehicle", capacity_per_second=3),
        }
