from app.models.expense import Expense, ExpenseSplit
from app.models.settlement import Settlement
from app.models.group import Group, GroupMember
from app.models.user import User
from app.extensions import db


class BalanceService:
    @staticmethod
    def get_group_member_balances(group_id: int) -> dict[int, float]:
        group = db.session.get(Group, group_id)
        if not group:
            return {}

        member_ids = [m.user_id for m in group.members]
        net_balances = {uid: 0.0 for uid in member_ids}

        # Add amounts paid for expenses
        expenses = Expense.query.filter_by(group_id=group_id).all()
        for expense in expenses:
            if expense.paid_by in net_balances:
                net_balances[expense.paid_by] += expense.amount

            # Subtract amounts owed from splits
            for split in expense.splits:
                if split.user_id in net_balances:
                    net_balances[split.user_id] -= split.amount

        # Account for completed settlements
        settlements = Settlement.query.filter_by(group_id=group_id, status="completed").all()
        for s in settlements:
            if s.payer_id in net_balances:
                net_balances[s.payer_id] += s.amount
            if s.receiver_id in net_balances:
                net_balances[s.receiver_id] -= s.amount

        return {uid: round(bal, 2) for uid, bal in net_balances.items()}

    @staticmethod
    def get_user_group_balance(user_id: int, group_id: int) -> dict:
        balances = BalanceService.get_group_member_balances(group_id)
        net_balance = balances.get(user_id, 0.0)

        # Calculate raw paid and owed totals
        expenses_paid = (
            db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0.0))
            .filter(Expense.group_id == group_id, Expense.paid_by == user_id)
            .scalar()
        )

        splits_owed = (
            db.session.query(db.func.coalesce(db.func.sum(ExpenseSplit.amount), 0.0))
            .join(Expense, ExpenseSplit.expense_id == Expense.id)
            .filter(Expense.group_id == group_id, ExpenseSplit.user_id == user_id)
            .scalar()
        )

        return {
            "user_id": user_id,
            "group_id": group_id,
            "total_paid": round(float(expenses_paid), 2),
            "total_owed": round(float(splits_owed), 2),
            "net_balance": round(net_balance, 2),
        }

    @staticmethod
    def get_user_overall_summary(user_id: int) -> dict:
        user_groups = (
            Group.query.join(GroupMember, Group.id == GroupMember.group_id)
            .filter(GroupMember.user_id == user_id)
            .all()
        )

        total_paid = 0.0
        total_owed = 0.0
        total_you_owe = 0.0
        total_you_are_owed = 0.0
        net_balance = 0.0

        for group in user_groups:
            group_bal = BalanceService.get_group_member_balances(group.id)
            user_net = group_bal.get(user_id, 0.0)

            net_balance += user_net
            if user_net > 0:
                total_you_are_owed += user_net
            elif user_net < 0:
                total_you_owe += abs(user_net)

            group_summary = BalanceService.get_user_group_balance(user_id, group.id)
            total_paid += group_summary["total_paid"]
            total_owed += group_summary["total_owed"]

        return {
            "user_id": user_id,
            "total_paid": round(total_paid, 2),
            "total_owed": round(total_owed, 2),
            "total_you_owe": round(total_you_owe, 2),
            "total_you_are_owed": round(total_you_are_owed, 2),
            "net_balance": round(net_balance, 2),
        }
