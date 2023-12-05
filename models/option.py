from extensions import db

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(5), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    
    def __init__(self, value, description, question_id):
        self.value = value
        self.description = description
        self.question_id = question_id    
