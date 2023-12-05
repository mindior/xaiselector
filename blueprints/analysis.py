from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, Response, send_file, current_app
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import distinct, not_, or_, func
from models.project import Project
from models.form import Form
from models.question import Question
from models.answer import Answer
from utils import get_projects
from utils import get_forms
from itertools import combinations
from sklearn.metrics import cohen_kappa_score
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial import ConvexHull
import itertools
import plot_likert
import statsmodels.stats.inter_rater as ir        
from extensions import db
import pandas as pd
import numpy as np
import os
import io
from blueprints.main import PER_PAGE

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

analysis_blueprint = Blueprint('analysis', __name__)
previous_values = []

@analysis_blueprint.route('/screen_dataset/<int:project_id>', methods=['GET'])    
@login_required
def screen_dataset(project_id):

    """
    Select the forms that have questions on a Likert scale from 1 to 5 
    or inverted questions to assemble the variable selection screen
    
    Parameters:
    
    project_id (int): id of project
    
    Returns:

    list: List of Forms
    
    """
    
    forms = get_forms(project_id,-1)
    
    forms_to_request = []
    
    for form in forms:
    
        invalid = False
        
        for question in form.questions:
        
            for option in question.options:
            
                if option.value not in ('1','2','3','4','5','0.5','0.33','0.25','0.2'): #Change here to add 7 or 9 point Likert scale
                
                    invalid = True
                    
        if not invalid:            
            
            forms_to_request.append(form)
                
    
    return render_template('define_dataset.html', forms=forms_to_request, project_id=project_id)
    
@analysis_blueprint.route('/generate_dataset', methods=['POST','GET'])    
@login_required
def generate_dataset():

    """
    Assemble the dataset with questions to generate the likert scale EDA graph    
    
    Parameters:
    
    project_id (int): id of project
    
    Returns:

    dataset: Dataset of questions and answers 
    
    """

    question_ids = []

    if request.method == 'POST':
    
        project_id = request.form.get('project_id')
        
    else:
    
        project_id = request.args.get('project_id')

    checked_boxes = {k: v for k, v in request.form.items() if k.startswith('question_')} # Select the variables selected 
             
    for question in checked_boxes.keys():
                
        question_ids.append(question.split("_")[1])
            
    results = db.session.query(
        (Question.variable + ': ' + Form.name + '.' + Question.description).label("combined_label"),
        Question.variable.label("question_variable"),
        Answer.value.label("answer_value"),
        Answer.session_id.label("answer_session_id")
    ).select_from(Question) \
    .join(
        Form, Question.form_id == Form.id
    ).join(
        Project, Project.id == Form.project_id
    ).filter(
        Project.user_id == current_user.id
    ).join(
        Answer, Answer.question_id == Question.id
    ).filter(
        Question.id.in_(question_ids),
        Answer.is_valid == True
    ).order_by(Question.variable.asc()).all()

    if not results:
   
        flash("You tried to access an entity that does not exist or does not belong to your user.")
        return redirect("/invalid_entity")      

    df = pd.DataFrame(results)
    
    df = df.drop_duplicates(subset=['answer_session_id', 'question_variable'], keep='first')
    pivot_df = df.pivot(index='answer_session_id', columns='question_variable', values='answer_value')
               
    scale_map = {
        '1.0': 'Strongly disagree',
        '2.0': 'Disagree',
        '3.0': 'Neither agree nor disagree',
        '4.0': 'Agree',
        '5.0': 'Strongly agree',
        '1'	: 'Strongly disagree',
        '0.5': 'Disagree',
        '0.33': 'Neither agree nor disagree',
        '0.25':	'Agree',
        '0.2': 'Strongly agree'
    }

    pivot_df.replace(scale_map, inplace=True)
    
    parquet_folder_path = os.path.join(current_app.root_path, 'parquet')

    pivot_df.to_parquet(f"{parquet_folder_path}\{request.cookies.get('session')}.parquet")
    
    legend_results = db.session.query(
        ('Variable: ' + Question.variable + ', Form: ' + Form.name + ', Question: ' + Question.description).label("combined_label")
    ).join(
        Form, Question.form_id == Form.id
    ).join(
        Project, Project.id == Form.project_id
    ).join(
        Answer, Answer.question_id == Question.id
    ).filter(
        Project.user_id == current_user.id,
        Question.id.in_(question_ids),
        Answer.is_valid == True
    ).group_by(
        Question.variable, Form.name, Question.description
    ).order_by(Question.variable.asc(), Form.name, Question.description).all()
    
    generate_image()
                           
    return render_template('eda.html', results = legend_results)    
    
