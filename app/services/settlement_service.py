from datetime import datetime, timezone
from app.extensions import db
from app.models.settlement import Settlement
from app.models.group import Group, GroupMember
from app.models.user import User
from app.models.notification import Notification
from app.services.balance_service import BalanceService


class SettlementService:
    @staticmethod
    def simplify_group_debts(group_id: int) -> list[dict]:
        balances = BalanceService.get_group_member_balances(group_id)

        # Separate creditors and debtors
        debtors = []   # list of [user_id, amount_owed] (amount_owed > 0)
        creditors = [] # list of [user_id, amount_receivable] (amount_receivable > 0)

        for uid, net in balances.items():
            if net < -0.01:
                debtors.append([uid, abs(net)])
            elif net > 0.01:
                creditors.append([uid, net])

        # Sort debtors and creditors descending by amount
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)

        simplified_transactions = []
        i = 0
        j = 0

        while i < len(debtors) and j < len(creditors):
            debtor_id, debt_amt = debtors[i]
            creditor_id, credit_amt = creditors[j]

            settle_amt = round(min(debt_amt, credit_amt), 2)

            if settle_amt > 0.01:
                payer = db.session.get(User, debtor_id)
                receiver = db.session.get(User, creditor_id)

                simplified_transactions.append({
                    "group_id": group_id,
                    "payer_id": debtor_id,
                    "payer_name": payer.name if payer else f"User #{debtor_id}",
                    "receiver_id": creditor_id,
                    "receiver_name": receiver.name if receiver else f"User #{creditor_id}",
                    "amount": settle_amt,
                })

            debtors[i][1] = round(debt_amt - settle_amt, 2)
            creditors[j][1] = round(credit_amt - settle_amt, 2)

            if debtors[i][1] <= 0.01:
                i += 1
            if creditors[j][1] <= 0.01:
                j += 1

        return simplified_transactions

    @staticmethod
    def record_settlement(group_id: int, payer_id: int, receiver_id: int, amount: float) -> Settlement:
        if amount <= 0:
            raise ValueError("Settlement amount must be greater than zero.")

        group = db.session.get(Group, group_id)
        if not group:
            raise ValueError("Group not found.")

        payer = db.session.get(User, payer_id)
        receiver = db.session.get(User, receiver_id)

        settlement = Settlement(
            group_id=group_id,
            payer_id=payer_id,
            receiver_id=receiver_id,
            amount=round(amount, 2),
            status="completed",
            settled_at=datetime.now(timezone.utc),
        )
        db.session.add(settlement)

        # Create notification for receiver
        notification = Notification(
            user_id=receiver_id,
            title="Payment Received",
            message=f"{payer.name} settled ₹{amount:.2f} with you in '{group.name}'.",
            type="settlement",
        )
        db.session.add(notification)

        db.session.commit()
        return settlement

    @staticmethod
    def get_group_settlements(group_id: int) -> list[Settlement]:
        return (
            Settlement.query.filter_by(group_id=group_id)
            .order_by(Settlement.settled_at.desc())
            .all()
        )
