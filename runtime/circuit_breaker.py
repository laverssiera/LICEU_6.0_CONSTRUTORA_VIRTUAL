# Circuit Breaker por monólito
import time

class CircuitBreaker:
    def __init__(self, threshold=0.1, window=60):
        self.threshold = threshold  # taxa de erro
        self.window = window  # segundos
        self.failures = []
        self.disabled = False
        self.disabled_at = None

    def record_failure(self):
        now = time.time()
        self.failures = [t for t in self.failures if now - t < self.window]
        self.failures.append(now)
        if self.error_rate() > self.threshold:
            self.disabled = True
            self.disabled_at = now
            print("[CIRCUIT BREAKER] Monólito desabilitado por alta taxa de erro!")

    def record_success(self):
        now = time.time()
        self.failures = [t for t in self.failures if now - t < self.window]
        if self.disabled and self.error_rate() <= self.threshold:
            self.disabled = False
            print("[CIRCUIT BREAKER] Monólito reabilitado!")

    def error_rate(self):
        return len(self.failures) / self.window

    def is_disabled(self):
        return self.disabled
