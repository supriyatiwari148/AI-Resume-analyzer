# AI Career Copilot

AI Career Copilot is a Flask web application that analyzes a user's resume against a target career goal using a locally-hosted LLM (via [Ollama](https://ollama.com/)). It identifies relevant skills, highlights missing skills, generates a personalized learning roadmap, and produces role-specific interview questions — then saves every analysis to a per-user history.

## Features

- **User authentication** — simple email/password signup and login with session-based access control
- **Resume input** — paste resume text directly, or upload a `.pdf` or `.docx` file for automatic text extraction
- **AI-powered analysis** — a local LLM (`llama3.2:3b` via Ollama) evaluates the resume against the stated career goal and returns:
  - Relevant skills found in the resume
  - Missing skills for the target role
  - A learning roadmap to close the gap
  - Suggested interview questions for the target role
- **Analysis history** — every report is persisted and viewable later from the History page
- **Graceful error handling** — clear feedback when the AI service is unavailable, times out, or returns malformed data

## Tech Stack

| Layer         | Technology                          |
|---------------|--------------------------------------|
| Backend       | Python, Flask                       |
| Database      | MySQL-compatible (TiDB Cloud), SQLAlchemy ORM |
| AI / LLM      | Ollama (local inference, `llama3.2:3b`) |
| File parsing  | PyPDF2 (PDF), python-docx (DOCX)    |
| Frontend      | Jinja2 templates, HTML, CSS         |

## Project Structure

```
AI/
├── app.py              # Flask routes: auth, dashboard, history, logout
├── ai.py                # Resume analysis logic (calls the Ollama API)
├── db.py                # SQLAlchemy engine/session configuration
├── models.py             # User and Report ORM models
├── init_db.py            # One-off script to create database tables
├── test_ollama.py        # Quick script to verify the Ollama connection
├── static/
│   └── style.css         # Application styling
├── templates/
│   ├── base.html          # Shared layout and navigation
│   ├── login.html         # Login page
│   ├── signup.html        # Signup page
│   ├── dashboard.html      # Resume upload/paste + analysis results
│   └── history.html        # Past analysis reports
└── ca.pem                 # TLS CA certificate for the database connection
```

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running locally, with the `llama3.2:3b` model pulled:
  ```bash
  ollama pull llama3.2:3b
  ```
- Access to a MySQL-compatible database (the project is configured for [TiDB Cloud](https://tidbcloud.com/))

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask sqlalchemy pymysql PyPDF2 python-docx requests
   ```

4. **Configure the database connection**

   Database credentials are currently defined directly in `db.py`. Before running the app, replace the placeholder connection details with your own, and update the certificate path to point at your local copy of `ca.pem`:
   ```python
   DATABASE_URL = "mysql+pymysql://<user>:<password>@<host>:<port>/<database>"
   ```
   > **Recommended:** move these values into environment variables (e.g. with `python-dotenv`) rather than committing them to source control, and use `os.environ` to load them in `db.py`.

5. **Initialize the database tables**
   ```bash
   python init_db.py
   ```

6. **Start Ollama** (in a separate terminal, if not already running)
   ```bash
   ollama serve
   ```

7. **Run the application**
   ```bash
   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000`.

## Usage

1. Sign up for an account, then log in.
2. On the Dashboard, either paste your resume text or upload a `.pdf`/`.docx` file.
3. Enter your target role or career goal (e.g. *"Java Backend Developer"*).
4. Submit the form to receive your relevant skills, skill gaps, roadmap, and interview questions.
5. Visit the History page at any time to review past analyses.

## Known Limitations & Suggested Improvements

This project was built as a functional prototype. Before any production or public deployment, consider addressing the following:

- **Plaintext passwords** — user passwords are currently stored and compared as plain text. Use a hashing library such as `werkzeug.security` or `bcrypt`.
- **Hardcoded secret key** — `app.secret_key` is a static string in `app.py`. Generate a strong random key and load it from an environment variable.
- **Hardcoded database credentials** — move the contents of `db.py`'s `DATABASE_URL` (and the certificate path) into environment variables or a `.env` file excluded from version control.
- **No `requirements.txt`** — consider running `pip freeze > requirements.txt` in a clean virtual environment to pin dependencies for reproducible installs.
- **Debug mode** — `app.run(debug=True)` should be disabled in production.
