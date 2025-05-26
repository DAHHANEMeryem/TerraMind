from app import db

class Assistant(db.Model):
    __tablename__ = 'assistants'

    assistantId = db.Column(db.Integer, primary_key=True)
    domaine = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    isActive = db.Column(db.Boolean, default=True)

