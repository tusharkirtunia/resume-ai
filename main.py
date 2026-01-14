from flask import Flask, jsonify, request
from storage import load_state, save_state
from state import initial_state
from editor import update_bullet
from rewriter import rewrite_bullet
from scoring import score_resume
import json

app = Flask(__name__)

# =========================================================
# STATE INITIALIZATION
# =========================================================

state = load_state() or initial_state()


def get_active_resume():
    active = state["active_variant"]
    return state["variants"][active]


def ensure_not_base():
    if state["active_variant"] == "base":
        return jsonify({
            "error": "Base resume is read-only. Create a variant to edit."
        }), 403
    return None


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/")
def home():
    return "Backend is alive"


# =========================================================
# RESUME READ
# =========================================================

@app.route("/api/resume", methods=["GET"])
def get_resume():
    return jsonify(get_active_resume())


# =========================================================
# RESUME SAVE
# =========================================================

@app.route("/api/resume", methods=["POST"])
def save_resume_api():
    guard = ensure_not_base()
    if guard:
        return guard

    payload = request.get_json()
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid payload"}), 400

    active = state["active_variant"]
    state["variants"][active] = payload
    save_state(state)

    return jsonify({"status": "saved"})


# =========================================================
# BULLET UPDATE
# =========================================================

@app.route("/api/resume/bullet", methods=["POST"])
def update_bullet_api():
    guard = ensure_not_base()
    if guard:
        return guard

    payload = request.get_json()
    exp_index = payload.get("exp_index")
    bullet_index = payload.get("bullet_index")
    text = payload.get("text")

    if not all([
        isinstance(exp_index, int),
        isinstance(bullet_index, int),
        isinstance(text, str)
    ]):
        return jsonify({"error": "Invalid input"}), 400

    resume = get_active_resume()
    updated = update_bullet(resume, exp_index, bullet_index, text)

    if updated is None:
        return jsonify({"error": "Update failed"}), 400

    active = state["active_variant"]
    state["variants"][active] = updated
    save_state(state)

    return jsonify({"status": "updated"})


# =========================================================
# BULLET REWRITE
# =========================================================

@app.route("/api/rewrite", methods=["POST"])
def rewrite_api():
    payload = request.get_json()
    bullet = payload.get("bullet")
    job = payload.get("job")

    if not isinstance(bullet, str) or not isinstance(job, str):
        return jsonify({"error": "Invalid input"}), 400

    rewritten = rewrite_bullet(bullet, job)
    return jsonify({"rewritten": rewritten})


# =========================================================
# VARIANT CREATE / ACTIVATE / LIST
# =========================================================

@app.route("/api/variant", methods=["POST"])
def create_variant():
    payload = request.get_json()
    name = payload.get("name")

    if not name or name in state["variants"]:
        return jsonify({"error": "Invalid or duplicate name"}), 400

    base = state["variants"]["base"]
    clone = json.loads(json.dumps(base))

    state["variants"][name] = clone
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

    return jsonify({"status": "active variant changed", "active": name})


@app.route("/api/variants", methods=["GET"])
def list_variants():
    return jsonify({
        "variants": list(state["variants"].keys()),
        "active": state["active_variant"]
    })


# =========================================================
# VARIANT SCORE (LOCAL SEMANTIC)
# =========================================================

@app.route("/api/variant/score", methods=["POST"])
def score_variant():
    payload = request.get_json()
    job = payload.get("job")

    if not isinstance(job, str) or not job.strip():
        return jsonify({"error": "Invalid job description"}), 400

    active = state["active_variant"]
    base = state["variants"]["base"]
    variant = state["variants"][active]

    base_score = score_resume(base, job)
    variant_score = score_resume(variant, job)

    return jsonify({
        "variant": active,
        "base_score": base_score,
        "variant_score": variant_score,
        "improvement": variant_score - base_score
    })


# =========================================================
# AUTO IMPROVE — SINGLE PASS
# =========================================================

