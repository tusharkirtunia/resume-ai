import json
from pathlib import Path
from typing import Dict, Any, List

METRICS_FILE = Path("metrics_history.json")


def load_metrics() -> List[Dict[str, Any]]:
    if not METRICS_FILE.exists():
        return []
    with open(METRICS_FILE, "r") as f:
        return json.load(f)


def save_run_metrics(run_metrics: Dict[str, Any]) -> None:
    history = load_metrics()
    history.append(run_metrics)
    with open(METRICS_FILE, "w") as f:
        json.dump(history, f, indent=2)


def aggregate_metrics() -> Dict[str, Any]:
    history = load_metrics()
    if not history:
        return {
            "runs": 0,
            "total_score_gain": 0.0,
            "average_gain_per_run": 0.0,
            "change_type_effectiveness": {},
        }

    total_gain = 0.0
    change_effects = {}

    for run in history:
        gain = run.get("net_score_gain", 0.0)
        total_gain += gain

        for change_type, count in run.get("change_types", {}).items():
            change_effects[change_type] = change_effects.get(change_type, 0) + count

    return {
        "runs": len(history),
        "total_score_gain": round(total_gain, 4),
        "average_gain_per_run": round(total_gain / len(history), 4),
        "change_type_effectiveness": change_effects,
    }