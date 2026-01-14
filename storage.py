import json
import os
from schema import validate_state

STATE_FILE = "resume_state.json"
TMP_FILE = "resume_state.tmp"


def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

        if not validate_state(state):
            print("Invalid state file detected. Ignoring.")
            return None

        return state

    except Exception as e:
        print("Failed to load state:", e)
        return None


def save_state(state):
    if not validate_state(state):
        raise ValueError("Attempted to save invalid state")

    try:
        with open(TMP_FILE, "w") as f:
            json.dump(state, f, indent=2)

        os.replace(TMP_FILE, STATE_FILE)

    except Exception as e:
        print("Failed to save state:", e)
        raise