from app import db 
from .association import user_assistants


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True)
    nom = db.Column(db.String(100))
    nom_utilisateur = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  
    role = db.relationship('Role', back_populates='users')
    is_blocked = db.Column(db.Boolean, default=False)
     
    assistants = db.relationship('Assistant', secondary=user_assistants, backref='users')




