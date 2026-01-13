from flask import Flask, jsonify, request, send_from_directory
from storage import load_state, save_state
from state import initial_state
from editor import update_bullet
from rewriter import rewrite_bullet
import json

app = Flask(__name__)

# ---------- STATE INITIALIZATION ----------

state = load_state() or initial_state()

def get_active_resume():
    active = state["active_variant"]
    return state["variants"][active]

# ---------- BASIC HEALTH CHECK ----------

@app.route("/")
def home():
    return "Backend is alive"

# ---------- RESUME READ ----------

@app.route("/api/resume", methods=["GET"])
def get_resume():
    active = state["active_variant"]
    resume = state["variants"][active]
    return jsonify(resume)

# ---------- RESUME SAVE ----------

@app.route("/api/resume", methods=["POST"])
def save_resume():
    payload = request.get_json()

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid payload"}), 400

    active = state["active_variant"]
    state["variants"][active] = payload
    save_state(state)

    return jsonify({"status": "saved"})

# ---------- BULLET UPDATE ----------

@app.route("/api/resume/bullet", methods=["POST"])
def update_bullet_api():
    payload = request.get_json()

    exp_index = payload.get("exp_index")
    bullet_index = payload.get("bullet_index")
    text = payload.get("text")

    if not (
        isinstance(exp_index, int)
        and isinstance(bullet_index, int)
        and isinstance(text, str)
    ):
        return jsonify({"error": "Invalid input"}), 400

    resume = get_active_resume()
    updated = update_bullet(resume, exp_index, bullet_index, text)

    if updated is None:
        return jsonify({"error": "Update failed"}), 400

    active = state["active_variant"]
    state["variants"][active] = updated
    save_state(state)

    return jsonify({"status": "updated"})

# ---------- CREATE NEW VARIANT ----------

@app.route("/api/variant", methods=["POST"])
def create_variant():
    payload = request.get_json()
    name = payload.get("name")

    if not name or name in state["variants"]:
        return jsonify({"error": "Invalid or duplicate name"}), 400

    base = state["variants"]["base"]
    clone = json.loads(json.dumps(base))  # deep copy

    state["variants"][name] = clone
    state["active_variant"] = name
    save_state(state)

    return jsonify({"status": "created", "active": name})

# ---------- LIST VARIANTS ----------

@app.route("/api/variants", methods=["GET"])
def list_variants():
    return jsonify({
        "active": state["active_variant"],
        "variants": list(state["variants"].keys())
    })

# ---------- ACTIVATE VARIANT ----------

@app.route("/api/variant/activate", methods=["POST"])
def activate_variant():
    payload = request.get_json()
    name = payload.get("name")

    if name not in state["variants"]:
        return jsonify({"error": "Variant not found"}), 404

    state["active_variant"] = name
    save_state(state)

    return jsonify({"active": name})

# ---------- REWRITE BULLET ----------

@app.route("/api/rewrite", methods=["POST"])
def rewrite_api():
    payload = request.get_json()

    bullet = payload.get("bullet")
    job = payload.get("job")

    if not isinstance(bullet, str) or not isinstance(job, str):
        return jsonify({"error": "Invalid input"}), 400

    rewritten = rewrite_bullet(bullet, job)
    return jsonify({"rewritten": rewritten})

# ---------- STATIC UI ----------

@app.route("/ui")
def ui():
    return send_from_directory(".", "index.html")

# ---------- RUN ----------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)