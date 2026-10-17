from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import db
from models import Student, AttendanceSession, AttendanceRecord
from utils import counts
from constants import P, A, V, MODES

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def home():
    if current_user.role == 'student':
        rows = (db.session.query(AttendanceSession, AttendanceRecord).join(AttendanceRecord, AttendanceRecord.session_id == AttendanceSession.id)
                .filter(AttendanceRecord.student_id == current_user.student_id)
                .order_by(AttendanceSession.date.desc(), AttendanceSession.lecture.desc()).all())
        subj, tot = {}, {P: 0, A: 0, V: 0}
        for s, r in rows:
            if s.status == 'finalized':
                d = subj.setdefault(s.subject.name, {P: 0, A: 0, V: 0, 'n': 0})
                d[r.status] += 1; d['n'] += 1; tot[r.status] += 1
        n = sum(tot.values())
        pct = round(100 * tot[P] / n, 1) if n else 0
        return render_template('dashboards/student.html', rows=rows, subj=subj, tot=tot, n=n, pct=pct)
    today = AttendanceSession.query.filter_by(date=date.today()).all()
    return render_template('dashboards/staff.html', total=Student.query.filter_by(active=True).count(),
        today=today, counts={s.id: counts(s) for s in today},
        review=AttendanceSession.query.filter_by(status='submitted').order_by(AttendanceSession.date.desc()).all(),
        recent=AttendanceSession.query.order_by(AttendanceSession.created_at.desc()).limit(10).all(), MODES=MODES)
