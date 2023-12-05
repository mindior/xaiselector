from extensions import db

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technique = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    images = db.relationship('Image', backref='form', lazy=True, cascade="all,delete")
    questions = db.relationship('Question', backref='form', lazy=True, cascade="all,delete")
    
    def __init__(self, name, order, description, technique, project_id):
        self.name = name
        self.order = order
        self.description = description
        self.technique = technique        
        self.project_id = project_id