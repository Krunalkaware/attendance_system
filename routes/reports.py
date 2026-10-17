import csv, io
from datetime import date
from flask import Blueprint, render_template, request, Response
from sqlalchemy import or_
from extensions import db
from models import Subject, Student, AttendanceSession, AttendanceRecord
from utils import roles, roll_key
from constants import P

bp = Blueprint('reports', __name__)

def report_rows():
    q = (db.session.query(AttendanceSession, AttendanceRecord, Student).join(AttendanceRecord, AttendanceRecord.session_id == AttendanceSession.id)
         .join(Student, Student.id == AttendanceRecord.student_id))
    f = request.args
    if f.get('subject'): q = q.filter(AttendanceSession.subject_id == int(f['subject']))
    try:
        if f.get('from'): q = q.filter(AttendanceSession.date >= date.fromisoformat(f['from']))
        if f.get('to'): q = q.filter(AttendanceSession.date <= date.fromisoformat(f['to']))
    except ValueError: pass
    if f.get('q'): q = q.filter(or_(Student.roll.ilike(f"%{f['q']}%"), Student.name.ilike(f"%{f['q']}%")))
    rows = q.order_by(AttendanceSession.date.desc(), AttendanceSession.lecture).all()
    rows.sort(key=lambda r: (-r[0].date.toordinal(), r[0].lecture, roll_key(r[2].roll)))
    return rows

@bp.route('/reports')
@roles('teacher', 'cr')
def reports():
    rows, pc = report_rows(), {}
    for s, r, st in rows:
        if s.status == 'finalized':
            d = pc.setdefault(st.roll, {'name': st.name, P: 0, 'n': 0})
            d['n'] += 1; d[P] += r.status == P
    return render_template('reports/index.html', rows=rows, pc=sorted(pc.items(), key=lambda x: roll_key(x[0])),
                           subjects=Subject.query.order_by(Subject.name).all(), f=request.args)

@bp.route('/reports.csv')
@roles('teacher', 'cr')
def reports_csv():
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(['Date', 'Subject', 'Lecture', 'Roll', 'Name', 'Status', 'Session status'])
    for s, r, st in report_rows():
        w.writerow([s.date, s.subject.name, s.lecture, st.roll, st.name, r.status, s.status])
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=attendance.csv'})
