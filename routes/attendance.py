from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import current_user
from extensions import db
from models import Subject, Student, AttendanceSession, AttendanceRecord
from utils import roles, log, can_edit, roster, counts, upsert
from constants import P, A, V, MODES

bp = Blueprint('attendance', __name__)

@bp.route('/start', methods=['GET', 'POST'])
@roles('teacher', 'cr')
def start():
    if request.method == 'POST':
        name, mode = request.form.get('subject', '').strip(), request.form.get('mode')
        try:
            lec = int(request.form.get('lecture', ''))
            d = date.fromisoformat(request.form.get('date', ''))
        except ValueError:
            flash('Enter a valid lecture number and date.', 'error'); return redirect(url_for('attendance.start'))
        if not name or lec < 1 or mode not in MODES:
            flash('Subject, lecture and mode are required.', 'error'); return redirect(url_for('attendance.start'))
        sub = Subject.query.filter(db.func.lower(Subject.name) == name.lower()).first()
        if not sub: sub = Subject(name=name); db.session.add(sub); db.session.flush()
        s = AttendanceSession.query.filter_by(subject_id=sub.id, lecture=lec, date=d).first()
        if s: flash('Session already exists – resumed it instead of creating a duplicate.', 'ok')
        else:
            s = AttendanceSession(subject_id=sub.id, lecture=lec, date=d, created_by=current_user.id)
            db.session.add(s); db.session.flush(); log(s.id, 'created')
        db.session.commit()
        return redirect(url_for('attendance.session_view', i=s.id, mode=mode))
    return render_template('attendance/start.html', subjects=Subject.query.order_by(Subject.name).all(),
                           today=date.today().isoformat(), mode=request.args.get('mode', 'voice_roll'), MODES=MODES)

@bp.route('/session/<int:i>')
@roles('teacher', 'cr')
def session_view(i):
    s = db.get_or_404(AttendanceSession, i)
    recs = {r.student_id: r.status for r in AttendanceRecord.query.filter_by(session_id=i)}
    data = dict(sid=i, mode=request.args.get('mode', 'manual'), role=current_user.role, canEdit=can_edit(s),
                roster=[dict(id=x.id, roll=x.roll, name=x.name, status=recs.get(x.id)) for x in roster(s)])
    return render_template('attendance/session.html', s=s, data=data, MODES=MODES)

def api_session(i, edit=True):
    s = db.get_or_404(AttendanceSession, i)
    if edit and not can_edit(s): abort(403)
    return s

@bp.route('/api/session/<int:i>/mark', methods=['POST'])
@roles('teacher', 'cr')
def api_mark(i):
    s = api_session(i); j = request.get_json(silent=True) or {}
    st = db.session.get(Student, j.get('student_id'))
    if not st or j.get('status') not in (P, A, V): abort(400)
    upsert(i, st.id, j['status'])
    return jsonify(ok=True)

@bp.route('/api/session/<int:i>/bulk', methods=['POST'])
@roles('teacher', 'cr')
def api_bulk(i):
    s = api_session(i); act = (request.get_json(silent=True) or {}).get('action')
    recs = {r.student_id: r for r in AttendanceRecord.query.filter_by(session_id=i)}
    for x in roster(s):
        r = recs.get(x.id)
        if act == 'all_present': new = P
        elif act == 'rest_absent' and not r: new = A
        else: continue
        if r: r.status, r.updated_at = new, datetime.utcnow()
        else: db.session.add(AttendanceRecord(session_id=i, student_id=x.id, status=new))
    log(i, 'bulk ' + str(act)); db.session.commit()
    return jsonify(ok=True)

@bp.route('/api/session/<int:i>/state', methods=['POST'])
@roles('teacher', 'cr')
def api_state(i):
    """action: autosave | draft | submit | finalize | reopen"""
    s = db.get_or_404(AttendanceSession, i); j = request.get_json(silent=True) or {}; act = j.get('action')
    if act == 'reopen':
        if current_user.role != 'teacher' or s.status != 'finalized' or not (j.get('reason') or '').strip(): abort(400)
        s.status = 'draft'; log(i, 'reopened', j['reason'][:300])
    elif act == 'finalize':
        if current_user.role != 'teacher' or s.status == 'finalized': abort(403)
        c = counts(s)
        if c[V] or c['unreviewed']:
            return jsonify(ok=False, error=f"Review first: {c[V]} pending, {c['unreviewed']} unreviewed."), 400
        s.status, s.finalized_by = 'finalized', current_user.id; log(i, 'finalized')
    elif act in ('autosave', 'draft', 'submit'):
        if not can_edit(s): abort(403)
        if act == 'submit' or (act == 'autosave' and current_user.role == 'cr'):
            s.status, s.submitted_by = 'submitted', current_user.id; log(i, 'submitted')
        else: s.status = 'draft'
    else: abort(400)
    s.updated_at = datetime.utcnow(); db.session.commit()
    return jsonify(ok=True, status=s.status, counts=counts(s))