@app.route("/api/variant/auto-improve", methods=["POST"])
def auto_improve_variant():
    payload = request.get_json()
    job = payload.get("job")

    if not isinstance(job, str) or not job.strip():
        return jsonify({"error": "Invalid job description"}), 400

    active = state["active_variant"]
    if active == "base":
        return jsonify({"error": "Cannot auto-improve base variant"}), 403

    variant = state["variants"][active]
    best_score = score_resume(variant, job)
    improvements = []

    for exp_i, exp in enumerate(variant.get("experience", [])):
        for b_i, original in enumerate(exp.get("bullets", [])):
            rewritten = rewrite_bullet(original, job)
            exp["bullets"][b_i] = rewritten
            new_score = score_resume(variant, job)

            if new_score > best_score:
                best_score = new_score
                improvements.append({
                    "experience_index": exp_i,
                    "bullet_index": b_i,
                    "old": original,
                    "new": rewritten,
                    "score": new_score
                })
            else:
                exp["bullets"][b_i] = original

    save_state(state)

    return jsonify({
        "variant": active,
        "final_score": best_score,
        "improvements": improvements
    })


# =========================================================
# AUTO IMPROVE — LOOP
# =========================================================

@app.route("/api/variant/auto-improve/loop", methods=["POST"])
def auto_improve_loop():
    payload = request.get_json()
    job = payload.get("job")
    max_iters = payload.get("iterations", 3)

    if not isinstance(job, str) or not isinstance(max_iters, int):
        return jsonify({"error": "Invalid input"}), 400

    active = state["active_variant"]
    if active == "base":
        return jsonify({"error": "Cannot auto-improve base variant"}), 403

    variant = state["variants"][active]
    history = []
    base_score = score_resume(state["variants"]["base"], job)
    best_score = score_resume(variant, job)

    for iteration in range(max_iters):
        improved = False

        for exp_i, exp in enumerate(variant.get("experience", [])):
            for b_i, original in enumerate(exp.get("bullets", [])):
                rewritten = rewrite_bullet(original, job)
                exp["bullets"][b_i] = rewritten
                new_score = score_resume(variant, job)

                if new_score > best_score:
                    best_score = new_score
                    improved = True
                    history.append({
                        "iteration": iteration + 1,
                        "experience_index": exp_i,
                        "bullet_index": b_i,
                        "old": original,
                        "new": rewritten,
                        "score": new_score
                    })
                else:
                    exp["bullets"][b_i] = original

        if not improved:
            break

    save_state(state)

    return jsonify({
        "variant": active,
        "base_score": base_score,
        "final_score": best_score,
        "iterations_run": len(history),
        "history": history
    })


# =========================================================
# AUTO IMPROVE — DIVERSE
# =========================================================

@app.route("/api/variant/auto-improve/diverse", methods=["POST"])
def auto_improve_diverse():
    payload = request.get_json()
    job = payload.get("job")
    candidates = payload.get("candidates", 3)

    if not isinstance(job, str) or not isinstance(candidates, int):
        return jsonify({"error": "Invalid input"}), 400

    active = state["active_variant"]
    if active == "base":
        return jsonify({"error": "Cannot auto-improve base variant"}), 403

    variant = state["variants"][active]
    base_score = score_resume(state["variants"]["base"], job)
    best_score = score_resume(variant, job)
    accepted = []

    for exp_i, exp in enumerate(variant.get("experience", [])):
        for b_i, original in enumerate(exp.get("bullets", [])):
            best_local = original
            best_local_score = best_score

            for _ in range(candidates):
                rewritten = rewrite_bullet(original, job)
                exp["bullets"][b_i] = rewritten
                score = score_resume(variant, job)

                if score > best_local_score:
                    best_local = rewritten
                    best_local_score = score

            exp["bullets"][b_i] = best_local

            if best_local != original:
                best_score = best_local_score
                accepted.append({
                    "experience_index": exp_i,
                    "bullet_index": b_i,
                    "old": original,
                    "new": best_local,
                    "score": best_local_score
                })

    save_state(state)

    return jsonify({
        "variant": active,
        "base_score": base_score,
        "final_score": best_score,
        "accepted": accepted
    })


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)