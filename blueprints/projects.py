from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from sqlalchemy import orm
from models.project import Project
from models.form import Form
from models.image import Image
from models.question import Question
from models.option import Option
from utils import get_projects
from utils import get_forms
from utils import check_user_id
from extensions import db
import uuid
import random
import string
from blueprints.main import PER_PAGE

projects_blueprint = Blueprint('projects', __name__)

@projects_blueprint.route('/projects', methods=['POST'])
@projects_blueprint.route('/projects/<int:page>', methods=['GET'])
@login_required
def projects(page=1):
    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        description = request.form['description']
        quantity = request.form['quantity']        
        if 'is_active' in request.form:
            is_active = 1
        else:
            is_active = 0
        user_id = current_user.id
        new_project = Project(code=code, name=name, description=description, quantity=quantity, is_active=is_active, user_id=user_id)
        db.session.add(new_project)
        db.session.commit()

    offset = (page - 1) * PER_PAGE
    projects = get_projects(offset)

    total_projects = Project.query.count()
    total_pages = (total_projects - 1) // PER_PAGE + 1

    return render_template('projects.html', projects=projects, current_page=page, total_pages=total_pages)

@projects_blueprint.route('/add_project', methods=['GET', 'POST'])
@login_required
@check_user_id
def add_project():        
    
    code = get_next_project_code()

    return render_template('project.html', user_id=current_user.id, code=code)

@projects_blueprint.route('/edit_project', methods=['POST','GET'])    
@login_required
@check_user_id
def edit_project():

    if request.method == 'GET':

        project_id = request.args.get('project_id')

    elif request.method == 'POST':

        project_id = request.form.get('project_id')

    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
    
        flash("You tried to access an entity that does not exist or does not belong to your user.")        
        return redirect("/invalid_entity")

    if request.method == 'POST':
        project.name = request.form['name']
        project.description = request.form['description']
        project.quantity = request.form['quantity']
        if 'is_active' in request.form:
            project.is_active = 1
        else:
            project.is_active = 0
        db.session.commit()
        return redirect('/projects/1')

    offset = (page - 1) * PER_PAGE
    forms = get_forms(project_id,offset)

    total_forms = Form.query.filter_by(project_id=project_id).count()
    total_pages = (total_forms - 1) // PER_PAGE + 1   

    return render_template('edit_project.html', forms=forms, project=project, current_page=page, total_pages=total_pages)    

@projects_blueprint.route('/show_project/<int:project_id>/<int:page>')
@login_required
def show_project(project_id, page):

    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        
        flash("You tried to access an entity that does not exist or does not belong to your user.")    
        return redirect("/invalid_entity")

    offset = (page - 1) * PER_PAGE
    forms = get_forms(project_id,offset)

    total_forms = Form.query.filter_by(project_id=project_id).count()
    total_pages = (total_forms - 1) // PER_PAGE + 1   

    return render_template('edit_project.html', forms=forms, project=project, current_page=page, total_pages=total_pages)    
    
@projects_blueprint.route('/delete_project/<int:project_id>/<int:page>', methods=['GET'])
@login_required
@check_user_id
def delete_project(project_id,page):

    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
    
        flash("You tried to access an entity that does not exist or does not belong to your user.")        
        return redirect("/invalid_entity")
        
    if project.is_active:
        flash("Unable to delete an active project!", 'danger')
        return redirect(f'/projects/{page}')    

    db.session.delete(project)
    db.session.commit()

    return redirect(f'/projects/{page}')
    
@projects_blueprint.route('/get_project', methods=['POST','GET'])
def get_project():

    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    if request.method == 'GET':

        code = request.args.get('code')

    elif request.method == 'POST':
    
        code = request.form.get('code')
       
    project = Project.query.filter_by(code=code, is_active=True).first()
    
    if not project:
    
        flash('Non-existent survey! Check that the code was typed correctly.')
        return redirect("/")
    
    return render_template('show_explanations.html', forms=project.forms, project=project, code=code)
   
@projects_blueprint.route('/forms', methods=['POST'])   
@projects_blueprint.route('/forms/<int:project_id>/<int:page>', methods=['GET'])
@login_required
def forms(project_id=None,page=1):
    if request.method == 'POST':
        name = request.form['name']
        order = request.form['order']
        description = request.form['description']
        technique = request.form['technique']
        project_id = request.form['project_id']
        
        new_form = Form(name=name, order=order, description=description, technique=technique, project_id=project_id)
        db.session.add(new_form)
        db.session.commit()
        
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
        if not project:
        
            return redirect("/invalid_entity")   

        if not project_id:
            project_id = request.args.get('project_id', type=int)        
        if not page:
            page = request.args.get('page', 1, type=int)

        offset = (page - 1) * PER_PAGE
        forms = get_forms(project_id,offset)

        total_forms = Form.query.filter_by(project_id=project.id).count()
        total_pages = (total_forms - 1) // PER_PAGE + 1

        return render_template('edit_project.html', forms=forms, project=project, current_page=page, total_pages=total_pages)