@analysis_blueprint.route('/generate_image')
@login_required
def generate_image():

    """
    Creates the image of the EDA
      
    Returns:

    image: Image of EDA
    
    """
    parquet_folder_path = os.path.join(current_app.root_path, 'parquet')

    df = pd.read_parquet(f"{parquet_folder_path}\{request.cookies.get('session')}.parquet")
    
    ax = plot_likert.plot_likert(df, plot_likert.scales.agree, plot_percentage=True, figsize=(30,25))
    
    fig = ax.get_figure()
    
    fig.suptitle('Exploratory Data Analysis', fontsize=25)
    plt.savefig(f"static/{request.cookies.get('session')}.png", dpi=300)
    plt.close()

@analysis_blueprint.route('/eda_menu', methods=['GET'])
@login_required
def eda_menu():

    """
    Prepare to assemble the EDA menu
       
    Returns:

    template: EDA menu with the user's projects
    
    """
  
    projects = get_projects()

    return render_template('eda_menu.html', projects=projects)

@analysis_blueprint.route('/metric_menu', methods=['GET'])
@login_required
def metric_menu():

    """
    Prepare to assemble the metric menu
       
    Returns:

    template: Metric menu with the user's projects
    
    """
  
    projects = get_projects()

    return render_template('metric_menu.html', projects=projects)

def calculate_min_max_for_arrays(arrays):
    num_rows = arrays[0].shape[0]
    
    mins_list = []
    maxs_list = []
    
    for row in range(num_rows):
        # Extract the current row from each array
        rows = [arr[row, :] for arr in arrays]
        
        # Concatenate the current row vertically
        concatenated_row = np.vstack(rows)
        
        # Calculate the min and max for the concatenated row
        min_values = np.min(concatenated_row, axis=0)
        max_values = np.max(concatenated_row, axis=0)
        
        mins_list.append(min_values)
        maxs_list.append(max_values)
    
    combined_mins = np.vstack(mins_list)
    combined_maxs = np.vstack(maxs_list)
    
    return combined_mins, combined_maxs
                 
def get_answers(project_id, ids):

    """
    Select the questions with the values of the answers
    
    Parameters:
    
    project_id (int): id of project
    ids (list): ids of questions
    
    Returns:

    dataset: Dataset of questions with answers
    
    """

    results = db.session.query( \
        Question.variable.label("question_variable"), \
        Answer.value.label("answer_value"), \
        Answer.session_id.label("answer_session_id")
    ).select_from(Question) \
    .join( \
        Form, Question.form_id == Form.id \
    ).join( \
        Project, Project.id == Form.project_id \
    ).filter( \
        Project.user_id == current_user.id \
    ).join( \
        Answer, Answer.question_id == Question.id \
    ).filter( \
        Question.id.in_(ids), \
        Answer.is_valid == True, \
        Project.id == project_id \
    ).order_by(Question.variable.asc()).all()
  
    return results

def make_pivot_table(df):

    """
    Create a pivot table
    
    Parameters:
    
    df (dataframe): dataframe of questions and answers
    
    Returns:

    pivot dataframe: Dataframe of questions with answers in a pivot format
    
    """

    pivot_df = df.pivot(index='answer_session_id', columns='question_variable', values='answer_value')
    pivot_df = pivot_df.sort_index(axis=1)    

    return pivot_df
    
def partition_dataframe(num_partitions, cols_per_partition, df):

    """
    Partition the dataframe into multiple dataframes of the respective techniques
    
    Parameters:
    
    num_partitions (int): Number of partitions. One partition for each technique
    cols_per_partition (int): Number of questions for each partition
    df (dataframe): dataframe of questions and answers
    
    Returns:

    list of dataframes: List with dataframes of questions with answers for each technique
    
    """
    partitioned_dfs = [df.iloc[:, i:i+cols_per_partition] for i in range(0, df.shape[1], cols_per_partition)]
    
    return partitioned_dfs
    
