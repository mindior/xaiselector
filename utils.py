from flask import flash, redirect
from flask_login import current_user
from models.project import Project
from models.form import Form
from models.user import User
from extensions import db
from functools import wraps
from blueprints.main import PER_PAGE

def check_user_id(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.id == 1:
            flash('Invalid Operation! This project is read-only.', 'warning')
            return redirect("/projects/1")  
        return func(*args, **kwargs)
    return decorated_function

def get_users(offset=0):
    return User.query.limit(PER_PAGE).offset(offset).all()

def get_projects(offset=0):

    return Project.query.filter_by(user_id=current_user.id).filter(Project.id != 1).order_by(Project.id).limit(PER_PAGE).offset(offset).all() #Does not display the default project that has id 1

def get_forms(project_id,offset=0):

    if offset==-1:

        return db.session.query(Form).join(Project).filter(Project.user_id == current_user.id).filter(Project.id == project_id).order_by(Form.order).all()

    else:    

        return db.session.query(Form).join(Project).filter(Project.user_id == current_user.id).filter(Project.id == project_id).order_by(Form.order).limit(PER_PAGE).offset(offset).all()
