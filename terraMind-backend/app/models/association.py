from app import db

user_assistants = db.Table('user_assistants',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('assistant_id', db.Integer, db.ForeignKey('assistants.assistantId'), primary_key=True)
)
