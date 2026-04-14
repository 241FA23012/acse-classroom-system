from flask import Flask, render_template
import sqlite3
from datetime import datetime
import pandas as pd
import re

app = Flask(__name__)

# -------- 5TH FLOOR CLASSROOMS --------
FIFTH_FLOOR_ROOMS = [
"501","502","503","504","505",
"506","507","508",
"511","512","513",
"514","515","516","517","518"
]

# -------- 6TH FLOOR CLASSROOMS --------
SIXTH_FLOOR_ROOMS = [
"601A","601B","602","604","605","606","607","608",
"611","612","613",
"614","614A","614B",
"615","616","617","618",
"619A","619B"
]

# ---------------- DATABASE INIT ----------------
def init_db():

    conn = sqlite3.connect("acse.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timetable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section TEXT,
        day TEXT,
        start_time TEXT,
        end_time TEXT,
        room TEXT,
        subject TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------------- IMPORT EXCEL DATA ----------------
def insert_sample_data():

    conn = sqlite3.connect("acse.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM timetable")

    excel_file = "timetable.xlsx"

    time_slots = [
        ("08:15","09:05"),
        ("09:05","09:55"),
        ("10:10","11:00"),
        ("11:00","11:50"),
        ("11:50","12:40"),
        ("13:40","14:30"),
        ("14:30","15:20"),
        ("15:20","16:05"),
    ]

    sheets = pd.read_excel(excel_file, sheet_name=None, header=None)

    for sheet_name, df in sheets.items():

        current_section = None

        for row_index in range(len(df)):

            first_cell = str(df.iloc[row_index,0]).strip()

            if any(branch in first_cell.upper() for branch in
                   ["AIML","CSE","DS","CSBS","IT","ECE"]):

                current_section = first_cell
                continue

            day_cell = first_cell.upper()

            valid_days = {
                "MON":"MON",
                "TUE":"TUE",
                "WED":"WED",
                "THU":"THU",
                "FRI":"FRI",
                "SAT":"SAT",
                "MONDAY":"MON",
                "TUESDAY":"TUE",
                "WEDNESDAY":"WED",
                "THURSDAY":"THU",
                "FRIDAY":"FRI",
                "SATURDAY":"SAT"
            }

            if day_cell in valid_days and current_section:

                day_cell = valid_days[day_cell]

                for col_index in range(1,9):

                    cell_value = df.iloc[row_index,col_index]

                    if pd.notna(cell_value):

                        text = str(cell_value).strip()
                        lines = text.split("\n")

                        subject = lines[0]
                        room = "N/A"

                        for line in lines:

                            match = re.search(r'\b\d{3}[A-Z]?\b', line)

                            if match:

                                possible_room = match.group()

                                if possible_room in FIFTH_FLOOR_ROOMS or possible_room in SIXTH_FLOOR_ROOMS:

                                    room = possible_room
                                    break

                        start_time,end_time = time_slots[col_index-1]

                        cursor.execute("""
                        INSERT INTO timetable
                        (section,day,start_time,end_time,room,subject)
                        VALUES(?,?,?,?,?,?)
                        """,(
                            current_section,
                            day_cell,
                            start_time,
                            end_time,
                            room,
                            subject
                        ))

    conn.commit()
    conn.close()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------- ACSE PAGE ----------------
@app.route("/acse")
def acse():
    return render_template("floors.html")


# ---------------- FLOOR DASHBOARD FUNCTION ----------------
def generate_dashboard(room_list):

    conn = sqlite3.connect("acse.db")
    cursor = conn.cursor()

    current_day = datetime.now().strftime("%a").upper()
    current_time = datetime.now().strftime("%H:%M")

    room_status_list = []

    for room in room_list:

        cursor.execute("""
        SELECT section,subject FROM timetable
        WHERE room=?
        AND day=?
        AND start_time<=?
        AND end_time>?
        """,(room,current_day,current_time,current_time))

        current_class = cursor.fetchone()

        cursor.execute("""
        SELECT section,subject,start_time FROM timetable
        WHERE room=?
        AND day=?
        AND start_time>?
        ORDER BY start_time ASC
        LIMIT 1
        """,(room,current_day,current_time))

        next_class = cursor.fetchone()

        room_status_list.append({

            "room":room,
            "occupied": True if current_class else False,
            "section": current_class[0] if current_class else "",
            "subject": current_class[1] if current_class else "",
            "next_section": next_class[0] if next_class else "",
            "next_subject": next_class[1] if next_class else "",
            "next_time": next_class[2] if next_class else ""

        })

    conn.close()

    return render_template(
        "dashboard.html",
        rooms=room_status_list,
        current_day=current_day,
        current_time=current_time
    )


# ---------------- FLOOR ROUTES ----------------
@app.route("/floor5")
def floor5():
    return generate_dashboard(FIFTH_FLOOR_ROOMS)


@app.route("/floor6")
def floor6():
    return generate_dashboard(SIXTH_FLOOR_ROOMS)


# ---------------- MAIN ----------------
# ---------------- MAIN ----------------
if __name__ == "__main__":

    init_db()
    insert_sample_data()

    app.run(host="0.0.0.0", port=10000, debug=True)