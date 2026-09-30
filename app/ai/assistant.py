import re
from app.ai.expense_parser import AIExpenseParser
from app.services.group_service import GroupService
from app.services.balance_service import BalanceService
from app.services.analytics_service import AnalyticsService


class AIAssistant:
    @staticmethod
    def process_expense_prompt(user_id: int, group_id: int, prompt_text: str) -> dict:
        group = GroupService.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found.")

        member_names = [m.user.name for m in group.members]
        parsed_data = AIExpenseParser.parse_natural_language_expense(prompt_text, member_names)

        # Default all group members if none specifically detected
        if not parsed_data["members"]:
            parsed_data["members"] = member_names

        parsed_data["group_id"] = group.id
        parsed_data["group_name"] = group.name
        parsed_data["member_objects"] = [
            {"id": m.user.id, "name": m.user.name} for m in group.members if m.user.name in parsed_data["members"]
        ]

        return parsed_data

    @staticmethod
    def ask_assistant(user_id: int, message_text: str, group_id: int = None) -> dict:
        text_lower = message_text.strip().lower()

        # 1. Check for Expense Creation Intent (e.g., "paid", "spent", "bought", "cost", "rs", "₹", "bill", "split")
        expense_keywords = ["paid", "spent", "bought", "cost", "rs", "₹", "inr", "rupees", "dollar", "$", "bill", "split"]
        is_expense_intent = any(k in text_lower for k in expense_keywords) and any(c.isdigit() for c in text_lower)

        user_groups = GroupService.get_user_groups(user_id)
        target_group = None
        if group_id:
            target_group = GroupService.get_group_by_id(group_id)
        if not target_group and user_groups:
            target_group = user_groups[0]

        if is_expense_intent and target_group:
            try:
                parsed = AIAssistant.process_expense_prompt(user_id, target_group.id, message_text)
                members_str = ", ".join(parsed['members'])
                reply = (
                    f"I've analyzed your prompt and extracted the expense details!\n\n"
                    f"• **Description**: {parsed['description']}\n"
                    f"• **Amount**: ₹{parsed['amount']:.2f}\n"
                    f"• **Category**: {parsed['category']} (ML Predicted)\n"
                    f"• **Group**: {parsed['group_name']}\n"
                    f"• **Participants**: {members_str}\n\n"
                    f"Review the generated action card below to log this expense."
                )
                return {
                    "type": "expense_action",
                    "message": reply,
                    "expense_data": parsed
                }
            except Exception:
                pass

        # 2. Check for Greetings & Intros
        if text_lower in ["hi", "hello", "hey", "nexus", "nexus.ai"] or any(k in text_lower for k in ["who are you", "what can you do"]):
            reply = (
                "Hello! 👋 I am **Nexus.AI**, your intelligent financial & expense assistant.\n\n"
                "I work conversationally just like ChatGPT to manage all your shared expenses and finances. Here is what I can do:\n\n"
                "1. **Log Expenses**: Type commands like *'I paid ₹1200 for dinner with Alex and Rahul'* or *'Spent 450 rs on cab ride'*.\n"
                "2. **Check Balances & Debts**: Ask *'Who owes me money?'* or *'What is my net balance?'*.\n"
                "3. **Analyze Spending**: Ask *'How much did I spend this month?'* or *'Show category breakdown'*.\n"
                "4. **Financial Advice**: Ask for budgeting tips, the 50/30/20 rule, or how to split bills fairly!\n\n"
                "How can I assist you right now?"
            )
            return {
                "type": "info",
                "message": reply
            }

        # 3. Check for Balance / Debt Inquiries
        if any(k in text_lower for k in ["balance", "owe", "owed", "who owes", "settlement", "debt", "summary"]):
            summary = BalanceService.get_user_overall_summary(user_id)
            reply = (
                f"### 💳 Financial Balance Overview\n\n"
                f"Here is your current balance summary across all active groups:\n\n"
                f"- **Net Balance**: **₹{summary['net_balance']:,.2f}**\n"
                f"- **Awaiting Payment (You are Owed)**: **₹{summary['total_you_are_owed']:,.2f}**\n"
                f"- **Awaiting Approval (You Owe)**: **₹{summary['total_you_owe']:,.2f}**\n"
                f"- **Total Expenses Paid by You**: **₹{summary['total_paid']:,.2f}**\n\n"
            )
            if summary['total_you_are_owed'] > 0:
                reply += "✨ *Tip: You have pending settlements owed to you! Check Settlements to record payments.*"
            elif summary['total_you_owe'] > 0:
                reply += "⚠️ *Reminder: You have pending debts to clear. Settle up with group members on the Settlements tab.*"
            else:
                reply += "🎉 *All settled up! You have no outstanding debts.*"

            return {
                "type": "info",
                "message": reply
            }

        # 4. Check for Analytics / Spending Insights
        if any(k in text_lower for k in ["analytics", "insights", "highest", "spent", "category", "trend", "monthly"]):
            insights = AnalyticsService.generate_spending_insights(user_id)
            cat_spending = AnalyticsService.get_category_spending(user_id)
            reply = "### 📊 Spending & Category Analytics\n\n"
            for ins in insights:
                reply += f"- {ins}\n"

            if cat_spending:
                reply += "\n**Category Distribution Breakdown:**\n"
                for cat, amt in cat_spending.items():
                    reply += f"• **{cat}**: ₹{amt:,.2f}\n"

            return {
                "type": "info",
                "message": reply
            }

        # 5. Check for Budgeting / Tips / General Advice
        if any(k in text_lower for k in ["rule", "50", "30", "20", "budget", "save", "tip", "help", "how"]):
            reply = (
                "### 💡 Smart Financial & Expense Management Tips\n\n"
                "Here are key practices for managing shared & personal finances effectively:\n\n"
                "1. **The 50/30/20 Rule**:\n"
                "   - **50% Needs**: Essential living expenses, rent, utilities, and groceries.\n"
                "   - **30% Wants**: Dining out, entertainment, and shopping.\n"
                "   - **20% Savings**: Emergency fund, debt payments, and investments.\n\n"
                "2. **Group Expense Best Practices**:\n"
                "   - Log shared bills immediately after payment to maintain transparency.\n"
                "   - Use **Debt Simplification** to consolidate multiple small debts into a single settlement.\n"
                "   - Scan receipt photos via **Receipt OCR** for automatic category & total extraction.\n\n"
                "Ask me to log expenses, check balances, or summarize your spending anytime!"
            )
            return {
                "type": "info",
                "message": reply
            }

        # 6. General Conversational Nexus.AI Fallback
        reply = (
            f"Hello! I am **Nexus.AI**, your ChatGPT-style financial assistant 🤖✨\n\n"
            f"You can ask me questions or give commands like:\n"
            f"- **Log Expenses**: *'I paid ₹1200 for dinner with Arun and Rahul'*\n"
            f"- **Check Debts**: *'Who owes me money?'* or *'What is my total balance?'*\n"
            f"- **Analyze Spending**: *'How much did I spend this month?'* or *'Show category insights'*\n"
            f"- **Financial Advice**: *'How to save money on group trips?'*\n\n"
            f"What would you like to do?"
        )
        return {
            "type": "info",
            "message": reply
        }
