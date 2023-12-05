from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, Response, current_app
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash
from models.user import User
from utils import get_users, check_user_id
from blueprints.main import PER_PAGE
from blueprints.projects import check_user_id
from extensions import db


users_blueprint = Blueprint('users', __name__)

@users_blueprint.route('/recover_password', methods=['GET'])
def recover_password():        
    return render_template('password_recover.html')

@users_blueprint.route('/new_password/<string:token>', methods=['GET'])
def new_password(token):
    return render_template('new_password.html', token=token)

@users_blueprint.route('/recover', methods=['POST'])
def recover():
    if request.method == 'POST':      

        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:

            token = generate_token(email)
            recovery_url = url_for('users.new_password', token=token, _external=True)
            send_recovery_email(email, recovery_url)
            flash('Email recover sent!', 'success')
       
    return redirect(url_for('index'))

def send_recovery_email(email, recovery_url):
    msg = Message('XAI Selector Password Recovery', sender=current_app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f'Click the following link to reset your password: {recovery_url}'
    mail = current_app.extensions['mail']
    mail.send(msg)

@users_blueprint.route('/set_password', methods=['POST'])
def set_password():

    if request.method == 'POST':
        
        token = request.form['token']
        email = verify_token(token)

        user = User.query.filter_by(email=email).first()

        user.password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        db.session.commit()

        flash('Successfully registered user!')

        return render_template('index.html')

def generate_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-recovery-salt')

def verify_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-recovery-salt', max_age=expiration)
    except:
        return False
    return email

@users_blueprint.route('/add_user', methods=['GET', 'POST'])
@login_required 
def add_user():        
    return render_template('user.html')

@users_blueprint.route('/add_user_internet', methods=['GET', 'POST'])
def add_user_internet():        
    return render_template('user_internet.html')

@users_blueprint.route('/users_internet', methods=['GET', 'POST'])
def users_internet():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Successfully registered user!')

        return render_template('index.html')
    
@users_blueprint.route('/edit_user/', methods=['POST'])   
@login_required 
@check_user_id
def edit_user():

    user_id = current_user.id

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        db.session.commit()
        return redirect('/projects/1')
    
    return render_template('edit_user.html', projects=user.projects, user=user)    

@users_blueprint.route('/show_user/', methods=['GET'])
@login_required
def show_user():

    user_id = current_user.id

    user = User.query.get_or_404(user_id)

    return render_template('edit_user.html', user=user)    
    
@users_blueprint.route('/delete_user/<int:user_id>', methods=['GET'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect('/users')    

