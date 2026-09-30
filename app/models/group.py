from datetime import datetime, timezone
from app.extensions import db


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    members = db.relationship("GroupMember", backref="group", lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="group", lazy=True, cascade="all, delete-orphan")
    settlements = db.relationship("Settlement", backref="group", lazy=True, cascade="all, delete-orphan")
    recurring_expenses = db.relationship("RecurringExpense", backref="group", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_members=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "member_count": len(self.members),
        }
        if include_members:
            data["members"] = [member.user.to_dict() for member in self.members]
        return data

    def __repr__(self):
        return f"<Group {self.name}>"


class GroupMember(db.Model):
    __tablename__ = "group_members"
    __table_args__ = (db.UniqueConstraint("group_id", "user_id", name="unique_group_user"),)

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<GroupMember User:{self.user_id} Group:{self.group_id}>"