@projects_blueprint.route('/add_form/<int:project_id>', methods=['GET', 'POST'])
@login_required
@check_user_id
def add_form(project_id):        

    return render_template('form.html',project_id=project_id)
    
@projects_blueprint.route('/edit_form/', methods=['POST','GET'])    
@login_required
@check_user_id
def edit_form():

    if request.method == 'GET':

        form_id = request.args.get('form_id')

    elif request.method == 'POST':

        form_id = request.form.get('form_id')

    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()
    
    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    #form = Form.query.get_or_404(form_id)

    if request.method == 'POST':

        form.name = request.form['name']
        form.order = request.form['order']        
        form.description = request.form['description']
        form.technique = request.form['technique']
        db.session.commit()
        return render_template('edit_form.html', images=form.images, questions=form.questions, form=form)
    
    return render_template('edit_form.html', images=form.images, questions=form.questions, form=form)
       
@projects_blueprint.route('/show_form/<int:form_id>', methods=['GET'])
@login_required
def show_form(form_id):

    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()
    
    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    return render_template('edit_form.html', form=form, images=form.images, questions=form.questions)
    
@projects_blueprint.route('/delete_form/<int:form_id>/<int:page>', methods=['GET'])
@login_required
@check_user_id
def delete_form(form_id,page):

    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()
    
    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    try:
        db.session.delete(form)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Cannot delete this entity. Please delete related entities first.', 'danger')    
    
    project = Project.query.filter_by(id=form.project_id).first()

    offset = (page - 1) * PER_PAGE
    forms = get_forms(project.id,offset)

    total_forms = Form.query.filter_by(project_id=project.id).count()
    total_pages = (total_forms - 1) // PER_PAGE + 1

    return render_template('edit_project.html', forms=forms, project=project, current_page=page, total_pages=total_pages)

@projects_blueprint.route('/image_form/<int:image_id>')
def image_form(image_id):
    image = db.session.query(Image).filter(Image.id == image_id).first()

    if image:
        return Response(image.image, content_type='image/png')
    return "Image not available" 

@projects_blueprint.route('/images/<int:form_id>', methods=['GET', 'POST'])
@login_required
@check_user_id
def images(form_id):

    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()
    
    if not form:
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    if request.method == 'POST':
        description = request.form['description']
        image_file = request.files['image']

        if not image_file.filename.endswith('.png'):
            flash('Only PNG images are allowed.', 'warning')
            return redirect(request.url)

        if len(image_file.read()) > 200 * 1024:  # 200KB
            flash('The image size should not exceed 200KB.', 'warning')
            return redirect(request.url)

        image_data = image_file.read()
        image = Image(description=description, image=image_data, form_id=form_id)
        db.session.add(image)
        db.session.commit()

    return render_template('edit_form.html', images=form.images, questions=form.questions, form=form)

@projects_blueprint.route('/questions/<int:form_id>', methods=['GET', 'POST'])
@login_required
def questions(form_id):

    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()
    
    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    if request.method == 'POST':
        variable = request.form['variable']
        description = request.form['description']
        if 'seniority' in request.form:
            seniority = 1
        else:
            seniority = 0  
        question = Question(description=description,variable=variable,seniority=seniority,form_id=form_id)
        db.session.add(question)
        db.session.commit()

    return render_template('edit_form.html', images=form.images, questions=form.questions, form=form)

@projects_blueprint.route('/add_image/<int:form_id>', methods=['GET', 'POST'])
@login_required
def add_image(form_id):        

    return render_template('image.html', form_id=form_id)

@projects_blueprint.route('/add_question/<int:form_id>', methods=['GET', 'POST'])
@login_required
def add_question(form_id):        

    return render_template('question.html', form_id=form_id)
    
