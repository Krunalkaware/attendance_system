# MCA Attendance System (Flask)

## Structure
```
mca_attendance/
├── app.py            # app factory (create_app) + entry point
├── config.py         # settings (DB URL, secret key)
├── extensions.py     # db, csrf, login_manager, migrate
├── cli.py            # flask init-db / create-user
├── constants.py      # statuses (P/A/V) and attendance modes
├── utils.py          # role decorator, audit log, counts, upsert helpers
├── requirements.txt
├── sample_roster.csv
├── models/           # DB table schemas, one file per table
│   ├── user.py  student.py  subject.py  attendance.py  audit.py
├── routes/           # one blueprint per feature
│   ├── auth.py  dashboard.py  students.py  attendance.py  reports.py
├── templates/        # base.html + one folder per feature
│   ├── auth/  dashboards/  students/  attendance/  reports/
├── static/ css/  js/attendance.js  images/
└── migrations/       # created by `flask db init` (below)
```

## Run (Windows / PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app init-db
flask --app app create-user
flask --app app run
```
Database: PostgreSQL `localhost:2005` (override with `DATABASE_URL`). Open http://127.0.0.1:5000 in Chrome/Edge.

## Migrations (when you change a model later)
```powershell
flask --app app db init       # once; creates migrations/
flask --app app db migrate -m "change description"
flask --app app db upgrade
```
(If tables already exist from `init-db`, run `flask --app app db stamp head` after `db migrate` on a first run.)

## Login
Teacher/CR: the account made with `create-user`. Student: username = roll number, password = roll number.
