from typing import List, Dict, Any
import re


def classify_change(old: str, new: str) -> str:
    if len(new) > len(old):
        return "Expanded detail"
    if "%" in new or any(ch.isdigit() for ch in new):
        return "Added quantification"
    if re.search(r"\b(led|owned|designed|built)\b", new.lower()):
        return "Stronger ownership signal"
    return "Clarity rewrite"


def build_improvement_report(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {
        "total_changes": len(history),
        "net_score_gain": 0.0,
        "change_types": {},
        "changes": [],
    }

    for h in history:
        delta = h.get("delta", 0.0)
        summary["net_score_gain"] += delta

        reason = classify_change(h["old"], h["new"])
        summary["change_types"][reason] = summary["change_types"].get(reason, 0) + 1

        summary["changes"].append(
            {
                "bullet_index": h["bullet_index"],
                "before": h["old"],
                "after": h["new"],
                "delta": round(delta, 4),
                "reason": reason,
            }
        )

    summary["net_score_gain"] = round(summary["net_score_gain"], 4)
    return summary