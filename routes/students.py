import csv, io, re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Student, User, AttendanceRecord, AttendanceSession
from utils import roles, roll_key

bp = Blueprint('students', __name__)
ROLL_KEYS = {'roll', 'rollno', 'rollnumber', 'rollnum', 'enrollment', 'enrollmentno', 'regno', 'registrationno', 'studentid', 'id'}
NAME_KEYS = {'name', 'studentname', 'fullname', 'candidatename', 'nameofstudent', 'studentfullname'}
MAIL_KEYS = {'email', 'emailid', 'mail', 'emailaddress'}
HOME = lambda: redirect(url_for('students.students'))


def _norm(h): return re.sub(r'[^a-z0-9]', '', (h or '').lower())


def _clean_roll(v):
    v = (v or '').strip()
    return v[:-2] if re.fullmatch(r'\d+\.0', v) else v   # Excel turns 101 into 101.0


@bp.route('/students')
@roles('teacher', 'cr')
def students():
    rows = sorted(Student.query.all(), key=lambda s: roll_key(s.roll))   # numeric order: 1, 2, 10, 100
    return render_template('students/list.html', rows=rows)


@bp.route('/students/add', methods=['POST'])
@roles('teacher')
def student_add():
    roll, name = request.form.get('roll', '').strip(), request.form.get('name', '').strip()
    if not roll or not name: flash('Roll and name are required.', 'error')
    elif Student.query.filter_by(roll=roll).first(): flash('Roll number already exists.', 'error')
    else:
        db.session.add(Student(roll=roll, name=name, email=request.form.get('email', '').strip() or None))
        db.session.commit(); flash('Student added (login = roll number).', 'ok')
    return HOME()


@bp.route('/students/<int:i>', methods=['POST'])
@roles('teacher')
def student_edit(i):
    st = db.get_or_404(Student, i)
    if request.form.get('toggle'): st.active = not st.active
    elif request.form.get('name', '').strip():
        st.name = request.form['name'].strip(); st.email = request.form.get('email', '').strip() or None
    db.session.commit(); return HOME()


@bp.route('/students/upload', methods=['POST'])
@roles('teacher')
def student_upload():
    f = request.files.get('file')
    if not f or not f.filename:
        flash('Choose a CSV file.', 'error'); return HOME()
    raw = f.stream.read()
    for enc in ('utf-8-sig', 'utf-16', 'cp1252'):
        try: text = raw.decode(enc); break
        except UnicodeError: continue
    try: dialect = csv.Sniffer().sniff(text[:2048], delimiters=',;\t|')
    except csv.Error: dialect = csv.excel
    rows = [r for r in csv.reader(io.StringIO(text), dialect) if any(c.strip() for c in r)]
    if not rows:
        flash('The file is empty.', 'error'); return HOME()
    heads = [_norm(c) for c in rows[0]]
    ri = next((i for i, h in enumerate(heads) if h in ROLL_KEYS), None)
    ni = next((i for i, h in enumerate(heads) if h in NAME_KEYS), None)
    ei = next((i for i, h in enumerate(heads) if h in MAIL_KEYS), None)
    if ri is not None and ni is not None: data = rows[1:]
    else:
        ri, ni, ei = 0, 1, 2
        data = rows if re.search(r'\d', rows[0][0] if rows[0] else '') else rows[1:]
    existing = {r for (r,) in db.session.query(Student.roll)}     # one query, not one per row
    new, ok, skip, bad, problems = [], 0, 0, 0, []
    for n, row in enumerate(data, start=2):
        get = lambda i: row[i].strip() if i is not None and i < len(row) else ''
        roll, name, email = _clean_roll(get(ri)), get(ni), get(ei)
        if not roll or not name or len(roll) > 20:
            bad += 1
            if len(problems) < 3: problems.append(f"row {n}: roll='{roll}' name='{name}'")
        elif roll in existing: skip += 1
        else:
            existing.add(roll); new.append(Student(roll=roll, name=name, email=email or None)); ok += 1
    db.session.add_all(new); db.session.commit()
    msg = f'Import: {ok} added, {skip} skipped (duplicate), {bad} invalid.'
    if problems: msg += ' Examples: ' + '; '.join(problems)
    flash(msg, 'ok' if ok else 'error')
    return HOME()


@bp.route('/students/<int:i>/delete', methods=['POST'])
@roles('teacher')
def student_delete(i):
    st = db.get_or_404(Student, i); name = st.name
    AttendanceRecord.query.filter_by(student_id=i).delete()      # permanent: nothing is kept
    User.query.filter_by(student_id=i).delete()
    db.session.delete(st); db.session.commit()
    flash(f'{name} deleted permanently.', 'ok'); return HOME()


@bp.route('/students/delete-all', methods=['POST'])
@roles('teacher')
def student_delete_all():
    AttendanceRecord.query.delete(); AttendanceSession.query.delete()
    User.query.filter(User.student_id.isnot(None)).delete(synchronize_session=False)
    n = Student.query.delete(); db.session.commit()
    flash(f'{n} students and all attendance data deleted.', 'ok'); return HOME()
