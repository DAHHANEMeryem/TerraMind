from app import db
from datetime import datetime

class ChatSession(db.Model):
    __tablename__ = 'chat_session'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    assistant_id = db.Column(db.Integer, db.ForeignKey('assistants.assistantId'), nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('SearchHistory', backref='chat_session', lazy=True , cascade='all, delete-orphan')
    
