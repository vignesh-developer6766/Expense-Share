from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.recurring_expense import RecurringExpense
from app.models.group import Group, GroupMember
from app.services.expense_service import ExpenseService
from app.services.notification_service import NotificationService


class RecurringService:
    @staticmethod
    def create_recurring_expense(
        group_id: int,
        description: str,
        amount: float,
        frequency: str,
        next_due_date: datetime,
        category: str,
        creator_id: int,
    ) -> RecurringExpense:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        group = db.session.get(Group, group_id)
        if not group:
            raise ValueError("Group not found.")

        rec = RecurringExpense(
            group_id=group_id,
            description=description.strip(),
            amount=round(amount, 2),
            frequency=frequency.lower(),
            next_due_date=next_due_date,
            category=category if category else "Other",
            created_by=creator_id,
            active=True,
        )
        db.session.add(rec)
        db.session.commit()
        return rec

    @staticmethod
    def get_user_recurring_expenses(user_id: int) -> list[RecurringExpense]:
        user_group_ids = [
            m.group_id for m in GroupMember.query.filter_by(user_id=user_id).all()
        ]
        if not user_group_ids:
            return []
        return (
            RecurringExpense.query.filter(RecurringExpense.group_id.in_(user_group_ids))
            .order_by(RecurringExpense.next_due_date.asc())
            .all()
        )

    @staticmethod
    def toggle_active_status(recurring_id: int, user_id: int) -> tuple[bool, str]:
        rec = db.session.get(RecurringExpense, recurring_id)
        if not rec:
            return False, "Recurring expense not found."

        rec.active = not rec.active
        db.session.commit()
        status_str = "activated" if rec.active else "deactivated"
        return True, f"Recurring expense '{rec.description}' {status_str}."

    @staticmethod
    def process_due_recurring_expenses() -> int:
        now = datetime.now(timezone.utc)
        due_expenses = RecurringExpense.query.filter(
            RecurringExpense.active == True,
            RecurringExpense.next_due_date <= now,
        ).all()

        processed_count = 0
        for rec in due_expenses:
            # Auto-create actual expense
            group_members = [m.user_id for m in rec.group.members]
            ExpenseService.create_expense(
                group_id=rec.group_id,
                description=f"[Recurring] {rec.description}",
                amount=rec.amount,
                category=rec.category,
                paid_by=rec.created_by,
                split_type="equal",
                split_data={"users": group_members},
                notes=f"Auto-generated recurring expense ({rec.frequency}).",
            )

            # Advance next_due_date
            if rec.frequency == "daily":
                rec.next_due_date += timedelta(days=1)
            elif rec.frequency == "weekly":
                rec.next_due_date += timedelta(weeks=1)
            elif rec.frequency == "monthly":
                rec.next_due_date += timedelta(days=30)
            elif rec.frequency == "yearly":
                rec.next_due_date += timedelta(days=365)

            # Notify group members
            for uid in group_members:
                NotificationService.create_notification(
                    user_id=uid,
                    title=f"Recurring Expense Due: {rec.description}",
                    message=f"Recurring expense '{rec.description}' of ₹{rec.amount:.2f} was automatically processed for group '{rec.group.name}'.",
                    type="reminder",
                )

            processed_count += 1

        db.session.commit()
        return processed_count
