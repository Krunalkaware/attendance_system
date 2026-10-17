from flask_login import UserMixin
from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    pw = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # teacher / cr / student
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