def generate_line_plot(sorted_dict, x_labels):

    """
    Generate the line plot
    
    Parameters:
    
    sorted_dict (dict): Dictionary ordered by the medians of metric values
    x_labels (list): Combinations of weights
    
    """

    formatted_x_labels = [f"({x[0]:.3f},{x[1]:.3f})" for x in x_labels]

    markers=['o','s','^','v','<','>','p','*']
     
    max_y_value = max([max(values[0]) for values in sorted_dict.values()])
    min_y_value = min([min(values[0]) for values in sorted_dict.values()])
    
    # Calculate middle y value for text placement
    middle_y_value = (max_y_value + min_y_value) / 2

    plt.figure(figsize=(12, 8))
    for (key, values), marker in zip(sorted_dict.items(), markers):
        plt.plot(formatted_x_labels, values[0], label=key, marker=marker) 

    # Adjust text positions to be in the middle of the plot
    plt.text(0, middle_y_value, "+trust -satisfaction", va='center', ha='left', fontsize=14, color='black')
    plt.text(len(formatted_x_labels) - 1, middle_y_value, "-trust +satisfaction", va='center', ha='right', fontsize=14, color='black')
    
    plt.legend()
    plt.title('Sensitivity Analysis')
    plt.xlabel('Weights')
    plt.ylabel('Value')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"static/{request.cookies.get('session')}.png",dpi=300)
    plt.close()

def generate_boxplot(sorted_dict):
    """
    Generate the boxplots with variable box widths based on Weighted' Kappa values.

    Parameters:
    sorted_dict (dict): Dictionary ordered by the medians of metric values and Weighted Kappa values.
    """

    kappa_scale = {
        "0.81 - 1.00": "Almost perfect agreement",
        "0.61 - 0.80": "Substantial agreement",
        "0.41 - 0.60": "Moderate agreement",
        "0.21 - 0.40": "Fair agreement",
        "0.00 - 0.20": "Slight agreement",
        "< 0": "Poor agreement"
    }

    sorted_techniques = sorted(sorted_dict.keys(), key=lambda x: np.median(sorted_dict[x][0]), reverse=True)

    sorted_data = [sorted_dict[technique][0] for technique in sorted_techniques]
    weighted_kappa = [sorted_dict[technique][1] for technique in sorted_techniques]

    min_kappa = min(weighted_kappa)
    max_kappa = max(weighted_kappa)
    kappa_range = max_kappa - min_kappa

    box_widths = [(kappa - min_kappa) / kappa_range for kappa in weighted_kappa]

    plt.figure(figsize=(12, 8))
    boxplot = plt.boxplot(sorted_data, vert=True, patch_artist=True)

    for box, width in zip(boxplot['boxes'], box_widths):
        box.set_linewidth(2 + width * 10)

    plt.xticks(range(1, len(sorted_techniques) + 1), sorted_techniques, rotation=0) 
    plt.ylabel('Value')
    plt.title('Boxplot of Techniques with Variable Box Widths Based on Weighted\' Kappa')
    
    for idx, (key, value) in enumerate(kappa_scale.items()):
        plt.text(0, -0.07 - 0.025 * idx, f'{key}: {value}', transform=plt.gca().transAxes, fontsize=9)   
    
    plt.tight_layout()

    for i, technique in enumerate(sorted_techniques):
        kappa_text = f'Kappa: {weighted_kappa[i]:.3f}'
        upper_whisker = boxplot['whiskers'][i * 2 + 1]
        plt.text(i + 1, upper_whisker.get_ydata()[1] + 0.002, kappa_text, ha='center', va='bottom', fontsize=10)

    plt.savefig(f"static/{request.cookies.get('session')}.png", dpi=300)
    plt.close()

def get_techniques_names(project_id):

    distinct_techniques = (db.session.query(distinct(func.trim(Form.technique)).label('trimmed_technique'))
                       .filter(Form.project_id == project_id)
                       .filter(not_(or_(Form.technique == None, func.trim(Form.technique) == '')))
                       .order_by(func.trim(Form.technique).asc())
                       .all())

    distinct_techniques = [item[0] for item in distinct_techniques]

    return distinct_techniques

def make_dists(results,quantity,project_id, kappa):

    """
    Create the metric distributions
    
    Parameters:
    
    results (dataset): Mean of user's values of metric
    
    Returns:      
    
    """

    distinct_techniques = get_techniques_names(project_id)

    dists = {}

    if len(distinct_techniques) == quantity:

        for index, value in enumerate(distinct_techniques):

            dists[f"{value}"] = []
    
        for df in results:

            for index, value in enumerate(distinct_techniques):
                
                dists[f'{value}'].append(df[index][0])

    for index, key in enumerate(dists):
    
        dists[key] = (dists[key], kappa[index])

    dists = dict(sorted(dists.items(), key=lambda item: np.median(item[1][0]), reverse=True))        

    return dists
    
