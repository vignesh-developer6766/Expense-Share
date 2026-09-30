from datetime import datetime, timezone
from app.extensions import db


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="Other")
    paid_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expense_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text, nullable=True)
    receipt_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    splits = db.relationship("ExpenseSplit", backref="expense", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_splits=True):
        data = {
            "id": self.id,
            "group_id": self.group_id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "paid_by": self.paid_by,
            "payer_name": self.payer.name if self.payer else None,
            "expense_date": self.expense_date.isoformat() if self.expense_date else None,
            "notes": self.notes,
            "receipt_image": self.receipt_image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_splits:
            data["splits"] = [split.to_dict() for split in self.splits]
        return data

    def __repr__(self):
        return f"<Expense {self.description} : {self.amount}>"


class ExpenseSplit(db.Model):
    __tablename__ = "expense_splits"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    split_type = db.Column(db.String(20), nullable=False, default="equal")  # equal, exact, percentage, shares
    amount = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=True)
    shares = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "expense_id": self.expense_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "split_type": self.split_type,
            "amount": self.amount,
            "percentage": self.percentage,
            "shares": self.shares,
        }

    def __repr__(self):
        return f"<ExpenseSplit User:{self.user_id} Amount:{self.amount}>"
