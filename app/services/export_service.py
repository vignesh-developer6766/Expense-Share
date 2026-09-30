import csv
import io
from app.services.expense_service import ExpenseService


class ExportService:
    @staticmethod
    def export_expenses_to_csv(user_id: int, group_id: int = None, category: str = None) -> str:
        expenses = ExpenseService.get_user_expenses(user_id=user_id, group_id=group_id, category=category)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["ID", "Date", "Description", "Category", "Amount (INR)", "Group Name", "Paid By", "Split Count"])

        for exp in expenses:
            date_str = exp.expense_date.strftime("%Y-%m-%d %H:%M:%S") if exp.expense_date else ""
            payer_name = exp.payer.name if exp.payer else f"User #{exp.paid_by}"
            group_name = exp.group.name if exp.group else ""

            writer.writerow([
                exp.id,
                date_str,
                exp.description,
                exp.category,
                f"{exp.amount:.2f}",
                group_name,
                payer_name,
                len(exp.splits),
            ])

        return output.getvalue()