def get_seniority_question_id(project_id):

    """
    Get the id of seniority question. The question has the variable name of dm_timesc
    
    Parameters:
    
    project_id (int): id of project
    
    Returns:

    id (int): Id of seniority question
    
    """


    question = (db.session.query(Question.id, Question.variable)
        .join(Form, Form.id == Question.form_id)
        .join(Project, Project.id == Form.project_id)
        .filter(Project.user_id == current_user.id, Project.id == project_id, Question.seniority == True)
        .order_by(Question.variable.asc(), Question.id)
        .distinct(Question.variable, Question.id)
        .first())        
    
    return question.id

def prepare_data(project_id):

    questions = (db.session.query(Question.id, Question.variable)
        .join(Form, Form.id == Question.form_id)
        .join(Project, Project.id == Form.project_id)
        .filter(Project.user_id == current_user.id, Project.id == project_id)
        .distinct(Question.id, Question.variable)
        .order_by(Question.variable.asc(), Question.id)
        .all())


    df = pd.DataFrame(questions)

    #ids = df['id'].tolist()  # ids of questions of trust before    
    #results = get_answers(project_id, ids)
    #df = pd.DataFrame(results)
    #make_pivot_table(df).to_csv("ex2.csv")

    tb_ids = df[df['variable'].str.startswith('tb_')]['id'].tolist()  # ids of questions of trust before
    us_ids = df[df['variable'].str.startswith('us_')]['id'].tolist()  # ids of questions of user satisfaction
    ta_ids = df[df['variable'].str.startswith('ta_')]['id'].tolist()  # ids of questions of trust after

    results_tb = get_answers(project_id, tb_ids)
    df_tb = pd.DataFrame(results_tb)
    pivot_df_tb = make_pivot_table(df_tb)

    results_us = get_answers(project_id, us_ids)
    df_us = pd.DataFrame(results_us)
    pivot_df_us = make_pivot_table(df_us)

    results_ta = get_answers(project_id, ta_ids)
    df_ta = pd.DataFrame(results_ta)
    pivot_df_ta = make_pivot_table(df_ta)

    df_taus = pivot_df_us.join(pivot_df_ta)

    num_partitions = len(get_techniques_names(project_id))

    cols_per_partition_ta = pivot_df_ta.shape[1] // num_partitions
    cols_per_partition_us = pivot_df_us.shape[1] // num_partitions

    partitioned_dfs_ta = partition_dataframe(num_partitions, cols_per_partition_ta, pivot_df_ta)
    partitioned_dfs_us = partition_dataframe(num_partitions, cols_per_partition_us, pivot_df_us)

    return partitioned_dfs_ta, partitioned_dfs_us, pivot_df_tb, pivot_df_us, df_taus, cols_per_partition_ta, cols_per_partition_us

    
def preparate_for_metric_calculation(project_id):

    """
    Prepare for the metric calculation
    
    Parameters:
    
    project_id (int): id of project
    
    Returns:

    w1 (dataframe): Seniority weights
    w2 (int): Trust weight
    w3 (int): Satisfaction weigth
    dataframes_results_final_tr (dataframe): Results of trust
    dataframes_results_final_us (dataframe): Results of satisfaction
    
    """  
    partitioned_dfs_ta, partitioned_dfs_us, pivot_df_tb, pivot_df_us, df_taus, cols_per_partition_ta, cols_per_partition_us = prepare_data(project_id)
  
    dataframes_numerator = []
       
    for df in partitioned_dfs_ta:
           
        dataframes_numerator.append(df.astype(float).values  - pivot_df_tb.astype(float).values)
        
    dataframes_results = []
    
    for df in dataframes_numerator:    

        df = (((df.astype(float)+4)/8)).sum(axis=1).reshape(-1, 1)
        dataframes_results.append(df)      

    dataframes_results_final_tr = []

    for df in dataframes_results:    

        dataframes_results_final_tr.append(df / cols_per_partition_ta)
         
    us_dataframes = []
    
    for df_ in partitioned_dfs_us:
    
        us_dataframes.append(df_.astype(float).values)
               
    dataframes_results = []
    
    for df in us_dataframes:  
        df = (((df.astype(float)-1)/4).sum(axis=1)).reshape(-1, 1) # alterado
        dataframes_results.append(df)

    dataframes_results_final_us = []

    for df in dataframes_results:    
    
        dataframes_results_final_us.append(df /cols_per_partition_us)

    seniority_question_id = get_seniority_question_id(project_id)
    
    results_sn = get_answers(project_id, [seniority_question_id])

    df_sn = pd.DataFrame(results_sn)

    pivot_df_sn = df_sn.pivot(index='answer_session_id', columns='question_variable', values='answer_value')
    
    w1 = pivot_df_sn.astype(float).values.reshape(-1, 1)
    w2 = float(1)
    w3 = abs(1 - w2)

    kappa = weighted_kappa(df_taus,project_id)
         
    return w1, w2, w3, dataframes_results_final_tr, dataframes_results_final_us, kappa 

