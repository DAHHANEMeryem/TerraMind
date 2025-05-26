from app import db

class Execution(db.Model):
    __tablename__ = 'execution'

    typeId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    count = db.Column(db.Integer, default=0)

