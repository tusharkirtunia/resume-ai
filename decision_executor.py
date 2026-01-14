from collections import defaultdict

class DecisionExecutor:
    """
    Applies bullet-level decisions using confirmation thresholds.
    """

    def __init__(self, min_confirmations: int = 2):
        self.min_confirmations = min_confirmations
        self.confirmation_counts = defaultdict(int)

    def process(self, decisions: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Returns (actions_to_apply, actions_deferred)
        """
        actions_to_apply = []
        actions_deferred = []

        for decision in decisions:
            key = (
                decision["experience_index"],
                decision["bullet_index"],
                decision["action"]
            )

            self.confirmation_counts[key] += 1

            if self.confirmation_counts[key] >= self.min_confirmations:
                actions_to_apply.append(decision)
            else:
                actions_deferred.append(decision)

        return actions_to_apply, actions_deferred