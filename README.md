# xaiselector
Decision support system to evaluate the adaptation of XAI techniques and a given context

The XAI Selector application is a prototype built to facilitate the evaluation of different explanations, provided by a set of pre-defined XAI methods, by a group of end users. This application is the result of an experimental academic project, and the code provided is a prototype created to validate the concept, although it is fully functional. The application was implemented using the Python language and the Flask web framework. Some conventions must be followed in order to make the prototype work correctly. No functionalities have been implemented to control these conventions in this first version of the prototype, therefore the prototype can only work correctly if the conventions listed below are strictly followed:

IMPORTANT: You can access the software available at https://www.xaiselector.com and view the experiment data using the user contact@xaiexplained.com and the password 'senha'. You can also use the code UMX971 in the Access Survey field to view the user data collection screen. The application is fully functional and you can carry out your own experiments by registering a new user on the main page. To do this, follow the instructions below:

1) For each of the XAI methods evaluated, there should be a questionnaire for assessing satisfaction with the explanations and another for assessing the trust in the model after the explanations have been presented.


2) The evaluation process requires at least two XAI methods.


3) A demographic form should be created, which must include a single question about the seniority of the participants. This question must have the seniority field selected in the application interface.


4) A form should also be created to collect the user trust ratings in the system before providing any explanations.


5) The questions (q) in the questionnaire of trust before the explanations (tb) should follow the writing convention tb_q1, tb_q2, etc.


6) The questions (q) in the questionnaire of trust after the explanations (ta) should follow the writing convention ta_technique_q1, e.g. ta_LIME_q1, ta_LIME_q2, etc.


7) The questions (q) in the questionnaire of user satisfaction with the explanations (us) should follow the writing convention us_technique_q1, e.g. us_LIME_q1, us_LIME_q2 etc.


8) The technique field in the confidence and satisfaction forms must match the name of the technique in the form variables. Ex: us_Decision_q1


9) The application is implemented to support satisfaction and trust questionnaires with a five-point Likert scale, with normal questions having options with values from 1 to 5 and inverted questions having values of 1, 0.5, 0.33, 0.25 and 0.2.


10) The 'generate default project' functionality will only work if the backup of the database provided is recovered.


11) There is a feature on the main page of the application, 'create user', which is not available on the web, but only in the source code. Without this functionality it is not possible to create experiments.


12) To create an experiment, please register a user and access the application through it. This will give you access to the experiment management module.


Please, when accessing the application on the web, use the logout functionality to exit the application. Do not simply close the browser. This ensures that the files generated during access are removed from the server, avoiding unnecessary disk space consumption.
We do not guarantee to provide any kind of support, but you can contact the developer of the tool and first author of the work via e-mail at mindior@gmail.com.
We will be very pleased to hear from you if you report any inconsistencies in the prototype.

