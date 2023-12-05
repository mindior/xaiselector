from extensions import db

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    
    def __init__(self, description, form_id, image=None):
        self.description = description
        self.image = image
        self.form_id = form_id
