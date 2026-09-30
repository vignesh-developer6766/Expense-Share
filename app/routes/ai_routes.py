from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.ai.assistant import AIAssistant
from app.ml.predict_category import predict_category
from app.services.group_service import GroupService

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")


def _get_or_create_user_groups(user_id):
    groups = GroupService.get_user_groups(user_id)
    if not groups:
        GroupService.create_group("Personal Expenses", "Default personal group for expenses & AI assistant", user_id)
        groups = GroupService.get_user_groups(user_id)
    return groups


@ai_bp.route("")
@ai_bp.route("/")
@login_required
def index():
    user_groups = _get_or_create_user_groups(current_user.id)
    return render_template("ai/assistant.html", groups=user_groups)


@ai_bp.route("/predict-category", methods=["POST"])
@login_required
def predict_category_api():
    data = request.get_json() or {}
    description = data.get("description", "")
    result = predict_category(description)
    return jsonify(result), 200


@ai_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    raw_gid = data.get("group_id")
    group_id = int(raw_gid) if raw_gid is not None and str(raw_gid).isdigit() else None

    if not message:
        return jsonify({"status": "error", "message": "Message content cannot be empty."}), 400

    result = AIAssistant.ask_assistant(current_user.id, message, group_id)
    return jsonify({"status": "success", "data": result}), 200


@ai_bp.route("/parse", methods=["POST"])
@login_required
def parse_expense_text():
    group_id = request.form.get("group_id", type=int)
    prompt_text = request.form.get("prompt_text", "").strip()

    user_groups = _get_or_create_user_groups(current_user.id)
    if not group_id and user_groups:
        group_id = user_groups[0].id

    if not prompt_text:
        flash("Please enter a question or expense prompt for Nexus.AI.", "danger")
        return redirect(url_for("ai.index"))

    try:
        assistant_reply = AIAssistant.ask_assistant(current_user.id, prompt_text, group_id)
        parsed_result = assistant_reply.get("expense_data")
        return render_template(
            "ai/assistant.html",
            groups=user_groups,
            selected_group_id=group_id,
            assistant_reply=assistant_reply,
            parsed_result=parsed_result,
            prompt_text=prompt_text,
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("ai.index"))