@projects_blueprint.route('/edit_question', methods=['POST'])    
@login_required
@check_user_id
def edit_question():

    if request.method == 'GET':

        form_id = request.args.get('form_id')

    elif request.method == 'POST':

        form_id = request.form.get('form_id')

   
    form_id = request.form['form_id']   

    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()
    
    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      
   
    question_id = request.form['question_id']
    
    question = Question.query.join(Form, Question.form_id == Form.id).join(Project, Form.project_id == Project.id).filter(Question.id==question_id, Project.user_id == current_user.id).first()
    
    if not question:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      
    

    if request.method == 'POST':
        question.description = request.form['description']
        question.variable = request.form['variable']
        if 'seniority' in request.form:
            seniority = 1
        else:
            seniority = 0        
        question.seniority = seniority
        db.session.commit()
        
        return render_template('edit_form.html', form=form, images=form.images, questions=form.questions)

@projects_blueprint.route('/show_question/<int:form_id>/<int:question_id>', methods=['GET'])
@login_required
def show_question(form_id, question_id):

    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()
    
    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    question = Question.query.join(Form, Question.form_id == Form.id).join(Project, Form.project_id == Project.id).filter(Question.id==question_id, Project.user_id == current_user.id).first()
    
    if not question:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      


    return render_template('edit_question.html', options=question.options, question=question, form=form)

@projects_blueprint.route('/delete_image/<int:form_id>/<int:image_id>', methods=['GET'])
@login_required
@check_user_id
def delete_image(form_id, image_id):

    image = Image.query.join(Form, Image.form_id == Form.id).join(Project, Form.project_id == Project.id).filter(Image.id==image_id, Project.user_id == current_user.id).first()
    
    if not image:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    try:
        db.session.delete(image)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Cannot delete this entity. Please delete related entities first.', 'danger')
  
    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()  

    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      
    
    return render_template('edit_form.html', form=form, images=form.images, questions=form.questions)

    
@projects_blueprint.route('/delete_question/<int:form_id>/<int:question_id>', methods=['GET'])
@login_required
@check_user_id
def delete_question(form_id, question_id):

    question = Question.query.join(Form, Question.form_id == Form.id).join(Project, Form.project_id == Project.id).filter(Question.id==question_id, Project.user_id == current_user.id).first()
    
    if not question:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    try:
        db.session.delete(question)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Cannot delete this entity. Please delete related entities first.', 'danger')
  
    form = db.session.query(Form).join(Project).filter(Form.id == form_id, Project.user_id == current_user.id).first()  

    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      
    
    return render_template('edit_form.html', form=form, images=form.images, questions=form.questions)

@projects_blueprint.route('/options/<int:question_id>', methods=['GET', 'POST'])
@login_required
@check_user_id
def options(question_id):

    question = Question.query.join(Form, Question.form_id == Form.id).join(Project, Form.project_id == Project.id).filter(Question.id==question_id, Project.user_id == current_user.id).first()
    
    if not question:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      


    if request.method == 'POST':
        value = request.form['value']
        description = request.form['description']
        option = Option(value=value,description=description,question_id=question_id)
        db.session.add(option)
        db.session.commit()
        question = Question.query.get_or_404(question_id)
        form = db.session.query(Form).join(Project).filter(Form.id == question.form_id, Project.user_id == current_user.id).first() 
        
        if not form:
   
            flash("You tried to access an entity that does not exist or does not belong to your user.")
            return redirect("/invalid_entity")      


    return render_template('edit_question.html', options=question.options, question=question, form=form)

@projects_blueprint.route('/add_option/<int:form_id>/<int:question_id>', methods=['GET', 'POST'])
@login_required
@check_user_id
def add_option(form_id, question_id):  

    return render_template('option.html', form_id=form_id, question_id=question_id)

@projects_blueprint.route('/delete_option/<int:question_id>/<int:option_id>', methods=['GET'])
@login_required
@check_user_id
def delete_option(question_id,option_id):

    option = Option.query.get_or_404(option_id)
    db.session.delete(option)
    db.session.commit()
    
    question = Question.query.join(Form, Question.form_id == Form.id).join(Project, Form.project_id == Project.id).filter(Question.id==question_id, Project.user_id == current_user.id).first()
    
    if not question:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    form = db.session.query(Form).join(Project).filter(Form.id == question.form_id, Project.user_id == current_user.id).first() 
        
    if not form:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      
    
    return render_template('edit_question.html', options=question.options, question=question, form=form)
    
def get_next_project_code():

    letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
    digits = ''.join(random.choice(string.digits) for _ in range(3))

    return letters + digits

