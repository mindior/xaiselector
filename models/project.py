from extensions import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False, unique=True)        
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    forms = db.relationship('Form', backref='project', lazy=True, order_by="Form.id", cascade="all,delete")

    def __init__(self, code, name, description, quantity, user_id, is_active=True):
        self.code = code
        self.name = name
        self.description = description
        self.quantity = quantity
        self.user_id = user_id
        self.is_active = is_active    
