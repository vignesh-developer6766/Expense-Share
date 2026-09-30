from typing import Dict, List, Tuple
from app.models.expense import ExpenseSplit
from app.extensions import db


class SplitService:
    @staticmethod
    def calculate_equal_split(total_amount: float, user_ids: List[int]) -> List[Tuple[int, float]]:
        if not user_ids:
            raise ValueError("At least one user must be included in the split.")

        count = len(user_ids)
        base_share = round(total_amount / count, 2)
        splits = [(uid, base_share) for uid in user_ids]

        # Adjust cent rounding difference on first user's share
        current_sum = round(sum(amount for _, amount in splits), 2)
        diff = round(total_amount - current_sum, 2)
        if diff != 0:
            first_uid, first_amt = splits[0]
            splits[0] = (first_uid, round(first_amt + diff, 2))

        return splits

    @staticmethod
    def calculate_exact_split(total_amount: float, exact_map: Dict[int, float]) -> List[Tuple[int, float]]:
        if not exact_map:
            raise ValueError("Exact amounts must be specified for involved users.")

        total_exact = round(sum(exact_map.values()), 2)
        if abs(total_exact - round(total_amount, 2)) > 0.01:
            raise ValueError(f"Sum of exact amounts (₹{total_exact}) does not equal total expense amount (₹{total_amount}).")

        return [(uid, round(amt, 2)) for uid, amt in exact_map.items()]

    @staticmethod
    def calculate_percentage_split(total_amount: float, percentage_map: Dict[int, float]) -> List[Tuple[int, float, float]]:
        if not percentage_map:
            raise ValueError("Percentages must be specified for involved users.")

        total_pct = round(sum(percentage_map.values()), 2)
        if abs(total_pct - 100.0) > 0.01:
            raise ValueError(f"Sum of percentages ({total_pct}%) must equal 100%.")

        splits = []
        for uid, pct in percentage_map.items():
            amt = round(total_amount * (pct / 100.0), 2)
            splits.append((uid, amt, pct))

        # Adjust cent rounding on first user
        current_sum = round(sum(amt for _, amt, _ in splits), 2)
        diff = round(total_amount - current_sum, 2)
        if diff != 0:
            uid, amt, pct = splits[0]
            splits[0] = (uid, round(amt + diff, 2), pct)

        return splits

    @staticmethod
    def calculate_shares_split(total_amount: float, shares_map: Dict[int, float]) -> List[Tuple[int, float, float]]:
        if not shares_map:
            raise ValueError("Shares must be specified for involved users.")

        total_shares = sum(shares_map.values())
        if total_shares <= 0:
            raise ValueError("Total shares must be greater than zero.")

        splits = []
        for uid, shares in shares_map.items():
            amt = round(total_amount * (shares / total_shares), 2)
            splits.append((uid, amt, shares))

        # Adjust cent rounding on first user
        current_sum = round(sum(amt for _, amt, _ in splits), 2)
        diff = round(total_amount - current_sum, 2)
        if diff != 0:
            uid, amt, shares = splits[0]
            splits[0] = (uid, round(amt + diff, 2), shares)

        return splits

    @staticmethod
    def create_splits(
        expense_id: int,
        split_type: str,
        split_data: dict,
        total_amount: float,
        group_user_ids: List[int],
    ) -> List[ExpenseSplit]:
        splits_to_create = []

        if split_type == "equal":
            target_users = split_data.get("users", group_user_ids)
            calculated = SplitService.calculate_equal_split(total_amount, target_users)
            for uid, amt in calculated:
                splits_to_create.append(
                    ExpenseSplit(expense_id=expense_id, user_id=uid, split_type="equal", amount=amt)
                )

        elif split_type == "exact":
            exact_map = {int(uid): float(amt) for uid, amt in split_data.get("exact", {}).items() if float(amt) > 0}
            calculated = SplitService.calculate_exact_split(total_amount, exact_map)
            for uid, amt in calculated:
                splits_to_create.append(
                    ExpenseSplit(expense_id=expense_id, user_id=uid, split_type="exact", amount=amt)
                )

        elif split_type == "percentage":
            pct_map = {int(uid): float(pct) for uid, pct in split_data.get("percentage", {}).items() if float(pct) > 0}
            calculated = SplitService.calculate_percentage_split(total_amount, pct_map)
            for uid, amt, pct in calculated:
                splits_to_create.append(
                    ExpenseSplit(
                        expense_id=expense_id,
                        user_id=uid,
                        split_type="percentage",
                        amount=amt,
                        percentage=pct,
                    )
                )

        elif split_type == "shares":
            shares_map = {int(uid): float(sh) for uid, sh in split_data.get("shares", {}).items() if float(sh) > 0}
            calculated = SplitService.calculate_shares_split(total_amount, shares_map)
            for uid, amt, shares in calculated:
                splits_to_create.append(
                    ExpenseSplit(
                        expense_id=expense_id,
                        user_id=uid,
                        split_type="shares",
                        amount=amt,
                        shares=shares,
                    )
                )
        else:
            raise ValueError(f"Unsupported split type '{split_type}'.")

        db.session.add_all(splits_to_create)
        db.session.commit()
        return splits_to_create