def calculate_measures(project_id):
   
    """
    Calculate measures
    
    Parameters:
    
    project_id (int): id of project
    
    Returns:

    w1 (dataframe): Seniority weights
    w2 (int): Trust weight
    w3 (int): Satisfaction weigth
    dataframes_results_final_tr (dataframe): Results of trust
    dataframes_results_final_us (dataframe): Results of satisfaction
    
    """
    
    partitioned_dfs_ta, partitioned_dfs_us, pivot_df_tb, pivot_df_us, df_taus, cols_per_partition_ta, cols_per_partition_us = prepare_data(project_id)    
       
    sums_ta = [df.astype(float).sum().sum() for df in partitioned_dfs_ta]

    labels = get_techniques_names(project_id)

    plt.figure(figsize=(16, 8))    
    plt.bar(labels, sums_ta)
    plt.ylabel('Trust After')
    plt.title('Trust After Summary')
    plt.savefig(f"static/{request.cookies.get('session')}_ta.png",dpi=300)
    plt.close()  
    
    sums_us = [df.astype(float).sum().sum() for df in partitioned_dfs_us]

    labels = get_techniques_names(project_id)

    plt.figure(figsize=(16, 8))    
    plt.bar(labels, sums_us)
    plt.ylabel('User Satisfaction')
    plt.title('User Satisfaction Summary')
    plt.savefig(f"static/{request.cookies.get('session')}_us.png",dpi=300)
    plt.close()  
    
    dataframes_numerator = []
       
    for df in partitioned_dfs_ta:
           
        dataframes_numerator.append(df.astype(float).values  - pivot_df_tb.astype(float).values)
    
    sums_diff = [df.astype(float).sum().sum() for df in dataframes_numerator]

    labels = get_techniques_names(project_id)

    plt.figure(figsize=(16, 8))    
    plt.bar(labels, sums_diff)
    plt.ylabel('Difference')
    plt.title('Difference between Trust After and Trust Before Summary')
    plt.savefig(f"static/{request.cookies.get('session')}_diff.png",dpi=300)
    plt.close()  

    dataframes_results = [((df.astype(float)+4)/8).sum().sum() for df in dataframes_numerator] # alterado
    
    plt.figure(figsize=(16, 8))    
    plt.bar(labels, dataframes_results)
    plt.ylabel('Ratio')
    plt.title('Ratio between Difference Trust and Mean Summary')
    plt.savefig(f"static/{request.cookies.get('session')}_ratio_ta.png",dpi=300)
    plt.close()  
    
    us_dataframes = []
    
    for df_ in partitioned_dfs_us:
    
        us_dataframes.append(df_.astype(float).values)
               
    dataframes_results = []
    
    dataframes_results = [((df.astype(float)-1)/4).sum().sum() for df in us_dataframes] #alterado
    
    plt.figure(figsize=(16, 8))    
    plt.bar(labels, dataframes_results)
    plt.ylabel('Ratio')
    plt.title('Ratio between User Satisfaction and Mean Summary')
    plt.savefig(f"static/{request.cookies.get('session')}_ratio_us.png",dpi=300)
    plt.close()  
           
