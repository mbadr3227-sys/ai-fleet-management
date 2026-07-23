from flask import Flask, render_template, request, redirect, session
import sqlite3
from openai import OpenAI
import os
from dotenv import load_dotenv
import random
from datetime import date

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = Flask(__name__)

app.secret_key = "driver_secret_key"

def get_db_connection():
    conn = sqlite3.connect("driver_system.db")
    conn.row_factory = sqlite3.Row
    return conn

drivers_data = [
    {"id": 1, "name": "Ahmed", "license": "B"},
    {"id": 2, "name": "Mohamed", "license": "C"},
    {"id": 3, "name": "Ali", "license": "D"}
]

vans_data = [
    {"reg": "AB12 XYZ", "model": "Ford Transit", "status": "Available"},
    {"reg": "CD34 VAN", "model": "Mercedes Sprinter", "status": "In Use"}
]

availability_data = [
    {"driver": "Ahmed", "day": "Monday", "time": "09:00 - 17:00"},
    {"driver": "Mohamed", "day": "Tuesday", "time": "10:00 - 18:00"}
]

@app.route("/")
def home():
    conn = get_db_connection()

    total_drivers = conn.execute(
        "SELECT COUNT(*) FROM drivers"
    ).fetchone()[0]

    total_vans = conn.execute(
        "SELECT COUNT(*) FROM vans"
    ).fetchone()[0]

    assigned_today = conn.execute("""
        SELECT COUNT(*)
        FROM driver_van_log
        WHERE work_date = date('now')
    """).fetchone()[0]

    available_today = total_vans - assigned_today

    utilisation = round((assigned_today / total_vans) * 100, 1) if total_vans > 0 else 0

    ai_insight = f"Fleet utilisation today is {utilisation}%. {available_today} van(s) are still available."

    conn.close()

    return render_template(
        "index.html",
        total_drivers=total_drivers,
        total_vans=total_vans,
        assigned_today=assigned_today,
        available_today=available_today,
        ai_insight=ai_insight
    )

@app.route("/drivers")
def drivers():
    conn = get_db_connection()
    drivers = conn.execute("SELECT * FROM drivers").fetchall()
    conn.close()
    return render_template("drivers.html", drivers=drivers)

@app.route("/vans")
def vans():
    conn = get_db_connection()
    vans = conn.execute("SELECT * FROM vans").fetchall()
    conn.close()
    return render_template("vans.html", vans=vans)

@app.route("/availability")
def availability():
    conn = get_db_connection()
    availability = conn.execute("SELECT * FROM availability").fetchall()
    conn.close()
    return render_template(
        "availability.html",
        availability=availability
    )

@app.route("/delete_driver/<int:id>")
def delete_driver(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM drivers WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/drivers")

@app.route("/edit_driver/<int:id>", methods=["GET", "POST"])
def edit_driver(id):
    conn = get_db_connection()
    driver = conn.execute(
        "SELECT * FROM drivers WHERE id = ?",
        (id,)
    ).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        license = request.form["license"]

        conn.execute(
            "UPDATE drivers SET name = ?, license = ? WHERE id = ?",
            (name, license, id)
        )
        conn.commit()
        conn.close()

        return redirect("/drivers")

    conn.close()
    return render_template("edit_driver.html", driver=driver)

@app.route("/add_driver", methods=["GET", "POST"])
def add_driver():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]

        license = "N/A"

        user_id = str(random.randint(1000, 9999))

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO drivers (name, license, email, user_id, phone) VALUES (?, ?, ?, ?, ?)",
            (name, license, email, user_id, phone)
        )
        conn.commit()
        conn.close()

        return redirect("/drivers")

    return render_template("add_driver.html")

@app.route("/add_van", methods=["GET", "POST"])
def add_van():
    if request.method == "POST":
        reg = request.form["reg"]
        model = request.form["model"]
        status = request.form["status"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO vans (reg, model, status) VALUES (?, ?, ?)",
            (reg, model, status)
        )
        conn.commit()
        conn.close()

        return redirect("/vans")

    return render_template("add_van.html")

@app.route("/delete_van", methods=["POST"])
def delete_van():
    reg = request.form["reg"]

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM vans WHERE reg = ?",
        (reg,)
    )
    conn.commit()
    conn.close()

    return redirect("/vans")

@app.route("/add_availability", methods=["GET", "POST"])
def add_availability():
    if request.method == "POST":
        driver = request.form["driver"]
        day = request.form["day"]
        time = request.form["time"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO availability (driver, day, time) VALUES (?, ?, ?)",
            (driver, day, time)
        )
        conn.commit()
        conn.close()
        return redirect("/availability")

    return render_template("add_availability.html")

@app.route("/delete_availability", methods=["POST"])
def delete_availability():
    driver = request.form["driver"]

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM availability WHERE driver = ?",
        (driver,)
    )
    conn.commit()
    conn.close()

    return redirect("/availability")
