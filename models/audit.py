from datetime import datetime
from extensions import db


class Audit(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    session_id = db.Column(db.Integer)
    action = db.Column(db.String(200))
    reason = db.Column(db.String(300))
    at = db.Column(db.DateTime, default=datetime.utcnow)
