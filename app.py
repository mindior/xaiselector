from flask import Flask, render_template
from flask_login import LoginManager
from flask_paginate import Pagination
from flask_mail import Mail, Message
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session    
from extensions import login_manager, db, session
import plot_likert
import os
import re
import matplotlib

from models.user import User
from models.project import Project
from models.form import Form
from models.question import Question
from models.option import Option
from models.answer import Answer

matplotlib.use('agg')

mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 
    
def create_app():
    from blueprints.users import users_blueprint
    from blueprints.projects import projects_blueprint
    from blueprints.analysis import analysis_blueprint
    from blueprints.surveys import surveys_blueprint
    from blueprints.main import main_blueprint

    app = Flask(__name__)

    # Configuração do PostgreSQL
    #DATABASE_URL = 'postgresql://user:passworddb:5432/xaiselector'
    DATABASE_URL =  'postgresql://user:passworddb:5432/xaiselector'
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_COOKIE_NAME'] = "session"
    app.config['SECRET_KEY'] = "put your key here"    
    app.config['MAIL_SERVER'] = 'server'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'email'
    app.config['MAIL_PASSWORD'] = 'password'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False    
    
    db.init_app(app)
    login_manager.init_app(app)
    session.init_app(app)
    mail.init_app(app)    
    login_manager.login_view = 'index'

    app.register_blueprint(users_blueprint)
    app.register_blueprint(projects_blueprint)
    app.register_blueprint(analysis_blueprint)
    app.register_blueprint(surveys_blueprint)
    app.register_blueprint(main_blueprint)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        app.run(debug=True)
