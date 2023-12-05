from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, Response, current_app
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models.form import Form
from models.answer import Answer
from extensions import db
from blueprints.main import PER_PAGE

surveys_blueprint = Blueprint('surveys', __name__)

@surveys_blueprint.route('/show_explanation/<int:form_id>/<string:code>', methods=['GET'])
def show_explanation(form_id,code):
  
    form = Form.query.get_or_404(form_id)

    return render_template('show_explanation.html', form=form, code=code)
    
@surveys_blueprint.route('/response_survey', methods=['POST'])
def response_survey():

    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        
    session_id = session.get('session_id')

    code = request.form['code']
    form_id = request.form['form_id']
       
    questions = {float(k.split('_')[1]): float(v) for k, v in request.form.items() if k.startswith('question_')}
    
    for key, value in questions.items():
        
        answer = Answer(value=value, question_id=key, session_id=session_id)
        db.session.add(answer)
        db.session.commit()
              
    if session.get('forms'):
    
        forms = session.get('forms')
        forms.append(form_id)
    
    else:
    
        forms = [form_id]
          
    session['forms'] = forms
      
    return redirect(url_for('projects.get_project', code=code))
    
@surveys_blueprint.route('/finish_survey', methods=['GET'])
def finish_survey():

    session_id = session.get('session_id')

    Answer.query.filter_by(session_id=session_id).update({Answer.is_valid: True})
    db.session.commit()

    session.clear()
    response = make_response(redirect(url_for('main.index')))    
    response.delete_cookie(current_app.config['SESSION_COOKIE_NAME'])
    
    return response