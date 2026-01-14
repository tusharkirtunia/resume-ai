from flask import Flask, jsonify, request
import json
import statistics

from storage import load_state, save_state
from state import initial_state
from editor import update_bullet
from scoring import score_resume, bullet_impact_scores
from metrics import MetricsStore
from metrics_aggregator import load_metrics, aggregate_metrics
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
metrics = MetricsStore()

# =========================================================
# STATE
# =========================================================

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

    for name, resume in state["variants"].items():
        if not isinstance(resume, dict):
            raise RuntimeError(f"Variant '{name}' is not a dict")

        exp = resume.get("experience")
        if not isinstance(exp, list):
            raise RuntimeError(f"Variant '{name}': experience must be list")

        for i, e in enumerate(exp):
            bullets = e.get("bullets")
            if not isinstance(bullets, list):
                raise RuntimeError(f"{name}.experience[{i}].bullets must be list")
            if not all(isinstance(b, str) and b.strip() for b in bullets):
                raise RuntimeError(f"{name}.experience[{i}].bullets invalid")

validate_state_or_die(state)

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

for name, resume in state["variants"].items():
    if not validate_resume(resume):
        raise RuntimeError(f"Invalid resume structure in variant '{name}'")


def get_active_resume():
    return state["variants"][state["active_variant"]]


def ensure_not_base():
    if state["active_variant"] == "base":
        return jsonify({
            "error": "Base resume is read-only. Create a variant to edit."
        }), 403
    return None

def is_dry_run(payload):
    return payload.get("dry_run", False) is True


# =========================================================
# BULLET DECISION LOGIC (PHASE 28.x)
# =========================================================

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


# =========================================================
# PHASE 29.1 — DRY-RUN EXECUTION PLAN
# =========================================================

def build_execution_plan(decisions):
    plan = {
        "KEEP": [],
        "REVIEW": [],
        "REMOVE": []
    }

    for d in decisions:
        plan[d["action"]].append(d)

    return plan


# =========================================================
# BULLET REMOVAL HELPER
# =========================================================

def apply_removals(resume, decisions):
    updated = json.loads(json.dumps(resume))
    removals = [
        d for d in decisions if d["action"] == "REMOVE"
    ]

    for d in sorted(removals, key=lambda x: (x["experience_index"], x["bullet_index"]), reverse=True):
        exp_i = d["experience_index"]
        b_i = d["bullet_index"]

        try:
            updated["experience"][exp_i]["bullets"].pop(b_i)
        except (IndexError, KeyError):
            continue

    return updated


# =========================================================
# HEALTH
# =========================================================

@app.route("/")
def home():
    return "Backend is alive"


# =========================================================
# RESUME
# =========================================================

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
        return jsonify({"error": "Invalid payload"}), 400

    if not validate_resume(payload):
        return jsonify({"error": "Invalid resume structure"}), 400

    state["variants"][state["active_variant"]] = payload
    save_state(state)
    return jsonify({"status": "saved"})


@app.route("/api/resume/bullet", methods=["POST"])
def update_bullet_api():
    guard = ensure_not_base()
    if guard:
        return guard

    payload = request.get_json()
    exp_index = payload.get("exp_index")
    bullet_index = payload.get("bullet_index")
    text = payload.get("text")

    if not all(isinstance(x, int) for x in [exp_index, bullet_index]) or not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Invalid input"}), 400

    resume = get_active_resume()
    try:
        resume["experience"][exp_index]["bullets"][bullet_index]
    except (IndexError, KeyError, TypeError):
        return jsonify({"error": "Index out of range"}), 400

    updated = update_bullet(resume, exp_index, bullet_index, text)

    if updated is None:
        return jsonify({"error": "Update failed"}), 400

    state["variants"][state["active_variant"]] = updated
    save_state(state)
    return jsonify({"status": "updated"})


# =========================================================
# VARIANTS
# =========================================================

@app.route("/api/variant", methods=["POST"])
def create_variant():
    payload = request.get_json()
    name = payload.get("name")

    if not name or name in state["variants"]:
        return jsonify({"error": "Invalid or duplicate name"}), 400

    base_copy = json.loads(json.dumps(state["variants"]["base"]))
    state["variants"][name] = base_copy
    state["active_variant"] = name
    save_state(state)

    return jsonify({"status": "created", "active": name})


@app.route("/api/variant/activate", methods=["POST"])
def activate_variant():
    payload = request.get_json()
    name = payload.get("name")

    if name not in state["variants"]:
        return jsonify({"error": "Variant not found"}), 404

    state["active_variant"] = name
    save_state(state)
    return jsonify({"active": name})


@app.route("/api/variants", methods=["GET"])
def list_variants():
    return jsonify({
        "variants": list(state["variants"].keys()),
        "active": state["active_variant"]
    })


