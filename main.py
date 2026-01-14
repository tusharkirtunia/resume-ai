from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import statistics
import os
import sys

# ---------------------------------------------------------
# APP INIT (FIXED: SINGLE INITIALIZATION)
# ---------------------------------------------------------

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

# ---------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------

from storage import load_state, save_state
from state import initial_state
from editor import update_bullet
from scoring import score_resume, bullet_impact_scores
from metrics import MetricsStore
from metrics_aggregator import load_metrics, aggregate_metrics

metrics = MetricsStore()

# ---------------------------------------------------------
# CONSTANTS (DEPLOYMENT SAFETY)
# ---------------------------------------------------------

MAX_BULLETS = 50  # Free-tier safety guard

# ---------------------------------------------------------
# STATE LOAD + FAIL-FAST VALIDATION
# ---------------------------------------------------------

state = load_state() or initial_state()

def validate_state_or_die(state: dict):
    if not isinstance(state, dict):
        raise RuntimeError("State is not a dict")

    if "active_variant" not in state:
        raise RuntimeError("active_variant missing")

    if "variants" not in state or not isinstance(state["variants"], dict):
        raise RuntimeError("variants missing or invalid")

    if "base" not in state["variants"]:
        raise RuntimeError("base variant missing")

    active = state["active_variant"]
    if active not in state["variants"]:
        raise RuntimeError(f"active_variant '{active}' not found")

validate_state_or_die(state)

# ---------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------

def normalize_resume(payload):
    resume = {
        "id": payload.get("id", state["active_variant"]),
        "summary": payload.get("summary", ""),
        "experience": []
    }

    for i, exp in enumerate(payload.get("experience", [])):
        resume["experience"].append({
            "id": exp.get("id", f"exp_{i}"),
            "company": exp.get("company", ""),
            "role": exp.get("role", ""),
            "bullets": [
                b for b in exp.get("bullets", [])
                if isinstance(b, str) and b.strip()
            ]
        })

    return resume

def validate_resume(resume):
    if not isinstance(resume, dict):
        return False
    experience = resume.get("experience")
    if not isinstance(experience, list):
        return False
    for exp in experience:
        if not isinstance(exp, dict):
            return False
        bullets = exp.get("bullets")
        if not isinstance(bullets, list):
            return False
        if not all(isinstance(b, str) for b in bullets):
            return False
    return True

def guard_resume_size(resume):
    total = sum(len(e.get("bullets", [])) for e in resume.get("experience", []))
    if total > MAX_BULLETS:
        raise RuntimeError("Resume too large for free-tier deployment")

def get_active_resume():
    return state["variants"][state["active_variant"]]

def ensure_not_base():
    if state["active_variant"] == "base":
        return jsonify({"error": "Base resume is read-only"}), 403
    return None

def is_dry_run(payload):
    return payload.get("dry_run", False) is True

# ---------------------------------------------------------
# BULLET DECISION LOGIC
# ---------------------------------------------------------

def make_bullet_decisions(impacts):
    scores = [i["impact"] for i in impacts]
    if not scores:
        return []

    mean = statistics.mean(scores)
    std = statistics.pstdev(scores) if len(scores) > 1 else 0.0

    high = mean + 0.5 * std
    low = mean - 0.5 * std

    decisions = []
    for item in impacts:
        impact = item["impact"]
        if impact >= high:
            action = "KEEP"
        elif impact <= low:
            action = "REMOVE"
        else:
            action = "REVIEW"

        decisions.append({
            "experience_index": item["experience_index"],
            "bullet_index": item["bullet_index"],
            "bullet": item["bullet"],
            "impact": impact,
            "action": action
        })
    return decisions

def build_execution_plan(decisions):
    plan = {"KEEP": [], "REVIEW": [], "REMOVE": []}
    for d in decisions:
        plan[d["action"]].append(d)
    return plan

def apply_removals(resume, decisions):
    updated = json.loads(json.dumps(resume))
    removals = [d for d in decisions if d["action"] == "REMOVE"]

    for d in sorted(removals, key=lambda x: (x["experience_index"], x["bullet_index"]), reverse=True):
        try:
            updated["experience"][d["experience_index"]]["bullets"].pop(d["bullet_index"])
        except (IndexError, KeyError):
            continue
    return updated

# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.route("/")
def home():
    return "Backend is alive"

# ---------------------------------------------------------
# RESUME
# ---------------------------------------------------------

@app.route("/api/resume", methods=["GET"])
def get_resume():
    return jsonify(get_active_resume())

