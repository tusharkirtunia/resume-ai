# metrics.py

import time


class MetricsStore:
    def __init__(self):
        self.events = []

    def log(self, audit: dict):
        audit["timestamp"] = time.time()
        self.events.append(audit)

    def summary(self):
        total_runs = len(self.events)
        accepted = sum(1 for e in self.events if e.get("accepted"))

        return {
            "total_runs": total_runs,
            "accepted_runs": accepted,
            "accept_rate": accepted / total_runs if total_runs else 0.0
        }

    def history(self):
        return self.events