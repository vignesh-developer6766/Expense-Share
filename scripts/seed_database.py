import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.services.expense_service import ExpenseService
from app.services.settlement_service import SettlementService
from app.services.recurring_service import RecurringService
from datetime import datetime, timezone, timedelta


def seed():
    app = create_app("development")
    with app.app_context():
        print("Resetting database tables...")
        db.drop_all()
        db.create_all()

        print("Creating users: Vignesh, Arun, Rahul, Karthik...")
        users_data = [
            ("Vignesh", "vignesh@example.com"),
            ("Arun", "arun@example.com"),
            ("Rahul", "rahul@example.com"),
            ("Karthik", "karthik@example.com"),
        ]

        users = {}
        for name, email in users_data:
            u = User(name=name, email=email)
            u.set_password("Password123")
            db.session.add(u)
            users[name] = u

        db.session.commit()

        print("Creating groups: College Trip, Roommates, Friends...")
        g1 = Group(name="College Trip", description="Goa Trip 2026", created_by=users["Vignesh"].id)
        g2 = Group(name="Roommates", description="Flat 302 Monthly Expenses", created_by=users["Arun"].id)
        g3 = Group(name="Friends", description="Weekend Hangouts", created_by=users["Rahul"].id)
        db.session.add_all([g1, g2, g3])
        db.session.commit()

        # Memberships
        # College Trip: Vignesh, Arun, Rahul, Karthik
        for u in users.values():
            db.session.add(GroupMember(group_id=g1.id, user_id=u.id))

        # Roommates: Vignesh, Arun, Rahul
        for u in [users["Vignesh"], users["Arun"], users["Rahul"]]:
            db.session.add(GroupMember(group_id=g2.id, user_id=u.id))

        # Friends: Vignesh, Arun, Rahul, Karthik
        for u in [users["Vignesh"], users["Arun"], users["Rahul"], users["Karthik"]]:
            db.session.add(GroupMember(group_id=g3.id, user_id=u.id))

        db.session.commit()

        print("Adding realistic sample expenses...")
        all_ids = [u.id for u in users.values()]

        # 1. Dinner (Food) ₹1200 / 4 = 300 each
        ExpenseService.create_expense(
            group_id=g1.id,
            description="Team Dinner at Fisherman Wharf",
            amount=1200.0,
            category="Food",
            paid_by=users["Vignesh"].id,
            split_type="equal",
            split_data={"users": all_ids},
        )

        # 2. Uber (Transport) ₹400 / 4 = 100 each
        ExpenseService.create_expense(
            group_id=g1.id,
            description="Uber Ride to Calangute Beach",
            amount=400.0,
            category="Transport",
            paid_by=users["Arun"].id,
            split_type="equal",
            split_data={"users": all_ids},
        )

        # 3. Hotel Resort (Travel) ₹6000
        ExpenseService.create_expense(
            group_id=g1.id,
            description="Goa Beach Resort Room",
            amount=6000.0,
            category="Travel",
            paid_by=users["Vignesh"].id,
            split_type="equal",
            split_data={"users": all_ids},
        )

        # 4. Movie (Entertainment) ₹800
        ExpenseService.create_expense(
            group_id=g3.id,
            description="PVR Movie Tickets",
            amount=800.0,
            category="Entertainment",
            paid_by=users["Rahul"].id,
            split_type="equal",
            split_data={"users": [users["Vignesh"].id, users["Arun"].id, users["Rahul"].id, users["Karthik"].id]},
        )

        # 5. Groceries (Food) ₹1500
        ExpenseService.create_expense(
            group_id=g2.id,
            description="Supermarket Monthly Groceries",
            amount=1500.0,
            category="Food",
            paid_by=users["Arun"].id,
            split_type="equal",
            split_data={"users": [users["Vignesh"].id, users["Arun"].id, users["Rahul"].id]},
        )

        # 6. Electricity (Utilities) ₹900
        ExpenseService.create_expense(
            group_id=g2.id,
            description="Electricity Bill Payment",
            amount=900.0,
            category="Utilities",
            paid_by=users["Vignesh"].id,
            split_type="equal",
            split_data={"users": [users["Vignesh"].id, users["Arun"].id, users["Rahul"].id]},
        )

        print("Recording sample settlement...")
        SettlementService.record_settlement(
            group_id=g1.id,
            payer_id=users["Arun"].id,
            receiver_id=users["Vignesh"].id,
            amount=500.0,
        )

        print("Creating sample recurring expense...")
        RecurringService.create_recurring_expense(
            group_id=g2.id,
            description="Flat Wifi Internet Bill",
            amount=799.0,
            frequency="monthly",
            next_due_date=datetime.now(timezone.utc) + timedelta(days=5),
            category="Utilities",
            creator_id=users["Vignesh"].id,
        )

        print("Database seeded successfully!")


if __name__ == "__main__":
    seed()
