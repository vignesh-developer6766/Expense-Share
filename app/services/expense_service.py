import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import db
from app.models.expense import Expense
from app.models.group import Group, GroupMember
from app.services.split_service import SplitService


class ExpenseService:
    @staticmethod
    def create_expense(
        group_id: int,
        description: str,
        amount: float,
        category: str,
        paid_by: int,
        split_type: str,
        split_data: dict,
        notes: str = "",
        receipt_file=None,
    ) -> Expense:
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")

        group = db.session.get(Group, group_id)
        if not group:
            raise ValueError("Group not found.")

        # Check membership
        if not GroupMember.query.filter_by(group_id=group_id, user_id=paid_by).first():
            raise ValueError("Payer must be a member of the group.")

        # Handle receipt upload
        receipt_filename = None
        if receipt_file and receipt_file.filename:
            filename = secure_filename(receipt_file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            receipt_filename = timestamp + filename
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], receipt_filename)
            receipt_file.save(upload_path)

        expense = Expense(
            group_id=group_id,
            description=description.strip(),
            amount=round(amount, 2),
            category=category.strip() if category else "Other",
            paid_by=paid_by,
            notes=notes.strip() if notes else "",
            receipt_image=receipt_filename,
            expense_date=datetime.now(timezone.utc),
        )
        db.session.add(expense)
        db.session.flush()

        group_members = [m.user_id for m in group.members]
        SplitService.create_splits(
            expense_id=expense.id,
            split_type=split_type,
            split_data=split_data,
            total_amount=expense.amount,
            group_user_ids=group_members,
        )

        return expense

    @staticmethod
    def get_user_expenses(
        user_id: int,
        group_id: int = None,
        category: str = None,
        search: str = None,
        sort_by: str = "newest",
    ):
        user_group_ids = [
            m.group_id for m in GroupMember.query.filter_by(user_id=user_id).all()
        ]

        if not user_group_ids:
            return []

        query = Expense.query.filter(Expense.group_id.in_(user_group_ids))

        if group_id:
            query = query.filter(Expense.group_id == group_id)

        if category and category.lower() != "all":
            query = query.filter(Expense.category == category)

        if search:
            query = query.filter(Expense.description.ilike(f"%{search.strip()}%"))

        if sort_by == "oldest":
            query = query.order_by(Expense.expense_date.asc())
        elif sort_by == "highest":
            query = query.order_by(Expense.amount.desc())
        elif sort_by == "lowest":
            query = query.order_by(Expense.amount.asc())
        else:  # newest
            query = query.order_by(Expense.expense_date.desc())

        return query.all()

    @staticmethod
    def get_expense_by_id(expense_id: int) -> Expense:
        return db.session.get(Expense, expense_id)

    @staticmethod
    def delete_expense(expense_id: int, current_user_id: int) -> tuple[bool, str]:
        expense = db.session.get(Expense, expense_id)
        if not expense:
            return False, "Expense not found."

        # Authorized if paid_by or group creator
        if expense.paid_by != current_user_id and expense.group.created_by != current_user_id:
            return False, "You do not have permission to delete this expense."

        db.session.delete(expense)
        db.session.commit()
        return True, "Expense deleted successfully."
