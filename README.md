# ExpenseShare AI

> **Smart Group Expense Management, AI-Powered Expense Categorization, Financial Analytics and Intelligent Settlement.**

ExpenseShare AI is a production-grade full-stack web application designed for group expense management, multi-method debt splitting, automated debt simplification, time-series spending forecasting, statistical anomaly detection, AI natural language expense entry, and receipt OCR processing.

---

## Key Features

- **Authentication & User Management**: Secure registration, login session persistence, password hashing via Werkzeug, and CSRF protection.
- **Group Management**: Create, edit, and manage groups, invite members by email, and maintain member rosters.
- **Expense Recording & Multi-Method Split Engine**:
  - Equal split ($A / N$ with cent rounding adjustment)
  - Exact split (exact per-user amounts)
  - Percentage split (percentage validation totaling 100%)
  - Shares split (proportional weighted parts)
- **Balance Calculation Engine**: Net balance computation (`total_paid - total_owed + settlements_paid - settlements_received`).
- **Smart Debt Simplification Algorithm**: Transaction minimization using greedy matching to reduce circular group debts into minimal settlements.
- **Fintech Dashboard & Analytics**: Interactive Chart.js category distribution doughnut charts, 6-month spending trend line charts, group comparisons, and dynamic AI insight statements.
- **Machine Learning Category Classifier**: TF-IDF Vectorizer + Logistic Regression pipeline predicting expense categories (`Food`, `Transport`, `Shopping`, `Entertainment`, `Utilities`, `Travel`, `Rent`, `Other`) with confidence scores.
- **AI Natural-Language Expense Parser**: Natural language expense entry (e.g. *"I paid ₹1200 for dinner with Arun and Rahul"*) extracting amounts, descriptions, categories, and participants.
- **Duplicate Expense Detection**: SequenceMatcher text similarity, 5%/₹1.00 amount delta thresholds, date proximity, and same-payer matching to prevent double entries.
- **Receipt OCR**: Image/PDF scanner using `pytesseract` and `Pillow` to extract vendor names, total amounts, dates, and categories.
- **Expense Forecasting**: Weighted moving average time-series projection for next-month spending.
- **Anomaly Detection**: Statistical Interquartile Range ($Q3 + 1.5 \times IQR$) outlier detection for unusually large expenses.
- **Recurring Expenses**: Automated processing for daily, weekly, monthly, and yearly bills (rent, wifi, subscriptions).
- **In-App Notification Center**: Unread notification badge counter, settlement alerts, and bill reminders.
- **CSV Data Export**: One-click expense export matching filters.
- **RESTful API**: Comprehensive API endpoints returning JSON with standard HTTP status codes.

---

## Tech Stack

- **Backend**: Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Werkzeug, Pydantic
- **Database**: SQLite (Development/Testing), PostgreSQL-ready SQLAlchemy models
- **Frontend**: HTML5, CSS3, JavaScript, Jinja2, Bootstrap 5, Bootstrap Icons, Chart.js
- **Machine Learning & NLP**: Scikit-Learn, NumPy, Pandas, Joblib, Regex NLP Engine
- **OCR**: Pytesseract, Pillow
- **Testing & DevOps**: Pytest, Docker, Docker Compose, Git

---

## Project Structure

```text
ExpenseShare/
├── app/
│   ├── __init__.py           # Application Factory & Blueprint Registration
│   ├── config.py             # Config classes (Dev, Testing, Prod)
│   ├── extensions.py         # Flask extensions (db, migrate, login_manager, csrf)
│   ├── models/               # SQLAlchemy Models (User, Group, Expense, Settlement, etc.)
│   ├── routes/               # Flask Blueprints (auth, groups, expenses, settlements, analytics, ai, ocr, api, etc.)
│   ├── services/             # Business Logic Services (ExpenseService, SplitService, BalanceService, SettlementService, etc.)
│   ├── ml/                   # Machine Learning & Statistical Modules (predict_category, forecasting, anomaly_detector, duplicate_detector)
│   ├── ai/                   # AI Natural Language Parser & Prompts
│   ├── ocr/                  # Receipt Processing & Text Extractor
│   ├── templates/            # Jinja2 HTML Templates
│   └── static/               # CSS, JS, and Assets
├── data/                     # Raw & Processed Datasets (sample_expenses.csv)
├── models/                   # Serialized ML Models (.pkl)
├── scripts/                  # Seed Script & Model Training Script
├── tests/                    # Pytest Suite (47 passing unit tests)
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── Dockerfile                # Production Docker build container
├── docker-compose.yml        # Docker Compose orchestration
└── run.py                    # Entry point script
```

---

## Quick Start & Installation

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-username/ExpenseShare-AI.git
cd ExpenseShare-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

### 3. Train ML Models

```bash
python scripts/train_models.py
```

### 4. Seed Database

```bash
python scripts/seed_database.py
```

*Default Seed Credentials:*
- `vignesh@example.com` / `Password123`
- `arun@example.com` / `Password123`
- `rahul@example.com` / `Password123`
- `karthik@example.com` / `Password123`

### 5. Run Application

```bash
python run.py
```

Access application at `http://127.0.0.1:5000`.

---

## Running Test Suite

Run the full pytest suite (47 tests):

```bash
pytest tests/
```

---

## Docker Deployment

Build and run using Docker Compose:

```bash
docker compose up --build
```

---

## REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Authenticate user |
| `GET` | `/api/groups` | List user's groups |
| `POST` | `/api/groups` | Create group |
| `GET` | `/api/expenses` | List/Filter expenses |
| `POST` | `/api/expenses` | Create expense |
| `GET` | `/api/balances` | User/Group net balances |
| `POST` | `/api/settlements` | Record debt settlement |
| `GET` | `/api/analytics` | Analytics summary & insights |
| `POST` | `/api/ml/predict-category` | Predict expense category |
| `POST` | `/api/ai/parse-expense` | Parse natural language expense text |

---

## Author

Developed by **Vignesh Rahul E**.
