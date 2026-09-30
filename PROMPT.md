# EXPENSESHARE AI — MASTER BUILD & ARCHITECTURE PROMPT

Use the following master prompt to build, instruct an AI assistant, or document the complete **ExpenseShare AI** application architecture:

```text
Build a complete production-ready full-stack web application called:

ExpenseShare AI

Tagline: Smart Group Expense Management, AI-Powered Expense Categorization, Financial Analytics and Intelligent Settlement.

================================================================================
1. CORE ARCHITECTURE & TECH STACK
================================================================================
- Backend: Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Werkzeug, Pydantic
- Database: SQLite (Development/Testing), PostgreSQL-compatible SQLAlchemy models
- Frontend: HTML5, CSS3, Jinja2, Bootstrap 5, Bootstrap Icons, Chart.js
- Machine Learning: Scikit-learn, TF-IDF Vectorizer + Logistic Regression, Joblib
- NLP & AI: Natural Language Expense Parser with custom pattern extraction and AI prompt structure
- OCR: Pytesseract, Pillow OCR extraction with regex line parsing
- Testing: Pytest (100% test pass requirement across all modules)
- DevOps: Dockerfile, docker-compose.yml, environment variable management (.env)

================================================================================
2. DATABASE MODEL SCHEMAS
================================================================================
- User: id, name, email (unique, index), password_hash, profile_image, created_at, updated_at.
- Group: id, name, description, created_by (FK -> User), created_at.
- GroupMember: id, group_id (FK -> Group), user_id (FK -> User), joined_at. Unique constraint on (group_id, user_id).
- Expense: id, group_id (FK), description, amount, category, paid_by (FK -> User), expense_date, notes, receipt_image, created_at.
- ExpenseSplit: id, expense_id (FK), user_id (FK), split_type (equal, exact, percentage, shares), amount, percentage, shares.
- Settlement: id, group_id (FK), payer_id (FK), receiver_id (FK), amount, status, settled_at, created_at.
- RecurringExpense: id, group_id (FK), description, amount, frequency (daily, weekly, monthly, yearly), next_due_date, category, created_by (FK), active.
- Notification: id, user_id (FK), title, message, type, is_read, created_at.

================================================================================
3. CORE MODULES & FEATURES TO IMPLEMENT
================================================================================
1. Authentication: Registration, login, logout, password hashing, Flask-Login session management, CSRF protection.
2. Group Management: Group creation, listing, detail view, member roster, invite member by email, member removal.
3. Split Engine:
   - Equal Split: A / N with cent rounding adjustment.
   - Exact Split: Sum validation = total expense amount.
   - Percentage Split: Sum validation = 100%.
   - Shares Split: Proportional weighted parts (amount * shares / total_shares).
4. Balance Engine: Net balance formula = (total_paid - total_owed) + settlements_paid - settlements_received.
5. Smart Debt Simplification: Greedy matching algorithm to minimize multi-party circular transactions into minimal settlement payments.
6. Fintech Dashboard & Analytics: Summary cards (Net Balance, You Owe, You Are Owed, Total Group Expenses), Chart.js category doughnut chart, 6-month spending trend line chart, group comparison bar chart, and automated spending insights statements.
7. ML Expense Categorization: Scikit-learn TF-IDF + Logistic Regression trained on sample_expenses.csv to classify Food, Transport, Shopping, Entertainment, Utilities, Travel, Rent, Other with confidence scores.
8. AI Natural-Language Expense Entry: Natural language parser (e.g. "I paid ₹1200 for dinner with Arun and Rahul") producing structured confirmation cards.
9. Duplicate Detection: SequenceMatcher text similarity, 5%/₹1.00 amount delta thresholds, date proximity, and same-payer checks.
10. Receipt OCR Scanner: Upload image/PDF, extract vendor, total amount, date, ML category prediction, and show edit/confirm card.
11. Expense Forecasting: Weighted moving average time-series projection for next-month spending.
12. Anomaly Detection: Statistical Interquartile Range (Q3 + 1.5 * IQR) outlier detection for unusually large expenses.
13. Recurring Expenses: Automated processing for daily, weekly, monthly, and yearly bills (rent, wifi, subscriptions).
14. In-App Notifications: Notification center with unread badge counter in navbar, settlement alerts, and bill reminders.
15. Data Export: Export filtered expenses to CSV.
16. RESTful API: Complete JSON endpoints for auth, groups, expenses, balances, settlements, analytics, ML, and AI parsing under /api/.
17. Seed Script: Pre-populate database with users (Vignesh, Arun, Rahul, Karthik), groups, expenses, settlements, and recurring bills.
18. Docker & Documentation: Production Dockerfile, docker-compose.yml, and comprehensive README.md.
```
