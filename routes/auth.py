from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from models import User, Student

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname, pw = request.form.get('username', '').strip(), request.form.get('password', '')
        u = User.query.filter_by(username=uname).first()
        if not u:   # first student login: username = password = roll number
            st = Student.query.filter_by(roll=uname, active=True).first()
            if st and pw == st.roll:
                u = User(username=st.roll, name=st.name, role='student', student_id=st.id, pw=generate_password_hash(st.roll))
                db.session.add(u); db.session.commit()
        if u and check_password_hash(u.pw, pw):
            login_user(u); return redirect(url_for('dashboard.home'))
        flash('Invalid username or password.', 'error')
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user(); return redirect(url_for('auth.login'))
