
from flask import Flask, render_template, request, redirect, session
from db import Base, engine, SessionLocal
import models
import PyPDF2
import docx
import json

from ai import analyze_resume


app = Flask(__name__)

app.secret_key = "secret1234"

# Create database tables
Base.metadata.create_all(bind=engine)


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    if "user" in session:
        return redirect("/dashboard")

    return redirect("/login")


# ==========================================
# SIGNUP
# ==========================================


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        print("SIGNUP DATA:", email, password)

        if not email or not password:
            return "Email and password are required."

        db = SessionLocal()

        try:
            existing_user = (
                db.query(models.User)
                .filter_by(email=email)
                .first()
            )

            if existing_user:
                return "User already exists. Please login."

            new_user = models.User(
                email=email,
                password=password
            )

            db.add(new_user)
            db.commit()

            print("USER SAVED:", email)

            return redirect("/login")

        except Exception as e:

            db.rollback()

            print("SIGNUP ERROR:", e)

            return f"Signup error: {e}"

        finally:
            db.close()

    return render_template("signup.html")



# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    db = SessionLocal()

    try:

        if request.method == "POST":

            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()

            user = (
                db.query(models.User)
                .filter_by(
                    email=email,
                    password=password
                )
                .first()
            )

            if user:

                session["user"] = user.email

                return redirect("/dashboard")

            return "Invalid credentials"

        return render_template("login.html")

    except Exception as e:

        return f"Login error: {str(e)}"

    finally:

        db.close()


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":

        user_goal = request.form.get("role", "").strip()
        resume_text = request.form.get("resume", "").strip()

        # -------------------------------
        # FILE HANDLING
        # -------------------------------

        file = request.files.get("resume_file")

        if file and file.filename:

            filename = file.filename.lower()

            # PDF
            if filename.endswith(".pdf"):

                try:

                    pdf_reader = PyPDF2.PdfReader(file)

                    text = ""

                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""

                    resume_text = text.strip()

                except Exception as e:

                    result = {
                        "error": f"PDF error: {str(e)}"
                    }

            # DOCX
            elif filename.endswith(".docx"):

                try:

                    document = docx.Document(file)

                    text = ""

                    for paragraph in document.paragraphs:
                        text += paragraph.text + "\n"

                    resume_text = text.strip()

                except Exception as e:

                    result = {
                        "error": f"DOCX error: {str(e)}"
                    }

            else:

                result = {
                    "error": "Only PDF and DOCX files are supported."
                }

        # -------------------------------
        # AI ANALYSIS
        # -------------------------------

        if not result and resume_text and user_goal:

            try:

                result = analyze_resume(
                    resume_text,
                    user_goal
                )

                # -------------------------------
                # SAVE REPORT
                # -------------------------------

                db = SessionLocal()

                try:

                    user = (
                        db.query(models.User)
                        .filter_by(
                            email=session["user"]
                        )
                        .first()
                    )

                    if user:

                        report = models.Report(
                            user_id=user.id,
                            resume_text=resume_text,
                            results=json.dumps(result)
                        )

                        db.add(report)
                        db.commit()

                finally:

                    db.close()

            except Exception as e:

                result = {
                    "skills": [],
                    "missing_skills": [],
                    "roadmap": [],
                    "interview_questions": [],
                    "error": f"AI error: {str(e)}"
                }

        elif not resume_text or not user_goal:

            result = {
                "skills": [],
                "missing_skills": [],
                "roadmap": [],
                "interview_questions": [],
                "error": "Please provide both resume and career goal."
            }

    return render_template(
        "dashboard.html",
        user=session["user"],
        result=result
    )


# ==========================================
# HISTORY
# ==========================================

@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    db = SessionLocal()

    try:

        user = (
            db.query(models.User)
            .filter_by(
                email=session["user"]
            )
            .first()
        )

        if not user:
            session.pop("user", None)
            return redirect("/login")

        reports = (
            db.query(models.Report)
            .filter_by(
                user_id=user.id
            )
            .order_by(models.Report.id.desc())
            .all()
        )

        parsed_reports = []

        for report in reports:

            try:

                parsed_result = json.loads(
                    report.results
                )

            except Exception:

                parsed_result = {
                    "skills": [],
                    "missing_skills": [],
                    "roadmap": [],
                    "interview_questions": []
                }

            parsed_reports.append({
                "resume": report.resume_text,
                "result": parsed_result
            })

        return render_template(
            "history.html",
            reports=parsed_reports
        )

    finally:

        db.close()


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)
