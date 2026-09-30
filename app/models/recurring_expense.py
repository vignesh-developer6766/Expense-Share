from datetime import datetime, timezone
from app.extensions import db


class RecurringExpense(db.Model):
    __tablename__ = "recurring_expenses"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False, default="monthly")  # daily, weekly, monthly, yearly
    next_due_date = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="Other")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "description": self.description,
            "amount": self.amount,
            "frequency": self.frequency,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "category": self.category,
            "created_by": self.created_by,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<RecurringExpense {self.description} ({self.frequency}): ₹{self.amount}>"
