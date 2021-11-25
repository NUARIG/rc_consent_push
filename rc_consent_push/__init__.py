import os
import click
from flask import Flask, render_template, request, flash, current_app
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


    ##########
    # ROUTES #
    ##########

    # HOME: list of projects and STUs with their link outs for convenience

    @app.route("/")
    def index():
        from rc_consent_push import models
        myprojects = models.Project.query.order_by(models.Project.stu, models.Project.pid).all()
        return render_template('home.html', projects = myprojects)

    # Project administration

    @app.route("/project/new")
    def new_project():
        return render_template('newproject.html')

    @app.route('/project/add_confirm', methods = ['post'])
    def add_confirm_project():
        mystu = request.form.get('stu', None)
        mytoken = request.form.get('api_token', None)

        if not mystu or not mytoken:
            flash('Need both an STU # and an API TOKEN')
            return redirect(url_for('index'))

        from rc_consent_push import redcap,models

        # Check if the API token was already used. To enforce that project can only be associated with 1 STU#
        mycount = models.Project.query.filter(models.Project.api_token==mytoken).count()
        if mycount > 0: 
            flash(f'Cannot proceed; {mycount} projects already exist with this API Token', 'error')
            return redirect(url_for('index'))
        
        # Create a project object via REDCap call and populate with fetched attributes AND the STU#
        try:
            myproject = redcap.make_project_from_token( mytoken, mystu )
        except RuntimeError as e:
            flash(f'There was an error while using the API token to create a project: {e}', 'error')
            return redirect(url_for('index'))

        flash('Retrieved a project from REDCap')
        return render_template('addconfirmproject.html', project = myproject)

    @app.route("/project/add", methods = ['post'])
    def add_project():
        from rc_consent_push import redcap,models
        myproject = models.Project(
            pid = request.form.get('pid', None),
            stu = request.form.get('stu', None),
            project_title = request.form.get('project_title', None),
            api_token = request.form.get('api_token', None)
        )

        try: 
            db.session.add(myproject) 
            db.session.commit()
        except RuntimeError as e:
            flash(f'Could not commit project {myproject.pid} into database','error')
            return redirect(url_for('index'))

        flash(f'Added project (pid={myproject.pid}, stu={myproject.stu}) to DB')
        return redirect(url_for('index'))

    # Studies


    ##################
    # Shell commands #
    ##################
    
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


    ###########

    return app
