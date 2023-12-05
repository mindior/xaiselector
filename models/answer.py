from extensions import db

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(200), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    session_id = db.Column(db.String(50), nullable=False)
    is_valid = db.Column(db.Boolean, default=False)