# =========================================================
# SCORING
# =========================================================

@app.route("/api/variant/score", methods=["POST"])
def score_variant():
    payload = request.get_json()
    job = payload.get("job")
    if not isinstance(job, str) or not job.strip():
        return jsonify({"error": "Invalid job description"}), 400
    job = job.strip()

    base = state["variants"]["base"]
    variant = get_active_resume()

    base_score = score_resume(base, job)
    variant_score = score_resume(variant, job)

    return jsonify({
        "variant": state["active_variant"],
        "base_score": base_score,
        "variant_score": variant_score,
        "improvement": variant_score - base_score
    })


# =========================================================
# BULLET IMPACT + DECISIONS
# =========================================================

@app.route("/api/variant/bullet-impact", methods=["POST"])
def bullet_impact_api():
    payload = request.get_json()
    job = payload.get("job")
    if not isinstance(job, str) or not job.strip():
        return jsonify({"error": "Invalid job description"}), 400
    job = job.strip()

    impacts = bullet_impact_scores(get_active_resume(), job)
    return jsonify({
        "variant": state["active_variant"],
        "impacts": impacts
    })


@app.route("/api/variant/bullet-decisions", methods=["POST"])
def bullet_decisions_api():
    payload = request.get_json()
    job = payload.get("job")
    if not isinstance(job, str) or not job.strip():
        return jsonify({"error": "Invalid job description"}), 400
    job = job.strip()

    impacts = bullet_impact_scores(get_active_resume(), job)
    decisions = make_bullet_decisions(impacts)

    return jsonify({
        "variant": state["active_variant"],
        "decisions": decisions
    })



# =========================================================
# PHASE 29.1 — DECISION PLAN (DRY RUN)
# =========================================================

@app.route("/api/variant/decision-plan", methods=["POST"])
def decision_plan_api():
    payload = request.get_json()
    job = payload.get("job")
    if not isinstance(job, str) or not job.strip():
        return jsonify({"error": "Invalid job description"}), 400
    job = job.strip()

    impacts = bullet_impact_scores(get_active_resume(), job)
    decisions = make_bullet_decisions(impacts)
    plan = build_execution_plan(decisions)

    return jsonify({
        "variant": state["active_variant"],
        "plan": plan
    })


# =========================================================
# PHASE 29.4 — PRIORITIZED REVIEW QUEUE
# =========================================================

@app.route("/api/variant/review-priority", methods=["POST"])
def review_priority_api():
    payload = request.get_json()
    job = payload.get("job")
    if not isinstance(job, str) or not job.strip():
        return jsonify({"error": "Invalid job description"}), 400
    job = job.strip()

    impacts = bullet_impact_scores(get_active_resume(), job)
    decisions = make_bullet_decisions(impacts)

    review = [d for d in decisions if d["action"] == "REVIEW"]

    if not review:
        return jsonify({
            "variant": state["active_variant"],
            "review_queue": []
        })

    impacts_only = [d["impact"] for d in review]
    mean = statistics.mean(impacts_only)

    prioritized = sorted(
        review,
        key=lambda d: abs(d["impact"] - mean),
        reverse=True
    )

    return jsonify({
        "variant": state["active_variant"],
        "review_queue": prioritized
    })



@app.route("/api/variant/apply-removals", methods=["POST"])
def apply_removals_api():
    guard = ensure_not_base()
    if guard:
        return guard

    payload = request.get_json()
    job = payload.get("job")
    if not isinstance(job, str) or not job.strip():
        return jsonify({"error": "Invalid job description"}), 400
    job = job.strip()
    confirm = payload.get("confirm", False)

    if confirm is not True:
        return jsonify({
            "error": "Confirmation required",
            "hint": "Set confirm=true to apply removals"
        }), 400

    resume = get_active_resume()
    impacts = bullet_impact_scores(resume, job)
    decisions = make_bullet_decisions(impacts)

    updated = apply_removals(resume, decisions)

    if is_dry_run(payload):
        return jsonify({
            "variant": state["active_variant"],
            "removed": [d for d in decisions if d["action"] == "REMOVE"],
            "status": "dry-run"
        })

    state["variants"][state["active_variant"]] = updated
    save_state(state)

    return jsonify({
        "variant": state["active_variant"],
        "removed": [d for d in decisions if d["action"] == "REMOVE"],
        "status": "applied"
    })


# =========================================================
# METRICS
# =========================================================

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    return jsonify(metrics.summary())


@app.route("/api/metrics/latest", methods=["GET"])
def latest_metrics():
    history = load_metrics()
    if not history:
        return jsonify({"error": "No metrics available"}), 404
    return jsonify(history[-1])


@app.route("/api/metrics/aggregate", methods=["GET"])
def aggregated_metrics():
    return jsonify(aggregate_metrics())


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)