from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, current_app
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from extensions import login_manager
from models.user import User
import glob
import os

PER_PAGE = 10

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def index():
    return render_template('index.html')

@main_blueprint.route('/login', methods=['POST'])
def login():
  
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        login_user(user)
        flash('Login success!', 'success')
        return redirect('/projects/1')
    else:
        flash('Invalid Credentials. Try Again.', 'danger')
        return redirect(url_for('index'))    

@main_blueprint.route('/logout', methods=['GET'])
@login_required
def logout():
    
    logout_user()        
    session.clear()

    image_folder_path = os.path.join(current_app.root_path, 'static')

    matching_files = glob.glob(os.path.join(image_folder_path, f"*{request.cookies.get('session')}*.png"))
    
    for file_path in matching_files:
        if os.path.exists(file_path):
            os.remove(file_path)

    parquet_folder_path = os.path.join(current_app.root_path, 'parquet')

    if os.path.exists(f"{parquet_folder_path}\{request.cookies.get('session')}.parquet"):
        os.remove(f"{parquet_folder_path}\{request.cookies.get('session')}.parquet")

    response = make_response(redirect(url_for('index')))    
    response.delete_cookie(current_app.config['SESSION_COOKIE_NAME'])

    return response

@main_blueprint.route('/invalid_entity', methods=['GET'])
@login_required
def invalid_entity():
       
    return render_template('invalid_entity.html')


