from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGTEXT

class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    query = db.Column(db.Text, nullable=False)
    result = db.Column(LONGTEXT, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


