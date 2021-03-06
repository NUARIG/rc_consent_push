import os
import click
from flask import Flask, render_template, request, flash, current_app, abort
from flask import url_for, redirect 

from flask_bootstrap import Bootstrap

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='postgresql://localhost/rccp',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        LOGGING_LEVEL='DEBUG',
        REDCAP_URL='https://redcap.nubic.northwestern.edu/api/'
    )

    if test_config is None:
        app.config.from_pyfile('application.cfg', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    Bootstrap(app)
    db.init_app(app)
    toolbar.init_app(app)


    ######################
    # ROUTES and Actions #
    ######################

    #####################################################
    # Backend project configuration and admin functions #
    #####################################################

    @app.route("/")
    def index():
        from rc_consent_push import models
        mystmt = db.select( models.Project ).order_by(models.Project.stu, models.Project.pid)
        myprojects = db.session.execute( mystmt ).scalars() #use scalars so it's a container of objects not container of rows - a python SQLAlchemy thing
        return render_template('home.html', projects = myprojects)

    @app.route("/project/new")
    def new_project():
        return render_template('newproject.html')

    @app.route('/project/add_confirm', methods = ['post'])
    def add_confirm_project():
        mystu = request.form.get('stu', None)
        mytoken = request.form.get('api_token', None)

        if not mystu or not mytoken:
            flash('Need both an STU # and an API TOKEN','error')
            return redirect(request.referrer)

        from rc_consent_push import redcap,models

        # Check if the API token was already used. To enforce that project can only be associated with 1 STU#
        mycount = models.Project.query.filter(models.Project.api_token==mytoken).count()
        if mycount > 0: 
            flash(f'Cannot proceed; {mycount} projects already exist with this API Token', 'error')
            return redirect(request.referrer)
        
        # Create a project object via REDCap call and populate with fetched attributes AND the STU#
        try:
            myproject = redcap.make_project_from_token( mytoken, mystu )
        except RuntimeError as e:
            flash(f'There was an error while using the API token to create a project: {e}', 'error')
            return redirect(request.referrer)

        flash('Retrieved a project from REDCap')
        return render_template('addconfirmproject.html', project = myproject)

    @app.route("/project/add", methods = ['post'])
    def add_project():
        from rc_consent_push import models
        myproject = models.Project(
            pid = request.form.get('pid', None),
            stu = request.form.get('stu', None),
            project_title = request.form.get('project_title', None),
            api_token = request.form.get('api_token', None),
            is_longitudinal = request.form.get('is_longitudinal', None),
            has_repeating_instruments_or_events = request.form.get('has_repeating_instruments_or_events', None),
            surveys_enabled = request.form.get('surveys_enabled', None)
        )

        try: 
            db.session.add(myproject) 
            db.session.commit()
        except RuntimeError as e:
            flash(f'Could not commit project {myproject.pid} into database','error')
            return redirect(url_for('index'))

        flash(f'Added project (pid={myproject.pid}, stu={myproject.stu}) to DB')
        return redirect(url_for('show_study_project', stu=myproject.stu, pid=myproject.pid))

    @app.route('/study/<stu>')
    def show_study(stu):
        from rc_consent_push import models
        mystmt = db.select(models.Project).where(models.Project.stu == stu)
        myresult = db.session.execute(mystmt).scalars().all()
        return render_template('study.html', stu = stu, projects = myresult)

    @app.route('/study/<stu>/project/<pid>')
    def show_study_project(stu, pid):
        from rc_consent_push import models,redcap
        mystmt = db.select(models.Project).where(models.Project.stu == stu, models.Project.pid == pid)
        myproject = db.session.execute(mystmt).scalar()
        if myproject is None:
            flash(f'could not find project = {pid} in study = {stu}')
            return redirect(url_for('index'))
        try: 
            select2_instrument_array = redcap.fetch_project_instruments_as_select2(myproject)
            select2_field_array = redcap.fetch_project_fields_as_select2(myproject)
        except RuntimeError as e:
            flash(f'Could not connect to REDCap to get the instrument list','error')
            return redirect(request.referrer)

        return render_template(
            'project.html', 
            project = myproject, 
            select2_instrument_array = select2_instrument_array,
            select2_field_array = select2_field_array)

    @app.route('/study/<stu>/project/<pid>/instrument/add', methods=['post'])
    def add_instrument(stu,pid):
        from rc_consent_push import models, redcap
        myproject = db.session.execute( db.select(models.Project).where(models.Project.pid == pid) ).scalar()
        if myproject.stu != stu:
            flash('The STU # and Project ID are not associated.', 'error')
            return redirect(request.referrer)
        myinstrument_name = request.form.get('instrument_name', None)
        myconsent_date_var = request.form.get('consent_date_var', None)
        mycase_number_var = request.form.get('case_number_var', None)

        if not stu or not pid or not myinstrument_name or not mycase_number_var or not myconsent_date_var:
            flash('All instrument information are required', 'error')
            return redirect(request.referrer)
        
        try: 
            all_project_instruments = redcap.fetch_project_instruments(myproject)
        except RuntimeError as e:
            flash('There was an error connecting to REDCap to fetch instrument information','error')
            return redirect(request.referrer)

        myinstrument = None
        for project_instrument in all_project_instruments:
            if project_instrument.instrument_name == myinstrument_name:
                myinstrument = project_instrument
                break

        if myinstrument is None:
            flash(f'The instrument name you provided {myinstrument_name} does not exist in the project', 'error')
            return redirect(request.referrer)

        myinstrument.case_number_var = mycase_number_var
        myinstrument.consent_date_var = myconsent_date_var

        try:
            db.session.add(myinstrument)
            db.session.commit()
        except Exception as e:
            flash(f'Could not save instrument {myinstrument.instrument_name} to project {myinstrument.pid} most likely because the instrument was already saved before.')
            return redirect(request.referrer)

        flash(f'Added instrument ({myinstrument.instrument_name}) to project ({myinstrument.pid})')
        return redirect(url_for('show_study_project', pid = pid, stu = stu))

    ############################
    # Shell commands for Setup #
    ############################
    
    @app.cli.command('dropdb')
    def dropdb():
        from rc_consent_push import models
        click.echo('Dropping Database...')
        db.drop_all()

    @app.cli.command('initdb')
    def initdb():
        from rc_consent_push import models
        click.echo('Initializing Database...')
        db.create_all()


    ##############################
    # Landing routes from REDCap #
    ##############################

    @app.route('/redcap/push/s', methods = ['get'])
    def redcap_simple():
        # We will probably not use this. Kept here as demo of what simple link does.
        return render_template('simplebookmark.html')

    @app.route('/redcap/push/a', methods = ['post'])
    def redcap_advanced():
        from rc_consent_push import redcap,models
        myauthkey = request.form.get('authkey', None)

        # Send a 401 Unauthorized if the token is a dud 
        if myauthkey is None:
            abort(401)
        try:
            my_advanced_link_info = redcap.fetch_advanced_link_info(myauthkey)
        except RuntimeError as e:
            abort(401)

        # RECORD and EVENT are appended to the URL not part of the authkey-mediated info
        my_advanced_link_info['get_record'] = request.args.get('record', None)
        my_advanced_link_info['get_event'] = request.args.get('event', None)

        # Check if the project referenced is registered in the system and associated with a study
        # If not registered then Send a 401 Unauthorized error or recover gracefully in CTMS
        myproject = db.session.execute( db.select(models.Project).where(models.Project.pid == my_advanced_link_info['project_id']) ).scalar()
        if myproject is None:
            abort(401)

        # Should probably kick them out if the username (i.e. netid) is not allowed in the study
        # def check_apl_or_something_in_CTMS( myresponse['username'], myproject.stu ) --> True|False
        # (Not done here)

        if my_advanced_link_info['get_record'] is None:
            flash('did not pass a record id, no further action taken to fetch records', 'warning')
            myrecords = None
        else:
            myrecords = redcap.fetch_advanced_link_records(myproject, my_advanced_link_info)

        return render_template('advanced_landing_select.html', redcap_response = my_advanced_link_info, redcap_project = myproject, redcap_records = myrecords)

    ##################################################################
    # Needed last step as all this above was an app factory function #
    ##################################################################

    return app
