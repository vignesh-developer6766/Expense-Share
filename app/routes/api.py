from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user
from app.extensions import db, csrf
from app.models.user import User
from app.services.group_service import GroupService
from app.services.expense_service import ExpenseService
from app.services.balance_service import BalanceService
from app.services.settlement_service import SettlementService
from app.services.analytics_service import AnalyticsService
from app.ml.predict_category import predict_category
from app.ai.expense_parser import AIExpenseParser

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Exclude REST API endpoints from CSRF form checks for programmatic clients
csrf.exempt(api_bp)


@api_bp.route("/auth/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 400

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201


@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    login_user(user)
    return jsonify({"message": "Logged in successfully", "user": user.to_dict()}), 200


@api_bp.route("/groups", methods=["GET"])
def api_get_groups():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
    groups = GroupService.get_user_groups(current_user.id)
    return jsonify([g.to_dict(include_members=True) for g in groups]), 200


@api_bp.route("/groups", methods=["POST"])
def api_create_group():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return jsonify({"error": "Group name is required"}), 400

    group = GroupService.create_group(name=name, description=description, creator_id=current_user.id)
    return jsonify(group.to_dict(include_members=True)), 201


@api_bp.route("/groups/<int:group_id>", methods=["GET"])
def api_get_group_detail(group_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
    if not GroupService.is_member(group_id, current_user.id):
        return jsonify({"error": "Access denied"}), 403

    group = GroupService.get_group_by_id(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    return jsonify(group.to_dict(include_members=True)), 200


@api_bp.route("/expenses", methods=["GET"])
def api_get_expenses():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401

    group_id = request.args.get("group_id", type=int)
    category = request.args.get("category", type=str)
    search = request.args.get("search", type=str)

    expenses = ExpenseService.get_user_expenses(
        user_id=current_user.id,
        group_id=group_id,
        category=category,
        search=search,
    )
    return jsonify([e.to_dict() for e in expenses]), 200


@api_bp.route("/expenses", methods=["POST"])
def api_create_expense():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    try:
        expense = ExpenseService.create_expense(
            group_id=data.get("group_id"),
            description=data.get("description", ""),
            amount=float(data.get("amount", 0)),
            category=data.get("category", "Other"),
            paid_by=data.get("paid_by", current_user.id),
            split_type=data.get("split_type", "equal"),
            split_data=data.get("split_data", {}),
            notes=data.get("notes", ""),
        )
        return jsonify(expense.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/balances", methods=["GET"])
def api_get_balances():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401

    group_id = request.args.get("group_id", type=int)
    if group_id:
        return jsonify(BalanceService.get_user_group_balance(current_user.id, group_id)), 200

    return jsonify(BalanceService.get_user_overall_summary(current_user.id)), 200


@api_bp.route("/settlements", methods=["POST"])
def api_record_settlement():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    try:
        settlement = SettlementService.record_settlement(
            group_id=data.get("group_id"),
            payer_id=data.get("payer_id"),
            receiver_id=data.get("receiver_id"),
            amount=float(data.get("amount", 0)),
        )
        return jsonify(settlement.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/analytics", methods=["GET"])
def api_get_analytics():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = current_user.id
    return jsonify({
        "category_spending": AnalyticsService.get_category_spending(user_id),
        "monthly_trend": AnalyticsService.get_monthly_spending(user_id),
        "group_comparison": AnalyticsService.get_group_spending_comparison(user_id),
        "insights": AnalyticsService.generate_spending_insights(user_id),
    }), 200


@api_bp.route("/ml/predict-category", methods=["POST"])
def api_predict_category():
    data = request.get_json() or {}
    description = data.get("description", "")
    return jsonify(predict_category(description)), 200


@api_bp.route("/ai/parse-expense", methods=["POST"])
def api_parse_expense():
    data = request.get_json() or {}
    text = data.get("text", "")
    members = data.get("members", [])
    return jsonify(AIExpenseParser.parse_natural_language_expense(text, members)), 200