@analysis_blueprint.route('/metric', methods=['POST'])
@login_required
def metric():

    project_id = request.form.get("project_id")
    plot_type = int(request.form.get("plot_type")) 
    
    w1, w2, w3, dataframes_results_final_tr, dataframes_results_final_us, kappa = preparate_for_metric_calculation(project_id)
    
    results = []
    
    x_labels = []   
    
    for i in range(1,42):

        df_result = (w1 * w2 * dataframes_results_final_tr) + ( w1 * w3 * dataframes_results_final_us ) #Calculate the metric
        results.append(df_result.mean(axis=1))

        x_labels.append((w2,w3))

        w2 = round(abs(w2 - 0.025),3)
        w3 = round(abs(1 - w2),3)
               
    project = Project.query.get(project_id)

    dists = make_dists(results,project.quantity,project_id,kappa) 

    if plot_type == 1:
         
        generate_line_plot(dists, x_labels)
    
    elif plot_type == 2:
    
        generate_boxplot(dists)
        
    elif plot_type == 3:
    
        pareto_plot(dists)

    return render_template('metric.html')        
    
def radar_plot_line(data,fig,ax, color):

    """
    Print one radar line
          
    """

    labels = data.columns.tolist()
    num_vars = len(labels)
    
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]
    labels += labels[:1]

    values = data.values.tolist()
    for i in range(len(values)):
        values[i] += values[i][:1]

    for value in values:
        linewidth = 2
        for prev_value in previous_values:
            if all(np.isclose(value, prev_value)):
                linewidth += 3
                break
    
        ax.plot(angles, value, color=color, linewidth=linewidth)
        ax.fill(angles, value, color=color, alpha=0)
    
        previous_values.append(value)

    ax.set_yticklabels([])
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, rotation=45)
     
@analysis_blueprint.route('/measurement_bulletin/<int:project_id>', methods=['POST'])
@login_required
def measurement_bulletin(project_id):

    calculate_measures(project_id)

    return render_template('measurement_bulletin.html')    
      
def pareto_plot(sorted_dict):    

    kappa_scale = {
        "0.81 - 1.00": "Almost perfect agreement",
        "0.61 - 0.80": "Substantial agreement",
        "0.41 - 0.60": "Moderate agreement",
        "0.21 - 0.40": "Fair agreement",
        "0.00 - 0.20": "Slight agreement",
        "< 0": "Poor agreement"
    }


    df = pd.DataFrame({
        'Technique': list(sorted_dict.keys()),
        'Kappa': [value[1] for value in sorted_dict.values()],
        'Metric': [sum(value[0])/len(value[0]) for value in sorted_dict.values()]  # Média dos 41 valores
    })
    
    df_sorted = df.sort_values(by=['Kappa', 'Metric'])    

    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=df_sorted, x='Kappa', y='Metric', hue='Technique', palette='tab10', s=100)

    for index, row in df_sorted.iterrows():
        plt.text(row['Kappa'], row['Metric'] - 0.001, row['Technique'], horizontalalignment='center')

    plt.title('Pareto Chart')

    for idx, (key, value) in enumerate(kappa_scale.items()):
        plt.text(0, -0.07 - 0.025 * idx, f'{key}: {value}', transform=plt.gca().transAxes, fontsize=9)      
        
    plt.subplots_adjust(bottom=0.2)        
    
    plt.savefig(f"static/{request.cookies.get('session')}.png",dpi=300)
    plt.close()  

def weighted_kappa(df,project_id):        
    
    techniques = get_techniques_names(project_id)
    final_weighted_kappa = []
    resultados_kappa = []
    mapping = {0.5: 2, 0.33: 3, 0.25: 4, 0.2: 5}

    for technique in techniques:
        columns_us = [f'us_{technique}_q{i}' for i in range(1, 9)]
        columns_ta = [f'ta_{technique}_q{i}' for i in range(1, 8)]
        df_us = df[columns_us]
        df_ta = df[columns_ta]
        df_values = df_us.join(df_ta)
        df_values = df_values.reset_index(drop=True)
        for avaliador1, avaliador2 in combinations(df_values.index, 2):
            kappa = cohen_kappa_score(df_values.iloc[avaliador1], df_values.iloc[avaliador2], weights='quadratic')
            resultados_kappa.append((f"Avaliador {avaliador1 + 1}", f"Avaliador {avaliador2 + 1}", kappa))
        df_kappa = pd.DataFrame(resultados_kappa, columns=["Avaliador 1", "Avaliador 2", "Kappa Ponderado"])
        final_weighted_kappa.append(df_kappa["Kappa Ponderado"].mean())
        
    return final_weighted_kappa

    