@app.route("/api/resume", methods=["POST"])
def save_resume_api():
    guard = ensure_not_base()
    if guard:
        return guard

    payload = request.get_json()
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid resume"}), 400

    normalized = normalize_resume(payload)
    guard_resume_size(normalized)

    state["variants"][state["active_variant"]] = normalized
    save_state(state)
    return jsonify({"status": "saved"})

@app.route("/api/resume/bullet", methods=["POST"])
def update_bullet_api():
    guard = ensure_not_base()
    if guard:
        return guard

    payload = request.get_json()
    exp_i = payload.get("exp_index")
    b_i = payload.get("bullet_index")
    text = payload.get("text")

    if not all(isinstance(x, int) for x in [exp_i, b_i]) or not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Invalid input"}), 400

    resume = get_active_resume()
    updated = update_bullet(resume, exp_i, b_i, text)
    if updated is None:
        return jsonify({"error": "Update failed"}), 400

    state["variants"][state["active_variant"]] = updated
    save_state(state)
    return jsonify({"status": "updated"})

# ---------------------------------------------------------
# VARIANTS
# ---------------------------------------------------------

@app.route("/api/variant", methods=["POST"])
def create_variant():
    name = request.get_json().get("name")
    if not name or name in state["variants"]:
        return jsonify({"error": "Invalid name"}), 400

    state["variants"][name] = json.loads(json.dumps(state["variants"]["base"]))
    state["active_variant"] = name
    save_state(state)
    return jsonify({"status": "created", "active": name})

@app.route("/api/variant/activate", methods=["POST"])
def activate_variant():
    name = request.get_json().get("name")
    if name not in state["variants"]:
        return jsonify({"error": "Not found"}), 404

    state["active_variant"] = name
    save_state(state)
    return jsonify({"active": name})

@app.route("/api/variants", methods=["GET"])
def list_variants():
    return jsonify({
        "variants": list(state["variants"].keys()),
        "active": state["active_variant"]
    })

# ---------------------------------------------------------
# SCORING + DECISIONS
# ---------------------------------------------------------

@app.route("/api/variant/score", methods=["POST"])
def score_variant():
    job = request.get_json().get("job", "").strip()
    if not job:
        return jsonify({"error": "Invalid job"}), 400

    base = state["variants"]["base"]
    variant = get_active_resume()
    guard_resume_size(variant)

    return jsonify({
        "variant": state["active_variant"],
        "base_score": score_resume(base, job),
        "variant_score": score_resume(variant, job),
        "improvement": score_resume(variant, job) - score_resume(base, job)
    })

@app.route("/api/variant/bullet-impact", methods=["POST"])
def bullet_impact_api():
    job = request.get_json().get("job", "").strip()
    resume = get_active_resume()
    guard_resume_size(resume)

    return jsonify({
        "variant": state["active_variant"],
        "impacts": bullet_impact_scores(resume, job)
    })

@app.route("/api/variant/bullet-decisions", methods=["POST"])
def bullet_decisions_api():
    job = request.get_json().get("job", "").strip()
    resume = get_active_resume()
    guard_resume_size(resume)

    impacts = bullet_impact_scores(resume, job)
    return jsonify({
        "variant": state["active_variant"],
        "decisions": make_bullet_decisions(impacts)
    })

@app.route("/api/variant/apply-removals", methods=["POST"])
def apply_removals_api():
    guard = ensure_not_base()
    if guard:
        return guard

    payload = request.get_json()
    job = payload.get("job", "").strip()
    confirm = payload.get("confirm", False)

    if not confirm:
        return jsonify({"error": "confirm=true required"}), 400

    resume = get_active_resume()
    guard_resume_size(resume)

    impacts = bullet_impact_scores(resume, job)
    decisions = make_bullet_decisions(impacts)
    updated = apply_removals(resume, decisions)

    if is_dry_run(payload):
        return jsonify({"status": "dry-run"})

    state["variants"][state["active_variant"]] = updated
    save_state(state)
    return jsonify({"status": "applied"})

# ---------------------------------------------------------
# METRICS
# ---------------------------------------------------------

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    return jsonify(metrics.summary())

@app.route("/api/metrics/latest", methods=["GET"])
def latest_metrics():
    history = load_metrics()
    if not history:
        return jsonify({"error": "No metrics"}), 404
    return jsonify(history[-1])

@app.route("/api/metrics/aggregate", methods=["GET"])
def aggregate():
    return jsonify(aggregate_metrics())

# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)