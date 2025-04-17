from datetime import datetime
from .. import db

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # create, update, delete
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
