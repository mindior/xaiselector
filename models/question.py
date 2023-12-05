from extensions import db

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    variable = db.Column(db.String(30), nullable=False)
    seniority = db.Column(db.Boolean, default=False)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True, cascade="all,delete")
    answers = db.relationship('Answer', backref='question', lazy=True, cascade="all,delete")
    
    def __init__(self, description, variable, seniority, form_id):
        self.description = description
        self.variable = variable
        self.seniority = seniority
        self.form_id = form_id