@projects_blueprint.route('/clone_project/<int:project_id>/', methods=['GET'])
@login_required
@check_user_id
def clone_project(project_id):
    # Recupere o projeto original usando a sessão principal
    project = db.session.query(Project).options(
        joinedload(Project.forms).joinedload(Form.questions).joinedload(Question.options)
    ).filter(Project.id == project_id).one()

    # Extraia as informações do projeto original
    project_data = {
        'name': project.name,
        'description': project.description,
        'quantity': project.quantity,
        'user_id': project.user_id,
        'is_active': project.is_active
    }

    new_project_code = get_next_project_code()
    if not new_project_code:
        return "Error: Failed to generate a new project code", 500

    # Crie o novo projeto clonado
    new_project = Project(code=new_project_code, name=project_data['name'], description=project_data['description'], quantity=project_data['quantity'], user_id=current_user.id, is_active=project_data['is_active'])
    db.session.add(new_project)
    db.session.flush()  # Para garantir que new_project.id seja definido

    project.forms = sorted(project.forms, key=lambda x: x.id)  # Ordena os forms
    for form in project.forms:
        
        new_form = Form(name=form.name, order=form.order, description=form.description, technique=form.technique, project_id=new_project.id)
        db.session.add(new_form)
        db.session.flush()  # Para garantir que new_form.id seja definido

        for image_ in form.images:
            new_image = Image(description=image_.description, image=image_.image, form_id=new_form.id)
            db.session.add(new_image)
            db.session.flush() 

        form.questions = sorted(form.questions, key=lambda x: x.id)  # Ordena as questions
        for question in form.questions:
            new_question = Question(description=question.description, variable=question.variable, seniority=question.seniority, form_id=new_form.id)
            db.session.add(new_question)
            db.session.flush()  # Para garantir que new_question.id seja definido

            question.options = sorted(question.options, key=lambda x: x.id)  # Ordena as options
            for option in question.options:
                new_option = Option(value=option.value, description=option.description, question_id=new_question.id)
                db.session.add(new_option)

    # Faça o commit
    db.session.commit()

    # Recupere o projeto clonado com seus 'forms' para a exibição
    new_project = db.session.query(Project).options(
        joinedload(Project.forms)
    ).filter_by(id=new_project.id).first()

    page = 1
    offset = (page - 1) * PER_PAGE
    projects = get_projects(offset)

    total_projects = Project.query.count()
    total_pages = (total_projects - 1) // PER_PAGE + 1

    return render_template('projects.html', projects=projects, current_page=page, total_pages=total_pages)


@projects_blueprint.route('/clone_form/<int:project_id>/<int:form_id>/<int:page>', methods=['GET'])
@login_required
@check_user_id
def clone_form(project_id,form_id,page):

    form = db.session.query(Form).options(
        joinedload(Form.questions).joinedload(Question.options)
    ).filter(Form.id == form_id, Project.user_id == current_user.id).one()

    form_data = {
        'name': form.name,
        'order': form.order,
        'description': form.description,
        'technique': form.technique,
        'project_id': form.project_id
    }

    new_form = Form(name=form_data['name'], order=form_data['order'], description=form_data['description'], technique=form_data['technique'], project_id=form_data['project_id'])
    db.session.add(new_form)
    db.session.flush()

    for image_ in form.images:
        new_image = Image(description=image_.description, image=image_.image, form_id=new_form.id)
        db.session.add(new_image)
        db.session.flush() 

    form.questions = sorted(form.questions, key=lambda x: x.id)
    for question in form.questions:
        new_question = Question(description=question.description, variable=question.variable, seniority=question.seniority, form_id=new_form.id)
        db.session.add(new_question)
        db.session.flush()

        question.options = sorted(question.options, key=lambda x: x.id)
        for option in question.options:
            new_option = Option(value=option.value, description=option.description, question_id=new_question.id)
            db.session.add(new_option)

    db.session.commit()

    new_project = db.session.query(Project).options(
        joinedload(Project.forms)
    ).filter_by(id=form.project_id).first()

    if not page:

        page = 1

    offset = (page - 1) * PER_PAGE
    forms = get_forms(project_id,offset)

    total_forms = Form.query.filter_by(project_id=project_id).count()
    total_pages = (total_forms - 1) // PER_PAGE + 1   

    return render_template('edit_project.html', forms=forms, project=new_project, current_page=page, total_pages=total_pages)    

@projects_blueprint.route('/generate_default_project/', methods=['GET'])
@login_required
@check_user_id
def generate_default_project():

    clone_project(1)

    page = 1
    offset = (page - 1) * PER_PAGE
    projects = get_projects(offset)

    total_projects = Project.query.count()
    total_pages = (total_projects - 1) // PER_PAGE + 1

    return render_template('projects.html', projects=projects, current_page=page, total_pages=total_pages)


