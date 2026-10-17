from datetime import datetime
from extensions import db


class AttendanceSession(db.Model):
    __tablename__ = 'att_sessions'
    __table_args__ = (db.UniqueConstraint('subject_id', 'lecture', 'date'),)
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    lecture = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), default='in_progress', nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    finalized_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject = db.relationship('Subject')


class AttendanceRecord(db.Model):
    __tablename__ = 'records'
    __table_args__ = (db.UniqueConstraint('session_id', 'student_id'),)
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('att_sessions.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