@app.route("/driver_login", methods=["GET", "POST"])
def driver_login():
    if request.method == "POST":
        email = request.form["email"]
        user_id = request.form["user_id"]

        conn = get_db_connection()

        driver = conn.execute(
            "SELECT * FROM drivers WHERE email = ? AND user_id = ?",
            (email, user_id)
        ).fetchone()

        conn.close()

        if driver:
            session["driver_name"] = driver["name"]
            session["driver_email"] = driver["email"]
            session["driver_id"] = driver["user_id"]

            return redirect("/driver_dashboard")

    return render_template("driver_login.html")

@app.route("/driver_dashboard", methods=["GET", "POST"])
def driver_dashboard():

    if "driver_name" not in session:
        return redirect("/driver_login")

    conn = get_db_connection()

    vans = conn.execute("""
    SELECT * FROM vans
    WHERE reg NOT IN (
        SELECT van_reg
        FROM driver_van_log
        WHERE work_date = date('now')
    )
    """).fetchall()

    conn.close()

    if request.method == "POST":
        van_reg = request.form["van_reg"]
        work_date = request.form["work_date"]
        shift_time = request.form["shift_time"]
        notes = request.form["notes"]

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO driver_van_log
            (driver_name, driver_email, van_reg, work_date, shift_time, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["driver_name"],
            session["driver_email"],
            van_reg,
            work_date,
            shift_time,
            notes
        ))
        conn.commit()
        conn.close()

        return redirect("/driver_dashboard")

    return render_template(
        "driver_dashboard.html",
        name=session["driver_name"],
        email=session["driver_email"],
        user_id=session["driver_id"],
        vans=vans,
        today=date.today().isoformat()
    )

@app.route("/van_history", methods=["GET", "POST"])
def van_history():
    records = []

    if request.method == "POST":
        search_date = request.form["work_date"]

        conn = get_db_connection()
        records = conn.execute(
            "SELECT * FROM driver_van_log WHERE work_date = ?",
            (search_date,)
        ).fetchall()
        conn.close()

    return render_template("van_history.html", records=records)

@app.route("/current_allocations")
def current_allocations():

    conn = get_db_connection()

    records = conn.execute("""
        SELECT *
        FROM driver_van_log
        WHERE work_date = date('now')
    """).fetchall()

    conn.close()

    return render_template(
        "current_allocations.html",
        records=records
    )

@app.route("/ai_assistant", methods=["GET", "POST"])
def ai_assistant():
    answer = ""

    if request.method == "POST":
        question = request.form["question"]

        try:
           conn = get_db_connection()

           total_drivers = conn.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
           total_vans = conn.execute("SELECT COUNT(*) FROM vans").fetchone()[0]

           assigned_today = conn.execute("""
               SELECT driver_name, driver_email, van_reg, work_date, shift_time, notes
               FROM driver_van_log
               WHERE work_date = date('now')
           """).fetchall()

           available_vans = conn.execute("""
               SELECT reg, model
               FROM vans
               WHERE reg NOT IN (
                   SELECT van_reg
                   FROM driver_van_log
                   WHERE work_date = date('now')
               )
           """).fetchall()

           conn.close()

           fleet_context = f"""
Fleet data:
Total drivers: {total_drivers}
Total vans: {total_vans}
Assigned vans today: {len(assigned_today)}
Available vans today: {len(available_vans)}

Assigned today:
{[dict(row) for row in assigned_today]}

Available vans:
{[dict(row) for row in available_vans]}
"""

           completion = client.chat.completions.create(
               model="gpt-4.1-mini",
               messages=[
                   {
                       "role": "system",
                       "content": """
You are a professional AI Fleet Management Assistant.
Answer naturally like ChatGPT.
Use the fleet data provided to answer questions about drivers, vans, allocation, availability, and daily fleet status.
If the user writes with spelling mistakes, understand their meaning and answer clearly.
Keep answers professional and simple.
"""
                   },
                   {
                       "role": "user",
                       "content": fleet_context + "\nUser question: " + question
                   }
               ]
           )

           answer = completion.choices[0].message.content

        except Exception as e:
            answer = str(e)

    return render_template("ai_assistant.html", answer=answer)

def setup_database():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            license TEXT NOT NULL,
            email TEXT,
            uswe_id TEXT
        )
    """)

    count = conn.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]

    if count == 0:
        conn.execute("INSERT INTO drivers (name, license) VALUES (?, ?)", ("Ahmed", "B"))
        conn.execute("INSERT INTO drivers (name, license) VALUES (?, ?)", ("Mohamed", "C"))
        conn.execute("INSERT INTO drivers (name, license) VALUES (?, ?)", ("Ali", "D"))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
    app.run(host="0.0.0.0", port=5000)
