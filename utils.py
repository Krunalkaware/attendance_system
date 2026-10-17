from datetime import datetime
from functools import wraps
from flask import abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import Student, AttendanceRecord, Audit
from constants import P, A, V


def roles(*r):
    def deco(f):
        @wraps(f)
        @login_required
        def w(*a, **k):
            if current_user.role not in r: abort(403)
            return f(*a, **k)
        return w
    return deco

def log(sid, action, reason=None):
    db.session.add(Audit(user_id=current_user.id, session_id=sid, action=action, reason=reason))

def can_edit(s):
    if s.status == 'finalized': return False
    if current_user.role == 'cr' and s.status == 'submitted': return False
    return current_user.role in ('teacher', 'cr')

def roster(s):
    ids = [r.student_id for r in AttendanceRecord.query.filter_by(session_id=s.id)]
    return sorted(Student.query.filter(or_(Student.active, Student.id.in_(ids or [0]))).all(), key=lambda s: roll_key(s.roll))

def counts(s):
    c = {P: 0, A: 0, V: 0}
    for r in AttendanceRecord.query.filter_by(session_id=s.id): c[r.status] += 1
    c['unreviewed'] = len(roster(s)) - sum(c.values())
    return c

def upsert(sid, stid, status):
    for _ in range(2):
        r = AttendanceRecord.query.filter_by(session_id=sid, student_id=stid).first()
        if r: r.status, r.updated_at = status, datetime.utcnow()
        else: db.session.add(AttendanceRecord(session_id=sid, student_id=stid, status=status))
        try:
            db.session.commit(); return
        except IntegrityError: db.session.rollback()


def roll_key(r):
    """Numeric rolls sort as numbers (1, 2, 10, 100); others alphabetically after them."""
    r = str(r)
    return (0, int(r), '') if r.isdigit() else (1, 0, r.lower())
