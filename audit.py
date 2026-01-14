import json
import time
from pathlib import Path

AUDIT_FILE = Path("audit_log.json")


def load_audit_log():
    if not AUDIT_FILE.exists():
        return []
    return json.loads(AUDIT_FILE.read_text())


def append_audit_entry(entry: dict):
    history = load_audit_log()
    history.append(entry)
    AUDIT_FILE.write_text(json.dumps(history, indent=2))


def latest_audit():
    history = load_audit_log()
    return history[-1] if history else None