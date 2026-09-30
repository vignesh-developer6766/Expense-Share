import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.ocr.receipt_processor import ReceiptProcessor
from app.ml.duplicate_detector import DuplicateDetector
from app.services.group_service import GroupService

ocr_bp = Blueprint("ocr", __name__, url_prefix="/ocr")


def _get_or_create_user_groups(user_id):
    groups = GroupService.get_user_groups(user_id)
    if not groups:
        GroupService.create_group("Personal Expenses", "Default personal group for receipt scans & expenses", user_id)
        groups = GroupService.get_user_groups(user_id)
    return groups


@ocr_bp.route("/upload")
@ocr_bp.route("")
@login_required
def upload():
    user_groups = _get_or_create_user_groups(current_user.id)
    selected_group = user_groups[0] if user_groups else None
    return render_template("ocr/upload.html", groups=user_groups, selected_group=selected_group)


@ocr_bp.route("/process", methods=["POST"])
@login_required
def process():
    user_groups = _get_or_create_user_groups(current_user.id)
    group_id = request.form.get("group_id", type=int)
    receipt_file = request.files.get("receipt")

    if not group_id and user_groups:
        group_id = user_groups[0].id

    if not group_id or not receipt_file or not receipt_file.filename:
        flash("Please select a group and upload a valid receipt image.", "danger")
        return redirect(url_for("ocr.upload"))

    # Save temp upload
    filename = secure_filename(receipt_file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
    saved_filename = timestamp + filename
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_filename)
    receipt_file.save(filepath)

    # Run OCR Processor
    ocr_result = ReceiptProcessor.process_receipt_image(filepath)
    ocr_result["receipt_filename"] = saved_filename

    # Check for Duplicate Expense
    duplicate_info = DuplicateDetector.check_duplicate(
        group_id=group_id,
        description=ocr_result["description"],
        amount=ocr_result["amount"],
        paid_by=current_user.id,
    )

    selected_group = GroupService.get_group_by_id(group_id) or user_groups[0]

    return render_template(
        "ocr/upload.html",
        groups=user_groups,
        selected_group=selected_group,
        ocr_result=ocr_result,
        duplicate_info=duplicate_info,
    )
